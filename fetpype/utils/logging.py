import os
import sys
import logging
import time
from nipype import config
from nipype import logging as nlogging
from nipype.interfaces.base import CommandLine
import subprocess

# Use Nipype's concurrent rotating handler if available (multi-proc safe)
try:
    from nipype.external.cloghandler import (
        ConcurrentRotatingFileHandler as RFH,
    )
except Exception:
    from logging.handlers import RotatingFileHandler as RFH

_start_times = {}


class StdToLogger:
    """Redirect a stream (stdout/stderr) into a logger (line-buffered).

    Args:
        logger (logging.Logger): The logger to which the stream will
            be redirected.
        level (int): The logging level (e.g., logging.INFO, logging.ERROR).

    """

    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self._buf = ""

    def write(self, s):
        if not s:
            return
        s = s.replace("\r\n", "\n")
        parts = (self._buf + s).split("\n")
        for line in parts[:-1]:
            if line:
                self.logger.log(self.level, line)
        self._buf = parts[-1]

    def flush(self):
        if self._buf:
            self.logger.log(self.level, self._buf)
            self._buf = ""


def setup_logging(
    base_dir,
    debug=False,
    verbose=False,
    capture_prints=True,
    container_logger_name="nipype.container",
):
    """
    Set up logging for the Nipype workflow.
    Ensures the possibility of limited console output
    while providing detailed logging to a file.

    Args:
        base_dir (str): The base directory for the workflow.
        debug (bool): Enable debug logging.
            Logging to <log_file> will be at the DEBUG level.
        verbose (bool): Enable verbose logging. Logging level to
            console will be set to INFO if `debug` is `False` and
            to DEBUG if `debug` is `True`.
        capture_prints (bool): Capture print statements.
        container_logger_name (str): The name of the container logger.

    """
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "pypeline.log")
    try:
        os.remove(log_file)  # start fresh each run
    except FileNotFoundError:
        pass

    file_level = "DEBUG" if debug else "INFO"

    # Effective console level when verbose
    to_console = (
        "DEBUG" if (verbose and debug) else "INFO" if verbose else "ERROR"
    )

    # Tell Nipype to log to file
    config.update_config(
        {
            "logging": {
                "log_to_file": True,
                "log_directory": log_dir,
                "log_size": str(50 * 1024 * 1024),
                "log_rotate": "5",
                "workflow_level": file_level,
                "interface_level": file_level,
                "utils_level": file_level,
            },
            "execution": {
                "crashdump_dir": log_dir,  # ← fixed key name
                "crashfile_format": "txt",
            },
        }
    )
    nlogging.update_logging(config)

    # Parent 'nipype' console handler → quiet or verbose
    nipype_root = logging.getLogger("nipype")
    for h in list(nipype_root.handlers):
        if isinstance(h, logging.StreamHandler) and not isinstance(
            h, logging.FileHandler
        ):
            h.setLevel(getattr(logging, to_console))
            h.setFormatter(logging.Formatter("%(message)s"))
            h.stream = sys.__stdout__

    # Plain-lines logger to the SAME file (no header per line)
    container_log = logging.getLogger(container_logger_name)
    container_log.setLevel(getattr(logging, file_level))
    container_log.propagate = False  # don't bubble into 'nipype' handlers

    # Ensure we have exactly one rotating file handler to pypeline.log
    if not any(
        isinstance(h, RFH) and getattr(h, "baseFilename", None) == log_file
        for h in container_log.handlers
    ):
        ch = RFH(log_file, maxBytes=50 * 1024 * 1024, backupCount=5)
        ch.setLevel(getattr(logging, file_level))
        ch.setFormatter(logging.Formatter("%(message)s"))  # no header
        container_log.addHandler(ch)

    # In verbose mode, also mirror container lines to the console
    if verbose and not any(
        isinstance(h, logging.StreamHandler) for h in container_log.handlers
    ):
        sh = logging.StreamHandler(stream=sys.__stdout__)
        sh.setLevel(getattr(logging, to_console))  # INFO or DEBUG
        sh.setFormatter(logging.Formatter("%(message)s"))
        container_log.addHandler(sh)

    # Route print()/tracebacks to the Nipype workflow logger (file) if desired
    if capture_prints:
        nipype_workflow_log = logging.getLogger("nipype.workflow")
        nipype_workflow_log.propagate = True
        sys.stdout = StdToLogger(nipype_workflow_log, logging.INFO)
        sys.stderr = StdToLogger(nipype_workflow_log, logging.ERROR)

    # Where Nipype interfaces send their stdout/stderr
    # - verbose=True  → stream to terminal
    # - verbose=False → save to stdout.nipype / stderr.nipype in node workdirs
    CommandLine.set_default_terminal_output("stream" if verbose else "file")

    logging.captureWarnings(True)

    def _excepthook(exc_type, exc, tb):
        logging.getLogger("nipype.workflow").error(
            "Uncaught exception", exc_info=(exc_type, exc, tb)
        )
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _excepthook


def status_line(node, status, **_):
    """
    Print the status line for a Nipype node.

    Args:
        node: The Nipype node.
        status: The status of the node (e.g., "start", "end", "exception").
    """
    out = sys.__stdout__
    name = getattr(node, "fullname", str(node))

    if status == "start":
        _start_times[name] = time.time()
        print(f"▶ {name}", file=out, flush=True)
    elif status == "end":
        dt = max(time.time() - _start_times.get(name, time.time()), 0)
        print(f"✔ {name} ({dt:.1f}s)", file=out, flush=True)
    elif status == "exception":
        print(f"✖ {name} failed (see crashfile & logs)", file=out, flush=True)


def run_and_tee(cmd, *, prefix=""):
    """
    Run a command, stream output live to terminal, and log every line.
    Returns the full combined output; raises RuntimeError on non-zero exit.

    Args:
        cmd (str): The command to run.
        prefix (str): A prefix to add to each line of output.

    Returns:
        str: The combined output of the command.
    """

    log_plain = logging.getLogger("nipype.container")  # message-only
    log_evt = logging.getLogger("nipype.workflow")  # structured events

    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")  # flush Python in container
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("TQDM_DISABLE", "1")  # avoid CR-based progress bars

    proc = subprocess.Popen(
        cmd,
        shell=True,  # keep if you're passing a single string
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # merge stderr -> stdout
        text=True,
        bufsize=1,  # line-buffered
        env=env,
    )

    log_evt.info("Running: %s", cmd)  # one structured line

    captured = []
    for line in proc.stdout:
        line = line.rstrip("\n")
        captured.append(line)
        log_plain.info("%s%s", prefix, line)  # file: plain line
        sys.__stdout__.write(prefix + line + "\n")  # console: live
        sys.__stdout__.flush()

    proc.stdout.close()
    rc = proc.wait()
    output = "".join(captured)

    if rc != 0:
        raise RuntimeError(
            f"Docker call failed with exit code {rc}.\n"
            f"Command: {cmd}\n"
            f"Output:\n{output.strip() or '<<no output>>'}"
        )

    return output

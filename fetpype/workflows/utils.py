import argparse
import hydra
import os
from omegaconf import OmegaConf


def get_default_parser(desc):

    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument(
        "--data",
        type=str,
        required=True,
        help=(
            "BIDS-formatted directory containing anatomical "
            "fetal brain MRI scans"
        ),
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help=(
            "Output directory, where all outputs will be saved. "
            "Formatted as <out>/derivatives/pipeline_name."
        ),
    )

    parser.add_argument(
        "--nipype_dir",
        type=str,
        required=False,
        help=(
            "Directory, where the nipype processing will be saved. "
            "(default: <out>/nipype/pipeline_name)"
        ),
    )
    parser.add_argument(
        "--subjects",
        "-sub",
        dest="sub",
        type=str,
        nargs="+",
        required=False,
        help=(
            "List of subjects to process (default: every subject in the "
            "data directory)."
        ),
    )
    parser.add_argument(
        "--sessions",
        "-ses",
        dest="ses",
        type=str,
        nargs="+",
        required=False,
        help=(
            "List of sessions to process (default: every session for each "
            "subject)."
        ),
    )
    parser.add_argument(
        "--acquisitions",
        "-acq",
        dest="acq",
        type=str,
        nargs="+",
        default=None,
        help=(
            "List of acquisitions to process (default: every acquisition for "
            "each subject/session combination)."
        ),
    )

    parser.add_argument(
        "--config",
        dest="cfg_path",
        default="../configs/default_docker.yaml",
        type=str,
        help=(
            "Parameters yaml file specifying the parameters, containers and "
            "functions to be used in the pipeline."
        ),
    )
    parser.add_argument(
        "--nprocs",
        dest="nprocs",
        type=int,
        default=1,
        help="Number of processes to allocate.",
        required=False,
    )

    parser.add_argument(
        "--save_intermediates",
        dest="save_intermediates",
        action="store_true",
        help="Save intermediate files.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode.",
        default=False,
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose mode. "
        "Console will show INFO (or DEBUG if --debug is set) "
        "messages. By default, only a minimal output is shown, "
        "the rest is logged at <nipype_dir>/logs/pypeline.log",
        default=False,
    )
    return parser


def get_pipeline_name(cfg, only_rec=False, only_seg=False, only_surf=False):
    """
    Get the pipeline name from the configuration file.
    Args:
        cfg: Configuration object.
    Returns:
        str: Pipeline name.
    """
    pipeline_name = []
    # Assert only one only_<type> flag is set at once
    assert (
        sum([only_rec, only_seg, only_surf]) <= 1
    ), "Only one of only_rec, only_seg, or only_surf can be True."
    if "reconstruction" in cfg and (not only_seg) and (not only_surf):
        pipeline_name += [cfg.reconstruction.pipeline]
    if "segmentation" in cfg and (not only_rec) and (not only_surf):
        pipeline_name += [cfg.segmentation.pipeline]
    if "surface" in cfg and (not only_rec) and (not only_seg):
        pipeline_name += [cfg.surface.pipeline]
    return "_".join(pipeline_name)


def init_and_load_cfg(cfg_path):
    """
    Initialize and load the configuration file.
    Args:
        cfg_path (str): Path to the configuration file.
    Returns:
        cfg: Loaded configuration.
    """
    # Get the path to this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.abspath(cfg_path)
    cfg_path = os.path.relpath(cfg_path, current_dir)
    cfg_dir = os.path.dirname(cfg_path)
    cfg_file = os.path.basename(cfg_path)

    # Transform the path into a relative
    with hydra.initialize(config_path=cfg_dir, version_base="1.2"):
        cfg = hydra.compose(config_name=cfg_file)
    print(OmegaConf.to_yaml(cfg))
    return cfg


def check_and_update_paths(data_dir, out_dir, nipype_dir, pipeline_name):
    """
    Check and update the paths for data_dir, out_dir, and nipype_dir.
    Args:
        data_dir (str): Path to the BIDS directory.
        out_dir (str): Path to the output directory.
        nipype_dir (str): Path to the nipype directory.
        pipeline_name (str): Name of the pipeline.
    Returns:
        tuple: Updated paths for data_dir, out_dir, and nipype_dir.
    """

    data_dir = os.path.abspath(data_dir)

    assert os.path.exists(data_dir), f"Error {data_dir} should be a valid dir"

    if out_dir is None:
        out_dir = data_dir

    if nipype_dir is None:
        nipype_dir = out_dir

    # derivatives
    out_dir = os.path.join(os.path.abspath(out_dir),
                           "derivatives", pipeline_name)

    os.makedirs(out_dir, exist_ok=True)

    # working directory
    nipype_dir = os.path.join(os.path.abspath(nipype_dir), "nipype")

    os.makedirs(nipype_dir, exist_ok=True)

    return data_dir, out_dir, nipype_dir


def check_valid_pipeline(cfg):
    """
    Check if the pipeline is valid.
    Args:
        cfg: Configuration object.
    """
    from fetpype import VALID_RECONSTRUCTION, VALID_SEGMENTATION, VALID_SURFACE

    if "reconstruction" in cfg:
        if cfg.reconstruction.pipeline not in VALID_RECONSTRUCTION:
            raise ValueError(
                f"Invalid reconstruction pipeline: "
                f"{cfg.reconstruction.pipeline}"
                f"Please choose one of {VALID_RECONSTRUCTION}"
            )
    if "segmentation" in cfg:
        if cfg.segmentation.pipeline not in VALID_SEGMENTATION:
            raise ValueError(
                f"Invalid segmentation pipeline: {cfg.segmentation.pipeline}."
                f"Please choose one of {VALID_SEGMENTATION}"
            )

    if "surface" in cfg:
        if cfg.surface.pipeline not in VALID_SURFACE:
            raise ValueError(
                f"Invalid surface pipeline: {cfg.surface.pipeline}."
                f"Please choose one of {VALID_SURFACE}"
            )

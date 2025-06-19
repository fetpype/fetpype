# Given a config file, check if the docker model is available
from collections import defaultdict
import subprocess
import sys


def flatten_cfg(cfg, base=""):
    """
    Flatten a nested configuration dictionary into a flat dictionary
    with keys as paths and values as the corresponding values.
    Args:
        cfg (dict): The configuration dictionary to flatten.
        base (str): The base path to prepend to the keys.
    Returns:
        generator: A generator that yields tuples of (path, value).
    """
    for k, v in cfg.items():
        if isinstance(v, dict):
            yield from flatten_cfg(v, "/".join([base, k]))
        else:
            yield ("/".join([base, k]), v)


def is_available_container(container_type, container_name):
    """
    Check if the container is available on the system.
    Args:
        container_type (str):   The type of container, either 'docker'
                                or 'singularity'
        container_name (str): The name of the container to check.
    Returns:
        bool: True if the container is available, False otherwise.
    """
    if container_type == "docker":
        try:
            subprocess.run(
                [container_type, "inspect", container_name],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError:
            return False
        else:
            return True
    elif container_type == "singularity":
        if os.path.isfile(container_name):
            return True
        else:
            return False
    else:
        raise ValueError(
            f"Container type {container_type} not supported. "
            "Please use 'docker' or 'singularity'."
        )


def retrieve_container(container_type, container_name):
    """
        Retrieve the container from the registry.
    Args:
        container_type (str):   The type of container, either 'docker' or
                                'singularity'
        container_name (str): The name of the container to retrieve.

    """
    if container_type == "docker":

        cmd = [container_type, "pull", container_name]
        print(f"Running {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for line in process.stdout:
            print(line, end="")

        process.wait()
        if process.returncode != 0:
            for line in process.stderr:
                print(line, end="")
            raise subprocess.CalledProcessError(
                process.returncode,
                cmd,
                output=process.stdout.read(),
                stderr=process.stderr.read(),
            )
    elif container_type == "singularity":
        raise NotImplementedError
    else:
        raise ValueError(
            f"Container type {container_type} not supported. "
            "Please use 'docker' or 'singularity'."
        )


def check_container_commands(container_type, cfg):
    """
    Check if the required docker or singularity images are available
    on the system.

    Args:
        container_type (str):   The type of container, either 'docker' or
                                'singularity'
        cfg (dict): The configuration dictionary containing the
                    container names.

    """
    # Check if the container_type is valid
    if container_type not in ["docker", "singularity"]:
        raise ValueError(
            f"Container type {container_type} not supported. "
            "Please use 'docker' or 'singularity'."
        )

    # Iterate the nested config dictionary
    cfg_dict = dict(flatten_cfg(cfg))
    container_names = {}
    for k, v in cfg_dict.items():
        # Return the word that is after the <mount> tag in the string v
        if container_type == "docker" and "docker" in k:
            docker_name = v.split("<mount>")[-1].split()[0]
            container_names[k] = docker_name
        elif container_type == "singularity" and "singularity" in k:
            # Find a string that ends with .sif
            if v is None:
                continue
            print("CHECKING PATH IN", k, v)
            singularity_name = [s for s in v.split(" ") if s.endswith(".sif")][
                0
            ]
            container_names[k] = singularity_name

    container_names_list = defaultdict(list)
    for k, v in container_names.items():
        container_names_list[v].append(k)

    # Check which containers are missing
    missing_containers = []
    for k, v in container_names_list.items():
        print(f"Checking {container_type} {k} -- Used by {', '.join(v)}")
        if not is_available_container(container_type, k):
            print("\tSTATUS: NOT FOUND")
            missing_containers.append(k)
        else:
            print("\tSTATUS: AVAILABLE")

    # Retrieve the missing containers
    if len(missing_containers) > 0 and container_type == "docker":
        var = input(
            f"Would you like me to retrieve the missing containers "
            f"{', '.join(missing_containers)}? (y/n) "
        )
        if var == "y":
            for k in missing_containers:
                retrieve_container(container_type, k)

        else:
            print("Exiting...")
            sys.exit(1)
    elif len(missing_containers) > 0 and container_type == "singularity":
        raise NotImplementedError(
            "Automated container retrieval for singularity is "
            "not implemented yet."
        )
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description=(
            "Given a cfg path, check if the docker model is available."
        )
    )
    parser.add_argument(
        "--cfg",
        type=str,
        required=True,
        help="Path to the config file",
    )
    args = parser.parse_args()
    # Load hydra config and convert it as a dict
    from omegaconf import OmegaConf
    from workflows.utils import init_and_load_cfg

    # hydra load nested config file
    print(os.getcwd())
    cfg = init_and_load_cfg(args.cfg)
    cfg = OmegaConf.to_container(cfg, resolve=True)

    check_container_commands("singularity", cfg)

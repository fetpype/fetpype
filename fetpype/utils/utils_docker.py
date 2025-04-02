# Given a config file, check if the docker model is available


def flatten_cfg(cfg, base=""):
    for k, v in d.items():
        if isinstance(v, dict):
            yield from flatten_cfg(v, " ".join([base, k]))
        else:
            yield (" ".join(base,k),v)

def check_container_commands(container_type, cfg):
    """
    Check if the docker model is available.
    """
    # The config is like a nested namespace, iterate it and find all the keys matching container_type
    # Check if the container_type is valid
    if container_type not in ["docker", "singularity"]:
        raise ValueError(
            f"Container type {container_type} not supported. "
            "Please use 'docker' or 'singularity'."
        )
    # Iterate the nested config dictionary
    cfg_dict = dict(flatten_cfg(cfg))
        



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

    # Load hydra config and convert it as a dict
    from omegaconf import OmegaConf
    from omegaconf import DictConfig
    cfg = OmegaConf.load(args.cfg)
    cfg = OmegaConf.to_container(cfg, resolve=True)

    check_container_commands("docker", cfg)
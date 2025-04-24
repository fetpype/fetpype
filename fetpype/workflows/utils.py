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
        help=(
            "Output directory, where all outputs will be saved. "
            "(default: <data>/derivatives/<out>/pipeline_name)"
        ),
    )

    parser.add_argument(
        "--nipype_dir",
        type=str,
        help=(
            "Directory, where the nipype processing will be saved. "
            "(default: nipype/ on the same folder as the data directory)"
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
            "List of subjects to process (default: every subject in the"
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

    return parser


def get_pipeline_name(cfg):
    """
    Get the pipeline name from the configuration file.
    Args:
        cfg: Configuration object.
    Returns:
        str: Pipeline name.
    """
    pipeline_name = []
    if "reconstruction" in cfg:
        pipeline_name += [cfg.reconstruction.pipeline]
    if "segmentation" in cfg:
        pipeline_name += [cfg.segmentation.pipeline]

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


def check_and_update_paths(data_dir, out_dir, nipype_dir, cfg):
    """
    Check and update the paths for data_dir, out_dir, and nipype_dir.
    Args:
        data_dir (str): Path to the BIDS directory.
        out_dir (str): Path to the output directory.
        nipype_dir (str): Path to the nipype directory.
        cfg: Configuration object.
    Returns:
        tuple: Updated paths for data_dir, out_dir, and nipype_dir.
    """
    data_dir = os.path.abspath(data_dir)

    if out_dir is None:
        out_dir = os.path.join(data_dir, "derivatives", get_pipeline_name(cfg))
    else:
        out_dir = os.path.join(
            os.path.abspath(out_dir), get_pipeline_name(cfg)
        )

    try:
        os.makedirs(out_dir)
    except OSError:
        print("out_dir {} already exists".format(out_dir))
    if nipype_dir is None:
        # Get parent directory of data_dir
        parent_dir = os.path.dirname(data_dir)
        nipype_dir = os.path.join(parent_dir, "nipype")
    else:
        nipype_dir = os.path.abspath(nipype_dir)

    os.makedirs(nipype_dir, exist_ok=True)

    return data_dir, out_dir, nipype_dir


def check_valid_pipeline(cfg):
    """
    Check if the pipeline is valid.
    Args:
        cfg: Configuration object.
    """
    from fetpype import VALID_RECONSTRUCTION, VALID_SEGMENTATION

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

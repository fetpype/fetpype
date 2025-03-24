#!/usr/bin/env python3
"""
Human fetal anatomical segmentation pipeline

Adapted in Nipype from an original pipeline of Alexandre Pron by David
Meunier.

parser, params are derived from macapype pipeline

Description
--------------
TODO :/

Arguments
-----------
-data
    Path to the BIDS directory that contain subjects' MRI data.

-out
    Nipype's processing directory.
    It's where all the outputs will be saved.

-sub
    IDs list of subjects to process.

-ses
    session (leave blank if None)

-acq [optional]
    type of acquisition (e.g. haste or trufisp)

-params
    json parameter file; leave blank if None

Example
---------
python pipeline_fet.py -data [PATH_TO_BIDS] -out ../local_tests/ -subjects
Elouk

Requirements
--------------
This workflow use:
    - ANTS (denoise)
    - nifyimic
"""

# Authors : David Meunier (david.meunier@univ-amu.fr)
#           Alexandre Pron (alexandre.pron@univ-amu.fr)
import os
import json
import argparse
import nipype.pipeline.engine as pe
import os.path as op

from fetpype.pipelines.full_pipeline import (
    create_fet_subpipes,
)


from fetpype.utils.utils_bids import (
    create_datasource,
    create_datasink,
    create_description_file,
)
import hydra
from omegaconf import OmegaConf

###############################################################################

__file_dir__ = os.path.dirname(os.path.abspath(__file__))


def create_main_workflow(
    data_dir,
    process_dir,
    subjects,
    sessions,
    acquisitions,
    cfg_path,
    nprocs,
    wf_name="fetpype",
    bids=False,
):
    """
    Create the main workflow of the fetpype pipeline.

    Params:
        data_path: pathlike str
            Path to the BIDS directory that contains anatomical images

        process_dir: pathlike str
            Path to the ouput directory (will be created if not alredy
            existing). Previous outputs maybe overwritten.

        subjects: list of str (optional)
            Subject's IDs to match to BIDS specification (sub-[SUB1],
            sub-[SUB2]...)

        sessions: list of str (optional)
            Session's IDs to match to BIDS specification (ses-[SES1],
            ses-[SES2]...)

        acquisitions: list of str (optional)
            Acquisition name to match to BIDS specification (acq-[ACQ1]...)

        params_file: path to a JSON file
            JSON file that specify some parameters of the pipeline.

        nprocs: integer
            number of processes that will be launched by MultiProc

    Returns:
        workflow: nipype.pipeline.engine.Workflow
    """

    # formating args
    data_dir = op.abspath(data_dir)

    try:
        os.makedirs(process_dir)
    except OSError:
        print("process_dir {} already exists".format(process_dir))

    # params
    cfg_path = op.abspath(cfg_path)
    cfg_path = os.path.relpath(cfg_path, __file_dir__)
    cfg_dir = os.path.dirname(cfg_path)
    cfg_file = os.path.basename(cfg_path)

    # Transform the path into a relative
    # assert op.exists(cfg_path), f"Error with file {cfg_path}"
    with hydra.initialize(config_path=cfg_dir):
        cfg = hydra.compose(config_name=cfg_file)
    # Show the configuration
    print(OmegaConf.to_yaml(cfg))

    # params = json.load(open(params_file))

    # if general, pipeline is not in params ,create it and set it to niftymic

    # main_workflow
    main_workflow = pe.Workflow(name=wf_name)
    main_workflow.base_dir = process_dir
    if cfg.reconstruction.pipeline in [
        "niftymic",
        "nesvor",
        "svrtk",
    ] and cfg.segmentation.pipeline in ["bounti"]:
        fet_pipe = create_fet_subpipes(cfg)

    output_query = {
        "stacks": {
            "datatype": "anat",
            "suffix": "T2w",
            "extension": ["nii", ".nii.gz"],
        }
    }

    # datasource
    datasource = create_datasource(
        output_query,
        data_dir,
        subjects,
        sessions,
        acquisitions,
    )

    # in both cases we connect datsource outputs to main pipeline
    main_workflow.connect(datasource, "stacks", fet_pipe, "inputnode.stacks")

    # DataSink

    pipeline_name = cfg.reconstruction.pipeline
    datasink_path = os.path.join(data_dir, "derivatives")

    # Create directory if not existing
    os.makedirs(os.path.join(datasink_path, pipeline_name), exist_ok=True)

    # Create json file to make it BIDS compliant if doesnt exist
    # Eventually, add all parameters to the json file
    create_description_file(
        os.path.join(datasink_path, pipeline_name), pipeline_name
    )

    params_regex_subs = cfg.regex_subs if "regex_subs" in cfg.keys() else {}
    params_subs = cfg.rsubs if "subs" in cfg.keys() else {}

    # Create datasink
    datasink = create_datasink(
        iterables=datasource.iterables,
        name=f"datasink_{pipeline_name}",
        params_subs=params_subs,
        params_regex_subs=params_regex_subs,
    )
    datasink.inputs.base_directory = datasink_path

    pipeline_name2 = (
        cfg.reconstruction.pipeline + "_" + cfg.segmentation.pipeline
    )
    os.makedirs(os.path.join(datasink_path, pipeline_name2), exist_ok=True)

    datasink2 = create_datasink(
        iterables=datasource.iterables,
        name=f"datasink_{pipeline_name2}",
        params_subs=params_subs,
        params_regex_subs=params_regex_subs,
    )
    datasink2.inputs.base_directory = datasink_path
    # Add the base directory

    # Connect the pipeline to the datasink
    main_workflow.connect(
        fet_pipe, "outputnode.output_srr", datasink, pipeline_name
    )
    main_workflow.connect(
        fet_pipe, "outputnode.output_seg", datasink2, pipeline_name2
    )

    if cfg.save_graph:
        main_workflow.write_graph(
            dotfilename="graph.dot",
            graph2use="colored",
            format="png",
            simple_form=True,
        )

    main_workflow.config["execution"] = {"remove_unnecessary_outputs": "false"}

    main_workflow.run(plugin="MultiProc", plugin_args={"n_procs": nprocs})


def main():
    # Command line parser
    parser = argparse.ArgumentParser(
        description="Run the entire Fetpype pipeline -- pre-processing, reconstruction and segmentation"
    )

    parser.add_argument(
        "--data",
        dest="data",
        type=str,
        required=True,
        help=(
            "BIDS-formatted directory containing anatomical fetal brain MRI scans"
        ),
    )
    parser.add_argument(
        "--out",
        dest="out",
        type=str,
        required=True,  # nargs='+',
        help="Output directory, where all outputs will be saved.",
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
        default="../config/default.yaml",
        type=str,
        help=(
            "Parameters yaml file specifying the parameters, containers and "
            "functions to be used in the pipeline."
        ),
    )
    parser.add_argument(
        "-nprocs",
        dest="nprocs",
        type=int,
        default=4,
        help="Number of processes to allocate.",
        required=False,
    )

    args = parser.parse_args()

    # main_workflow
    print("Initialising the pipeline...")
    create_main_workflow(
        data_dir=args.data,
        process_dir=args.out,
        subjects=args.sub,
        sessions=args.ses,
        acquisitions=args.acq,
        cfg_path=args.cfg_path,
        nprocs=args.nprocs,
    )


if __name__ == "__main__":
    main()

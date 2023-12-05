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
    -data:
        Path to the BIDS directory that contain subjects' MRI data.

    -out:
        Nipype's processing directory.
        It's where all the outputs will be saved.

    -subjects:
        IDs list of subjects to process.

    -ses
        session (leave blank if None)

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
from fetpype.pipelines.full_pipelines import (
    create_fet_subpipes,
    create_minimal_subpipes,
)
from fetpype.pipelines.niftymic import create_niftymic_subpipes

from fetpype.utils.utils_bids import create_datasource

import os
import os.path as op
import json
import argparse
import nipype.pipeline.engine as pe

###############################################################################


def create_main_workflow(
    data_dir,
    process_dir,
    subjects,
    sessions,
    acquisitions,
    params_file,
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
    if params_file is None:
        params = {}

    else:
        # params
        assert op.exists(params_file), "Error with file {}".format(params_file)

        print("Using orig params file:", params_file)

        params = json.load(open(params_file))

    # if general, pipeline is not in params ,create it and set it to niftymic
    if "pipeline" not in params["general"]:
        params["general"]["pipeline"] = "minimal"

    # main_workflow
    main_workflow = pe.Workflow(name=wf_name)
    main_workflow.base_dir = process_dir
    if params["general"]["pipeline"] in ["niftymic", "nesvor"]:
        fet_pipe = create_fet_subpipes(params=params)
    elif params["general"]["pipeline"] == "minimal":
        fet_pipe = create_minimal_subpipes(params=params)
    elif params["general"]["pipeline"] == "niftymic_recon":
        fet_pipe = create_niftymic_subpipes(params=params)

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

    # check if the parameter general/no_graph exists and is set to True
    # added as an option, as graph drawing fails in UPF cluster
    if "no_graph" in params["general"] and params["general"]["no_graph"]:
        main_workflow.write_graph(graph2use="colored")

    main_workflow.config["execution"] = {"remove_unnecessary_outputs": "false"}

    if nprocs is None:
        nprocs = 4
    # main_workflow.run()
    main_workflow.run(plugin="MultiProc", plugin_args={"n_procs": nprocs})


def main():
    # Command line parser
    parser = argparse.ArgumentParser(description="PNH segmentation pipeline")

    parser.add_argument(
        "-data",
        dest="data",
        type=str,
        required=True,
        help="BIDS-formatted directory containing low-resolution T2w MRI scans.",
    )
    parser.add_argument(
        "-out",
        dest="out",
        type=str,
        required=True,  # nargs='+',
        help="Output directory, where all outputs will be saved.",
    )

    parser.add_argument(
        "-subjects",
        "-sub",
        dest="sub",
        type=str,
        nargs="+",
        required=False,
        help=(
            "List of subjects to process (default: all subjects in the"
            "data directory)."
        ),
    )
    parser.add_argument(
        "-sessions",
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
        "-acquisitions",
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
        "-params",
        dest="params_file",
        type=str,
        help=(
            "Parameters JSON file specifying the parameters, containers and "
            "functions to be used in the pipeline. For now, there is only "
            "compatibility with singularity and docker containers and "
            " niftymic/nesvor pipelines"
        ),
        required=True,
    )
    parser.add_argument(
        "-nprocs",
        dest="nprocs",
        type=int,
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
        params_file=args.params_file,
        nprocs=args.nprocs,
    )


if __name__ == "__main__":
    main()

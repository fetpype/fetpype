#!/usr/bin/env python3
"""
    Human fetal anatomical segmentation pipeline

    Adapted in Nipype from an original pipeline of Alexandre Pron by David
    Meunier.

    parser, params are derived from macapype pipeline

    Description
    --------------
    Base pipeline for running the dhcp pipeline (segmentation and
    surface extraction) from a
    superresolution reconstructed T2w image (nesvor of niftymic)

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
import os
import os.path as op
import json
import argparse
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as niu
from nipype.interfaces import fsl
from fetpype.pipelines.full_pipelines import (
    create_dhcp_subpipe,
)
from fetpype.utils.utils_bids import create_datasource, get_gestational_age

fsl.FSLCommand.set_default_output_type("NIFTI_GZ")

###############################################################################


def create_main_workflow(
    data_dir,
    process_dir,
    derivative,
    subjects,
    sessions,
    acquisitions,
    params_file,
    nprocs,
    wf_name="fetpype",
):
    """
    Create the main workflow of the fetpype pipeline.

    Params:
        data_path: pathlike str
            Path to the BIDS directory that contains anatomical images

        process_dir: pathlike str
            Path to the ouput directory (will be created if not alredy
            existing). Previous outputs maybe overwritten.

        derivative: str
            Name of the derivative which contains the reconstructions

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
        print(f"process_dir {process_dir} already exists")

    # params
    if params_file is None:
        params = {}

    else:
        # params
        assert op.exists(params_file), f"Error with file {params_file}"
        print("Using orig params file:", params_file)
        params = json.load(open(params_file, encoding="utf-8"))

    # main_workflow
    main_workflow = pe.Workflow(name=wf_name)
    main_workflow.base_dir = process_dir

    fet_pipe = create_dhcp_subpipe(params=params)
    output_query = {
        "T2": {
            "datatype": "anat",
            "suffix": "recon",
            "scope": derivative,
            "extension": ["nii", ".nii.gz"],
        },
        "mask": {
            "datatype": "anat",
            "suffix": "mask",
            "scope": derivative,
            "extension": ["nii", ".nii.gz"],
        },
    }

    # We need this for the datasource to find the derivatives
    index_derivative = True

    # datasource
    datasource = create_datasource(
        output_query,
        data_dir,
        subjects,
        sessions,
        acquisitions,
        index_derivative,
        derivative,
    )

    # Use fetpype utility to select the first T2 and the
    # first mask (ideally, there should only be one)
    # maybe not the best practice?
    # Create a Node for selecting the first element
    sl_t2 = pe.Node(niu.Select(), name="select_first_T2")
    sl_t2.inputs.index = [0]  # Select the first element
    main_workflow.connect(datasource, "T2", sl_t2, "inlist")
    main_workflow.connect(sl_t2, "out", fet_pipe, "inputnode.T2")

    sl_mask = pe.Node(niu.Select(), name="select_first_mask")
    sl_mask.inputs.index = [0]  # Select the first element
    main_workflow.connect(datasource, "mask", sl_mask, "inlist")
    main_workflow.connect(sl_mask, "out", fet_pipe, "inputnode.mask")

    # Create a node to get the gestational age
    gestational_age = pe.Node(
        interface=niu.Function(
            input_names=["bids_dir", "T2"],
            output_names=["gestational_age"],
            function=get_gestational_age,
        ),
        name="gestational_age",
    )

    main_workflow.connect(sl_t2, "out", gestational_age, "T2")
    gestational_age.inputs.bids_dir = data_dir

    # Connect the gestational age
    main_workflow.connect(
        gestational_age,
        "gestational_age",
        fet_pipe,
        "inputnode.gestational_age",
    )

    # check if the parameter general/no_graph exists and is set to True
    # added as an option, as graph drawing fails in UPF cluster
    if "no_graph" in params["general"] and params["general"]["no_graph"]:
        main_workflow.write_graph(graph2use="colored")

    main_workflow.config["execution"] = {"remove_unnecessary_outputs": "false"}

    if nprocs is None:
        nprocs = 4

    # commented for testing
    main_workflow.run()
    # main_workflow.run(plugin="MultiProc", plugin_args={"n_procs": nprocs})


def main():
    # Command line parser
    parser = argparse.ArgumentParser(description="dHCP segmentation pipeline")

    parser.add_argument(
        "-data",
        dest="data",
        type=str,
        required=True,
        help=(
            "BIDS-formatted directory containing low-resolution T2w MRI scans"
        ),
    )

    parser.add_argument(
        "-out",
        dest="out",
        type=str,
        required=True,  # nargs='+',
        help="Output directory, where all outputs will be saved.",
    )

    parser.add_argument(
        "-derivative",
        dest="derivative",
        type=str,
        required=True,  # nargs='+',
        help=(
            "Derivative inside the BIDS directory that contain"
            "reconstructions and their corresponding masks."
        ),
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
            " niftymic/nesvor pipelines, plus the dhcp pipeline."
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
        derivative=args.derivative,
        subjects=args.sub,
        sessions=args.ses,
        acquisitions=args.acq,
        params_file=args.params_file,
        nprocs=args.nprocs,
    )


if __name__ == "__main__":
    main()

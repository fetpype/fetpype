#!/usr/bin/env python3
"""
Human fetal anatomical segmentation pipeline

Adapted in Nipype from an original pipeline of Alexandre Pron by David
Meunier.

parser, params are derived from macapype pipeline

Description
--------------
Fetal MRI processing pipeline with BIDS-compliant inputs and outputs.
The pipeline performs brain extraction, reconstruction, and segmentation
of fetal MRI data in a BIDS-organized directory structure.

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

-save_intermediates
    When set, intermediate results from each processing step will
    be saved in BIDS-compatible format in the derivatives folder

Example
---------
python pipeline_fet.py -data [PATH_TO_BIDS] -out ../local_tests/ -subjects
Elouk -save_intermediates

Requirements
--------------
This workflow use:
    - ANTS (denoise)
    - nifyimic/nesvor/svrtk
    - dhcp/bounti for segmentation
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
    create_bids_datasink
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
    save_intermediates=False,
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
            
        save_intermediates: boolean
            If True, intermediate results will be saved in BIDS format

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

    # main_workflow
    main_workflow = pe.Workflow(name=wf_name)
    main_workflow.base_dir = process_dir
    
    # Extract subject IDs without 'sub-' prefix for datasink creation
    subject_ids = [sub.replace('sub-', '') if sub.startswith('sub-') else sub for sub in subjects] if subjects else None
    session_ids = [ses.replace('ses-', '') if ses.startswith('ses-') else ses for ses in sessions] if sessions else None
    acq_ids = [acq.replace('acq-', '') if acq.startswith('acq-') else acq for acq in acquisitions] if acquisitions else None
        
    if cfg.reconstruction.pipeline in [
        "niftymic",
        "nesvor",
        "svrtk",
    ] and cfg.segmentation.pipeline in ["bounti"]:
        fet_pipe = create_fet_subpipes(
            cfg,
        )

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

    # in both cases we connect datasource outputs to main pipeline
    main_workflow.connect(datasource, "stacks", fet_pipe, "inputnode.stacks")

    # DataSink - Create BIDS-compliant outputs for final results
    # Create json file to make it BIDS compliant if doesn't exist
    # Setup final datasinks for reconstruction results
    # using wf_name, could combine with recon + segmentation pip name, but believe it is better
    # to give user full control of name
    pipeline_name = f"{wf_name}" # _{cfg.reconstruction.pipeline}_{cfg.segmentation.pipeline}"

    recon_method = cfg.reconstruction.pipeline
    seg_method = cfg.segmentation.pipeline
    datasink_path = os.path.join(data_dir, "derivatives")

    # Create directory if not existing
    os.makedirs(os.path.join(datasink_path, pipeline_name), exist_ok=True)

    # Create json file to make it BIDS compliant if doesn't exist
    create_description_file(
        os.path.join(datasink_path, pipeline_name), pipeline_name
    )

    if save_intermediates:
        # Create a datasink for the preprocessing pipeline
        preprocessing_datasink = create_bids_datasink(
            data_dir=data_dir,
            pipeline_name=pipeline_name,  # Use combined name
            step_name="preprocessing",
            subjects=subject_ids,
            sessions=session_ids,
            acquisitions=acq_ids,
            name="preprocessing_datasink",
            recon_method=recon_method,
            seg_method=seg_method
        )
        # Connect the pipeline to the datasinks
        main_workflow.connect(
            fet_pipe, "Preprocessing.outputnode.stacks", preprocessing_datasink, "stacks"
        )
        main_workflow.connect(
            fet_pipe, "Preprocessing.outputnode.masks", preprocessing_datasink, "masks"
        )

    # Create final datasinks using BIDS-compliant organization
    recon_datasink = create_bids_datasink(
        data_dir=data_dir,
        pipeline_name=pipeline_name,  # Use combined name
        step_name="reconstruction",
        subjects=subject_ids,
        sessions=session_ids,
        acquisitions=acq_ids,
        name="final_recon_datasink",
        recon_method=recon_method,
        seg_method=seg_method
    )

    # Create another datasink for the segmentation pipeline
    seg_datasink = create_bids_datasink(
        data_dir=data_dir,
        pipeline_name=pipeline_name,
        step_name="segmentation",
        subjects=subject_ids,
        sessions=session_ids,
        acquisitions=acq_ids,
        name="final_seg_datasink",
        recon_method=recon_method,
        seg_method=seg_method
    )


    main_workflow.connect(
        fet_pipe, "outputnode.output_srr", recon_datasink, "@reconstruction"
    )
    main_workflow.connect(
        fet_pipe, "outputnode.output_seg", seg_datasink, "@segmentation"
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
    parser = argparse.ArgumentParser(description="Fetal MRI processing pipeline")

    parser.add_argument(
        "--data",
        dest="data",
        type=str,
        required=True,
        help=("BIDS-formatted directory containing anatomical MRI scans"),
    )
    parser.add_argument(
        "--out",
        dest="out",
        type=str,
        required=True,  # nargs='+',
        help="Output directory, where all nipype intermediate files, logs and cache will be saved.",
    )
    parser.add_argument(
        "--subjects",
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
        "--pipeline_name",
        "-name",
        dest="name",
        type=str,
        default="fetpype",
        help=("Name of the pipeline, the name of the folder that will be "
              "created in the derivatives/ folder of the BIDS directory"),
    )

    parser.add_argument(
        "--config",
        dest="cfg_path",
        default="../configs/default.yaml",
        type=str,
        help=(
            "Parameters yaml file specifying the parameters, containers and "
            "functions to be used in the pipeline. For now, there is only "
            "compatibility with singularity and docker containers and "
            " niftymic/nesvor pipelines"
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
    parser.add_argument(
        "--save_intermediates",
        action="store_true",
        help="Save intermediate results in BIDS format",
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
        save_intermediates=args.save_intermediates,
        wf_name=args.name
    )


if __name__ == "__main__":
    main()
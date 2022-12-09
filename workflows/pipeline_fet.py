#!/usr/bin/env python3
"""
    Non humain primates anatomical segmentation pipeline based ANTS

    Adapted in Nipype from an original pipelin of Kepkee Loh wrapped.

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
    python segment_pnh.py -data [PATH_TO_BIDS] -out ../local_tests/ -subjects Elouk

    Requirements
    --------------
    This workflow use:
        - ANTS
        - AFNI
        - FSL
"""

# Authors : David Meunier (david.meunier@univ-amu.fr)
#           Bastien Cagna (bastien.cagna@univ-amu.fr)
#           Kepkee Loh (kepkee.loh@univ-amu.fr)
#           Julien Sein (julien.sein@univ-amu.fr)

import os
import os.path as op

import argparse
import json
import pprint

import nipype

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as niu

import nipype.interfaces.fsl as fsl
fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

from fetpype.pipelines.full_pipelines import (
    create_fet_subpipes)

from fetpype.utils.utils_bids import (create_datasource,
                                       create_datasink)

###############################################################################

def create_main_workflow(data_dir, process_dir, subjects, sessions,
                         acquisitions, reconstructions, nprocs, wf_name="fetpype",):

    # macapype_pipeline
    """ Set up the segmentatiopn pipeline based on ANTS

    Arguments
    ---------
    data_path: pathlike str
        Path to the BIDS directory that contains anatomical images

    out_path: pathlike str
        Path to the ouput directory (will be created if not alredy existing).
        Previous outputs maybe overwritten.


    subjects: list of str (optional)
        Subject's IDs to match to BIDS specification (sub-[SUB1], sub-[SUB2]...)

    sessions: list of str (optional)
        Session's IDs to match to BIDS specification (ses-[SES1], ses-[SES2]...)

    acquisitions: list of str (optional)
        Acquisition name to match to BIDS specification (acq-[ACQ1]...)

    Returns
    -------
    workflow: nipype.pipeline.engine.Workflow


    """

    # formating args
    data_dir = op.abspath(data_dir)


    try:
        os.makedirs(process_dir)
    except OSError:
        print("process_dir {} already exists".format(process_dir))

    # main_workflow
    main_workflow = pe.Workflow(name= wf_name)
    main_workflow.base_dir = process_dir
    fet_pipe = create_fet_subpipes()


    # list of all required outputs
    output_query = {}

    # T1 (mandatory, always added)

    output_query['T2'] = {
        "datatype": "anat", "suffix": "T2w",
        "extension": ["nii", ".nii.gz"]}

    #output_query['haste_stacks'] = {
        #"datatype": "haste", "suffix": "T1w",
        #"extension": ["nii", ".nii.gz"]}

    #output_query['haste_masks'] = {
        #"datatype": "haste", "suffix": "brainmask",
        #"extension": ["nii", ".nii.gz"]}

    output_query['haste_stacks'] = {
        "datatype": "anat", "suffix": "T1w",
        "extension": ["nii", ".nii.gz"]}

    output_query['haste_masks'] = {
        "datatype": "anat", "suffix": "T1w",
        "extension": ["nii", ".nii.gz"]}


    #### datasource
    datasource = create_datasource(
        output_query, data_dir, subjects,  sessions, acquisitions, reconstructions)

    main_workflow.connect(datasource, 'T2',
                          fet_pipe, 'inputnode.list_T2')

    main_workflow.connect(datasource, 'haste_stacks',
                          fet_pipe, 'inputnode.haste_stacks')

    main_workflow.connect(datasource, 'haste_masks',
                          fet_pipe, 'inputnode.haste_masks')


    main_workflow.write_graph(graph2use="colored")
    main_workflow.config['execution'] = {'remove_unnecessary_outputs': 'false'}

    if nprocs is None:
        nprocs = 4

    main_workflow.run(plugin='MultiProc', plugin_args={'n_procs' : nprocs})

def main():

    # Command line parser
    parser = argparse.ArgumentParser(
        description="PNH segmentation pipeline")

    parser.add_argument("-data", dest="data", type=str, required=True,
                        help="Directory containing MRI data (BIDS)")
    parser.add_argument("-out", dest="out", type=str, #nargs='+',
                        help="Output dir", required=True)
    parser.add_argument("-subjects", "-sub", dest="sub",
                        type=str, nargs='+', help="Subjects", required=False)
    parser.add_argument("-sessions", "-ses", dest="ses",
                        type=str, nargs='+', help="Sessions", required=False)
    parser.add_argument("-acquisitions", "-acq", dest="acq", type=str,
                        nargs='+', default=None, help="Acquisitions")
    parser.add_argument("-reconstructions", "-rec", dest="rec", type=str, nargs='+',
                        default=None, help="reconstructions")
    parser.add_argument("-nprocs", dest="nprocs", type=int,
                        help="number of processes to allocate", required=False)

    args = parser.parse_args()

    # main_workflow
    print("Initialising the pipeline...")
    create_main_workflow(
        data_dir=args.data,
        process_dir=args.out,
        subjects=args.sub,
        sessions=args.ses,
        acquisitions=args.acq,
        reconstructions=args.rec,
        nprocs=args.nprocs)

if __name__ == '__main__':
    main()

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
import nipype.interfaces.io as nio

import nipype.interfaces.fsl as fsl
fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

from fetpype.pipelines.full_pipelines import (
    create_fet_subpipes)

from fetpype.utils.utils_bids import (create_datasource,
                                       create_datasink)

###############################################################################

def create_main_workflow(data_dir, process_dir, subjects, sessions,
                         acquisitions, reconstructions, nprocs, wf_name="fetpype",bids = False):

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

    if bids:

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

    else:

        # we create a node to pass input filenames to DataGrabber from nipype

        infosource = pe.Node(interface=niu.IdentityInterface(
            fields=['subject_id','session']),
            name="infosource")

        infosource.iterables = [('subject_id', subjects),
            ('session', sessions)]

        # and a node to grab data. The template_args in this node iterate upon
        # the values in the infosource node

        datasource = pe.Node(interface=nio.DataGrabber(
            infields=['subject_id','session'],
            outfields= ['img_file','gm_anat_file','wm_anat_file','csf_anat_file']),
            name = 'datasource')

        datasource.inputs.base_directory = data_dir
        datasource.inputs.template = 'sub-%s/sub-%s_ses-%s/%s/NIFTI/sub-%s_ses-%s%s%s%s'
        datasource.inputs.template_args = dict(
        haste_stacks=[['subject_id','subject_id','session',"*T2HASTE*",'subject_id','session',"_T2_HASTE","*",".nii.gz"]],
        tru_stacks=[['subject_id','subject_id','session',"*T2TRUFI*",'subject_id','session',"_T2_TRUFI","*",".nii.gz"]],
            )

        datasource.inputs.sort_filelist = True

        main_workflow.connect(infosource, 'subject_id',
                              datasource, 'subject_id')

        main_workflow.connect(infosource, 'session',
                              datasource, 'session')

    # in both cases we connect datsource outputs to main pipeline

    main_workflow.connect(datasource, 'haste_stacks',
                        fet_pipe, 'inputnode.haste_stacks')

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
    parser.add_argument("-bids", dest="bids", action='store_true',
                        help="BIDS directory is provided",
                        required=False)
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
        bids=args.bids,
        sessions=args.ses,
        acquisitions=args.acq,
        reconstructions=args.rec,
        nprocs=args.nprocs)

if __name__ == '__main__':
    main()

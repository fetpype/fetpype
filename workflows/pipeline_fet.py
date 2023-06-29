#!/usr/bin/env python3
"""
    Human fetal anatomical segmentation pipeline

    Adapted in Nipype from an original pipeline of Alexandre Pron by David Meunier.

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
    python pipeline_fet.py -data [PATH_TO_BIDS] -out ../local_tests/ -subjects Elouk

    Requirements
    --------------
    This workflow use:
        - ANTS (denoise)
        - niftimic
"""

# Authors : David Meunier (david.meunier@univ-amu.fr)
#           Alexandre Pron (alexandre.pron@univ-amu.fr)

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

###############################################################################

def create_main_workflow(data_dir, process_dir, subjects, sessions,
                         acquisitions, reconstructions, params_file, nprocs, wf_name="fetpype",bids = False):

    # macapype_pipeline
    """ Set up the segmentatiopn pipeline based on ANTS

    Arguments
    ---------
    data_path: pathlike str
        Path to the BIDS directory that contains anatomical images

    process_dir: pathlike str
        Path to the ouput directory (will be created if not alredy existing).
        Previous outputs maybe overwritten.


    subjects: list of str (optional)
        Subject's IDs to match to BIDS specification (sub-[SUB1], sub-[SUB2]...)

    sessions: list of str (optional)
        Session's IDs to match to BIDS specification (ses-[SES1], ses-[SES2]...)

    acquisitions: list of str (optional)
        Acquisition name to match to BIDS specification (acq-[ACQ1]...)

    reconstructions: list of str (optional)
        Reconstructions name to match to BIDS specification (rec-[ACQ1]...)

    params_file: path to a JSON file
        JSON file that specify some parameters of the pipeline.

    nprocs: integer
        number of processes that will be launched by MultiProc

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

    #params
    if params_file is None:

       params = {}

    else:

        # params
        assert op.exists(params_file), "Error with file {}".format(
            params_file)

        print("Using orig params file:", params_file)

        params = json.load(open(params_file))

    # main_workflow
    main_workflow = pe.Workflow(name= wf_name)
    main_workflow.base_dir = process_dir
    fet_pipe = create_fet_subpipes(params=params)

    if bids:

        # list of all required outputs
        output_query = {}

        #output_query['haste_stacks'] = {
            #"datatype": "haste", "suffix": "T1w",
            #"extension": ["nii", ".nii.gz"]}

        #output_query['haste_masks'] = {
            #"datatype": "haste", "suffix": "brainmask",
            #"extension": ["nii", ".nii.gz"]}

        output_query['haste_stacks'] = {
            "datatype": "anat", "suffix": "T2w", "acquisition":"haste",
            "extension": ["nii", ".nii.gz"]}

        output_query['tru_stacks'] = {
            "datatype": "anat", "suffix": "T2w", "acquisition":"tru",
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

        #### from Xnat raw
        #datasource = pe.Node(interface=nio.DataGrabber(
            #infields=['subject_id','session'],
            #outfields= ['haste_stacks','tru_stacks']),
            #name = 'datasource')

        #datasource.inputs.base_directory = data_dir
        #datasource.inputs.template = 'sub-%s/sub-%s_ses-%s/%s/NIFTI/sub-%s_ses-%s%s%s%s'
        #datasource.inputs.template_args = dict(
        #haste_stacks=[['subject_id','subject_id','session',"*T2HASTE*",'subject_id','session',"_T2_HASTE","*",".nii.gz"]],
        #tru_stacks=[['subject_id','subject_id','session',"*T2TRUFI*",'subject_id','session',"_T2_TRUFI","*",".nii.gz"]],
            #)

        #### mesocentre
        datasource = pe.Node(interface=nio.DataGrabber(
            infields=['subject_id','session'],
            outfields= ['haste_stacks','tru_stacks']),
            name = 'datasource')

        datasource.inputs.base_directory = data_dir
        datasource.inputs.template = 'sub-%s/ses-%s/anat/sub-%s_ses-%s_acq-%s_%s%s'

        datasource.inputs.template_args = dict(
        tru_stacks=[['subject_id','session','subject_id','session',"tru","*","_T2w.nii.gz"]],
        haste_stacks=[['subject_id','session','subject_id','session',"haste","*","_T2w.nii.gz"]]
            )
        datasource.inputs.sort_filelist = True


        #datasource.inputs.base_directory = data_dir
        #datasource.inputs.template = 'sub-%s/ses-%s/anat/%s/sub-%s_ses-%s%s%s%s'
        #datasource.inputs.template_args = dict(
        #haste_stacks=[['subject_id','session',"haste",'subject_id','session',"_t2_haste","*",".nii.gz"]],
        #tru_stacks=[['subject_id','session',"tru",'subject_id','session',"_t2_trufi","*",".nii.gz"]],
            #)
        #datasource.inputs.sort_filelist = True

        main_workflow.connect(infosource, 'subject_id',
                              datasource, 'subject_id')

        main_workflow.connect(infosource, 'session',
                              datasource, 'session')

    # in both cases we connect datsource outputs to main pipeline

    main_workflow.connect(datasource, 'tru_stacks',
                        fet_pipe, 'inputnode.tru_stacks')

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
    parser.add_argument("-params", dest="params_file", type=str,
                        help="Parameters json file", required=False)
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
        params_file=args.params_file,
        nprocs=args.nprocs)

if __name__ == '__main__':
    main()

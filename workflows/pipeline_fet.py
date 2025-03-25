import sys
import os
import nipype.pipeline.engine as pe
from fetpype.pipelines.full_pipeline import (
    create_full_pipeline,
)
from fetpype.utils.utils_bids import (
    create_datasource,
    create_datasink,
    create_bids_datasink,
    create_description_file,
)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import (  # noqa: E402
    get_default_parser,
    init_and_load_cfg,
    check_and_update_paths,
    get_pipeline_name,
    check_valid_pipeline,
)

###############################################################################

__file_dir__ = os.path.dirname(os.path.abspath(__file__))


def create_main_workflow(
    data_dir,
    out_dir,
    nipype_dir,
    subjects,
    sessions,
    acquisitions,
    cfg_path,
    nprocs,
    save_intermediates=False,
):
    """
    Instantiates and runs the entire workflow of the fetpype pipeline.

    Args:
        data_dir (str):
            Path to the BIDS directory that contains anatomical images.
        out_dir (str):
            Path to the output directory (will be created if not already
            existing). Previous outputs may be overriden.
        nipype_dir (str):
            Path to the nipype directory.
        subjects (list[str], optional):
            List of subject IDs matching the BIDS specification
            (e.g., sub-[SUB1], sub-[SUB2], ...).
        sessions (list[str], optional):
            List of session IDs matching the BIDS specification
            (e.g., ses-[SES1], ses-[SES2], ...).
        acquisitions (list[str], optional):
            List of acquisition names matching the BIDS specification
            (e.g., acq-[ACQ1], ...).
        cfg_path (str):
            Path to a hydra  configuration file (YAML) specifying pipeline
            parameters.
        nprocs (int):
            Number of processes to be launched by MultiProc.

    """

    cfg = init_and_load_cfg(cfg_path, __file_dir__)
    data_dir, out_dir, nipype_dir = check_and_update_paths(
        data_dir, out_dir, nipype_dir, cfg
    )

    check_valid_pipeline(cfg)
    # if general, pipeline is not in params ,create it and set it to niftymic

    # main_workflow
    main_workflow = pe.Workflow(name=get_pipeline_name(cfg))
    main_workflow.base_dir = nipype_dir
    fet_pipe = create_full_pipeline(cfg)

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

    # Get subject, session and acquisition IDs from the datasource 
    subject_ids, session_ids, acq_ids = zip(*datasource.iterables[1])
    subject_ids, session_ids, acq_ids = list(subject_ids), list(session_ids), list(acq_ids)

    # Preprocessing data sink:
    if save_intermediates:
        datasink_path_intermediate = os.path.join(out_dir, "preprocessing")
        os.makedirs(datasink_path_intermediate, exist_ok=True)
        create_description_file(
            datasink_path_intermediate, "preprocessing", cfg=cfg.reconstruction
        )

        # Create a datasink for the preprocessing pipeline
        preprocessing_datasink = create_bids_datasink(
            out_dir=out_dir,
            pipeline_name="preprocessing",  # Use combined name
            step_name="preprocessing",
            subjects=subject_ids,
            sessions=session_ids,
            acquisitions=acq_ids,
            name="preprocessing_datasink",
            recon_method=cfg.reconstruction.pipeline,
            seg_method=cfg.segmentation.pipeline
        )
        # Connect the pipeline to the datasinks
        main_workflow.connect(
            fet_pipe, "Preprocessing.outputnode.stacks", preprocessing_datasink, "stacks"
        )
        main_workflow.connect(
            fet_pipe, "Preprocessing.outputnode.masks", preprocessing_datasink, "masks"
        )
    
    # Reconstruction data sink:
    pipeline_name = cfg.reconstruction.pipeline
    datasink_path = os.path.join(out_dir, pipeline_name)
    os.makedirs(datasink_path, exist_ok=True)
    desc_file = create_description_file(
        datasink_path, pipeline_name, cfg=cfg.reconstruction
    )

    recon_datasink = create_bids_datasink(
        out_dir=out_dir,
        pipeline_name=pipeline_name,  # Use combined name
        step_name="reconstruction",
        subjects=subject_ids,
        sessions=session_ids,
        acquisitions=acq_ids,
        name="final_recon_datasink",
        recon_method=cfg.reconstruction.pipeline,
        seg_method=cfg.segmentation.pipeline,
    )

    # Segmentation data sink

    datasink_path2 = os.path.join(out_dir, cfg.segmentation.pipeline)
    os.makedirs(datasink_path2, exist_ok=True)
    create_description_file(
        datasink_path2, cfg.segmentation.pipeline, desc_file, cfg.segmentation
    )

    # Create another datasink for the segmentation pipeline
    seg_datasink = create_bids_datasink(
        out_dir=out_dir,
        pipeline_name=pipeline_name,
        step_name="segmentation",
        subjects=subject_ids,
        sessions=session_ids,
        acquisitions=acq_ids,
        name="final_seg_datasink",
        recon_method=cfg.reconstruction.pipeline,
        seg_method=cfg.segmentation.pipeline,
    )

    # Connect the pipeline to the datasink
    main_workflow.connect(
        fet_pipe, "outputnode.output_srr", recon_datasink, pipeline_name
    )
    main_workflow.connect(
        fet_pipe, "outputnode.output_seg", seg_datasink, cfg.segmentation.pipeline
    )

    if cfg.save_graph:
        main_workflow.write_graph(
            graph2use="colored",
            format="png",
            simple_form=True,
        )

    main_workflow.config["execution"] = {"remove_unnecessary_outputs": "false"}
    main_workflow.run(plugin="MultiProc", plugin_args={"n_procs": nprocs})


def main():
    # Command line parser
    parser = get_default_parser(
        "Run the entire Fetpype pipeline -- "
        "pre-processing, reconstruction and segmentation"
    )

    args = parser.parse_args()

    # main_workflow
    print("Initialising the pipeline...")
    create_main_workflow(
        data_dir=args.data,
        out_dir=args.out,
        nipype_dir=args.nipype_dir,
        subjects=args.sub,
        sessions=args.ses,
        acquisitions=args.acq,
        cfg_path=args.cfg_path,
        nprocs=args.nprocs,
        save_intermediates=args.save_intermediates,
    )


if __name__ == "__main__":
    main()
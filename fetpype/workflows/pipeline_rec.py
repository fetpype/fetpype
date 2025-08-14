import os
import nipype.pipeline.engine as pe
from fetpype.pipelines.full_pipeline import (
    create_rec_pipeline,
)
from fetpype.utils.utils_bids import (
    create_datasource,
    create_bids_datasink,
    create_description_file,
)


from fetpype.workflows.utils import (
    init_and_load_cfg,
    check_and_update_paths,
    get_pipeline_name,
    get_default_parser,
    check_valid_pipeline,
)
from fetpype.utils.logging import setup_logging, status_line

###############################################################################


def create_rec_workflow(
    data_dir,
    masks_dir,
    out_dir,
    nipype_dir,
    subjects,
    sessions,
    acquisitions,
    cfg_path,
    nprocs,
    debug=False,
    verbose=False,
):
    """
    Instantiates and runs the entire workflow of the fetpype pipeline.

    Args:
        data_dir (str):
            Path to the BIDS directory that contains anatomical images.
        masks_dir (str):
            Path to the BIDS directory that contains brain masks.
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
        debug (bool):
            Whether to enable debug mode.
        verbose (bool):
            Whether to enable verbose mode.
    """

    cfg = init_and_load_cfg(cfg_path)

    data_dir, out_dir, nipype_dir = check_and_update_paths(
        data_dir, out_dir, nipype_dir, cfg
    )

    setup_logging(
        base_dir=nipype_dir,
        debug=debug,
        verbose=verbose,
        capture_prints=True,
    )

    load_masks = False
    if masks_dir is not None:
        # Check it exists
        if not os.path.exists(masks_dir):
            raise ValueError(
                f"Path to masks directory {masks_dir} does not exist."
            )
        masks_dir = os.path.abspath(masks_dir)
        load_masks = True
    check_valid_pipeline(cfg)
    # if general, pipeline is not in params ,create it and set it to niftymic

    # main_workflow
    main_workflow = pe.Workflow(name=get_pipeline_name(cfg))
    main_workflow.base_dir = nipype_dir
    fet_pipe = create_rec_pipeline(cfg, load_masks)

    output_query = {
        "stacks": {
            "datatype": "anat",
            "suffix": "T2w",
            "extension": ["nii", ".nii.gz"],
        },
    }
    if load_masks:
        output_query["masks"] = {
            "datatype": "anat",
            "suffix": "mask",
            "extension": ["nii", ".nii.gz"],
        }

    # datasource
    datasource = create_datasource(
        output_query,
        data_dir,
        subjects,
        sessions,
        acquisitions,
        extra_derivatives=masks_dir,
    )
    main_workflow.connect(datasource, "stacks", fet_pipe, "inputnode.stacks")
    if load_masks:
        main_workflow.connect(datasource, "masks", fet_pipe, "inputnode.masks")

    # DataSink

    # Reconstruction data sink:
    pipeline_name = cfg.reconstruction.pipeline
    create_description_file(out_dir, pipeline_name, cfg=cfg.reconstruction)

    datasink = create_bids_datasink(
        out_dir=out_dir,
        pipeline_name=pipeline_name,
        strip_dir=main_workflow.base_dir,
        name="final_recon_datasink",
        rec_label=cfg.reconstruction.pipeline,
    )
    # datasink.inputs.base_directory = datasink_path

    # Connect the pipeline to the datasink
    main_workflow.connect(
        fet_pipe, "outputnode.output_srr", datasink, f"@{pipeline_name}"
    )

    if cfg.save_graph:
        main_workflow.write_graph(
            graph2use="colored",
            format="png",
            simple_form=True,
        )

    main_workflow.run(
        plugin="MultiProc",
        plugin_args={"n_procs": nprocs, "status_callback": status_line},
    )


def main():
    # Command line parser
    parser = get_default_parser(
        "Run the Fetpype reconstruction pipeline -- "
        "pre-processing and reconstruction."
    )

    parser.add_argument(
        "--masks",
        type=str,
        default=None,
        help="Path to the BIDS directory that contains brain masks.",
    )
    args = parser.parse_args()

    # main_workflow
    print("Initialising the pipeline...")
    create_rec_workflow(
        data_dir=args.data,
        masks_dir=args.masks,
        out_dir=args.out,
        nipype_dir=args.nipype_dir,
        subjects=args.sub,
        sessions=args.ses,
        acquisitions=args.acq,
        cfg_path=args.cfg_path,
        nprocs=args.nprocs,
        debug=args.debug,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()

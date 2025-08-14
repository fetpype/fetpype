import os
import nipype.pipeline.engine as pe
from fetpype.pipelines.full_pipeline import (
    create_full_pipeline,
)
import nipype.interfaces.utility as niu
from fetpype.utils.utils_bids import (
    create_datasource,
    create_bids_datasink,
    create_description_file,
)

from fetpype.workflows.utils import (  # noqa: E402
    get_default_parser,
    init_and_load_cfg,
    check_and_update_paths,
    get_pipeline_name,
    check_valid_pipeline,
)
from fetpype.utils.logging import setup_logging, status_line
import logging


def create_main_workflow(
    data_dir,
    masks_dir,
    out_dir,
    nipype_dir,
    subjects,
    sessions,
    acquisitions,
    cfg_path,
    nprocs,
    save_intermediates=False,
    debug=False,
    verbose=False,
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
    log = logging.getLogger("nipype")
    # Print the three paths
    log.info(
        f"Data directory: {data_dir}\n"
        f"Output directory: {out_dir}\n"
        f"Nipype directory: {nipype_dir}"
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

    # main_workflow
    main_workflow = pe.Workflow(name=get_pipeline_name(cfg))
    main_workflow.base_dir = nipype_dir
    fet_pipe = create_full_pipeline(cfg, load_masks)

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

    input_data = pe.Workflow(name="input")

    output_fields = ["stacks"]
    if load_masks:
        output_fields.append("masks")
    output = pe.Node(
        niu.IdentityInterface(fields=output_fields), name="outputnode"
    )
    input_data.connect(datasource, "stacks", output, "stacks")
    if load_masks:
        input_data.connect(datasource, "masks", output, "masks")

    main_workflow.connect(
        input_data, "outputnode.stacks", fet_pipe, "inputnode.stacks"
    )
    if load_masks:
        main_workflow.connect(
            datasource, "outputnode.masks", fet_pipe, "inputnode.masks"
        )

    # Reconstruction data sink:
    pipeline_name = get_pipeline_name(cfg)

    # Preprocessing data sink:
    if save_intermediates:
        datasink_path_intermediate = os.path.join(out_dir, "preprocessing")
        os.makedirs(datasink_path_intermediate, exist_ok=True)
        create_description_file(
            datasink_path_intermediate, "preprocessing", cfg=cfg.reconstruction
        )

        # Create a datasink for the preprocessing pipeline
        preprocessing_datasink_denoised = create_bids_datasink(
            out_dir=datasink_path_intermediate,
            pipeline_name="preprocessing",  # Use combined name
            strip_dir=main_workflow.base_dir,
            name="preprocessing_datasink_denoised",
            desc_label="denoised",
        )
        preprocessing_datasink_masked = create_bids_datasink(
            out_dir=datasink_path_intermediate,
            pipeline_name="preprocessing",  # Use combined name
            strip_dir=main_workflow.base_dir,
            name="preprocessing_datasink_cropped",
            desc_label="cropped",
        )

        # Connect the pipeline to the datasinks
        main_workflow.connect(
            fet_pipe,
            "Preprocessing.outputnode.stacks",
            preprocessing_datasink_denoised,
            "@stacks",
        )
        main_workflow.connect(
            fet_pipe,
            "Preprocessing.outputnode.masks",
            preprocessing_datasink_masked,
            "@masks",
        )

    recon_datasink = create_bids_datasink(
        out_dir=out_dir,
        pipeline_name=pipeline_name,
        strip_dir=main_workflow.base_dir,
        name="final_recon_datasink",
        rec_label=cfg.reconstruction.pipeline,
    )

    # Create another datasink for the segmentation pipeline
    seg_datasink = create_bids_datasink(
        out_dir=out_dir,
        pipeline_name=pipeline_name,
        strip_dir=main_workflow.base_dir,
        name="final_seg_datasink",
        rec_label=cfg.reconstruction.pipeline,
        seg_label=cfg.segmentation.pipeline,
    )

    # Connect the pipeline to the datasink
    main_workflow.connect(
        fet_pipe, "outputnode.output_srr", recon_datasink, f"@{pipeline_name}"
    )
    main_workflow.connect(
        fet_pipe,
        "outputnode.output_seg",
        seg_datasink,
        f"@{cfg.segmentation.pipeline}",
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
    parser = get_default_parser(
        "Run the entire Fetpype pipeline -- "
        "pre-processing, reconstruction and segmentation"
    )

    parser.add_argument(
        "--masks",
        type=str,
        default=None,
        help="Path to the directory containing the masks.",
    )

    args = parser.parse_args()

    # main_workflow
    print("Initialising the pipeline...")
    create_main_workflow(
        data_dir=args.data,
        masks_dir=args.masks,
        out_dir=args.out,
        nipype_dir=args.nipype_dir,
        subjects=args.sub,
        sessions=args.ses,
        acquisitions=args.acq,
        cfg_path=args.cfg_path,
        nprocs=args.nprocs,
        save_intermediates=args.save_intermediates,
        debug=args.debug,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()

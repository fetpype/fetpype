import os
import json
import nipype.pipeline.engine as pe
from fetpype.pipelines.full_pipeline import (
    create_seg_pipeline,
)
from fetpype.utils.utils_bids import (
    create_datasource,
    create_bids_datasink,
    create_description_file,
)
from fetpype import VALID_RECONSTRUCTION
from fetpype.workflows.utils import (
    init_and_load_cfg,
    check_and_update_paths,
    get_pipeline_name,
    get_default_parser,
    check_valid_pipeline,
)


###############################################################################


def create_seg_workflow(
    data_dir,
    out_dir,
    nipype_dir,
    subjects,
    sessions,
    acquisitions,
    cfg_path,
    nprocs,
    ignore_checks=False,
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

    cfg = init_and_load_cfg(cfg_path)
    data_dir, out_dir, nipype_dir = check_and_update_paths(
        data_dir, out_dir, nipype_dir, cfg
    )
    check_valid_pipeline(cfg)
    # if general, pipeline is not in params ,create it and set it to niftymic

    data_desc = os.path.join(data_dir, "dataset_description.json")
    if not ignore_checks:
        if os.path.exists(data_desc):
            with open(data_desc, "r") as f:
                data_desc = json.load(f)
            name = data_desc.get("Name", None)
            if name not in VALID_RECONSTRUCTION:
                raise ValueError(
                    f"Method name <{data_desc['Name']}> is not a valid "
                    "reconstruction method. Are you sure that you are "
                    "passing a reconstructed dataset?\n"
                    "If you know what you are doing, you can ignore "
                    "this error by adding --ignore_check to the command line."
                )
        else:
            raise ValueError(
                f"dataset_description.json file not found in {data_dir}. "
                "Please provide a valid BIDS directory."
            )
    # main_workflow
    main_workflow = pe.Workflow(name=get_pipeline_name(cfg))
    main_workflow.base_dir = nipype_dir
    fet_pipe = create_seg_pipeline(cfg)

    output_query = {
        "srr_volume": {
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
    main_workflow.connect(
        datasource, "srr_volume", fet_pipe, "inputnode.srr_volume"
    )

    # DataSink

    # Segmentation data sink:
    pipeline_name = cfg.segmentation.pipeline
    datasink_path = os.path.join(out_dir, pipeline_name)
    # Create json file to make it BIDS compliant if doesnt exist
    # Eventually, add all parameters to the json file
    os.makedirs(datasink_path, exist_ok=True)

    # Create datasink
    pipeline_name = cfg.segmentation.pipeline
    os.makedirs(datasink_path, exist_ok=True)
    prev_desc = os.path.join(data_dir, "dataset_description.json")
    if not os.path.exists(prev_desc):
        prev_desc = None

    create_description_file(
        out_dir, pipeline_name, prev_desc, cfg.segmentation
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
    # Add the base directory

    # Connect the pipeline to the datasink
    main_workflow.connect(
        fet_pipe, "outputnode.output_seg", seg_datasink, pipeline_name
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
    parser = get_default_parser("Run the Fetpype segmentation pipeline.")

    parser.add_argument(
        "--ignore_checks",
        action="store_true",
        help=(
            "Ignore the check to only use data from the list of validated SRR "
            f"{', '.join(VALID_RECONSTRUCTION)}."
        ),
    )
    args = parser.parse_args()

    # main_workflow
    print("Initialising the pipeline...")
    create_seg_workflow(
        data_dir=args.data,
        out_dir=args.out,
        nipype_dir=args.nipype_dir,
        subjects=args.sub,
        sessions=args.ses,
        acquisitions=args.acq,
        cfg_path=args.cfg_path,
        nprocs=args.nprocs,
        ignore_checks=args.ignore_checks,
    )


if __name__ == "__main__":
    main()

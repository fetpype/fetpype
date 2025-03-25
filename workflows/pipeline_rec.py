import sys
import os
import nipype.pipeline.engine as pe
from fetpype.pipelines.full_pipeline import (
    create_rec_pipeline,
)
from fetpype.utils.utils_bids import (
    create_datasource,
    create_datasink,
    create_description_file,
)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


from utils import (  # noqa: E402
    init_and_load_cfg,
    check_and_update_paths,
    get_pipeline_name,
    get_default_parser,
    check_valid_pipeline,
)

###############################################################################

__file_dir__ = os.path.dirname(os.path.abspath(__file__))


def create_rec_workflow(
    data_dir,
    out_dir,
    nipype_dir,
    subjects,
    sessions,
    acquisitions,
    cfg_path,
    nprocs,
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

    import pdb

    data_dir, out_dir, nipype_dir = check_and_update_paths(
        data_dir, out_dir, nipype_dir, cfg
    )
    pdb.set_trace()
    check_valid_pipeline(cfg)
    # if general, pipeline is not in params ,create it and set it to niftymic

    # main_workflow
    main_workflow = pe.Workflow(name=get_pipeline_name(cfg))
    main_workflow.base_dir = nipype_dir
    fet_pipe = create_rec_pipeline(cfg)

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

    # DataSink

    # Reconstruction data sink:
    pipeline_name = cfg.reconstruction.pipeline
    datasink_path = os.path.join(out_dir, pipeline_name)
    # Create json file to make it BIDS compliant if doesnt exist
    # Eventually, add all parameters to the json file
    os.makedirs(datasink_path, exist_ok=True)
    create_description_file(
        datasink_path, pipeline_name, cfg=cfg.reconstruction
    )

    params_regex_subs = cfg.regex_subs if "regex_subs" in cfg.keys() else {}
    params_subs = cfg.rsubs if "subs" in cfg.keys() else {}

    # Create datasink
    datasink = create_datasink(
        iterables=datasource.iterables,
        name=f"datasink_{pipeline_name}",
        params_subs=params_subs,
        params_regex_subs=params_regex_subs,
    )
    datasink.inputs.base_directory = datasink_path
    pdb.set_trace()
    # Connect the pipeline to the datasink
    main_workflow.connect(
        fet_pipe, "outputnode.output_srr", datasink, pipeline_name
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
        "Run the Fetpype reconstruction pipeline -- "
        "pre-processing and reconstruction."
    )

    args = parser.parse_args()

    # main_workflow
    print("Initialising the pipeline...")
    create_rec_workflow(
        data_dir=args.data,
        out_dir=args.out,
        nipype_dir=args.nipype_dir,
        subjects=args.sub,
        sessions=args.ses,
        acquisitions=args.acq,
        cfg_path=args.cfg_path,
        nprocs=args.nprocs,
    )


if __name__ == "__main__":
    main()

import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe
from ..nodes.preprocessing import (
    CropStacksAndMasks,
    CheckAffineResStacksAndMasks,
    CheckAndSortStacksAndMasks,
    run_prepro_cmd,
)
from nipype import config
from fetpype.nodes.reconstruction import run_recon_cmd
from fetpype.nodes.segmentation import run_seg_cmd
from fetpype.utils.utils_bids import get_gestational_age


def print_files(files):
    print("Files:")
    print(files)
    return files


def get_prepro(cfg, load_masks=False, enabled_cropping=False):

    cfg_prepro = cfg.preprocessing

    prepro_pipe = pe.Workflow(name="Preprocessing")
    # Creating input node

    enabled_check = cfg_prepro.check_stacks_and_masks.enabled
    enabled_cropping = cfg_prepro.cropping.enabled and enabled_cropping
    if cfg_prepro.cropping.enabled != enabled_cropping:
        print("Overriding cropping enabled status for the selected pipeline.")
    enabled_denoising = True
    enabled_bias_corr = cfg_prepro.bias_correction.enabled

    # PREPROCESSING
    # 0. Define input and outputs
    in_fields = ["stacks"]
    if load_masks:
        in_fields += ["masks"]

    input = pe.Node(niu.IdentityInterface(fields=in_fields), name="inputnode")

    output = pe.Node(
        niu.IdentityInterface(fields=["stacks", "masks"]), name="outputnode"
    )
    # 1. Load masks or brain extraction
    container = cfg.container
    if load_masks:
        check_input = pe.Node(
            interface=CheckAndSortStacksAndMasks(), name="CheckInput"
        )

    else:
        be_config = cfg_prepro.brain_extraction
        be_cfg_cont = be_config[container]

        brain_extraction = pe.Node(
            interface=niu.Function(
                input_names=[
                    "input_stacks",
                    "name",
                    "cmd",
                    "singularity_path",
                    "singularity_mount",
                ],
                output_names=["output_masks"],
                function=run_prepro_cmd,
            ),
            name="BrainExtraction",
        )
        brain_extraction.inputs.cmd = be_cfg_cont.cmd
        brain_extraction.inputs.cfg = be_config
        # if the container is singularity, add
        # singularity path to the brain_extraction
        if cfg.container == "singularity":
            brain_extraction.inputs.singularity_path = cfg.singularity_path
            brain_extraction.inputs.singularity_mount = cfg.singularity_mount

    # 2. Check stacks and masks
    check_name = "CheckAffineAndRes"
    check_name += "_disabled" if not enabled_check else ""

    check_affine = pe.Node(
        interface=CheckAffineResStacksAndMasks(), name=check_name
    )
    check_affine.inputs.is_enabled = enabled_check
    # 3. Cropping
    cropping_name = "Cropping"
    cropping_name += "_disabled" if not enabled_cropping else ""
    cropping = pe.MapNode(
        interface=CropStacksAndMasks(),
        iterfield=["image", "mask"],
        name=cropping_name,
    )

    cropping.inputs.is_enabled = enabled_cropping
    # 4. Denoising
    denoising_name = "Denoising"
    denoising_name += "_disabled" if not enabled_denoising else ""

    denoising = pe.MapNode(
        interface=niu.Function(
            input_names=[
                "input_stacks",
                "is_enabled",
                "cmd",
                "singularity_path",
                "singularity_mount",
            ],
            output_names=["output_stacks"],
            function=run_prepro_cmd,
        ),
        iterfield=["input_stacks"],
        name=denoising_name,
    )

    denoising_cfg = cfg_prepro.denoising
    denoising.inputs.is_enabled = enabled_denoising
    denoising.inputs.cmd = denoising_cfg[container].cmd
    # if the container is singularity, add singularity path to the denoising
    if cfg.container == "singularity":
        denoising.inputs.singularity_path = cfg.singularity_path
        denoising.inputs.singularity_mount = cfg.singularity_mount

    merge_denoise = pe.Node(
        interface=niu.Merge(1, ravel_inputs=True), name="MergeDenoise"
    )
    # 5. Bias field correction
    bias_name = "BiasCorrection"
    bias_name += "_disabled" if not enabled_bias_corr else ""

    bias_corr = pe.MapNode(
        interface=niu.Function(
            input_names=[
                "input_stacks",
                "input_masks",
                "is_enabled",
                "cmd",
                "singularity_path",
                "singularity_mount",
            ],
            output_names=["output_stacks"],
            function=run_prepro_cmd,
        ),
        iterfield=["input_stacks", "input_masks"],
        name=bias_name,
    )
    bias_cfg = cfg_prepro.bias_correction
    bias_corr.inputs.is_enabled = enabled_bias_corr
    bias_corr.inputs.cmd = bias_cfg[container].cmd

    # if the container is singularity, add singularity path to the bias_corr
    if cfg.container == "singularity":
        bias_corr.inputs.singularity_path = cfg.singularity_path
        bias_corr.inputs.singularity_mount = cfg.singularity_mount

    # 6. Verify output
    check_output = pe.Node(
        interface=CheckAndSortStacksAndMasks(),
        name="CheckOutput",
    )

    # Connect nodes

    if load_masks:
        prepro_pipe.connect(input, "stacks", check_input, "stacks")
        prepro_pipe.connect(input, "masks", check_input, "masks")

        prepro_pipe.connect(
            check_input, "output_stacks", check_affine, "stacks"
        )
        prepro_pipe.connect(check_input, "output_masks", check_affine, "masks")

    else:
        prepro_pipe.connect(input, "stacks", brain_extraction, "input_stacks")

        prepro_pipe.connect(input, "stacks", check_affine, "stacks")
        prepro_pipe.connect(
            brain_extraction, "output_masks", check_affine, "masks"
        )

    prepro_pipe.connect(check_affine, "output_stacks", cropping, "image")
    prepro_pipe.connect(check_affine, "output_masks", cropping, "mask")

    prepro_pipe.connect(cropping, "output_image", denoising, "input_stacks")
    prepro_pipe.connect(denoising, "output_stacks", merge_denoise, "in1")

    prepro_pipe.connect(merge_denoise, "out", bias_corr, "input_stacks")
    prepro_pipe.connect(cropping, "output_mask", bias_corr, "input_masks")

    prepro_pipe.connect(bias_corr, "output_stacks", check_output, "stacks")
    prepro_pipe.connect(cropping, "output_mask", check_output, "masks")

    prepro_pipe.connect(check_output, "output_stacks", output, "stacks")
    prepro_pipe.connect(check_output, "output_masks", output, "masks")

    return prepro_pipe


def get_recon(cfg):
    """
    Get the reconstruction workflow based on the pipeline specified
    in params. Currently, the supported pipelines are niftymic and nesvor.

    Params:
        params:
            dictionary of parameters (default = {}). This
            dictionary contains the parameters given in a JSON
            config file. It specifies which containers to use
            for each step of the pipeline.

    Inputs:
        inputnode:
            stacks:
                list of T2w stacks
            masks:
                list of brain masks
    Outputs:
        outputnode:
            srr_volume:
                3D reconstructed volume
    """
    rec_pipe = pe.Workflow(name="Reconstruction")
    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["stacks", "masks"]), name="inputnode"
    )
    outputnode = pe.Node(
        niu.IdentityInterface(fields=["srr_volume"]), name="outputnode"
    )

    container = cfg.container
    cfg_reco_base = cfg.reconstruction
    cfg_reco = cfg.reconstruction[container]

    recon = pe.Node(
        interface=niu.Function(
            input_names=[
                "input_stacks",
                "input_masks",
                "cmd",
                "cfg",
                "singularity_path",
                "singularity_mount",
            ],
            output_names=["srr_volume"],
            function=run_recon_cmd,
        ),
        name=cfg_reco_base.pipeline,
    )

    recon.inputs.cmd = cfg_reco.cmd
    recon.inputs.cfg = cfg_reco_base
    # if the container is singularity, add singularity path to the recon node
    if cfg.container == "singularity":
        recon.inputs.singularity_path = cfg.singularity_path
        recon.inputs.singularity_mount = cfg.singularity_mount

    rec_pipe.connect(
        [
            (inputnode, recon, [("stacks", "input_stacks")]),
            (inputnode, recon, [("masks", "input_masks")]),
        ]
    )
    rec_pipe.connect(recon, "srr_volume", outputnode, "srr_volume")
    return rec_pipe


def get_seg(cfg):
    """
    Get the reconstruction workflow based on the pipeline specified
    in params. Currently, the supported pipelines are niftymic and nesvor.

    Params:
        cfg:
            dictionary of parameters (default = {}). This
            dictionary contains the parameters given in a JSON
            config file. It specifies which containers to use
            for each step of the pipeline.
        bids_dir:
            optional string representing the BIDS root directory.
            This is used to find the gestational age if needed.


    Inputs:
        inputnode:
            srr_volume:
                3D reconstructed volume
    Outputs:
        outputnode:
            output_segmentation:
                3D segmented volume
    """
    seg_pipe = pe.Workflow(name="Segmentation")
    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["srr_volume", "gestational_age"]),
        name="inputnode",
    )
    outputnode = pe.Node(
        niu.IdentityInterface(fields=["seg_volume"]), name="outputnode"
    )

    container = cfg.container
    cfg_seg_base = cfg.segmentation
    cfg_seg = cfg.segmentation[container]

    seg = pe.Node(
        interface=niu.Function(
            input_names=[
                "input_srr",
                "cmd",
                "cfg",
                "singularity_path",
                "singularity_mount",
                "gestational_age",
            ],
            output_names=["seg_volume"],
            function=run_seg_cmd,
        ),
        name=cfg_seg_base.pipeline,
    )

    seg.inputs.cmd = cfg_seg.cmd
    seg.inputs.cfg = cfg_seg_base
    if cfg.container == "singularity":
        seg.inputs.singularity_path = cfg.singularity_path
        seg.inputs.singularity_mount = cfg.singularity_mount

    seg_pipe.connect(inputnode, "srr_volume", seg, "input_srr")
    seg_pipe.connect(seg, "seg_volume", outputnode, "seg_volume")
    seg_pipe.connect(inputnode, "gestational_age", seg, "gestational_age")

    return seg_pipe


def create_full_pipeline(
    cfg, load_masks=False, bids_dir=None, name="full_pipeline"
):
    """
    Create the fetal processing pipeline (sub-workflow).

    Given an input of T2w stacks, this pipeline performs the following steps:
        1. Brain extraction using MONAIfbs (dirty wrapper around NiftyMIC's
           command niftymic_segment_fetal_brains)
        2. Denoising using ANTS' DenoiseImage
        3. Perform reconstruction using NiftyMIC's command
            niftymic_run_reconstruction_pipeline

    Params:
        name:
            pipeline name (default = "full_fet_pipe")
        params:
            dictionary of parameters (default = {}). This
            dictionary contains the parameters given in a JSON
            config file. It specifies which containers to use
            for each step of the pipeline.

    Inputs:
        inputnode:
            stacks:
                list of T2w stacks
    Outputs:
        outputnode:
            recon_files:
                list of reconstructed files

    """
    print("Full pipeline name: ", name)
    # Creating pipeline
    full_fet_pipe = pe.Workflow(name=name)

    config.update_config(full_fet_pipe.config)
    # Creating input node

    in_fields = ["stacks"]
    if load_masks:
        in_fields += ["masks"]
    inputnode = pe.Node(
        niu.IdentityInterface(fields=in_fields), name="inputnode"
    )

    enabled_cropping = (
        False if cfg.reconstruction.pipeline == "svrtk" else True
    )
    prepro_pipe = get_prepro(cfg, load_masks, enabled_cropping)
    recon = get_recon(cfg)
    segmentation = get_seg(cfg)

    full_fet_pipe.connect(inputnode, "stacks", prepro_pipe, "inputnode.stacks")

    # RECONSTRUCTION
    full_fet_pipe.connect(
        prepro_pipe, "outputnode.stacks", recon, "inputnode.stacks"
    )
    full_fet_pipe.connect(
        prepro_pipe, "outputnode.masks", recon, "inputnode.masks"
    )

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["output_srr", "output_seg"]),
        name="outputnode",
    )
    full_fet_pipe.connect(
        recon, "outputnode.srr_volume", outputnode, "output_srr"
    )

    # SEGMENTATION
    full_fet_pipe.connect(
        recon, "outputnode.srr_volume", segmentation, "inputnode.srr_volume"
    )

    full_fet_pipe.connect(
        segmentation, "outputnode.seg_volume", outputnode, "output_seg"
    )

    if cfg.segmentation.pipeline == "dhcp" and bids_dir is not None:
        # Create a node to extract the gestational age
        ga_node = pe.Node(
            interface=niu.Function(
                input_names=["bids_dir", "T2"],
                output_names=["gestational_age"],
                function=get_gestational_age,
            ),
            name="GetGestationalAge",
        )
        ga_node.inputs.bids_dir = bids_dir

        # Connect the first stack to the gestational age node
        full_fet_pipe.connect(inputnode, "stacks", ga_node, "T2")

        # Connect the gestational age node to the segmentation node
        full_fet_pipe.connect(
            ga_node,
            "gestational_age",
            segmentation,
            "inputnode.gestational_age",
        )
    # Do we need to pass none to the gestational age?

    return full_fet_pipe


def create_rec_pipeline(cfg, load_masks=False, name="rec_pipeline"):
    """
    Create the fetal processing pipeline (sub-workflow).

    Given an input of T2w stacks, this pipeline performs the following steps:
        1. Brain extraction using MONAIfbs (dirty wrapper around NiftyMIC's
           command niftymic_segment_fetal_brains)
        2. Denoising using ANTS' DenoiseImage
        3. Perform reconstruction using NiftyMIC's command
            niftymic_run_reconstruction_pipeline

    Params:
        name:
            pipeline name (default = "full_fet_pipe")
        params:
            dictionary of parameters (default = {}). This
            dictionary contains the parameters given in a JSON
            config file. It specifies which containers to use
            for each step of the pipeline.

    Inputs:
        inputnode:
            stacks:
                list of T2w stacks
    Outputs:
        outputnode:
            recon_files:
                list of reconstructed files

    """
    print("Full pipeline name: ", name)
    # Creating pipeline
    rec_pipe = pe.Workflow(name=name)
    rec_pipe.config["execution"] = {
        "remove_unnecessary_outputs": True,
        "stop_on_first_crash": True,
        "stop_on_first_rerun": True,
        "crashfile_format": "txt",
        "write_provenance": False,
    }
    config.update_config(rec_pipe.config)
    # Creating input node
    in_fields = ["stacks"]
    if load_masks:
        in_fields += ["masks"]
    inputnode = pe.Node(
        niu.IdentityInterface(fields=in_fields), name="inputnode"
    )

    enabled_cropping = (
        False if cfg.reconstruction.pipeline == "svrtk" else True
    )
    prepro_pipe = get_prepro(cfg, load_masks, enabled_cropping)
    recon = get_recon(cfg)

    rec_pipe.connect(inputnode, "stacks", prepro_pipe, "inputnode.stacks")
    if load_masks:
        rec_pipe.connect(inputnode, "masks", prepro_pipe, "inputnode.masks")
    # RECONSTRUCTION

    rec_pipe.connect(
        prepro_pipe, "outputnode.stacks", recon, "inputnode.stacks"
    )
    rec_pipe.connect(prepro_pipe, "outputnode.masks", recon, "inputnode.masks")

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["output_srr", "output_seg"]),
        name="outputnode",
    )
    rec_pipe.connect(recon, "outputnode.srr_volume", outputnode, "output_srr")

    return rec_pipe


def create_seg_pipeline(cfg, bids_dir=None, name="seg_pipeline"):
    """
    Create the fetal processing pipeline (sub-workflow).

    Given an input of T2w stacks, this pipeline performs the following steps:
        1. Brain extraction using MONAIfbs (dirty wrapper around NiftyMIC's
           command niftymic_segment_fetal_brains)
        2. Denoising using ANTS' DenoiseImage
        3. Perform reconstruction using NiftyMIC's command
            niftymic_run_reconstruction_pipeline

    Params:
        name:
            pipeline name (default = "full_fet_pipe")
        params:
            dictionary of parameters (default = {}). This
            dictionary contains the parameters given in a JSON
            config file. It specifies which containers to use
            for each step of the pipeline.

    Inputs:
        inputnode:
            stacks:
                list of T2w stacks
    Outputs:
        outputnode:
            recon_files:
                list of reconstructed files

    """
    print("Full pipeline name: ", name)
    # Creating pipeline
    seg_pipe = pe.Workflow(name=name)
    seg_pipe.config["execution"] = {
        "remove_unnecessary_outputs": True,
        "stop_on_first_crash": True,
        "stop_on_first_rerun": True,
        "crashfile_format": "txt",
        # "use_relative_paths": True,
        "write_provenance": False,
    }

    config.update_config(seg_pipe.config)
    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["srr_volume"]), name="inputnode"
    )

    segmentation = get_seg(cfg)

    seg_pipe.connect(
        inputnode, "srr_volume", segmentation, "inputnode.srr_volume"
    )

    if cfg.segmentation.pipeline == "dhcp" and bids_dir is not None:
        # Create a node to extract the gestational age
        ga_node = pe.Node(
            interface=niu.Function(
                input_names=["bids_dir", "T2"],
                output_names=["gestational_age"],
                function=get_gestational_age,
            ),
            name="GetGestationalAge",
        )
        ga_node.inputs.bids_dir = bids_dir
        # Connect the T2
        seg_pipe.connect(inputnode, "srr_volume", ga_node, "T2")
        # Connect the gestational age node to the segmentation node
        seg_pipe.connect(
            ga_node,
            "gestational_age",
            segmentation,
            "inputnode.gestational_age",
        )

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["output_seg"]),
        name="outputnode",
    )
    seg_pipe.connect(
        segmentation, "outputnode.seg_volume", outputnode, "output_seg"
    )

    return seg_pipe

import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe
from ..nodes.preprocessing import (
    CropStacksAndMasks,
    CheckAffineResStacksAndMasks,
    CheckAndSortStacksAndMasks,
    run_prepro_cmd,
)
from ..nodes.dhcp import dhcp_pipeline
from nipype import config
from fetpype.nodes.reconstruction import run_recon_cmd
from fetpype.nodes.segmentation import run_seg_cmd
from fetpype.nodes.surface_extraction import run_surf_cmd


def print_files(files):
    print("Files:")
    print(files)
    return files


def get_prepro(cfg, load_masks=False, enabled_cropping=False):
    """
    Create the preprocessing workflow based on config `cfg`.
    Given an input of T2w stacks, this pipeline performs the following steps:
        1. Brain extraction using MONAIfbs
        2. Check stacks and masks
        3. Check affine and resolution of stacks and masks
        4. Cropping stacks and masks
        5. Denoising stacks
        6. Bias field correction of stacks

    Args:
        cfg: Configuration object containing the parameters for the pipeline.
        load_masks: Boolean indicating whether to load masks or
                    perform brain extraction.
        enabled_cropping:   Boolean indicating whether cropping is enabled.
                            This is typically set to False for SVRTK
                            pipelines, as they handle cropping internally.

    Returns:
        prepro_pipe:    A Nipype workflow object that contains
                        the preprocessing steps.

    """
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
    in the config `cfg`.

    Args:
        cfg: Configuration object containing the parameters for the pipeline.

    Returns:
        rec_pipe:   A Nipype workflow object that contains
                    the reconstruction steps.
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
    Get the segmentation workflow based on the pipeline specified
    in the config `cfg`.

    Args:
        cfg: Configuration object containing the parameters for the pipeline.
    Returns:
        seg_pipe:   A Nipype workflow object that contains
                    the segmentation steps.
    """
    seg_pipe = pe.Workflow(name="Segmentation")
    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["srr_volume"]), name="inputnode"
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
                "singularity_home",
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
        seg.inputs.singularity_home = cfg.singularity_home

    seg_pipe.connect(inputnode, "srr_volume", seg, "input_srr")
    seg_pipe.connect(seg, "seg_volume", outputnode, "seg_volume")

    return seg_pipe


def get_surf(cfg):
    """
    Get the surface extraction workflow based on the pipeline specified
    in the config `cfg`.

    Args:
        cfg: Configuration object containing the parameters for the pipeline.
    Returns:
        surf_pipe:   A Nipype workflow object that contains
                    the surface extraction steps.
    """
    surf_pipe = pe.Workflow(name="SurfaceExtraction_lh")
    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["seg_volume"]), name="inputnode"
    )
    outputnode = pe.Node(
        niu.IdentityInterface(fields=["surf_volume_lh", "surf_volume_rh"]), name="outputnode"
    )

    print(cfg)

    0/0

    container = cfg.container
    cfg_surf_base = cfg.surface
    cfg_surf = cfg.surface[container]

    surf_lh= pe.Node(
        interface=niu.Function(
            input_names=[
                "input_seg",
                "cmd",
                "cfg",
                "singularity_path",
                "singularity_mount",
                "singularity_home",
            ],
            output_names=["surf_volume_lh"],
            function=run_surf_cmd,
        ),
        name="surf_lh",
    )

    surf_lh.inputs.cmd = cfg_surf.cmd
    surf_lh.inputs.cfg = cfg_surf_base.surface_lh

    if cfg.container == "singularity":
        surf_lh.inputs.singularity_path = cfg.singularity_path
        surf_lh.inputs.singularity_mount = cfg.singularity_mount
        surf_lh.inputs.singularity_home = cfg.singularity_home

    surf_pipe.connect(inputnode, "seg_volume", surf_lh, "input_seg")
    surf_pipe.connect(surf_lh, "surf_volume", outputnode, "surf_volume_lh")



    surf_rh= pe.Node(
        interface=niu.Function(
            input_names=[
                "input_seg",
                "cmd",
                "cfg",
                "singularity_path",
                "singularity_mount",
                "singularity_home",
            ],
            output_names=["surf_volume_rh"],
            function=run_surf_cmd,
        ),
        name="surf_rh",
    )

    surf_rh.inputs.cmd = cfg_surf.cmd
    surf_rh.inputs.cfg = cfg_surf_base.surface_rh

    if cfg.container == "singularity":
        surf_rh.inputs.singularity_path = cfg.singularity_path
        surf_rh.inputs.singularity_mount = cfg.singularity_mount
        surf_rh.inputs.singularity_home = cfg.singularity_home

    surf_pipe.connect(inputnode, "seg_volume", surf_rh, "input_seg")
    surf_pipe.connect(surf_rh, "surf_volume", outputnode, "surf_volume_rh")

    return surf_pipe



def create_full_pipeline(cfg, load_masks=False, name="full_pipeline"):
    """
    Create a full fetal processing pipeline by combining preprocessing,
    reconstruction, and segmentation workflows.

    Args:
        cfg: Configuration object containing the parameters for the pipeline.
        load_masks: Boolean indicating whether to load masks or perform
                    brain extraction.
        name: Name of the pipeline (default = "full_pipeline").

    Returns:
        full_fet_pipe:  A Nipype workflow object that contains
                        the full pipeline steps.

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

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["output_srr", "output_seg", "output_surf_lh", "output_surf_rh"]
        ),
        name="outputnode",
    )

    enabled_cropping = (
        False if cfg.reconstruction.pipeline == "svrtk" else True
    )
    prepro_pipe = get_prepro(cfg, load_masks, enabled_cropping)
    recon = get_recon(cfg)
    segmentation = get_seg(cfg)

    surface = get_surf(cfg)

    # PREPROCESSING

    full_fet_pipe.connect(inputnode, "stacks", prepro_pipe, "inputnode.stacks")

    # RECONSTRUCTION

    full_fet_pipe.connect(
        prepro_pipe, "outputnode.stacks", recon, "inputnode.stacks"
    )
    full_fet_pipe.connect(
        prepro_pipe, "outputnode.masks", recon, "inputnode.masks"
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

    # SURFACE EXTRACTION

    full_fet_pipe.connect(
        segmentation, "outputnode.seg_volume", surface, "inputnode.seg_volume"
    )

    full_fet_pipe.connect(
        surface, "outputnode.surf_volume_lh", outputnode, "output_surf_lh"
    )

    full_fet_pipe.connect(
        surface, "outputnode.surf_volume_rh", outputnode, "output_surf_rh"
    )

    return full_fet_pipe


def create_rec_pipeline(cfg, load_masks=False, name="rec_pipeline"):
    """
    Create the reconstruction workflow based on the pipeline specified
    in the config `cfg`.

    Args:
        cfg: Configuration object containing the parameters for the pipeline.
        load_masks: Boolean indicating whether to load masks or perform
                    brain extraction.
        name: Name of the pipeline (default = "rec_pipeline").

    Returns:
        rec_pipe: A Nipype workflow object that contains the
                  reconstruction steps.
    """
    print("Full pipeline name: ", name)
    # Creating pipeline
    rec_pipe = pe.Workflow(name=name)
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


def create_seg_pipeline(cfg, name="seg_pipeline"):
    """
    Create the segmentation workflow based on the pipeline specified
    in the config `cfg`.

    Args:
        cfg: Configuration object containing the parameters for the pipeline.
        name: Name of the pipeline (default = "seg_pipeline").
    Returns:
        seg_pipe: A Nipype workflow object that contains the segmentation steps
    """
    print("Full pipeline name: ", name)
    # Creating pipeline
    seg_pipe = pe.Workflow(name=name)
    config.update_config(seg_pipe.config)
    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["srr_volume"]), name="inputnode"
    )

    segmentation = get_seg(cfg)

    seg_pipe.connect(
        inputnode, "srr_volume", segmentation, "inputnode.srr_volume"
    )

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["output_seg"]),
        name="outputnode",
    )
    seg_pipe.connect(
        segmentation, "outputnode.seg_volume", outputnode, "output_seg"
    )

    return seg_pipe


def create_surf_pipeline(cfg, name="surf_pipeline"):
    """
    Create the surface extraction workflow based on the pipeline
    specified in the config `cfg`.

    Args:
        cfg: Configuration object containing the parameters for the pipeline.
        name: Name of the pipeline (default = "surf_pipeline").
    Returns:
        surf_pipe: A Nipype workflow object that contains the
            surface extraction steps
    """
    print("Full pipeline name: ", name)
    # Creating pipeline
    surf_pipe = pe.Workflow(name=name)
    config.update_config(surf_pipe.config)
    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["seg_volume"]), name="inputnode"
    )

    surface = get_surf(cfg)

    surf_pipe.connect(inputnode, "seg_volume", surface, "inputnode.seg_volume")

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["output_surf"]),
        name="outputnode",
    )
    surf_pipe.connect(
        surface, "outputnode.surf_volume", outputnode, "output_surf"
    )

    return surf_pipe


def create_dhcp_subpipe(name="dhcp_pipe", params={}):
    """
    Deprecated: Create a dHCP pipeline for fetal brain segmentation
    and surface extraction.
    """

    print("Full pipeline name: ", name)

    # Creating pipeline
    full_fet_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["T2", "mask", "gestational_age"]),
        name="inputnode",
    )

    # Check params to see if we need to run the seg or surf part, or both.
    # Params to look is [dhcp][seg] and [dhcp][surf]
    flag = None
    if "dhcp" in params.keys():
        if params["dhcp"]["surf"] and params["dhcp"]["seg"]:
            flag = "-all"
        elif params["dhcp"]["seg"]:
            flag = "-seg"
        elif params["dhcp"]["surf"]:
            flag = "-surf"

    else:
        print("No dhcp parameters found, running both seg and surf")
        flag = "-all"

    # PREPROCESSING
    # 1. Run the dhcp pipeline for segmentation
    dhcp_seg = pe.Node(
        interface=niu.Function(
            input_names=[
                "T2",
                "mask",
                "gestational_age",
                "pre_command",
                "dhcp_image",
                "threads",
                "flag",
            ],
            output_names=["dhcp_files"],
            function=dhcp_pipeline,
        ),
        name="dhcp_seg",
    )

    if "general" in params.keys():
        dhcp_seg.inputs.pre_command = params["general"].get("pre_command", "")
        dhcp_seg.inputs.dhcp_image = params["general"].get("dhcp_image", "")

    if "dhcp" in params.keys():
        dhcp_seg.inputs.threads = params["dhcp"].get("threads", "")
        dhcp_seg.inputs.flag = flag

    full_fet_pipe.connect(inputnode, "T2", dhcp_seg, "T2")
    full_fet_pipe.connect(inputnode, "mask", dhcp_seg, "mask")

    full_fet_pipe.connect(
        inputnode, "gestational_age", dhcp_seg, "gestational_age"
    )

    # OUTPUT
    outputnode = pe.Node(
        niu.IdentityInterface(fields=["dhcp_files"]), name="outputnode"
    )

    full_fet_pipe.connect(dhcp_seg, "dhcp_files", outputnode, "dhcp_files")

    return full_fet_pipe

import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from nipype.interfaces.ants.segmentation import DenoiseImage

# from nipype.interfaces.ants import N4BiasFieldCorrection


from ..nodes.preprocessing import (
    nesvor_brain_extraction,
    niftymic_brain_extraction,
    CropStacksAndMasks,
)
from ..nodes.dhcp import dhcp_pipeline
from nipype import config
from fetpype.nodes.reconstruction import run_recon_cmd
from fetpype.nodes.segmentation import run_seg_cmd

# from nipype import config
# config.enable_debug_mode()


def print_files(files):
    print("Files:")
    print(files)
    return files


def get_prepro(cfg):
    container = cfg.container
    cfg_prepro = cfg.preprocessing
    be_config = cfg_prepro.brain_extraction[container]

    prepro_pipe = pe.Workflow(name="Pre-processing")
    # Creating input node
    input = pe.Node(niu.IdentityInterface(fields=["stacks"]), name="inputnode")
    output = pe.Node(
        niu.IdentityInterface(fields=["stacks", "masks"]), name="outputnode"
    )

    # PREPROCESSING
    # 1. Brain extraction
    brain_extraction = pe.Node(
        interface=niu.Function(
            input_names=["raw_T2s", "pre_command", "nesvor_image"],
            output_names=["masks"],
            function=nesvor_brain_extraction,
        ),
        name="brain_extraction",
    )

    brain_extraction.inputs.pre_command = be_config.pre_command
    brain_extraction.inputs.nesvor_image = be_config.image

    prepro_pipe.connect(input, "stacks", brain_extraction, "raw_T2s")

    # 2. Cropping
    cropping = pe.MapNode(
        interface=CropStacksAndMasks(),
        iterfield=["input_image", "input_mask"],
        name="cropping",
    )

    prepro_pipe.connect(input, "stacks", cropping, "input_image")
    prepro_pipe.connect(brain_extraction, "masks", cropping, "input_mask")

    # 3. Denoising
    denoising = pe.MapNode(
        interface=DenoiseImage(), iterfield=["input_image"], name="denoising"
    )

    prepro_pipe.connect(cropping, "output_image", denoising, "input_image")

    # merge_denoise
    merge_denoise = pe.Node(
        interface=niu.Merge(1, ravel_inputs=True), name="merge_denoise"
    )

    prepro_pipe.connect(denoising, "output_image", merge_denoise, "in1")
    prepro_pipe.connect(
        [
            (merge_denoise, output, [("out", "stacks")]),
            (cropping, output, [("output_mask", "masks")]),
        ]
    )
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
            ],
            output_names=["srr_volume"],
            function=run_recon_cmd,
        ),
        name=cfg_reco_base.pipeline,
    )

    recon.inputs.cmd = cfg_reco.cmd
    recon.inputs.cfg = cfg_reco_base

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
        params:
            dictionary of parameters (default = {}). This
            dictionary contains the parameters given in a JSON
            config file. It specifies which containers to use
            for each step of the pipeline.

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
            ],
            output_names=["seg_volume"],
            function=run_seg_cmd,
        ),
        name=cfg_seg_base.pipeline,
    )

    seg.inputs.cmd = cfg_seg.cmd
    seg.inputs.cfg = cfg_seg_base

    seg_pipe.connect(inputnode, "srr_volume", seg, "input_srr")
    seg_pipe.connect(seg, "seg_volume", outputnode, "seg_volume")

    return seg_pipe


def create_fet_subpipes(cfg, name="full_fet_pipe"):
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
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["stacks"]), name="inputnode"
    )
    print("Full pipeline name: ", name)
    # Creating pipeline
    full_fet_pipe = pe.Workflow(name=name)
    full_fet_pipe.config["execution"] = {
        "remove_unnecessary_outputs": True,
        "stop_on_first_crash": True,
        "stop_on_first_rerun": True,
        "crashfile_format": "txt",
        # "use_relative_paths": True,
        "write_provenance": False,
    }
    config.update_config(full_fet_pipe.config)
    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["stacks"]), name="inputnode"
    )

    prepro_pipe = get_prepro(cfg)
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

    full_fet_pipe.connect(
        recon, "outputnode.srr_volume", segmentation, "inputnode.srr_volume"
    )

    full_fet_pipe.connect(
        segmentation, "outputnode.seg_volume", outputnode, "output_seg"
    )

    return full_fet_pipe


def create_dhcp_subpipe(name="dhcp_pipe", params={}):
    """
    Create a dhcp pipeline for segmentation of fetal MRI

    Given an reconstruction of fetal MRI and a mask, this
    pipeline performs the following steps:
        1. Run the dhcp pipeline for segmentation
        2. Run it for surface extraction

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
            MRI brain:
                Reconstruction of MRI brain
            Mask:
                Corresponding brain mask of the reconstruction
            GA:
                gestational age of the fetus
    Outputs:
        outputnode:
            dhcp_files:
                folder with dhcp outputs

    TODO:
    - EM algorithm halting, solve it better or in the messy way?
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

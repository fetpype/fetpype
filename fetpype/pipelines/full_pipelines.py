import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from fetpype.nodes.niftymic import niftymic_segment, niftymic_recon
from nipype.interfaces.ants.segmentation import DenoiseImage
from ..nodes.nesvor import (
    NesvorSegmentation,
    NesvorRegistration,
    NesvorReconstruction,
    NesvorFullReconstruction,
)

from ..nodes.dhcp import dhcp_segment, dhcp_surface

# from nipype import config
# config.enable_debug_mode()


def print_files(files):
    print("Files:")
    print(files)
    return files


def create_nesvor_subpipes_fullrecon(name="nesvor_pipe_full", params={}):
    """Nesvor based segmentation pipeline for fetal MRI

    Processing steps:
    - Brain extraction using MONAIfbs ( using the nesvor_image container)
    - Denoising using ANTS' DenoiseImage
    - Registration of slices using SVORT
    - Reconstruction using NesVoR

    Difference with the other pipeline is that we use the full reconstruction
    command from NesVoR, instead of each part separately

    Params:
    - name: pipeline name (default = "nesvor_pipe")
    - params: dictionary of parameters to be passed to the pipeline. We would
        need to specify the nesvor_image and pre_command parameters,
        right now.

    Outputs:
    - nesvor_pipe: nipype workflow implementing the pipeline
    """
    # get parameters
    if "general" in params.keys():
        pre_command = params["general"].get("pre_command", "")
        nesvor_image = params["general"].get("nesvor_image", "")

    # Creating pipeline
    nesvor_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["stacks"]), name="inputnode"
    )

    # PREPROCESSING
    # 1. Denoising
    denoising = pe.MapNode(
        interface=DenoiseImage(), iterfield=["input_image"], name="denoising"
    )

    nesvor_pipe.connect(inputnode, "stacks", denoising, "input_image")

    # merge_denoise
    merge_denoise = pe.Node(
        interface=niu.Merge(1, ravel_inputs=True), name="merge_denoise"
    )

    nesvor_pipe.connect(denoising, "output_image", merge_denoise, "in1")

    # 2 full recon
    full_recon = pe.Node(
        NesvorFullReconstruction(
            nesvor_image=nesvor_image, pre_command=pre_command
        ),
        name="full_recon",
    )
    nesvor_pipe.connect(merge_denoise, "out", full_recon, "input_stacks")

    # output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=["output_volume"]), name="outputnode"
    )

    nesvor_pipe.connect(
        full_recon, "output_volume", outputnode, "output_volume"
    )
    return nesvor_pipe


def create_nesvor_subpipes(name="nesvor_pipe", params={}):
    """Nesvor based segmentation pipeline for fetal MRI

    Processing steps:
    - Brain extraction using MONAIfbs ( using the nesvor_image container)
    - Denoising using ANTS' DenoiseImage
    - Registration of slices using SVORT
    - Reconstruction using NesVoR

    Params:
    - name: pipeline name (default = "nesvor_pipe")
    - params: dictionary of parameters to be passed to the pipeline. We would
        need to specify the nesvor_image and pre_command parameters,
        right now.

    Outputs:
    - nesvor_pipe: nipype workflow implementing the pipeline
    """

    # get parameters
    if "general" in params.keys():
        pre_command = params["general"].get("pre_command", "")
        nesvor_image = params["general"].get("nesvor_image", "")

    # Creating pipeline
    nesvor_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["stacks"]), name="inputnode"
    )

    # PREPROCESSING
    # 1. Denoising
    denoising = pe.MapNode(
        interface=DenoiseImage(), iterfield=["input_image"], name="denoising"
    )

    nesvor_pipe.connect(inputnode, "stacks", denoising, "input_image")

    # merge_denoise
    merge_denoise = pe.Node(
        interface=niu.Merge(1, ravel_inputs=True), name="merge_denoise"
    )

    nesvor_pipe.connect(denoising, "output_image", merge_denoise, "in1")

    # 2. Brain extraction
    mask = pe.Node(
        NesvorSegmentation(
            nesvor_image=nesvor_image,
            pre_command=pre_command,
            no_augmentation_seg=True,
        ),
        name="mask",
    )

    # 3. REGISTRATION WITH SVORT
    # registration Node
    registration = pe.Node(
        NesvorRegistration(nesvor_image=nesvor_image, pre_command=pre_command),
        name="registration",
    )

    nesvor_pipe.connect(
        [
            (merge_denoise, mask, [("out", "input_stacks")]),
            (merge_denoise, registration, [("out", "input_stacks")]),
            (mask, registration, [("output_stack_masks", "stack_masks")]),
        ]
    )

    # 4. RECONSTRUCTION
    # recon Node
    recon = pe.Node(
        NesvorReconstruction(
            nesvor_image=nesvor_image, pre_command=pre_command
        ),
        name="reconstruction",
    )

    nesvor_pipe.connect(registration, "output_slices", recon, "input_slices")

    # output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=["output_volume"]), name="outputnode"
    )

    nesvor_pipe.connect(recon, "output_volume", outputnode, "output_volume")
    return nesvor_pipe


def create_fet_subpipes(name="full_fet_pipe", params={}):
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

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["stacks"]), name="inputnode"
    )

    # PREPROCESSING
    # 1. Brain extraction
    brain_extraction = pe.Node(
        interface=niu.Function(
            input_names=["raw_T2s", "pre_command", "niftymic_image"],
            output_names=["bmasks"],
            function=niftymic_segment,
        ),
        name="brain_extraction",
    )

    if "general" in params.keys():
        brain_extraction.inputs.pre_command = params["general"].get(
            "pre_command", ""
        )
        brain_extraction.inputs.niftymic_image = params["general"].get(
            "niftymic_image", ""
        )

    full_fet_pipe.connect(inputnode, "stacks", brain_extraction, "raw_T2s")

    # 2. Denoising
    denoising = pe.MapNode(
        interface=DenoiseImage(), iterfield=["input_image"], name="denoising"
    )

    full_fet_pipe.connect(inputnode, "stacks", denoising, "input_image")

    # merge_denoise
    merge_denoise = pe.Node(
        interface=niu.Merge(1, ravel_inputs=True), name="merge_denoise"
    )

    full_fet_pipe.connect(denoising, "output_image", merge_denoise, "in1")

    # RECONSTRUCTION
    recon = pe.Node(
        interface=niu.Function(
            input_names=["stacks", "masks", "pre_command", "niftymic_image"],
            output_names=["recon_files"],
            function=niftymic_recon,
        ),
        name="recon",
    )

    if "general" in params.keys():
        recon.inputs.pre_command = params["general"].get("pre_command", "")
        recon.inputs.niftymic_image = params["general"].get(
            "niftymic_image", ""
        )

    # OUTPUT
    full_fet_pipe.connect(merge_denoise, "out", recon, "stacks")
    full_fet_pipe.connect(brain_extraction, "bmasks", recon, "masks")

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["recon_files"]), name="outputnode"
    )

    full_fet_pipe.connect(recon, "recon_files", outputnode, "recon_files")

    return full_fet_pipe


def create_dhcp_subpipe(name="dhcp_pipe", params={}):
    """
    Create a dhcp pipeline for segmentation of fetal MRI

    Given an reconstruction of fetal MRI and a mask, this pipeline performs the following steps:
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
    - define the parameters in a better way
    - EM algorithm halting, solve it better or in the messy way?
    - Do the masking (BET?) if no mask provided?
    - Ignore masking if the T2 is already masked? (but we need to provide the mask anyway)
    """

    print("Full pipeline name: ", name)

    # Creating pipeline
    full_fet_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=["T2", "mask", "gestational_age"]
        ),
        name="inputnode",
    )

    # PREPROCESSING
    # 1. Run the dhcp pipeline for segmentation
    dhcp_seg = pe.Node(
        interface=niu.Function(
            input_names=["T2", "mask", "gestational_age", "pre_command", "dhcp_image"],
            output_names=["dhcp_files"],
            function=dhcp_segment,
        ),
        name="dhcp_seg",
    )

    if "general" in params.keys():
        dhcp_seg.inputs.pre_command = params["general"].get("pre_command", "")
        dhcp_seg.inputs.dhcp_image = params["general"].get(
            "dhcp_image", ""
        )

    full_fet_pipe.connect(
        inputnode, "T2", dhcp_seg, "T2"
    )
    full_fet_pipe.connect(
        inputnode, "mask", dhcp_seg, "mask"
    )

    full_fet_pipe.connect(
        inputnode, "gestational_age", dhcp_seg, "gestational_age"
    )

    # 2. Run it for surface extraction
    """
    dhcp_surf = pe.Node(
        interface=niu.Function(
            input_names=["dhcp_files"],
            output_names=["dhcp_files"],
            function=dhcp_surface,
        ),
        name="dhcp_surf",
    )

    if "general" in params.keys():
        dhcp_surf.inputs.pre_command = params["general"].get("pre_command", "")
        dhcp_surf.inputs.image = params["general"].get(
            "dhcp_image", ""
        )

    full_fet_pipe.connect(
        dhcp_seg, "dhcp_files", dhcp_surf, "dhcp_files"
    )
    """
    # OUTPUT
    outputnode = pe.Node(
        niu.IdentityInterface(fields=["dhcp_files"]), name="outputnode"
    )

    full_fet_pipe.connect(dhcp_seg, "dhcp_files", outputnode, "dhcp_files")

    return full_fet_pipe

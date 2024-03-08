import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from fetpype.nodes.niftymic import niftymic_recon
from nipype.interfaces.ants.segmentation import DenoiseImage

from ..nodes.nesvor import (
    NesvorSegmentation,
    NesvorRegistration,
    NesvorReconstruction,
    NesvorFullReconstruction,
)

from ..nodes.preprocessing import (
    nesvor_brain_extraction,
    niftymic_brain_extraction,
    CropStacksAndMasks,
)
from ..nodes.dhcp import dhcp_pipeline

# from nipype import config
# config.enable_debug_mode()


def print_files(files):
    print("Files:")
    print(files)
    return files

def get_recon(params):
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
            output_volume:
                3D reconstructed volume
    """
    rec_pipe = pe.Workflow(name="Reconstruction")
    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["stacks", "masks"]), name="inputnode"
    )
    outputnode = pe.Node(
        niu.IdentityInterface(fields=["output_volume"]), name="outputnode"
    )

    pipeline = params["general"].get("pipeline", "")
    pre_command = params["general"].get("pre_command", "")

    if pipeline == "niftymic":
        recon = pe.Node(
            interface=niu.Function(
                input_names=[
                    "stacks",
                    "masks",
                    "pre_command",
                    "niftymic_image",
                ],
                output_names=["output_volume"],
                function=niftymic_recon,
            ),
            name="recon",
        )
        if "general" in params.keys():
            recon.inputs.pre_command = pre_command
            recon.inputs.niftymic_image = params["general"].get(
                "niftymic_image", ""
            )

        # OUTPUT
        rec_pipe.connect(inputnode, "stacks", recon, "stacks")
        rec_pipe.connect(inputnode, "masks", recon, "masks")
    elif pipeline == "nesvor":
        nesvor_image = params["general"].get("nesvor_image", "")
        recon = pe.Node(
            NesvorFullReconstruction(
                container_image=nesvor_image, pre_command=pre_command
            ),
            name="full_recon",
        )

        rec_pipe.connect(
            [
                (inputnode, recon, [("stacks", "input_stacks")]),
                (inputnode, recon, [("masks", "stack_masks")]),
            ]
        )
    else:
        raise ValueError(f"Pipeline {pipeline} not recognized")

    rec_pipe.connect(recon, "output_volume", outputnode, "output_volume")
    return rec_pipe


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
            input_names=["raw_T2s", "pre_command", "nesvor_image"],
            output_names=["masks"],
            function=nesvor_brain_extraction,
        ),
        name="brain_extraction",
    )

    if "general" in params.keys():
        brain_extraction.inputs.pre_command = params["general"].get(
            "pre_command", ""
        )
        brain_extraction.inputs.nesvor_image = params["general"].get(
            "nesvor_image", ""
        )

    full_fet_pipe.connect(inputnode, "stacks", brain_extraction, "raw_T2s")

    # 2. Cropping
    cropping = pe.MapNode(
        interface=CropStacksAndMasks(),
        iterfield=["input_image", "input_mask"],
        name="cropping",
    )

    full_fet_pipe.connect(inputnode, "stacks", cropping, "input_image")
    full_fet_pipe.connect(brain_extraction, "masks", cropping, "input_mask")

    # 3. Denoising
    denoising = pe.MapNode(
        interface=DenoiseImage(), iterfield=["input_image"], name="denoising"
    )

    full_fet_pipe.connect(cropping, "output_image", denoising, "input_image")

    # merge_denoise
    merge_denoise = pe.Node(
        interface=niu.Merge(1, ravel_inputs=True), name="merge_denoise"
    )

    full_fet_pipe.connect(denoising, "output_image", merge_denoise, "in1")

    # RECONSTRUCTION
    recon = get_recon(params)

    full_fet_pipe.connect(
        [
            (merge_denoise, recon, [("out", "inputnode.stacks")]),
            (cropping, recon, [("output_mask", "inputnode.masks")]),
        ]
    )

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["output_volume"]), name="outputnode"
    )
    full_fet_pipe.connect(
        recon, "outputnode.output_volume", outputnode, "output_volume"
    )

    return full_fet_pipe


def create_minimal_subpipes(name="minimal_pipe", params={}):
    """
    Create minimal pipeline (sub-workflow).

    Given an input, this pipeline performs BrainExtraction
    using NiftiMic in docker version

    Params:
        name:
            pipeline name (default = "minimal_pipe")
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
                list of reconstructed files

    """

    print("Full pipeline name: ", name)

    # Creating pipeline
    minimal_pipe = pe.Workflow(name=name)

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
            function=niftymic_brain_extraction,
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

    minimal_pipe.connect(inputnode, "stacks", brain_extraction, "raw_T2s")

    # OUTPUT
    outputnode = pe.Node(
        niu.IdentityInterface(fields=["masks"]), name="outputnode"
    )

    minimal_pipe.connect(brain_extraction, "bmasks", outputnode, "masks")

    return minimal_pipe


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

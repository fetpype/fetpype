import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe
from nipype.interfaces.ants.segmentation import DenoiseImage

from ..nodes.niftymic import (
    NiftymicBrainExtraction,
    NiftymicReconstructionPipeline
)
# from ..nodes.preprocessing import niftymic_brain_extraction
from ..nodes.preprocessing import (
    CropStacksAndMasks,
)

# from nipype import config
# config.enable_debug_mode()


def print_files(files):
    print("Files:")
    print(files)
    return files


def create_niftymic_subpipes(name="niftymic_pipe", params={}):
    """niftymic based pipeline for fetal MRI

    Processing steps:
    - Reconstruction using Niftymic

    Params:
    - name: pipeline name (default = "niftymic_pipe")
    - params: dictionary of parameters to be passed to the pipeline. We would
        need to specify the nifty_image and pre_command parameters,
        right now.

    Outputs:
    - niftymic_pipe: nipype workflow implementing the pipeline
    """

    # get parameters
    if "general" in params.keys():
        pre_command = params["general"].get("pre_command", "")
        niftymic_image = params["general"].get("niftymic_image", "")

    # Creating pipeline
    niftymic_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["stacks", "masks"]), name="inputnode"
    )

    # PREPROCESSING
    # 1. Brain extraction
    brain_extraction = pe.Node(
        NiftymicBrainExtraction(
            container_image=niftymic_image, pre_command=pre_command
        ),
        name="brain_extraction",
    )

    niftymic_pipe.connect(inputnode, "stacks",
                          brain_extraction, "input_stacks")

    # 2 denoising
    denoising = pe.MapNode(
        interface=DenoiseImage(), iterfield=["input_image"], name="denoising"
    )

    niftymic_pipe.connect(inputnode, "stacks", denoising, "input_image")

    # merge_denoise
    merge_denoise = pe.Node(
        interface=niu.Merge(1, ravel_inputs=True), name="merge_denoise"
    )

    niftymic_pipe.connect(denoising, "output_image", merge_denoise, "in1")

    # 3. Cropping
    cropping = pe.MapNode(
        interface=CropStacksAndMasks(),
        iterfield=["input_image", "input_mask"],
        name="cropping",
    )

    niftymic_pipe.connect(merge_denoise, "out", cropping, "input_image")
    niftymic_pipe.connect(brain_extraction,
                          "output_bmasks",
                          cropping,
                          "input_mask")

    # merge_masks
    merge_crops = pe.Node(
        interface=niu.Merge(1, ravel_inputs=True), name="merge_crops"
    )
    merge_masks = pe.Node(
        interface=niu.Merge(1, ravel_inputs=True), name="merge_masks"
    )

    niftymic_pipe.connect(cropping, "output_mask", merge_masks, "in1")
    niftymic_pipe.connect(cropping, "output_image", merge_crops, "in1")

    # 2. RECONSTRUCTION
    # recon Node
    recon = pe.Node(
        NiftymicReconstructionPipeline(
            container_image=niftymic_image, pre_command=pre_command
        ),
        name="recon",
    )

    niftymic_pipe.connect(merge_crops, "out", recon, "input_stacks")
    niftymic_pipe.connect(merge_masks, "out",
                          recon, "input_masks")

    # output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=["recon_file", "recon_mask_file"]),
        name="outputnode"
    )

    niftymic_pipe.connect(recon, "dir_output", outputnode, "recon_file")
    niftymic_pipe.connect(recon, "dir_output",
                          outputnode, "recon_mask_file")
    return niftymic_pipe

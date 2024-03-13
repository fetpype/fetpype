import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe
from nipype.interfaces.ants.segmentation import DenoiseImage

from ..nodes.nesvor import (
    NesvorFullReconstruction,
    NesvorSegmentation
)

from ..nodes.preprocessing import (
    CropStacksAndMasks,
    copy_header
)


def create_nesvor_subpipes(name="nesvor_pipe", params={}):
    """Nesvor based pipeline for fetal MRI

    Processing steps:
    - Segmentation using Nesvor
    - Registration using Nesvor
    - Reconstruction using Nesvor
    Parameters
    ----------
    name : str, optional
        name of the pipeline in nipype, by default "nesvor_pipe"
    params : dict, optional
        dictionary of parameters to be passed to the pipeline. We would
        need to specify the nesvor_image and pre_command parameters,
        right now. by default {}

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

    # 1 denoising
    denoising = pe.MapNode(
        interface=DenoiseImage(), iterfield=["input_image"], name="denoising"
    )

    nesvor_pipe.connect(inputnode, "stacks", denoising, "input_image")

    # 2. Brain extraction
    mask = pe.Node(
        NesvorSegmentation(
            container_image=nesvor_image,
            pre_command=pre_command,
        ),
        name="mask",
    )

    # mandatory for curr version, else, error
    mask.inputs.no_augmentation_seg = True
    nesvor_pipe.connect(inputnode, "stacks", mask, "input_stacks")

    # 1.1 node to copy the header of the input image to the denoise output
    copy_header_node = pe.MapNode(
        interface=niu.Function(
            input_names=["in_file", "ref_file"],
            output_names="out_file",
            function=copy_header
        ),
        iterfield=["in_file", "ref_file"],
        name="copy_header",
    )

    nesvor_pipe.connect(mask,
                        "output_stack_masks",
                        copy_header_node,
                        "ref_file")
    nesvor_pipe.connect(denoising, "output_image", copy_header_node, "in_file")

    # 3. Cropping
    cropping = pe.MapNode(
        interface=CropStacksAndMasks(),
        iterfield=["input_image", "input_mask"],
        name="cropping",
    )

    nesvor_pipe.connect(mask, "output_stack_masks", cropping, "input_mask")
    nesvor_pipe.connect(copy_header_node, "out_file", cropping, "input_image")

    # merge_masks
    merge_crops = pe.Node(
        interface=niu.Merge(1, ravel_inputs=True), name="merge_crops"
    )
    merge_masks = pe.Node(
        interface=niu.Merge(1, ravel_inputs=True), name="merge_masks"
    )

    nesvor_pipe.connect(cropping, "output_mask", merge_masks, "in1")
    nesvor_pipe.connect(cropping, "output_image", merge_crops, "in1")

    # 3. FULL PIPELINE
    recon = pe.Node(
        NesvorFullReconstruction(
            container_image=nesvor_image, pre_command=pre_command
        ),
        name="full_recon",
    )

    # parameters
    recon.inputs.bias_field_correction = True
    recon.inputs.n_levels_bias = 1

    nesvor_pipe.connect(
        [
            (merge_crops, recon, [("out", "input_stacks")]),
            (merge_masks, recon, [("out", "stack_masks")]),
        ]
    )

    # output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=["recon_file"]), name="outputnode"
    )

    nesvor_pipe.connect(recon, "output_volume", outputnode, "recon_file")
    return nesvor_pipe

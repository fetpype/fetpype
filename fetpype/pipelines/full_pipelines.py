import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from ..nodes.niftimic import niftimic_segment, niftimic_recon

from nipype.interfaces.ants.segmentation import DenoiseImage


def create_fet_subpipes(name="full_fet_pipe", params={}):
    """Description: SPM based segmentation pipeline from T1w and T2w images
    in template space

    Processing steps:

    - wraps niftimic dirty

    Params:

    -

    Inputs:

        inputnode:

            list_T2:
                T2 file names

        arguments:
            name:
                pipeline name (default = "full_spm_subpipes")

    Outputs:

            TODO
    """

    print("Full pipeline name: ", name)

    # Creating pipeline
    full_fet_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["stacks"]), name="inputnode"
    )

    # preprocessing
    niftymic_segment = pe.Node(
        interface=niu.Function(
            input_names=["raw_T2s", "pre_command", "niftimic_image"],
            output_names=["bmasks"],
            function=niftimic_segment,
        ),
        name="niftymic_segment",
    )

    if "general" in params.keys():
        if "pre_command" in params["general"]:
            niftymic_segment.inputs.pre_command = params["general"]["pre_command"]

        if "niftimic_image" in params["general"]:
            niftymic_segment.inputs.niftimic_image = params["general"]["niftimic_image"]

    else:
        niftymic_segment.inputs.pre_command = ""
        niftymic_segment.inputs.niftimic_image = ""

    full_fet_pipe.connect(inputnode, "stacks", niftymic_segment, "raw_T2s")

    # denoising
    denoising = pe.MapNode(
        interface=DenoiseImage(), iterfield=["input_image"], name="denoising"
    )

    full_fet_pipe.connect(inputnode, "stacks", denoising, "input_image")

    # merge_denoise
    merge_denoise = pe.Node(
        interface=niu.Merge(1, ravel_inputs=True), name="merge_denoise"
    )

    full_fet_pipe.connect(denoising, "output_image", merge_denoise, "in1")

    # recon
    recon = pe.Node(
        interface=niu.Function(
            input_names=["stacks", "masks", "pre_command", "niftimic_image"],
            output_names=["recon_files"],
            function=niftimic_recon,
        ),
        name="recon",
    )

    if "general" in params.keys():
        if "pre_command" in params["general"]:
            recon.inputs.pre_command = params["general"]["pre_command"]

        if "niftimic_image" in params["general"]:
            recon.inputs.niftimic_image = params["general"]["niftimic_image"]

    else:
        recon.inputs.pre_command = ""
        recon.inputs.niftimic_image = ""

    full_fet_pipe.connect(merge_denoise, "out", recon, "stacks")
    full_fet_pipe.connect(niftymic_segment, "bmasks", recon, "masks")

    # output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=["recon_files"]), name="outputnode"
    )

    full_fet_pipe.connect(recon, "recon_files", outputnode, "recon_files")

    return full_fet_pipe

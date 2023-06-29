
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from ..nodes.niftimic import niftimic_segment, niftimic_recon

from nipype.interfaces.ants.segmentation import DenoiseImage


def create_fet_subpipes(name="full_fet_pipe", params={}):

    """ Description: SPM based segmentation pipeline from T1w and T2w images
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
        niu.IdentityInterface(fields=["haste_stacks", "tru_stacks"]),
        name='inputnode'
    )

    # haste

    # preprocessing
    niftymic_segment_haste = pe.Node(
        interface=niu.Function(
            input_names=["raw_T2s", "pre_command", "niftimic_image"],
            output_names=["bmasks"],
            function=niftimic_segment),
        name="niftymic_segment_haste")

    full_fet_pipe.connect(inputnode, 'haste_stacks',
                          niftymic_segment_haste, "raw_T2s")

    # denoising_haste
    denoising_haste = pe.MapNode(
        interface=DenoiseImage(), iterfield=["input_image"],
        name="denoising_haste")

    full_fet_pipe.connect(inputnode, 'haste_stacks',
                          denoising_haste, "input_image")

    # merge_denoise
    merge_denoise_haste = pe.Node(
        interface=niu.Merge(1, ravel_inputs=True),
        name="merge_denoise_haste")

    full_fet_pipe.connect(denoising_haste, 'output_image',
                          merge_denoise_haste, "in1")

    # recon_haste
    recon_haste = pe.Node(
        interface=niu.Function(
            input_names=["stacks", "masks", "pre_command", "niftimic_image"],
            output_names=["recon_files"],
            function=niftimic_recon),
        name="recon_haste")

    if "general" in params.keys():
        if "pre_command" in params["general"]:
            recon_haste.inputs.pre_command = \
                params["general"]["pre_command"]

        if "niftimic_image" in params["general"]:
            recon_haste.inputs.niftimic_image = \
                params["general"]["niftimic_image"]

    else:
        recon_haste.inputs.pre_command = ""
        recon_haste.inputs.niftimic_image = ""

    full_fet_pipe.connect(merge_denoise_haste, 'out', recon_haste, "stacks")
    full_fet_pipe.connect(niftymic_segment_haste, 'bmasks',
                          recon_haste, "masks")

    # tru
    # preprocessing
    niftymic_segment_tru = pe.Node(
        interface=niu.Function(
            input_names=["raw_T2s", "pre_command", "niftimic_image"],
            output_names=["bmasks"],
            function=niftimic_segment),
        name="niftymic_segment_tru")

    full_fet_pipe.connect(inputnode, 'tru_stacks',
                          niftymic_segment_tru, "raw_T2s")

    # denoising_tru
    denoising_tru = pe.MapNode(
        interface=DenoiseImage(), iterfield=["input_image"],
        name="denoising_tru")

    full_fet_pipe.connect(inputnode, 'tru_stacks',
                          denoising_tru, "input_image")

    # merge_denoise
    merge_denoise_tru = pe.Node(
        interface=niu.Merge(1, ravel_inputs=True),
        name="merge_denoise_tru")

    full_fet_pipe.connect(denoising_tru, 'output_image',
                          merge_denoise_tru, "in1")

    # recon_tru
    recon_tru = pe.Node(
        interface=niu.Function(input_names=["stacks", "masks"],
                               output_names=["recon_files"],
                               function=niftimic_recon),
        name="recon_tru")

    if "general" in params.keys():
        if "pre_command" in params["general"]:
            recon_tru.inputs.pre_command = \
                params["general"]["pre_command"]

        if "niftimic_image" in params["general"]:
            recon_tru.inputs.niftimic_image = \
                params["general"]["niftimic_image"]

    else:
        recon_tru.inputs.pre_command = ""
        recon_tru.inputs.niftimic_image = ""

    full_fet_pipe.connect(merge_denoise_tru, 'out', recon_tru, "stacks")
    full_fet_pipe.connect(niftymic_segment_tru, 'bmasks',
                          recon_tru, "masks")

    # output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['recon_haste_files']),
        name='outputnode')

    full_fet_pipe.connect(recon_haste, "recon_files",
                          outputnode, "recon_haste_files")

    full_fet_pipe.connect(recon_tru, "recon_files",
                          outputnode, "recon_tru_files")

    return full_fet_pipe

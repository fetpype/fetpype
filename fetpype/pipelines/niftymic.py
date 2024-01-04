import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from fetpype.nodes.niftymic import niftymic_recon

from nipype.interfaces.ants.segmentation import DenoiseImage
from ..nodes.niftymic import (
    NiftymicReconstruction,
    NiftymicBrainExtraction
)
# from ..nodes.preprocessing import niftymic_brain_extraction

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
            niftymic_image=niftymic_image, pre_command=pre_command
        ),
        name="brain_extraction",
    )

    niftymic_pipe.connect(inputnode, "stacks", brain_extraction, "input_stacks")

    # old version
    # brain_extraction = pe.Node(
    #     interface=niu.Function(
    #         input_names=["raw_T2s", "pre_command", "niftymic_image"],
    #         output_names=["bmasks"],
    #         function=niftymic_brain_extraction,
    #     ),
    #     name="brain_extraction",
    # )
    # if "general" in params.keys():
    #     brain_extraction.inputs.pre_command = params["general"].get(
    #         "pre_command", ""
    #     )
    #     brain_extraction.inputs.niftymic_image = params["general"].get(
    #         "niftymic_image", ""
    #     )
    # niftymic_pipe.connect(inputnode, "stacks", brain_extraction, "raw_T2s")

    # 2. RECONSTRUCTION
    # recon Node
    recon = pe.Node(
        NiftymicReconstruction(
            niftymic_image=niftymic_image, pre_command=pre_command
        ),
        name="recon",
    )

    niftymic_pipe.connect(inputnode, "stacks", recon, "input_stacks")
    niftymic_pipe.connect(brain_extraction, "output_bmasks",
                          recon, "input_masks")
    #niftymic_pipe.connect(brain_extraction, "bmasks", recon, "input_masks")

    ## output node
    #outputnode = pe.Node(
        #niu.IdentityInterface(fields=["dir_output"]), name="outputnode"
    #)

    #niftymic_pipe.connect(recon, "dir_output", outputnode, "dir_output")
    return niftymic_pipe

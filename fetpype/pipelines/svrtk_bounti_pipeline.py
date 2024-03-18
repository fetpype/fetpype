import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from ..nodes.svrtk_bounti import (
    SvrtkBountiReconstruction,
    copy_T2stacks
)

from ..utils.utils_nodes import NodeParams
from ..misc import parse_key

# from nipype import config
# config.enable_debug_mode()


def print_files(files):
    print("Files:")
    print(files)
    return files


def create_svrtk_bounti_subpipes(name="svrtk_bounti_pipe", params={}):
    """svrtk_bounti based pipeline for fetal MRI

    Processing steps:
    - Reconstruction using svrtk_bounti

    Params:
    - name: pipeline name
    - params: dictionary of parameters to be passed to the pipeline. We would
        need to specify the folder and pre_command parameters,
        right now.

    Outputs:
    - svrtk_bounti_pipe: svrtk_bounti workflow implementing the pipeline
    """

    # get parameters
    # Creating pipeline
    svrtk_bounti_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["stacks"]), name="inputnode"
    )

    # 0. COPY T2stacks
    copy_T2 = pe.Node(
        niu.Function(
            input_names=["T2_stacks"],
            output_names=["output_dir"],
            function=copy_T2stacks
        ),
        name="copy_T2",
    )

    svrtk_bounti_pipe.connect(inputnode, "stacks", copy_T2, "T2_stacks")

    # 1. RECONSTRUCTION
    # recon Node
    recon = NodeParams(
        SvrtkBountiReconstruction(),
        params=parse_key(params, "recon"),
        name="recon",
    )

    svrtk_bounti_pipe.connect(copy_T2, "output_dir", recon, "input_dir")

    # output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=["output_dir", "recon_file"]),
        name="outputnode"
    )

    svrtk_bounti_pipe.connect(recon, "output_dir", outputnode, "output_dir")
    svrtk_bounti_pipe.connect(recon, "recon_file", outputnode, "recon_file")
    return svrtk_bounti_pipe

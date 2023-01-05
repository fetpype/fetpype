
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from ..nodes.niftimic import niftimic_segment, niftimic_recon
from ..nodes.denoise import denoise_slurm

from nipype.interfaces.ants.segmentation import DenoiseImage

def create_fet_subpipes(name = "full_fet_pipe"):


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

    # output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['out_outpuf_file']),
        name='outputnode')

    #### haste
    # preprocessing
    niftymic_segment_haste = pe.Node(interface = niu.Function(in_files = ["raw_T2s"], out_files = ["bmasks"], function = niftimic_segment), name = "niftymic_segment")

    full_fet_pipe.connect(inputnode, 'haste_stacks', niftymic_segment_haste, "raw_T2s")

    ## denoising_haste
    #denoising_haste = pe.MapNode(interface = DenoiseImage(), iterfield= ["input_image"],
                                 #name="denoising_haste")

    #full_fet_pipe.connect(inputnode, 'haste_stacks', denoising_haste, "input_image")

    # recon_haste
    recon_haste = pe.Node(interface = niu.Function(in_files = ["stacks", "masks"], out_files = ["recon_files"], function = niftimic_recon), name = "recon_haste")

    full_fet_pipe.connect(inputnode, 'haste_stacks', recon_haste, "stacks")
    #full_fet_pipe.connect(denoising_haste, 'output_image', recon_haste, "stacks")
    full_fet_pipe.connect(niftymic_segment_haste, 'bmasks', recon_haste, "masks")

    return full_fet_pipe

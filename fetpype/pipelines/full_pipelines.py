
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from ..nodes.niftimic import niftimic_segment, niftimic_recon
from ..nodes.denoise import denoise_slurm

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
        niu.IdentityInterface(fields=['list_T2', "haste_stacks", "tru_stacks", "haste_masks", "tru_masks"]),
        name='inputnode'
    )

    # output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['out_outpuf_file']),
        name='outputnode')

    ## preprocessing
    #niftymic_segment = pe.Node(interface = niu.Function(in_files = ["raw_T2s"], out_files = ["seg_T2s"], function = niftimic_segment), name = "niftymic_segment")

    #full_fet_pipe.connect(inputnode, 'list_T2', niftymic_segment, "raw_T2s")
    #full_fet_pipe.connect(niftymic_segment, "seg_T2s", outputnode, "out_outpuf_file")

    # denoising_haste
    denoising_haste = pe.Node(interface = niu.Function(in_files = ["raw_files"], out_files = ["denoised_files"], function = denoise_slurm), name = "denoising_haste")

    full_fet_pipe.connect(inputnode, 'haste_stacks', denoising_haste, "raw_files")


    #denoising_tru = pe.Node(interface = niu.Function(in_files = ["raw_files"], out_files = ["denoised_files"], function = denoise_slurm), name = "denoising_tru")

    #full_fet_pipe.connect(inputnode, 'tru', niftymic_segment, "raw_files")

    # recon_haste
    recon_haste = pe.Node(interface = niu.Function(in_files = ["in_stacks", "in_masks"], out_files = ["recon_files"], function = niftimic_recon), name = "recon_haste")

    full_fet_pipe.connect(denoising_haste, 'denoised_files', recon_haste, "in_stacks")
    full_fet_pipe.connect(inputnode, 'haste_masks', recon_haste, "in_masks")

    return full_fet_pipe

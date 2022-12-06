

def denoise_slurm(raw_files):


    """ Description: wraps niftimic_segment dirty

    Inputs:

        inputnode:

            raw_T2s:
                T2 raw file names

    Outputs:

            bmasks:
                bmasks
    """

    #TODO

    import os
    import subprocess

    denoise_files = []
    for in_stack in raw_files:

        f_out = os.path.basename(in_stack).replace(".nii.gz", "")
        filename_out = f_out + "_denoised.nii.gz"
        out_stack = os.path.abspath(filename_out)
        if not os.path.exists(out_stack):
            cmd = [
                "sbatch",
                "/scratch/apron/code/marsFet_management/marsFet/utils/slurm/denoising.slurm",
                in_stack,
                out_stack,
            ]
            subprocess.run(cmd)

        denoise_files.append(out_stack)


    return denoise_files

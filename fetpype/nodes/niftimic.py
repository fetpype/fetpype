import os


def niftimic_segment(raw_T2s):


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


    bmasks = [
        os.path.join(output_dir, os.path.basename(s)[:-7] + "_brain_mask.nii.gz",)
        for s in raw_T2s
    ]
    #cmd = "sbatch "
    #cmd += "/scratch/apron/code/marsFet_management/marsFet/utils/slurm/nifty_mic.slurm "
    #cmd += '" '
    cmd += "niftymic_segment_fetal_brains "
    cmd += "--filenames "
    for s in raw_T2s:
        cmd += s + " "
    cmd += "--filenames-masks "
    for b in bmasks:
        cmd += b + " "
    cmd += "--dir-output "
    cmd += output_dir + " "
    cmd += "--neuroimage-legacy-seg 0 "
    cmd += "--log-config 1"
    cmd += ' "'
    os.system(cmd)


    return bmasks

def niftimic_recon(stacks, masks):

    import os

    reconst_dir = os.path.abspath("srr_reconstruction")

    cmd_os = "niftymic_run_reconstruction_pipeline"
    # input stacks
    cmd_os += " --filenames "
    for v in stacks:
        cmd_os += v + " "
    # corresponding masks (previously obtained)
    cmd_os += " --filenames-masks "
    for u in masks:
        cmd_os += u + " "
    # output directory
    cmd_os += " --dir-output " + reconst_dir
    # bias field correction was already performed
    cmd_os += " --bias-field-correction 1"
    cmd_os += " --isotropic-resolution 0.5"
    # outliers rejection parameters
    cmd_os += " --run-bias-field-correction 1"
    cmd_os += " --run-diagnostics 0"

    #cmd = (
    #    "sbatch"
    #    + "  "
    #    + "/scratch/apron/code/marsFet_management/marsFet/utils/slurm/nifty_mic_singularity.slurm"
    #    + " "
    #    + '"'
    #    + cmd_os
    #    + '"'
    #    + " "
    #    + DB_path
    #)

    print(cmd_os)
    #os.system(cmd)

    os.system(cmd_os)
    return reconst_dir

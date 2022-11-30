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
    cmd = "sbatch "
    cmd += "/scratch/apron/code/marsFet_management/marsFet/utils/slurm/nifty_mic.slurm "
    cmd += '" '
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

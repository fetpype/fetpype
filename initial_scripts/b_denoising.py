"""Launch denoising of MRI stack volumes using ANTS DenoiseImage on
a slurm cluster e.g. the Aix-Marseille mesocentre or niolon
"""

import os
import re
import glob
import subprocess


def get_identifier(filepath, pattern):
    """Get project identifier(s)"""
    filename = os.path.basename(filepath)
    regex = re.compile(pattern)
    match = regex.search(filename)
    if match is not None:
        identifier = match.group()
    else:
        identifier = None
    return identifier


def denoise_volume(in_stack, dir_out, slurm_config):
    """Denoise an MRI volume using ANTs DenoiseImage function
    The denoising is launched in an sbatch slurm job parameterized
    by the slurm_config file.
    :param in_stack: input raw 3D nifti volume
    :param dir_out: output directory
    :param path_slurm:
    :return: None
     TODO: capture the status of the job for reporting
    """
    os.makedirs(dir_out, exist_ok=True)
    f_out = os.path.basename(in_stack).replace(".nii.gz", "")
    filename_out = f_out + "_denoised.nii.gz"
    out_stack = os.path.join(dir_out, filename_out)
    if not os.path.exists(out_stack):
        cmd = [
            "sbatch",
            slurm_config,
            in_stack,
            out_stack,
        ]
        subprocess.run(cmd)
    pass


if __name__ == "__main__":

    denoising_slurm = (
        "/scratch/apron/code/marsFet_management/marsFet/utils/slurm/denoising.slurm"
    )

    from marsFet.configuration import MARSFET_MESO_NIFTI, MARSFET_MESO_DENOIS

    MARSFET_MESO_RAW = "/scratch/apron/data/datasets/MarsFet/rawdata"
    input_data = MARSFET_MESO_RAW
    output_data = MARSFET_MESO_DENOIS

    subjects = os.listdir(input_data)
    for subject in subjects:
        dir_subject = os.path.join(input_data, subject)
        sessions = os.listdir(dir_subject)
        for session in sessions:
            dir_session = os.path.join(dir_subject, session)
            for sequence in ["haste", "tru"]:
                in_stacks = glob.glob(
                    os.path.join(dir_session, "anat", sequence, "*.nii.gz"),
                    recursive=True,
                )
                for in_stack in in_stacks:
                    subject_id = get_identifier(in_stack, "sub-\d\d\d\d")
                    session_id = get_identifier(in_stack, "ses-\d\d\d\d")
                    dir_out = os.path.join(
                        output_data, subject_id, session_id, sequence
                    )
                    denoise_volume(in_stack, dir_out, denoising_slurm)

"""
Launch brain segmentation on the mesocentre
TODO: use a config file instead so that it is more BIDS compliant
TODO: factor using function to ease readability
"""

import os
import glob


def extract_brain_mask(input_dir, output_dir):
    """Extract brain mask from the different MRI stacks (e.g. coronal, sagittal)
    of the same sequence (e.g. HASTE)
    :param input_dir: path of the directory containing the different MRI stacks
    :param output_dir: path of the directory containing the brain masks
    :return: None
    """

    in_stacks = glob.glob(os.path.join(input_dir, "*.nii.gz"))
    out_stacks = [os.path.join(output_dir, os.path.basename(s)) for s in in_stacks]
    exist_out_stacks = all([os.path.exists(s) for s in out_stacks])
    if not exist_out_stacks:
        bmasks = [
            os.path.join(output_dir, os.path.basename(s)[:-7] + "_brain_mask.nii.gz",)
            for s in in_stacks
        ]
        cmd = "sbatch "
        cmd += "/scratch/apron/code/marsFet_management/marsFet/utils/slurm/nifty_mic.slurm "
        cmd += '" '
        cmd += "niftymic_segment_fetal_brains "
        cmd += "--filenames "
        for s in in_stacks:
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
        pass


if __name__ == "__main__":

    from marsFet.configuration import MARSFET_MESO_NIFTI, MARSFET_MESO_BRAINSEG

    MARSFET_MESO_RAW = "/scratch/apron/data/datasets/MarsFet/rawdata"
    input_data = MARSFET_MESO_RAW

    output_data = MARSFET_MESO_BRAINSEG
    sequences = ["haste", "tru"]

    subjects = os.listdir(input_data)
    subjects.sort()

    for subject in subjects:
        dir_subject_in = os.path.join(input_data, subject)
        sessions = os.listdir(dir_subject_in)
        sessions.sort()
        for session in sessions:
            dir_session_in = os.path.join(dir_subject_in, session)
            for sequence in sequences:
                dir_sequence_in = os.path.join(dir_session_in, "anat", sequence)
                dir_sequence_out = os.path.join(output_data, subject, session, sequence)
                os.makedirs(dir_sequence_out, exist_ok=True)
                extract_brain_mask(dir_sequence_in, dir_sequence_out)

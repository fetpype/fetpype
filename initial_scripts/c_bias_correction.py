"""
Reconstruct all volumes available in the dataset
"""

import os
import glob


if __name__ == "__main__":

    DB_path = "/scratch/apron/data/datasets/MarsFet/derivatives"
    MARSFET = "/scratch/apron/data/datasets/MarsFet"

    subjects = os.listdir(os.path.join(DB_path, "denoising"))
    sequences = ["haste", "tru"]
    for subject in subjects:
        subj_dir = os.path.join(DB_path, "denoising", subject)
        sessions = os.listdir(subj_dir)
        for session in sessions:
            for sequence in sequences:
                print("--------------" + subject)
                dir_reconst = os.path.join(
                    DB_path,
                    "srr_reconstruction",
                    "default_pipeline_meso",
                    subject,
                    session,
                    sequence,
                )
                recon_final = os.path.join(
                    dir_reconst, "recon_template_space", "srr_template.nii.gz",
                )
                if not os.path.exists(recon_final):
                    dir_stacks = os.path.join(subj_dir, session, sequence)
                    dir_masks = os.path.join(
                        DB_path, "brain_seg", subject, session, sequence
                    )
                    stacks = glob.glob(os.path.join(dir_stacks, "*.nii.gz"))

                    masks = glob.glob(os.path.join(dir_masks, "*.nii.gz"))

                    stacks.sort()
                    masks.sort()
                    if not stacks or not masks:
                        print(
                            "Scan not preprocessed yet", subject, session, sequence,
                        )
                    # docker path
                    else:
                        sing_stacks = [s.replace(DB_path, "/data") for s in stacks]
                        sing_masks = [m.replace(DB_path, " /data") for m in masks]

                        reconst_dir = os.path.join(
                            "/data",
                            "srr_reconstruction",
                            "test_bias",
                            subject,
                            session,
                            sequence,
                        )

                        cmd_os = "niftymic_run_reconstruction_pipeline"
                        # input stacks
                        cmd_os += " --filenames "
                        for v in sing_stacks:
                            cmd_os += v + " "
                        # corresponding masks (previously obtained)
                        cmd_os += " --filenames-masks "
                        for u in sing_masks:
                            cmd_os += u + " "
                        # output directory
                        cmd_os += " --dir-output " + reconst_dir
                        # bias field correction was already performed
                        cmd_os += " --bias-field-correction 1"
                        cmd_os += " --isotropic-resolution 0.5"
                        # outliers rejection parameters
                        cmd_os += " --run-bias-field-correction 1"
                        cmd_os += " --run-diagnostics 0"

                        cmd = (
                            "sbatch"
                            + "  "
                            + "/scratch/apron/code/marsFet_management/marsFet/utils/slurm/nifty_mic_singularity.slurm"
                            + " "
                            + '"'
                            + cmd_os
                            + '"'
                            + " "
                            + DB_path
                        )

                        print(cmd_os)
                        os.system(cmd)
                else:
                    print(
                        subject,
                        session,
                        sequence,
                        "has already been processed successfully !",
                    )

def niftymic_recon(stacks, masks, pre_command="", niftymic_image=""):
    """
    Function wrapping niftymic_run_reconstruction_pipeline for use with nipype
    This is a quick and dirty implementation, to be replaced by a proper nipype
    interface in the future.

    Inputs:
        stacks:
            Preprocessed T2 file names
        masks:
            Brain masks for each T2 low-resolution stack given in stacks.
        pre_command:
            Command to run niftymic_image (e.g. docker run or singularity run)
        niftymic_image:
            niftymic_image name (e.g. renbem/niftymic:latest)

    Outputs:
        reconst_dir:
            Directory containing the reconstructed files
    """
    import os

    reconst_dir = os.path.abspath("srr_reconstruction")

    if "docker" in pre_command:
        stacks_dir = os.path.commonpath(stacks)
        masks_dir = os.path.commonpath(masks)
        stacks_docker = " ".join(
            [s.replace(stacks_dir, "/data") for s in stacks]
        )
        bmasks_docker = " ".join(
            [m.replace(masks_dir, "/masks") for m in masks]
        )
        cmd = pre_command
        cmd += (
            f"-v {stacks_dir}:/data "
            f"-v {masks_dir}:/masks "
            f"-v {reconst_dir}:/rec "
            f"{niftymic_image} niftymic_run_reconstruction_pipeline "
            f"--filenames {stacks_docker} "
            f"--filenames-masks {bmasks_docker} "
            "--dir-output /rec "
        )
    elif "singularity" in pre_command:
        stacks = " ".join(stacks)
        masks = " ".join(masks)

        cmd = pre_command + niftymic_image
        cmd += (
            "niftymic_run_reconstruction_pipeline"
            # input stacks
            f" --filenames {stacks}"
            # corresponding masks (previously obtained)
            f" --filenames-masks {masks}"
            # output directory
            f" --dir-output {reconst_dir} "
        )

    else:
        raise ValueError(
            "pre_command must either contain docker or singularity."
        )

    # bias field correction was already performed
    cmd += " --bias-field-correction 1"
    cmd += " --isotropic-resolution 0.5"
    # outliers rejection parameters
    cmd += " --run-bias-field-correction 1"
    cmd += " --run-diagnostics 0"

    print(cmd)

    os.system(cmd)
    return reconst_dir

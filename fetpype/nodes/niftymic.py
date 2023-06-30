def niftymic_segment(raw_T2s, pre_command="", niftymic_image=""):
    """
    Function wrapping niftymic_segment_fetal_brains for use with nipype
    This is a quick and dirty implementation, to be replaced by a proper nipype
    interface in the future.

    Inputs:
        raw_T2s:
            Raw T2 file names
        pre_command:
            Command to run niftymic_image (e.g. docker run or singularity run)
        niftymic_image:
            niftymic_image name (e.g. renbem/niftymic:latest)

    Outputs:
        bmasks:
            Brain masks for each T2 low-resolution stack given in raw_T2s.
    """
    import os

    output_dir = os.path.abspath("")

    # Why do we do [:-7] + .nii.gz?
    bmasks = [
        os.path.abspath(
            os.path.basename(s)[:-7].replace("_T2w", "_mask") + ".nii.gz",
        )
        for s in raw_T2s
    ]

    # DOCKER PATH
    if "docker" in pre_command:
        stacks_dir = os.path.commonpath(raw_T2s)
        masks_dir = os.path.commonpath(bmasks)
        stacks_docker = " ".join(
            [s.replace(stacks_dir, "/data") for s in raw_T2s]
        )
        bmasks_docker = " ".join(
            [m.replace(masks_dir, "/masks") for m in bmasks]
        )

        cmd = pre_command
        cmd += (
            f"-v {output_dir}:/masks "
            f"-v {stacks_dir}:/data "
            f"{niftymic_image} niftymic_segment_fetal_brains "
            f"--filenames {stacks_docker} "
            f"--filenames-masks {bmasks_docker} "
        )
    # SINGULARITY PATH
    elif "singularity" in pre_command:
        stacks = " ".join(raw_T2s)
        masks = " ".join(bmasks)

        cmd = pre_command + niftymic_image

        cmd += (
            "niftymic_segment_fetal_brains "
            f"--filenames {stacks} "
            f"--filenames-masks {masks} "
            # Test without dir_output for masks properly named
            # f"--dir-output {output_dir} "
        )
    else:
        raise ValueError(
            "pre_command must either contain docker or singularity."
        )
    cmd += "--neuroimage-legacy-seg 0 "
    # Commented out because the system crashes otherwise.
    # Do we need it at all?
    # cmd += "--log-config 1"

    print(cmd)
    os.system(cmd)

    for bmask in bmasks:
        print(bmask)
        assert os.path.exists(bmask), f"Error, {bmask} does not exist"

    return bmasks


def niftymic_recon(stacks, masks, pre_command="", niftymic_image=""):
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

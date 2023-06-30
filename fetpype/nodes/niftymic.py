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

    print(output_dir)

    print(pre_command + niftymic_image)

    # Why do we do [:-7] + .nii.gz?
    bmasks = [
        os.path.abspath(
            os.path.basename(s)[:-7].replace("_T2w", "_mask") + ".nii.gz",
        )
        for s in raw_T2s
    ]

    # DOCKER PATH
    if "docker" in pre_command:
        stacks_dir = os.path.dirname(raw_T2s[0])
        bmasks_docker = " ".join(
            [os.path.join("/masks", os.path.basename(m)) for m in bmasks]
        )
        stacks_docker = " ".join(
            [os.path.join("/data", os.path.basename(s)) for s in raw_T2s]
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

    cmd_os = pre_command + niftymic_image
    cmd_os += "niftymic_run_reconstruction_pipeline"
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

    print(cmd_os)

    os.system(cmd_os)
    return reconst_dir

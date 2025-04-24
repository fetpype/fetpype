def run_seg_cmd(
    input_srr, cmd, cfg, singularity_path=None, singularity_mount=None
):
    import os
    from fetpype import VALID_SEG_TAGS as VALID_TAGS
    from fetpype.nodes import is_valid_cmd, get_mount_docker

    is_valid_cmd(cmd, VALID_TAGS)

    # Check if input_srr is a directory or a file
    if isinstance(input_srr, list):
        if len(input_srr) == 1:
            input_srr = input_srr[0]
        else:
            raise ValueError(
                "input_srr is a list, and contains multiple elements. "
                "It should be a single element."
            )
    # Copy input_srr to input_directory
    # Avoid mounting problematic directories
    input_srr_dir = os.path.join(os.getcwd(), "seg/input")
    os.makedirs(input_srr_dir, exist_ok=True)
    os.system(f"cp {input_srr} {input_srr_dir}/input_srr.nii.gz")
    input_srr = os.path.join(input_srr_dir, "input_srr.nii.gz")

    output_dir = os.path.join(os.getcwd(), "seg/out")
    seg = os.path.join(output_dir, "seg.nii.gz")

    # In cmd, there will be things contained in <>.
    # Check that everything that is in <> is in valid_tags
    # If not, raise an error

    # Replace the tags in the command
    cmd = cmd.replace("<input_srr>", input_srr)
    cmd = cmd.replace("<input_dir>", input_srr_dir)
    cmd = cmd.replace("<output_seg>", seg)
    if "<output_dir>" in cmd:
        cmd = cmd.replace("<output_dir>", output_dir)
        # Assert that args.path_to_output is defined
        assert cfg.path_to_output is not None, (
            "<output_dir> found in the command of reconstruction, "
            " but path_to_output is not defined."
        )

        seg = os.path.join(output_dir, cfg.path_to_output)
        if "<basename>" in seg:
            # Remove all extensions from the basename
            # (handles .nii.gz correctly)
            basename = os.path.basename(input_srr)
            # Remove all extensions (handles both .nii.gz and .nii cases)
            basename_no_ext = basename.split(".")[0]
            seg = seg.replace("<basename>", basename_no_ext)
    if "<mount>" in cmd:
        mount_cmd = get_mount_docker(input_srr_dir, output_dir)
        cmd = cmd.replace("<mount>", mount_cmd)
    if "<singularity_path>" in cmd:
        # assume that if we have a singularity path,
        # we are using singularity and the
        # parameter has been set in the config file
        cmd = cmd.replace("<singularity_path>", singularity_path)
    if "<singularity_mount>" in cmd:
        # assume that if we have a singularity mount path,
        # we are using singularity and the
        # parameter has been set in the config file
        cmd = cmd.replace("<singularity_mount>", singularity_mount)
    print(f"Running command:\n {cmd}")
    os.system(cmd)
    return seg

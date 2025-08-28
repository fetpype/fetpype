def run_surf_cmd(
    input_seg,
    cmd,
    cfg,
    singularity_path=None,
    singularity_mount=None,
    singularity_home=None,
):
    """
    Run a segmentation command with the given input SRR.

    Args:
        input_seg (str or list): Path to the input segmentation file or a list
                                containing a single segmentation file.
        cmd (str): Command to run, with placeholders for input and output.
        cfg (object): Configuration object containing output directory.
        singularity_path (str, optional): Path to the Singularity executable.
        singularity_mount (str, optional): Mount point for Singularity.
    Returns:
        str: Path to the output segmentation file after running the command.

    """
    import os
    from fetpype import VALID_SURF_TAGS as VALID_TAGS
    from fetpype.nodes import is_valid_cmd, get_mount_docker
    from fetpype.utils.logging import run_and_tee

    is_valid_cmd(cmd, VALID_TAGS)

    # Check if input_srr is a directory or a file
    if isinstance(input_seg, list):
        if len(input_seg) == 1:
            input_seg = input_seg[0]
        else:
            raise ValueError(
                "input_seg is a list, and contains multiple elements. "
                "It should be a single element."
            )
    # Copy input_seg to input_directory
    # Avoid mounting problematic directories
    input_seg_dir = os.path.join(os.getcwd(), "seg/input")
    os.makedirs(input_seg_dir, exist_ok=True)
    os.system(f"cp {input_seg} {input_seg_dir}/input_seg.nii.gz")
    input_seg = os.path.join(input_seg_dir, "input_seg.nii.gz")

    output_dir = os.path.join(os.getcwd(), "surf/out")
    os.makedirs(output_dir, exist_ok=True)
    surf = os.path.join(output_dir, "surf.stl")
    #surf = os.path.join(output_dir, "surf.gii")


    # In cmd, there will be things contained in <>.
    # Check that everything that is in <> is in valid_tags
    # If not, raise an error

    # Replace the tags in the command
    cmd = cmd.replace("<input_seg>", input_seg)
    # cmd = cmd.replace("<input_dir>", input_seg_dir)
    cmd = cmd.replace("<output_surf>", surf)
    assert cfg.use_scheme in cfg.labelling_scheme, (
        f"Unknown labelling scheme: {cfg.use_scheme},"
        f"please choose from {list(cfg.labelling_scheme.keys())}"
    )
    labelling_scheme = cfg.labelling_scheme[cfg.use_scheme]
    labelling_scheme = ",".join(map(str, labelling_scheme))
    cmd = cmd.replace("<labelling_scheme>", labelling_scheme)

    # if "<output_dir>" in cmd:
    #     cmd = cmd.replace("<output_dir>", output_dir)
    #     # Assert that args.path_to_output is defined
    #     assert cfg.path_to_output is not None, (
    #         "<output_dir> found in the command of reconstruction, "
    #         " but path_to_output is not defined."
    #     )

    # seg = os.path.join(output_dir, cfg.path_to_output)
    # if "<basename>" in seg:
    #     # Remove all extensions from the basename
    #     # (handles .nii.gz correctly)
    #     basename = os.path.basename(input_srr)
    #     # Remove all extensions (handles both .nii.gz and .nii cases)
    #     basename_no_ext = basename.split(".")[0]
    #     seg = seg.replace("<basename>", basename_no_ext)
    if "<mount>" in cmd:
        mount_cmd = get_mount_docker(input_seg_dir, output_dir)
        cmd = cmd.replace("<mount>", mount_cmd)
    if "<singularity_path>" in cmd:
        cmd = cmd.replace("<singularity_path>", singularity_path)
    if "<singularity_mount>" in cmd:
        cmd = cmd.replace("<singularity_mount>", singularity_mount)

    if "<singularity_home>" in cmd:
        cmd = cmd.replace("<singularity_home>", singularity_home)

    run_and_tee(cmd)

    return surf

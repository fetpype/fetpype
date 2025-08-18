def run_recon_cmd(
    input_stacks,
    input_masks,
    cmd,
    cfg,
    singularity_path=None,
    singularity_mount=None,
):
    """
    Run a reconstruction command with the given input stacks and masks.

    Args:

        input_stacks (list): List of input stack file paths.
        input_masks (list): List of input mask file paths.
        cmd (str): Command to run, with placeholders for input and output.
        cfg (object): Configuration object containing output directory
                        and resolution.
        singularity_path (str, optional): Path to the Singularity executable.
        singularity_mount (str, optional): Mount point for Singularity.
    Returns:
        str: Path to the output volume after reconstruction.
    """
    import os
    import numpy as np
    import nibabel as nib
    import traceback
    from fetpype import VALID_RECON_TAGS as VALID_TAGS
    from fetpype.nodes import is_valid_cmd, get_directory, get_mount_docker
    from fetpype.utils.logging import run_and_tee

    is_valid_cmd(cmd, VALID_TAGS)
    output_dir = os.path.join(os.getcwd(), "recon")
    output_volume = os.path.join(output_dir, "recon.nii.gz")
    in_stacks_dir = get_directory(input_stacks)
    in_stacks = " ".join(input_stacks)
    in_masks_dir = get_directory(input_masks)
    in_masks = " ".join(input_masks)

    # In cmd, there will be things contained in <>.
    # Check that everything that is in <> is in valid_tags
    # If not, raise an error

    # Replace the tags in the command
    cmd = cmd.replace("<input_stacks>", in_stacks)
    cmd = cmd.replace("<input_dir>", in_stacks_dir)
    cmd = cmd.replace("<input_masks>", in_masks)
    cmd = cmd.replace("<input_masks_dir>", in_masks_dir)
    if "<output_volume>" in cmd:
        cmd = cmd.replace("<output_volume>", output_volume)
    if "<output_dir>" in cmd:
        cmd = cmd.replace("<output_dir>", output_dir)
        # Assert that args.path_to_output is defined
        assert cfg.path_to_output is not None, (
            "<output_dir> found in the command of reconstruction, "
            "but path_to_output is not defined."
        )
        output_volume = os.path.join(output_dir, cfg.path_to_output)
    if "<input_tp>" in cmd:
        try:
            input_tp = np.round(
                np.mean(
                    [
                        nib.load(stack).header.get_zooms()[2]
                        for stack in input_stacks
                    ]
                ),
                1,
            )
            cmd = cmd.replace("<input_tp>", str(input_tp))
        except Exception as e:

            raise ValueError(
                f"Error when calculating <input_tp>: {e}"
                f"\n{traceback.format_exc()}"
            )

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

    if "<output_res>" in cmd:
        output_res = cfg.output_resolution
        cmd = cmd.replace("<output_res>", str(output_res))
    if "<mount>" in cmd:
        mount_cmd = get_mount_docker(in_stacks_dir, in_masks_dir, output_dir)
        cmd = cmd.replace("<mount>", mount_cmd)

    run_and_tee(cmd)
    return output_volume

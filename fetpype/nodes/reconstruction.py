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


def run_postpro_cmd(
    input_stacks,
    cmd,
    is_enabled=True,
    input_masks=None,
    singularity_path=None,
    singularity_mount=None,
):
    """
    Run a postprocessing command on input stacks.

    Args:
        input_stacks (str or list): Input stacks to process.
        cmd (str): Command to run, with tags for input and output.
        is_enabled (bool): Whether the command should be executed.
        singularity_path (str, optional): Path to the Singularity executable.
        singularity_mount (str, optional): Mount point for Singularity.
    Returns:
        tuple: Output stacks and masks, if specified in the command.
               If only one of them is specified, returns that one.
               If none are specified, returns None.

    """
    import os
    from fetpype import VALID_PREPRO_TAGS
    from fetpype.utils.logging import run_and_tee

    # Important for mapnodes
    unlist_stacks = False
    unlist_masks = False

    # Making input_masks optional
    if input_masks:
        print("masks different than 0", input_masks)
        cmd = cmd.replace("<input_masks>", input_masks)
    else:
        print("masks 0", input_masks)
        cmd = cmd.replace("--input_masks <input_masks>", "")
        cmd = cmd.replace("<input_masks>", "")

    if isinstance(input_stacks, str):
        input_stacks = [input_stacks]
        unlist_stacks = True
    if isinstance(input_masks, str):
        input_masks = [input_masks]
        unlist_masks = True

    from fetpype.nodes import is_valid_cmd, get_directory, get_mount_docker

    is_valid_cmd(cmd, VALID_PREPRO_TAGS)
    if "<output_stacks>" not in cmd and "<output_masks>" not in cmd:
        raise RuntimeError(
            "No output stacks or masks specified in the command. "
            "Please specify <output_stacks> and/or <output_masks>."
        )

    if is_enabled:
        output_dir = os.path.join(os.getcwd(), "output")
        in_stacks_dir = get_directory(input_stacks)
        in_stacks = " ".join(input_stacks)

        in_masks = ""
        in_masks_dir = None
        if input_masks is not None:
            in_masks_dir = get_directory(input_masks)
            in_masks = " ".join(input_masks)

        output_stacks = None
        output_masks = None

        # In cmd, there will be things contained in <>.
        # Check that everything that is in <> is in valid_tags
        # If not, raise an error

        # Replace the tags in the command
        cmd = cmd.replace("<input_stacks>", in_stacks)
        cmd = cmd.replace("<input_masks>", in_masks)
        if "<output_stacks>" in cmd:
            output_stacks = [
                os.path.join(output_dir, os.path.basename(stack))
                for stack in input_stacks
            ]
            cmd = cmd.replace("<output_stacks>", " ".join(output_stacks))
        if "<output_masks>" in cmd:
            if input_masks:
                output_masks = [
                    os.path.join(output_dir, os.path.basename(mask))
                    for mask in input_masks
                ]
            else:
                output_masks = [
                    os.path.join(output_dir, os.path.basename(stack)).replace(
                        "_T2w", "_mask"
                    )
                    for stack in input_stacks
                ]
            cmd = cmd.replace("<output_masks>", " ".join(output_masks))

        if "<mount>" in cmd:
            mount_cmd = get_mount_docker(
                in_stacks_dir, in_masks_dir, output_dir
            )
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

        run_and_tee(cmd)

    else:
        output_stacks = input_stacks if "<output_stacks>" in cmd else None
        output_masks = input_masks if "<output_masks>" in cmd else None

    if output_stacks is not None and unlist_stacks:
        assert (
            len(output_stacks) == 1
        ), "More than one stack was returned, but unlist_stacks is True."
        output_stacks = output_stacks[0]
    if output_masks is not None and unlist_masks:
        assert (
            len(output_masks) == 1
        ), "More than one mask was returned, but unlist_masks is True."
        output_masks = output_masks[0]
    if output_stacks is not None and output_masks is not None:
        return output_stacks, output_masks
    elif output_stacks is not None:
        return output_stacks
    elif output_masks is not None:
        return output_masks


def clamp_intensities(
    cfg,
    input_stacks,
    is_enabled=True
):

    """
    Run an intensity clamping command on input stacks based on a specified
    quantile in the configuration file.

    Args:
        cfg (object): Configuration object containing output directory
                        and resolution.
        input_stacks (str or list): Input stacks to process.
        is_enabled (bool): Whether the command should be executed.
    Returns:
        output_stacks: Stacks that their intensity is clamped.

    """
    import os
    import numpy as np
    import nibabel as nib

    if is_enabled:
        nifti_img = nib.load(input_stacks)
        data = nifti_img.get_fdata()
        q_ratio = cfg.reconstruction.quantile_ratio
        flat_data = data.flatten()
        q = np.quantile(flat_data, q_ratio, axis=None)
        mask_pos = data >= q
        all_masks = mask_pos
        outliers_mask = np.zeros(data.shape, dtype=bool)
        outliers_mask[all_masks] = True
        replace_value_pos = np.max(data[(~outliers_mask) & (~np.isnan(data))])
        filtered_data_array = data.copy()
        filtered_data_array[mask_pos] = replace_value_pos
        output_stacks = os.path.join(
            os.getcwd(),
            os.path.basename(input_stacks).replace(
                ".nii.gz", "_clamped.nii.gz"
            )
        )
        image_clamped = nib.Nifti1Image(
            filtered_data_array,
            nifti_img.affine,
            nifti_img.header
        )
        nib.save(image_clamped, output_stacks)
        return output_stacks

    else:
        output_stacks = input_stacks

    return None

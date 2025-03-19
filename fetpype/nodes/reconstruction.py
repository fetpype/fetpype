def run_recon_cmd(input_stacks, input_masks, cmd, cfg):
    from fetpype.nodes.utils import (
        is_valid_cmd,
        get_directory,
        get_mount_docker,
    )
    import os
    import numpy as np
    import nibabel as nib
    import traceback

    VALID_TAGS = [
        "mount",
        "input_stacks",
        "input_dir",
        "input_masks",
        "input_masks_dir",
        "output_dir",
        "output_volume",
        "input_tp",
        "output_res",
    ]
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
        assert (
            cfg.path_to_output is not None
        ), "<output_dir> found in the command of reconstruction, but path_to_output is not defined."
        output_volume = os.path.join(output_dir, cfg.path_to_output)
    if "<input_tp>" in cmd:
        try:
            input_tp = np.round(
                np.mean([nib.load(stack).shape[2] for stack in input_stacks]),
                1,
            )
            cmd = cmd.replace("<input_tp>", str(input_tp))
        except Exception as e:

            raise ValueError(
                f"Error when calculating <input_tp>: {e}\n{traceback.format_exc()}"
            )

    if "<output_res>" in cmd:
        output_res = cfg.output_resolution
        cmd = cmd.replace("<output_res>", str(output_res))
    if "<mount>" in cmd:
        mount_cmd = get_mount_docker(in_stacks_dir, in_masks_dir, output_dir)
        cmd = cmd.replace("<mount>", mount_cmd)
    print(f"Running command:\n {cmd}")
    os.system(cmd)
    return output_volume

"""
Script that, for a set of slices, recreats the original 3D volumes.
"""

import os
import os.path as op
import argparse
import json
import nibabel as nib
import numpy as np

slices_path = "/homedtic/gmarti/DATA/ERANEU_BIDS_small/sub-003/ses-01/anat/slices"
slices_json = f"{slices_path}/slices.json"
output_folder = os.path.join(slices_path, "corrected_stacks")
os.makedirs(output_folder, exist_ok=True)

# Read the json file
with open(slices_json, "r") as f:
    slices = json.load(f)

# Get the list of stacks "input_stacks"
input_stacks = slices["input_stacks"]

i = 0
# iterate over the stacks
for stack in input_stacks:
    # load the stack
    stack_nii = nib.load(stack)
    stack_data = stack_nii.get_fdata()
    # get the shape of the stack
    stack_shape = stack_data.shape
    print(stack_shape)
    # get the number of slices
    # should be the smaller dimension
    n_slices = min(stack_shape)
    print(n_slices)
    # Get the dimension
    dim = np.argmin(stack_shape)

    # for the number of slices, iterate over the slices
    # and save the i.nii.gz and i_mask.nii.gz in a corresponding
    # 3D volume
    # Create the two 3D volumes
    stack_3D = np.zeros(stack_shape)
    stack_mask_3D = np.zeros(stack_shape)

    for j in reversed(range(n_slices)):
        print(i)
        # load the slice and mask
        slice_nii = nib.load(f"{slices_path}/{i}.nii.gz")
        slice_data = slice_nii.get_fdata()

        slice_mask_nii = nib.load(f"{slices_path}/mask_{i}.nii.gz")
        slice_mask_data = slice_mask_nii.get_fdata()

        # save the slice in the corresponding 3D volume,
        # depending on the dimension
        # very shitty
        if dim == 0:
            stack_3D[j, :, :] = slice_data.squeeze()
            stack_mask_3D[j, :, :] = slice_mask_data.squeeze()

        elif dim == 1:
            stack_3D[:, j, :] = slice_data.squeeze()
            stack_mask_3D[:, j, :] = slice_mask_data.squeeze()

        elif dim == 2:
            stack_3D[:, :, j] = slice_data.squeeze()
            stack_mask_3D[:, :, j] = slice_mask_data.squeeze()

        i += 1

    # Save the 3D volumes
    # Get the name of the stack
    stack_name = op.basename(stack)
    # Get the path of the stack
    stack_path = op.dirname(stack)
    # Save the 3D volumes
    stack_3D_nii = nib.Nifti1Image(stack_3D, stack_nii.affine, stack_nii.header)
    stack_mask_3D_nii = nib.Nifti1Image(
        stack_mask_3D, stack_nii.affine, stack_nii.header
    )
    nib.save(stack_3D_nii, f"{output_folder}/{stack_name}_3D.nii.gz")
    nib.save(stack_mask_3D_nii, f"{output_folder}/{stack_name}_3D_mask.nii.gz")

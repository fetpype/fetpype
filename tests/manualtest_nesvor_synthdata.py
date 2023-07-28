"""
Unit test using the test data from fabian.
Runs the whole nesvor pipeline and compare the output with the expected output.

TODO: automate + integrate it better with existing functions, make the option
of specifying masks better?
"""

import os
import json
import glob
import nibabel as nib
import numpy as np
from fetpype.utils.utils_bids import create_datasource
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as niu
from fetpype.pipelines.full_pipelines import create_nesvor_subpipes_fullrecon


def create_mask(nifti_image):
    """
    Create a mask from a nifti image.
    The mask is just by thresholding the image > 0.

    Return the mask with the same affine and header as the input image.
    """
    img = nib.load(nifti_image)
    data = img.get_fdata()
    mask = np.zeros(data.shape)
    mask[data > 0] = 1
    mask_img = nib.Nifti1Image(mask, img.affine, img.header)
    return mask_img


def change_suffix(stacks, new_suffix):
    masks = []
    for s in stacks:
        base, ext1, ext2 = s.rsplit(".", 2)
        new_string = f"{base}_{new_suffix}.{ext1}.{ext2}"
        masks.append(new_string)
    return masks


def move_to_BIDS(stacks, output_volume, derivatives_folder):
    """
    Function that, for a specific output volume, moves it to the derivatives
    folder, renaming the file and creating the appropiate subfolders.
    """
    import os
    import shutil

    # stacks is a list of files, we take the first one and extract
    # the subject and session
    sub, ses = stacks[0].split(os.sep)[-4:-2]
    # Extract the subject and session info from the strings
    sub = sub.split("-")[1]
    ses = ses.split("-")[1]

    subj_folder = os.path.join(
        derivatives_folder, f"sub-{sub}", f"ses-{ses}", "anat"
    )
    os.makedirs(subj_folder, exist_ok=True)
    # move the file with the new name
    new_name = os.path.join(subj_folder, f"sub-{sub}_ses-{ses}_recon.nii.gz")
    shutil.copy(output_volume, new_name)
    return new_name


# manual paths
fabian_path = "/home/gmarti/DATA/fabian/"
fabian_recon_path = "/home/gmarti/DATA/fabian/derivatives/recon/"
fabian_recon_path_baseline = (
    "/home/gmarti/DATA/fabian/derivatives/recon_baseline/"
)

params_file = "workflows/params_segment_fet_nesvor.json"
params = json.load(open(params_file, encoding="utf-8"))

# if fabian_recon_path does not exist, create it
if not os.path.exists(fabian_recon_path):
    os.makedirs(fabian_recon_path)

output_query = {
    "stacks": {
        "datatype": "anat",
        "suffix": "T2w",
        "extension": ["nii", ".nii.gz"],
    }
}

# for each subject, create the mask and the recon
# datasource
datasource = create_datasource(
    output_query,
    fabian_path,
)

output = datasource.run()

# for each subject scan
for t2w_image in output.outputs.stacks:
    # with the extension replaced by _mask.nii.gz
    mask_path = t2w_image.replace("_T2w.nii.gz", "_mask.nii.gz")

    # if the mask doenst exist
    if not os.path.exists(mask_path):
        # create the mask
        mask = create_mask(t2w_image)
        # save the mask
        nib.save(mask, mask_path)


# create another datasource
datasource = create_datasource(output_query, fabian_path)

# Creating pipeline
main_workflow = pe.Workflow(name="main_workflow")
main_workflow.base_dir = fabian_recon_path

# fet_pipe_1 = create_nesvor_subpipes(params=params)
fet_pipe_2 = create_nesvor_subpipes_fullrecon(params=params)

# main_workflow.connect(datasource, "stacks", fet_pipe_1, "inputnode.stacks")
main_workflow.connect(datasource, "stacks", fet_pipe_2, "inputnode.stacks")

# Add a new node that wraps the function connect to BIDS to move the output
# to the derivatives folder
move_to_BIDS_node = pe.Node(
    niu.Function(
        input_names=["stacks", "output_volume", "derivatives_folder"],
        output_names=["output_volume"],
        function=move_to_BIDS,
    ),
    name="move_to_BIDS_node",
)

# manually add the derivatives folder
move_to_BIDS_node.inputs.derivatives_folder = fabian_recon_path

# connect the output of the pipeline to the new node
main_workflow.connect(
    fet_pipe_2, "outputnode.output_volume", move_to_BIDS_node, "output_volume"
)

# connect subject and session of the datasource to the new node
main_workflow.connect(datasource, "stacks", move_to_BIDS_node, "stacks")

main_workflow.run()

# Now compare, for each subject and session in recon and recon_baseline,
# the output volumes, check that they are the same,
# with a tolerance of 1e3 per voxel

# for each subject
for sub in sorted(glob.glob("sub-*")):
    # for each session
    for ses in os.listdir(os.path.join(fabian_recon_path, sub)):
        # get the recon and recon_baseline volumes
        recon = nib.load(
            os.path.join(
                fabian_recon_path,
                sub,
                ses,
                "anat",
                f"{sub}_{ses}_recon.nii.gz",
            )
        )
        recon_baseline = nib.load(
            os.path.join(
                fabian_recon_path_baseline,
                sub,
                ses,
                "anat",
                f"{sub}_{ses}_recon.nii.gz",
            )
        )
        # check that the shape is the same
        assert recon.shape == recon_baseline.shape
        # check that the affine is the same
        assert np.allclose(recon.affine, recon_baseline.affine)
        # check that the data is the same
        assert np.allclose(
            recon.get_fdata(), recon_baseline.get_fdata(), atol=1e3
        )

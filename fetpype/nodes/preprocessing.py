import numpy as np
import nibabel as ni
import os
from nipype.interfaces.base import (
    traits,
    TraitedSpec,
    File,
    BaseInterface,
    BaseInterfaceInputSpec,
)

def nesvor_brain_extraction(raw_T2s, pre_command="", nesvor_image=""):
    """
    Function wrapping nesvor segment-stack for use with nipype

    Inputs:
        raw_T2s:
            Raw T2 file names
        pre_command:
            Command to run nesvor_image (e.g. docker run or singularity run)
        nesvor_image:
            nesvor_image name (e.g. junshenxu/nesvor:v0.5.0)

    Outputs:
        bmasks:
            Brain masks for each T2 low-resolution stack given in raw_T2s.
    """
    import os
    import nibabel as ni

    output_dir = os.path.abspath("")

    # [:-7] to strip out .nii.gz
    bmasks_tmp = [
        os.path.abspath(
            os.path.basename(s)[:-7].replace("_T2w", "_masktmp") + ".nii.gz",
        )
        for s in raw_T2s
    ]

    # DOCKER PATH
    if "docker" in pre_command:
        os.environ["CUDA_VISIBLE_DEVICES"] = "1"
        os.environ["MKL_THREADING_LAYER"] = "GNU"
        stacks_dir = os.path.commonpath(raw_T2s)
        masks_dir = os.path.commonpath(bmasks_tmp)
        stacks_docker = " ".join(
            [s.replace(stacks_dir, "/data") for s in raw_T2s]
        )
        bmasks_docker = " ".join(
            [m.replace(masks_dir, "/masks") for m in bmasks_tmp]
        )

        cmd = pre_command
        cmd += (
            f"-v {output_dir}:/masks "
            f"-v {stacks_dir}:/data "
            f"{nesvor_image} nesvor segment-stack "
            f"--input-stacks {stacks_docker} "
            f"--output-stack-masks {bmasks_docker} "
            "--no-augmentation-seg"
        )
    # SINGULARITY PATH
    elif "singularity" in pre_command:
        stacks = " ".join(raw_T2s)
        masks = " ".join(bmasks_tmp)

        cmd = pre_command + nesvor_image

        cmd += (
            "nesvor segment-stack "
            f"--input-stacks {stacks} "
            f"--output-stack-masks {masks} "
            "--no-augmentation-seg"
            # Test without dir_output for masks properly named
            # f"--dir-output {output_dir} "
        )
    else:
        raise ValueError(
            "pre_command must either contain docker or singularity."
        )

    print(cmd)
    os.system(cmd)
    bmasks = []
    for bmasktmp in bmasks_tmp:
        bmask = bmasktmp.replace("_masktmp", "_mask")
        mask = ni.load(bmasktmp)
        # For some reason, we need to swap the first axis of NeSVoR's BE mask
        # to have something consistent with our data.
        # This no longer happens?
        # ni.save(
        #     ni.Nifti1Image(mask.get_fdata()[::-1, :, :], mask.affine), bmask
        # )
        # copy mask to bmask using os.system
        os.system(f"cp {bmasktmp} {bmask}")

        assert os.path.exists(bmask), f"Error, {bmask} does not exist"
        bmasks.append(bmask)
    return bmasks


# This function is not currently used, as both nesvor_brain_extraction
# and niftymic_brain_extraction rely on MONAIfbs, except that the
# nesvor version is built in a docker with GPU compatibility.
# We might re-use this path in the future, if we want to use
# a CPU-based brain extraction.
def niftymic_brain_extraction(raw_T2s, pre_command="", niftymic_image=""):
    """
    Function wrapping niftymic_segment_fetal_brains for use with nipype.

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


class CropStacksAndMasksInputSpec(BaseInterfaceInputSpec):
    """Class used to represent the inputs of the
    CropStacksAndMasks interface.
    """

    input_image = File(mandatory=True, desc="Input image filename")
    input_mask = File(mandatory=True, desc="Input mask filename")
    boundary = traits.Int(
        15,
        desc="Padding (in mm) to be set around the cropped image and mask",
        usedefault=True,
    )
    disabled = traits.Bool(
        False, desc="Disable cropping", usedefault=True, mandatory=False
    )


class CropStacksAndMasksOutputSpec(TraitedSpec):
    """Class used to represent the outputs of the
    CropStacksAndMasks interface."""

    output_image = File(desc="Cropped image")
    output_mask = File(desc="Cropped mask")


class CropStacksAndMasks(BaseInterface):
    """Interface to crop the field of view of an image and its mask.

    Examples
    --------
    >>> from fetpype.nodes.preprocessing import CropStacksAndMasks
    >>> crop_input = CropStacksAndMasks()
    >>> crop_input.inputs.input_image = 'sub-01_acq-haste_run-1_T2w.nii.gz'
    >>> crop_input.inputs.input_mask = 'sub-01_acq-haste_run-1_T2w_mask.nii.gz'
    >>> crop_input.run() # doctest: +SKIP
    """

    input_spec = CropStacksAndMasksInputSpec
    output_spec = CropStacksAndMasksOutputSpec

    def _gen_filename(self, name):
        if name == "output_image":
            return os.path.abspath(os.path.basename(self.inputs.input_image))
        elif name == "output_mask":
            return os.path.abspath(os.path.basename(self.inputs.input_mask))
        return None

    def _squeeze_dim(self, arr, dim):
        if arr.shape[dim] == 1 and len(arr.shape) > 3:
            return np.squeeze(arr, axis=dim)
        return arr

    def _crop_stack_and_mask(
        self,
        image_path,
        mask_path,
        boundary_i=0,
        boundary_j=0,
        boundary_k=0,
        unit="mm",
    ):
        """
        Crops the input image to the field of view given by the bounding box
        around its mask.
        Code inspired from Michael Ebner:
        https://github.com/gift-surg/NiftyMIC/blob/master/niftymic/base/stack.py

        Input
        -----
        image_path: Str
            Path to a Nifti image
        mask_path: Str
            Path to the corresponding nifti mask
        boundary_i: int
            Boundary to add to the bounding box in the i direction
        boundary_j: int
            Boundary to add to the bounding box in the j direction
        boundary_k: int
            Boundary to add to the bounding box in the k direction
        unit: str
            The unit defining the dimension size in nifti

        Output
        ------
        image_cropped:
            Image cropped to the bounding box of mask_ni, including boundary
        mask_cropped
            Mask cropped to its bounding box
        """
        print(f"Working on {image_path} and {mask_path}")
        image_ni = ni.load(image_path)
        mask_ni = ni.load(mask_path)
        image = self._squeeze_dim(image_ni.get_fdata(), -1)
        mask = self._squeeze_dim(mask_ni.get_fdata(), -1)

        assert all([i >= m] for i, m in zip(image.shape, mask.shape)), (
            "For a correct cropping, the image should be larger "
            "or equal to the mask."
        )

        # Get rectangular region surrounding the masked voxels
        [x_range, y_range, z_range] = self._get_rectangular_masked_region(mask)

        if np.array([x_range, y_range, z_range]).all() is None:
            print("Cropping to bounding box of mask led to an empty image.")
            return None

        if unit == "mm":
            spacing = image_ni.header.get_zooms()
            boundary_i = np.round(boundary_i / float(spacing[0]))
            boundary_j = np.round(boundary_j / float(spacing[1]))
            boundary_k = np.round(boundary_k / float(spacing[2]))

        shape = [min(im, m) for im, m in zip(image.shape, mask.shape)]
        x_range[0] = np.max([0, x_range[0] - boundary_i])
        x_range[1] = np.min([shape[0], x_range[1] + boundary_i])

        y_range[0] = np.max([0, y_range[0] - boundary_j])
        y_range[1] = np.min([shape[1], y_range[1] + boundary_j])

        z_range[0] = np.max([0, z_range[0] - boundary_k])
        z_range[1] = np.min([shape[2], z_range[1] + boundary_k])

        new_origin = list(
            ni.affines.apply_affine(
                image_ni.affine, [x_range[0], y_range[0], z_range[0]]
            )
        ) + [1]

        new_affine = image_ni.affine
        new_affine[:, -1] = new_origin

        image_cropped = image[
            x_range[0] : x_range[1],  # noqa: E203
            y_range[0] : y_range[1],  # noqa: E203
            z_range[0] : z_range[1],  # noqa: E203
        ]
        mask_cropped = mask[
            x_range[0] : x_range[1],  # noqa: E203
            y_range[0] : y_range[1],  # noqa: E203
            z_range[0] : z_range[1],  # noqa: E203
        ]

        image_cropped = ni.Nifti1Image(image_cropped, new_affine)
        mask_cropped = ni.Nifti1Image(mask_cropped, new_affine)
        ni.save(image_cropped, self._gen_filename("output_image"))
        ni.save(mask_cropped, self._gen_filename("output_mask"))

    def _get_rectangular_masked_region(
        self,
        mask: np.ndarray,
    ) -> tuple:
        """
        Computes the bounding box around the given mask
        Code inspired from Michael Ebner:
        https://github.com/gift-surg/NiftyMIC/blob/master/niftymic/base/stack.py

        Input
        -----
        mask: np.ndarray
            Input mask
        range_x:
            pair defining x interval of mask in voxel space
        range_y:
            pair defining y interval of mask in voxel space
        range_z:
            pair defining z interval of mask in voxel space
        """
        if np.sum(abs(mask)) == 0:
            return None, None, None
        shape = mask.shape
        # Define the dimensions along which to sum the data
        sum_axis = [(1, 2), (0, 2), (0, 1)]
        range_list = []

        # Non-zero elements of numpy array along the the 3 dimensions
        for i in range(3):
            sum_mask = np.sum(mask, axis=sum_axis[i])
            ran = np.nonzero(sum_mask)[0]

            low = np.max([0, ran[0]])
            high = np.min([shape[0], ran[-1] + 1])
            range_list.append(np.array([low, high]).astype(int))

        return range_list

    def _run_interface(self, runtime):
        if not self.inputs.disabled:
            boundary = self.inputs.boundary
            self._crop_stack_and_mask(
                self.inputs.input_image,
                self.inputs.input_mask,
                boundary_i=boundary,
                boundary_j=boundary,
                boundary_k=boundary,
            )
        else:
            os.system(
                f"cp {self.inputs.input_image} "
                f"{self._gen_filename('output_image')}"
            )
            os.system(
                f"cp {self.inputs.input_mask} "
                f"{self._gen_filename('output_mask')}"
            )

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["output_image"] = self._gen_filename("output_image")
        outputs["output_mask"] = self._gen_filename("output_mask")
        return outputs


def copy_header(in_file, ref_file):
    import nibabel as ni

    # Load the data
    in_ni = ni.load(in_file)
    ref_ni = ni.load(ref_file)

    data = in_ni.get_fdata()

    # flip dimensions x and z
    data = data[::-1, :, :]

    # Copy the header
    new_img = in_ni.__class__(data, ref_ni.affine, ref_ni.header)

    # save new file, which has the same name, but adding _flipped to the end
    # before the extension
    in_file_new = in_file.replace(".nii.gz", "_flipped.nii.gz")

    ni.save(new_img, in_file_new)
    return in_file_new

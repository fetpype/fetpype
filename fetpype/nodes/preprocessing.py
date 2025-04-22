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
from fetpype.nodes.utils import get_run_id


class CropStacksAndMasksInputSpec(BaseInterfaceInputSpec):
    """Class used to represent the inputs of the
    CropStacksAndMasks interface.
    """

    image = File(mandatory=True, desc="Input image filename")
    mask = File(mandatory=True, desc="Input mask filename")
    boundary = traits.Int(
        15,
        desc="Padding (in mm) to be set around the cropped image and mask",
        usedefault=True,
    )

    is_enabled = traits.Bool(
        True,
        desc="Whether cropping and masking are enabled.",
        usedefault=True,
        mandatory=False,
    )


class CropStacksAndMasksOutputSpec(TraitedSpec):
    """Class used to represent the outputs of the
    CropStacksAndMasks interface."""

    output_image = File(desc="Cropped image")
    output_mask = File(desc="Cropped mask")


class CropStacksAndMasks(BaseInterface):
    """
    Interface to crop the field of view of an image and its mask.

    This class provides functionality to crop a Nifti image and its corresponding mask 
    to the bounding box defined by the mask. It also allows for adding boundaries 
    around the cropped region.

    Args:
        image (str): Input image filename
        mask (input; str): Input mask filename
        boundary (input; int): Padding (in mm) to be set around the cropped image and mask.
        is_enabled (input; bool): Whether cropping and masking are enabled.
        output_image (output; str): Path to the cropped image.
        output_mask (output; str): Path to the cropped mask.
    
    Examples:
        >>> from fetpype.nodes.preprocessing import CropStacksAndMasks
        >>> crop_input = CropStacksAndMasks()
        >>> crop_input.inputs.image = 'sub-01_acq-haste_run-1_T2w.nii.gz'
        >>> crop_input.inputs.mask = 'sub-01_acq-haste_run-1_T2w_mask.nii.gz'
        >>> crop_input.run() # doctest: +SKIP

    References:
        - Michael Ebner's NiftyMIC repository: https://github.com/gift-surg/NiftyMIC
    """

    input_spec = CropStacksAndMasksInputSpec
    output_spec = CropStacksAndMasksOutputSpec

    def _gen_filename(self, name):
        if name == "output_image":
            return os.path.abspath(os.path.basename(self.inputs.image))
        elif name == "output_mask":
            return os.path.abspath(os.path.basename(self.inputs.mask))
        return None

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

        Args:
            image_path (str): Path to a Nifti image.
            mask_path (str): Path to the corresponding Nifti mask.
            boundary_i (int): Boundary to add to the bounding box in the i direction.
            boundary_j (int): Boundary to add to the bounding box in the j direction.
            boundary_k (int): Boundary to add to the bounding box in the k direction.
            unit (str): The unit defining the dimension size in Nifti.

        Returns:
            image_cropped: Image cropped to the bounding box of mask_ni, including boundary.
            mask_cropped: Mask cropped to its bounding box.

        Notes:
            Code inspired by Michael Ebner:
            https://github.com/gift-surg/NiftyMIC/blob/master/niftymic/base/stack.py
        """
        print(f"Working on {image_path} and {mask_path}")
        image_ni = ni.load(image_path)
        mask_ni = ni.load(mask_path)

        image = image_ni.get_fdata()
        mask = mask_ni.get_fdata()

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
        Computes the bounding box around the given mask. 
        Code inspired by Michael Ebner:
        https://github.com/gift-surg/NiftyMIC/blob/master/niftymic/base/stack.py

        Args:
            mask (np.ndarray): Input mask.
            range_x (tuple): Pair defining x interval of mask in voxel space.
            range_y (tuple): Pair defining y interval of mask in voxel space.
            range_z (tuple): Pair defining z interval of mask in voxel space.

        Returns:
            tuple: A tuple containing the bounding box ranges for x, y, and z.
            
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
        if self.inputs.is_enabled:
            boundary = self.inputs.boundary
            self._crop_stack_and_mask(
                self.inputs.image,
                self.inputs.mask,
                boundary_i=boundary,
                boundary_j=boundary,
                boundary_k=boundary,
            )
        else:
            os.system(
                f"cp {self.inputs.image} "
                f"{self._gen_filename('output_image')}"
            )
            os.system(
                f"cp {self.inputs.mask} "
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


class CheckAffineResStacksAndMasksInputSpec(BaseInterfaceInputSpec):
    """Class used to represent the inputs of the
    CheckAffineResStacksAndMasks interface.
    """

    stacks = traits.List(
        traits.File(exists=True),
        desc="List of input stacks",
        mandatory=True,
    )
    masks = traits.List(
        traits.File(exists=True),
        desc="List of input masks",
        mandatory=True,
    )
    is_enabled = traits.Bool(
        True,
        desc="Is bias field correction enabled?",
        usedefault=True,
        mandatory=False,
    )


class CheckAffineResStacksAndMasksOutputSpec(TraitedSpec):
    """Class used to represent the outputs of the
    CheckAffineResStacksAndMasks interface."""

    output_stacks = traits.List(
        desc="List of bias corrected stacks",
    )
    output_masks = traits.List(
        desc="List of masks for bias corrected stacks",
    )


class CheckAffineResStacksAndMasks(BaseInterface):
    """
    Interface to check that the shape of stacks and masks are consistent.
    (e.g. no trailing dimensions of size 1).
    If enabled, also checks that the resolution, affine, and shape of the
    stacks and masks are consistent. Discards the stack and mask if they are
    not.

    Args:

        stacks (input; list): List of input stacks.
        masks (input; list): List of input masks.
        is_enabled (input; bool): Whether the check is enabled.
        output_stacks (output; list): List of stacks that passed the check.
        output_masks (output; list): List of masks that passed the check.
        
    Examples:
        >>> from fetpype.nodes.preprocessing import CheckAffineResStacksAndMasks
        >>> check_input = CheckAffineResStacksAndMasks()
        >>> check_input.inputs.stacks = ['sub-01_acq-haste_run-1_T2w.nii.gz']
        >>> check_input.inputs.masks = ['sub-01_acq-haste_run-1_T2w_mask.nii.gz']
        >>> check_input.run() # doctest: +SKIP
    """

    input_spec = CheckAffineResStacksAndMasksInputSpec
    output_spec = CheckAffineResStacksAndMasksOutputSpec
    _results = {}

    def _squeeze_dim(self, arr, dim):
        if arr.shape[dim] == 1 and len(arr.shape) > 3:
            return np.squeeze(arr, axis=dim)
        return arr

    def compare_resolution_affine(self, r1, a1, r2, a2, s1, s2) -> bool:
        r1 = np.array(r1)
        a1 = np.array(a1)
        r2 = np.array(r2)
        a2 = np.array(a2)
        if s1 != s2:
            return False
        if r1.shape != r2.shape:
            return False
        if np.amax(np.abs(r1 - r2)) > 1e-3:
            return False
        if a1.shape != a2.shape:
            return False
        if np.amax(np.abs(a1 - a2)) > 1e-3:
            return False
        return True

    def _run_interface(self, runtime):
        stacks_out = []
        masks_out = []
        for i, (imp, maskp) in enumerate(
            zip(self.inputs.stacks, self.inputs.masks)
        ):
            skip_stack = False
            out_stack = os.path.join(
                self._gen_filename("output_dir"), os.path.basename(imp)
            )
            out_mask = os.path.join(
                self._gen_filename("output_dir"),
                os.path.basename(maskp),
            )
            image_ni = ni.load(self.inputs.stacks[i])
            mask_ni = ni.load(self.inputs.masks[i])
            image = self._squeeze_dim(image_ni.get_fdata(), -1)
            mask = self._squeeze_dim(mask_ni.get_fdata(), -1)
            image_ni = ni.Nifti1Image(image, image_ni.affine, image_ni.header)
            mask_ni = ni.Nifti1Image(mask, mask_ni.affine, mask_ni.header)

            if self.inputs.is_enabled:
                im_res = image_ni.header["pixdim"][1:4]
                mask_res = mask_ni.header["pixdim"][1:4]
                im_aff = image_ni.affine
                mask_aff = mask_ni.affine
                im_shape = image_ni.shape
                mask_shape = mask_ni.shape
                if not self.compare_resolution_affine(
                    im_res, im_aff, mask_res, mask_aff, im_shape, mask_shape
                ):
                    skip_stack = True
                    print(
                        f"Resolution/shape/affine mismatch -- Skipping the stack {os.path.basename(imp)} and mask {os.path.basename(maskp)}"
                    )
            if not skip_stack:
                ni.save(image_ni, out_stack)
                ni.save(mask_ni, out_mask)
                stacks_out.append(str(out_stack))
                masks_out.append(str(out_mask))
        self._results["output_stacks"] = stacks_out
        self._results["output_masks"] = masks_out
        if len(stacks_out) == 0:
            raise ValueError(
                "All stacks and masks were discarded during the metadata check."
            )
        return runtime

    def _gen_filename(self, name):

        if name == "output_dir":
            return os.path.abspath("")
        return None

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["output_stacks"] = self._results.get(
            "output_stacks", self._gen_filename("output_stacks")
        )
        outputs["output_masks"] = self._results.get(
            "output_masks", self._gen_filename("output_masks")
        )
        return outputs


class CheckAndSortStacksAndMasksInputSpec(BaseInterfaceInputSpec):
    """Class used to represent the inputs of the
    SortStacksAndMasks interface.
    """

    stacks = traits.List(
        traits.File(exists=True),
        desc="List of input stacks",
        mandatory=True,
    )
    masks = traits.List(
        traits.File(exists=True),
        desc="List of input masks",
        mandatory=True,
    )


class CheckAndSortStacksAndMasksOutputSpec(TraitedSpec):
    """Class used to represent the outputs of the
    SortStacksAndMasks interface."""

    output_stacks = traits.List(
        desc="List of bias corrected stacks",
    )
    output_masks = traits.List(
        desc="List of masks for bias corrected stacks",
    )


class CheckAndSortStacksAndMasks(BaseInterface):
    """
    Interface to check the input stacks and masks and make sure that
    all stacks have a corresponding mask.
    """

    input_spec = CheckAndSortStacksAndMasksInputSpec
    output_spec = CheckAndSortStacksAndMasksOutputSpec
    _results = {}

    def _run_interface(self, runtime):

        # Check that stacks and masks run_ids match
        stacks_run = get_run_id(self.inputs.stacks)
        masks_run = get_run_id(self.inputs.masks)

        out_stacks = []
        out_masks = []
        for i, s in enumerate(stacks_run):
            in_stack = self.inputs.stacks[i]

            if s in masks_run:
                out_stack = os.path.join(
                    self._gen_filename("output_dir_stacks"),
                    os.path.basename(in_stack),
                )
                in_mask = self.inputs.masks[masks_run.index(s)]
                out_mask = os.path.join(
                    self._gen_filename("output_dir_masks"),
                    os.path.basename(in_mask),
                )
                out_stacks.append(out_stack)
                out_masks.append(out_mask)
            else:
                raise RuntimeError(
                    f"Stack {os.path.basename(self.inputs.stacks[i])} has "
                    f"no corresponding mask (existing IDs: {masks_run})."
                )

            os.system(f"cp {in_stack} " f"{out_stack}")
            os.system(f"cp {in_mask} " f"{out_mask}")
        self._results["output_stacks"] = out_stacks
        self._results["output_masks"] = out_masks
        return runtime

    def _gen_filename(self, name):
        if name == "output_dir_stacks":
            path = os.path.abspath("stacks")
            os.makedirs(path, exist_ok=True)
            return path
        elif name == "output_dir_masks":
            path = os.path.abspath("masks")
            os.makedirs(path, exist_ok=True)
            return path
        return None

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["output_stacks"] = self._results["output_stacks"]
        outputs["output_masks"] = self._results["output_masks"]
        return outputs


def run_prepro_cmd(
    input_stacks,
    cmd,
    is_enabled=True,
    input_masks=None,
    singularity_path=None
):
    import os
    from fetpype import VALID_PREPRO_TAGS

    # Important for mapnodes
    unlist_stacks = False
    unlist_masks = False

    if isinstance(input_stacks, str):
        input_stacks = [input_stacks]
        unlist_stacks = True
    if isinstance(input_masks, str):
        input_masks = [input_masks]
        unlist_masks = True

    from fetpype.nodes import is_valid_cmd, get_directory, get_mount_docker

    print(input_stacks, cmd, is_enabled, input_masks)
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
            # assume that if we have a singularity path, we are using singularity and the 
            # parameter has been set in the config file
            cmd = cmd.replace("<singularity_path>", singularity_path)

        print(f"Running command:\n {cmd}")
        os.system(cmd)
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

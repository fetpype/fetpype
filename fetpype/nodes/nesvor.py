"""
NesVoR pipeline using the nipype interface.

TODO:
- Make it an option to use the docker version instead of the singularity one
- Add all the options of the nesvor command line interface
- Add the rest of the NesVoR functions
"""

import os
from typing import Optional, List
from nipype.interfaces.base import (
    CommandLineInputSpec,
    File,
    TraitedSpec,
    traits,
    isdefined,
)
from .container import ContainerCommandLine


class NesvorSegmentationInputSpec(CommandLineInputSpec):
    """
    Class for the input for the NeSVoRSeg nipype interface.
    Inherits from CommandLineInputSpec.

    Attributes
    ----------
    input_stacks : traits.List
        List of input stacks
    output_stack_masks : traits.Either
        Either a list of files or a single file specifying the output folder
        for the masks
    no_augmentation_seg : traits.Bool
        Use no augmentation seg (mandatory for curr version, else error)
    pre_command : str
        Pre-command to be run before nesvor. Not used in the command line as a
        parameter.
    nesvor_image : str
        Singularity Nesvor command. Not used in the command line as a
        parameter.
    """

    input_stacks = traits.List(
        traits.File(exists=True),
        desc="List of input stacks",
        argstr="--input-stacks %s",
        mandatory=True,
    )

    output_stack_masks = traits.Either(
        traits.List(
            traits.File(),
            desc="List of output stack masks",
        ),
        traits.File(desc="Output folder for the masks"),
        genfile=True,
        hash_files=False,
        argstr="--output-stack-masks %s",
    )

    no_augmentation_seg = traits.Bool(
        argstr="--no-augmentation-seg",
        no_augmentation_seg=traits.Bool(
            argstr="--no-augmentation-seg",
            desc="use no augmentation seg (mandatory for curr version, "
            "else error)",
        ),
    )


class NesvorSegmentationOutputSpec(TraitedSpec):
    """
    Class for the output specification for the NeSVoRSeg nipype interface.
    Inherits from TraitedSpec.

    Attributes
    ----------
    output_stack_masks : traits.List
        List of output segmentation masks
    """

    output_stack_masks = traits.List(
        traits.File(),
        desc="List of output segmentation masks",
    )


class NesvorSegmentation(ContainerCommandLine):
    """
    Class for the NeSVoRSeg nipype interface.
    Inherits from ContainerCommandLine.

    This class calls the docker or the singularity container. There is no need
    to implement _run_interface, as it is inherited from
    ContainerCommandLine and we just need to change the _cmd
    attribute. Docker mounts are also managed by ContainerCommandLine

    Attributes
    ----------
    _cmd : str
        Command to be run.
    _mount_keys : list
        List of keys to be mounted on the docker image.
    input_spec : NesvorSegmentationInputSpec
        Class containing the input specification for the NeSVoRSeg
        nipype interface.
    output_spec : NesvorSegmentationOutputSpec
        Class containing the output specification for the NeSVoRSeg
        nipype interface.

    Methods
    -------
    _gen_filename(name: str) -> Optional[List[str]]
        Generate output filename if not defined.
    _list_outputs() -> dict
        List the outputs of the NesvorSegmentation.
    """

    input_spec = NesvorSegmentationInputSpec
    output_spec = NesvorSegmentationOutputSpec

    _cmd = "nesvor segment-stack"
    _mount_keys = ["input_stacks", "output_stack_masks"]

    def __init__(self, pre_command, container_image, **inputs):
        super(NesvorSegmentation, self).__init__(
            pre_command=pre_command, container_image=container_image, **inputs
        )

    def _gen_filename(self, name: str) -> Optional[List[str]]:
        """
        Generate output filename if not defined.

        Parameters
        ----------
        name : str
            Name of the attribute.

        Returns
        ----------
        output : Optional[List[str]]
            List of output filenames if name is "output_stack_masks",
            None otherwise.
        """
        if name == "output_stack_masks":
            output = self.inputs.output_stack_masks
            if not isdefined(output):
                output = []

                # get current working dir
                cwd = os.getcwd()

                for stack in self.inputs.input_stacks:
                    # remove .nii.gz extension and full path
                    base = os.path.basename(stack)
                    # get filename including extension
                    filename, _ = os.path.splitext(base)
                    # split the extension once
                    filename, _ = os.path.splitext(filename)
                    # split the extension again

                    # add the full path to the output
                    output.append(os.path.join(cwd, filename + "_mask.nii.gz"))

            return output
        return None

    def _list_outputs(self) -> dict:
        """
        List the outputs of the NesvorSegmentation.

        Returns
        ----------
        outputs : dict
            Dictionary of outputs.
        """
        outputs = self._outputs().get()
        if isdefined(self.inputs.output_stack_masks):
            outputs["output_stack_masks"] = self.inputs.output_stack_masks
        else:
            outputs["output_stack_masks"] = self._gen_filename(
                "output_stack_masks"
            )

        return outputs


class NesvorRegisterInputSpec(CommandLineInputSpec):
    """
    NesvorRegisterInputSpec is a class for specifying the input for
    the NeSVoRReg nipype interface. It inherits from CommandLineInputSpec.

    Attributes
    ----------
    input_stacks : TraitsList[File]
        List of input stacks.
    stack_masks : TraitsList[File]
        List of stack masks.
    output_slices : File
        Path to save output slices.
    output_json : File
        Path to save output JSON.
    output_log : File
        Path to save output log.
    pre_command : str
        Pre-command to be run before nesvor. Not used in the command line as a
        parameter.
    nesvor_image : str
        Singularity Nesvor command. Not used in the command line as a
        parameter.
    """

    input_stacks = traits.List(
        traits.File(exists=True),
        desc="List of input stacks",
        argstr="--input-stacks %s",
        mandatory=True,
    )

    stack_masks = traits.List(
        traits.File(exists=True),
        desc="List of stack masks",
        argstr="--stack-masks %s",
    )

    output_slices = File(
        desc="Path to save output slices",
        argstr="--output-slices %s",
        genfile=True,
        hash_files=False,
    )

    output_json = File(
        desc="Path to save output json",
        argstr="--output-json %s",
        keep_extension=True,
    )

    output_log = File(
        desc="Path to save output log",
        argstr="--output-log %s",
        keep_extension=True,
    )


class NesvorRegisterOutputSpec(TraitedSpec):
    """
    NesvorRegisterOutputSpec is a class for specifying the output for
    the NeSVoRReg nipype interface. It inherits from TraitedSpec.

    Attributes
    ----------
    output_slices : File
        Folder where the output slices are saved.
    """

    output_slices = File(
        desc="Folder where the output slices are saved",
    )


class NesvorRegistration(ContainerCommandLine):
    """
    NesvorRegistration is a class for the NeSVoRReg nipype interface.
    It inherits from ContainerCommandLine.

    This class calls the docker or the singularity container. There is no need
    to implement _run_interface, as it is inherited from
    ContainerCommandLine and we just need to change the _cmd
    attribute. Docker mounts are also managed by ContainerCommandLine

    Attributes
    ----------
    _cmd : str
        Command to be run.
    input_spec : NesvorRegisterInputSpec
        Class containing the input specification for the NeSVoRReg
        nipype interface.
    output_spec : NesvorRegisterOutputSpec
        Class containing the output specification for the NeSVoRReg
        nipype interface.
    Methods
    -------
    _gen_filename(self, name: str) -> str:
        Generates an output filename if not defined.
    _list_outputs(self) -> dict:
        Lists the outputs of the class if not defined.
    """

    input_spec = NesvorRegisterInputSpec
    output_spec = NesvorRegisterOutputSpec

    _cmd = "nesvor register"
    _mount_keys = ["input_stacks", "stack_masks", "output_slices"]

    def __init__(self, pre_command, container_image, **inputs):
        super(NesvorRegistration, self).__init__(
            pre_command=pre_command, container_image=container_image, **inputs
        )

    def _gen_filename(self, name: str) -> str:
        """
        Generate output filename if not defined.

        Parameters
        ----------
        name : str
            The name for the filename to generate.

        Returns
        -------
        str
            The generated filename.
        """
        if name == "output_slices":
            output = self.inputs.output_slices
            if not isdefined(output):
                # get current working dir
                cwd = os.getcwd()

                # add the name of the folder
                output = os.path.join(cwd, "slices")

                # create the folder if it does not exist
                os.makedirs(output, exist_ok=True)
            return output

        return None

    def _list_outputs(self) -> dict:
        """
        List the outputs.

        Returns
        -------
        dict
            The dictionary containing the output.
        """
        outputs = self._outputs().get()
        if isdefined(self.inputs.output_slices):
            outputs["output_slices"] = self.inputs.output_slices
        else:
            outputs["output_slices"] = self._gen_filename("output_slices")
        return outputs


class NesvorReconstructionInputSpec(CommandLineInputSpec):
    """
    NesvorReconstructionInputSpec is a class for the input specification for
    the NeSVoRRec nipype interface.
    It inherits from CommandLineInputSpec.

    Attributes
    ----------
    input_slices : traits.Directory
        The directory where the input slices are saved. This argument is
        mandatory.
    output_volume : traits.File
        The path where the output reconstruction is saved.
    pre_command : str
        Pre-command to be run before nesvor. Not used in the command line as a
        parameter.
    nesvor_image : str
        Singularity Nesvor command. Not used in the command line as a
        parameter.
    TODO:
    Currently, it only works with a list of slices,
    but it should also work with a list of stacks.
    We should add the rest of the options and parameters.
    """

    input_slices = traits.Directory(
        exists=True,
        desc="Folder where the input slices are saved",
        argstr="--input-slices %s",
        mandatory=True,
    )

    output_volume = File(
        desc="Path to save output reconstruction",
        argstr="--output-volume %s",
        genfile=True,
        hash_files=False,
    )
    # pre command and nesvor image
    # these two commands are not used in the command line
    pre_command = traits.Str(
        desc="Pre-command to be run",
        mandatory=True,
    )

    nesvor_image = traits.Str(
        desc="Singularity Nesvor command",
        mandatory=True,
    )


class NesvorReconstructionOutputSpec(TraitedSpec):
    """
    NesvorReconstructionOutputSpec is a class for the output specification for
    the NeSVoRRec nipype interface.
    It inherits from TraitedSpec.

    Attributes
    ----------
    output_volume : traits.File
        The reconstructed image.
    """

    output_volume = File(
        desc="The reconstructed image",
    )


class NesvorReconstruction(ContainerCommandLine):
    """
    NesvorReconstruction is a class for the NeSVoR nipype interface.
    It inherits from ContainerCommandLine.

    This class calls the docker or the singularity container. There is no need
    to implement _run_interface, as it is inherited from
    ContainerCommandLine and we just need to change the _cmd
    attribute. Docker mounts are also managed by ContainerCommandLine

    Attributes
    ----------
    _cmd : str
        The command to be run by the singularity container.
    input_spec : NesvorReconstructionInputSpec
        The input specifications for the NeSVoRRec interface.
    output_spec : NesvorReconstructionOutputSpec
        The output specifications for the NeSVoRRec interface.
    Methods
    -------
    _gen_filename(self, name: str) -> str:
        Generates an output filename if not defined.
    _list_outputs(self) -> dict:
        Lists the outputs of the class if not defined.

    """

    input_spec = NesvorReconstructionInputSpec
    output_spec = NesvorReconstructionOutputSpec

    _cmd = "nesvor reconstruct"
    _mount_keys = ["input_slices", "output_volume"]

    def __init__(self, pre_command, container_image, **inputs):
        super(NesvorReconstruction, self).__init__(
            pre_command=pre_command, container_image=container_image, **inputs
        )

    def _gen_filename(self, name: str) -> str:
        """
        Generates an output filename if not defined.

        Parameters
        ----------
        name : str
            The name of the file for which to generate a name.

        Returns
        -------
        str
            The generated filename.
        """
        if name == "output_volume":
            output = self.inputs.output_volume
            if not isdefined(output):
                cwd = os.environ["PWD"]

                # add the name of the folder
                output = os.path.join(cwd, "recon")

                # create the folder if it does not exist
                os.makedirs(output, exist_ok=True)

                # add the name of the file
                output = os.path.join(output, "recon.nii.gz")
            return output

        return None

    def _list_outputs(self) -> dict:
        """
        Lists the outputs of the class.

        Returns
        -------
        dict
            The dictionary of outputs.
        """
        outputs = self._outputs().get()
        if isdefined(self.inputs.output_volume):
            outputs["output_volume"] = self.inputs.output_volume
        else:
            outputs["output_volume"] = self._gen_filename("output_volume")
        return outputs


class NesvorFullReconstructionInputSpec(CommandLineInputSpec):
    """
    Class for the input for the NeSVoRRecon nipype interface.
    Inherits from ContainerCommandLine.

    Some attributes are missing. Need to be implemented later to complete the
    nipype interface.

    Attributes
    ----------
    input_stacks : traits.List
        List of input stacks
    thicknesses : traits.List
        List of thicknesses for each stack
    stack_masks : traits.List
        List of masks of input stacks
    volume_mask : traits.File
        Path to a 3D mask
    background_threshold : traits.Float
        Threshold for background
    otsu_thresholding : traits.Bool
        Apply Otsu thresholding to each input stack
    output_volume : traits.File
        Paths to the reconstructed volume
    output_slices : traits.File
        Folder to save the motion corrected slices
    simulated_slices : traits.File
        Folder to save the simulated (extracted) slices
    output_model : traits.File
        Path to save the output model
    output_json : traits.File
        Path to a json file for saving the inputs and results of the command.
    """

    input_stacks = traits.List(
        traits.File(exists=True),
        desc="Paths to the input stacks (NIfTI).",
        argstr="--input-stacks %s",
        mandatory=True,
    )
    output_volume = File(
        desc="Path to the reconstructed volume",
        argstr="--output-volume %s",
        genfile=True,
        hash_files=False,
    )
    thicknesses = traits.List(
        traits.Float(),
        desc="Slice thickness of each input stack.",
        argstr="--thicknesses %s",
    )
    input_slices = traits.Directory(
        exists=True,
        desc="Folder of the input slices.",
        argstr="--input-slices %s",
    )
    stack_masks = traits.List(
        traits.File(exists=True),
        desc="Paths to masks of input stacks.",
        argstr="--stack-masks %s",
    )
    volume_mask = traits.File(
        exists=True,
        desc="Path to a 3D mask which will be applied to each input stack.",
        argstr="--volume-mask %s",
    )
    stacks_intersection = traits.Bool(
        desc="Only consider the region defined by input stacks intersection.",
        argstr="--stacks-intersection",
    )
    background_threshold = traits.Float(
        desc="Pixels with value <= this threshold will be ignored.",
        argstr="--background-threshold %s",
    )
    otsu_thresholding = traits.Bool(
        desc="Apply Otsu thresholding to each input stack.",
        argstr="--otsu-thresholding",
    )
    output_slices = traits.Directory(
        desc="Folder to save the motion corrected slices.",
        argstr="--output-slices %s",
    )
    simulated_slices = traits.Directory(
        desc="Folder to save the simulated slices from the reconstruction.",
        argstr="--simulated-slices %s",
    )
    output_model = traits.File(
        desc="Path to save the output model (.pt).",
        argstr="--output-model %s",
    )
    output_json = traits.File(
        desc="Path to json for saving the inputs and results of the command.",
        argstr="--output-json %s",
    )
    output_resolution = traits.Float(
        desc="Isotropic resolution of the reconstructed volume.",
        argstr="--output-resolution %s",
        default_value=0.8,
    )
    bias_field_correction = traits.Bool(
        desc="Apply bias field correction to each input stack.",
        argstr="--bias-field-correction",
        default_value=True,
    )
    n_levels_bias = traits.Int(
        desc="Number of levels for the bias field correction.",
        argstr="--n-levels-bias %s",
        default_value=1,
    )


class NesvorFullReconstructionOutputSpec(TraitedSpec):
    """
    Class for the output specification for the NeSVoRRecon nipype interface.
    Inherits from TraitedSpec.

    Attributes
    ----------
    output_volume : traits.File
        Paths to the reconstructed volume
    output_slices : traits.File
        Folder to save the motion corrected slices
    simulated_slices : traits.File
        Folder to save the simulated (extracted) slices
    output_model : traits.File
        Path to save the output model
    # Add more attributes based on the command documentation
    """

    output_volume = traits.File(
        desc="Paths to the reconstructed volume",
    )


class NesvorFullReconstruction(ContainerCommandLine):
    """
    Class for the NeSVoRRecon nipype interface.
    Inherits from ContainerCommandLine.

    Attributes
    ----------
    _cmd : str
        Command to be run.
    _mount_keys : list
        List of keys to be mounted on the docker image.
    input_spec : NesvorFullReconstructionInputSpec
        Class containing the input specification for the NeSVoRRecon
        nipype interface.
    output_spec : NesvorFullReconstructionOutputSpec
        Class containing the output specification for the NeSVoRRecon
        nipype interface.
    """

    input_spec = NesvorFullReconstructionInputSpec
    output_spec = NesvorFullReconstructionOutputSpec

    _cmd = "nesvor reconstruct"
    _mount_keys = ["input_stacks", "stack_masks", "output_volume"]

    def __init__(self, pre_command, container_image, **inputs):
        super(NesvorFullReconstruction, self).__init__(
            pre_command=pre_command, container_image=container_image, **inputs
        )

    def _gen_filename(self, name: str) -> str:
        """
        Generates an output filename if not defined.

        Parameters
        ----------
        name : str
            The name of the file for which to generate a name.

        Returns
        -------
        str
            The generated filename.
        """
        if name == "output_volume":
            output = self.inputs.output_volume
            if not isdefined(output):
                # Create the output path from the
                # current working directory
                output = os.path.join(os.getcwd(), "recon/recon.nii.gz")

                # Create the folder if it does not exist
                os.makedirs(os.path.dirname(output), exist_ok=True)

            return output

        return None

    def _list_outputs(self) -> dict:
        """
        Lists the outputs of the class.

        Returns
        -------
        dict
            The dictionary of outputs.
        """
        outputs = self._outputs().get()
        if isdefined(self.inputs.output_volume):
            outputs["output_volume"] = self.inputs.output_volume
        else:
            outputs["output_volume"] = self._gen_filename("output_volume")
        return outputs

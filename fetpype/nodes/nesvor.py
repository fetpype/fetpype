"""
NesVoR pipeline using the nipype interface.

TODO:
- Make it an option to use the docker version instead of the singularity one
- Add all the options of the nesvor command line interface
- Add the rest of the NesVoR functions
"""

import os
from nipype.interfaces.base import (
    CommandLineInputSpec,
    File,
    TraitedSpec,
    CommandLine,
    traits,
    isdefined,
)

SINGULARITY_NESVOR = "/homedtic/gmarti/SINGULARITY/nesvor_latest.sif"
DOCKER_NESVOR = "junshenxu/nesvor:latest"


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
    """

    input_stacks = traits.List(
        traits.File(exists=True),
        desc="List of input stacks",
        argstr="--input-stacks %s",
        mandatory=True,
    )

    # This should be a traits.Either, either a list of files or a single file
    # specifying the output folder for the masks
    # output_stack_masks = traits.Either(
    #     traits.List(
    #         traits.File(),
    #         desc="List of output stack masks",
    #     ),
    #     traits.File(desc="Output folder for the masks"),
    #     genfile=True,
    #     hash_files=False,
    #     argstr="--output-stack-masks %s",
    #     mandatory=True,
    # )
    output_stack_masks = traits.List(
        traits.File(),
        desc="List of output stack masks",
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


class NesvorSegmentation(CommandLine):
    """
    Class for the NeSVoRSeg nipype interface.
    Inherits from CommandLine.

    Attributes
    ----------
    _cmd : str
        Command to be run.
    input_spec : NesvorSegmentationInputSpec
        Class containing the input specification for the NeSVoRSeg
        nipype interface.
    output_spec : NesvorSegmentationOutputSpec
        Class containing the output specification for the NeSVoRSeg
        nipype interface.

    _format_arg
    """

    _cmd = f"singularity exec --nv {SINGULARITY_NESVOR} \
        nesvor segment-stack"
    input_spec = NesvorSegmentationInputSpec
    output_spec = NesvorSegmentationOutputSpec

    def _gen_filename(self, name):
        """Generate output filename if not defined."""
        if name == "output_stack_masks":
            output = self.inputs.output_stack_masks
            if not isdefined(output):
                output = []
                for stack in self.inputs.input_stacks:
                    # Remove .nii.gz extension
                    name = stack.rsplit(".nii.gz", maxsplit=1)
                    output.append(name[0] + "_mask.nii.gz")
            print(output)
            return output
        return None

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.output_stack_masks):
            outputs["output_stack_masks"] = self.inputs.output_stack_masks
        else:
            outputs["output_stack_masks"] = self._gen_filename("output_stack_masks")
        print(outputs)
        return outputs


class NesvorRegisterInputSpec(CommandLineInputSpec):
    """Class for the input for the NeSVoRReg nipype interface.
    Inherits from CommandLineInputSpec.
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
    """Class for the output for the NeSVoRReg nipype interface.
    Inherits from TraitedSpec.
    """

    output_slices = File(
        desc="Folder where the output slices are saved",
    )

    #output_json = traits.File(
    #    desc="The json file saving the inputs and results",
    #)

    #output_log = traits.File(
    #    desc="The log file of the registration",
    #)


class NesvorRegistration(CommandLine):
    """Class for the NeSVoRReg nipype interface.
    Inherits from CommandLine.

    Calls the singularity container for NeSVoRReg.

    No need to implement _run_interface, as it is inherited from CommandLine
    and we just need to change the _cmd attribute.

    # TODO: if installed, use the docker version?
    """

    _cmd = f"singularity exec --nv {SINGULARITY_NESVOR} \
        nesvor register"

    input_spec = NesvorRegisterInputSpec
    output_spec = NesvorRegisterOutputSpec

    def _gen_filename(self, name):
        """Generate output filename if not defined."""
        if name == "output_slices":
            output = self.inputs.output_slices
            if not isdefined(output):
                # very hacky, fix
                # extract the full path of the folder
                output = os.path.dirname(self.inputs.input_stacks[0])
                # add a new folder named "slices"
                output = os.path.join(output, "slices")
                # create the folder if it does not exist
                os.makedirs(output, exist_ok=True)
            return output

        return None

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.output_slices):
            outputs["output_slices"] = self.inputs.output_slices
        else:
            outputs["output_slices"] = self._gen_filename("output_slices")
        return outputs



class NesvorReconstructionInputSpec(CommandLineInputSpec):
    """Class for the input for the NeSVoRRec nipype interface.
    Inherits from CommandLineInputSpec.
    TODO:
    Right now, it only works with a list of slices,
    but it should also work with a list of stacks,
    and we should add the rest of the options and parameters
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


class NesvorReconstructionOutputSpec(TraitedSpec):
    """Class for the output for the NeSVoRRec nipype interface.
    Inherits from TraitedSpec.
    """

    output_volume = File(
        desc="The reconstructed image",
    )


class NesvorReconstruction(CommandLine):
    """Class for the NeSVoR nipype interface.
    Inherits from CommandLine.

    Calls the singularity container for NeSVoRRec.

    No need to implement _run_interface, as it is inherited from CommandLine
    and we just need to change the _cmd attribute.
    """

    _cmd = f"singularity exec --nv {SINGULARITY_NESVOR} \
        nesvor reconstruct"
    input_spec = NesvorReconstructionInputSpec
    output_spec = NesvorReconstructionOutputSpec

    def _gen_filename(self, name):
        """Generate output filename if not defined."""
        if name == "output_volume":
            output = self.inputs.output_volume
            if not isdefined(output):
                # very hacky, fix
                # extract the full path of the folder
                output = os.path.dirname(self.inputs.input_slices)
                # add a new folder named "recon"
                output = os.path.join(output, "recon")
                # create the folder if it does not exist
                os.makedirs(output, exist_ok=True)
                # add the name of the file
                output = os.path.join(output, "recon.nii.gz")
            return output

        return None


    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.output_volume):
            outputs["output_volume"] = self.inputs.output_volume
        else:
            outputs["output_volume"] = self._gen_filename("output_volume")
        return outputs

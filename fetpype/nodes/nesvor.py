"""
NesVoR pipeline using the nipype interface.

Should be use CommandLine interface or Python interface?
As we are using Docker or singularity, we should use the CommandLine interface.

We introduce the NesVoR pipeline but not 
"""

from nipype.interfaces.base import (
    CommandLineInputSpec,
    File,
    TraitedSpec,
    CommandLine,
    traits,
    isdefined
)
import os

SINGULARITY_NESVOR = "/homedtic/gmarti/SINGULARITY/nesvor_latest.sif"
DOCKER_NESVOR = "junshenxu/nesvor:latest"

class NesvorSegmentationInputSpec(CommandLineInputSpec):
    input_stacks = traits.List(
        traits.File(exists=True),
        desc="List of input stacks",
        argstr="--input-stacks %s",
        mandatory=True,
    )

    # This should be a traits.Either, either a list of files or a single file
    # specifying the output folder for the masks
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
        argstr="--no-augmentation-seg", desc="use no augmentation seg (mandatory for curr version, else error)"
    )


class NesvorSegmentationOutputSpec(TraitedSpec):
    output_stack_masks = traits.List(
        traits.File(desc="the output segmentation masks"),
        desc="List of output segmentation masks",
    )


class NesvorSegmentation(CommandLine):
    """Class for the NeSVoRSeg nipype interface.
    Inherits from CommandLine.

    Calls the singularity container for NeSVoRSeg.

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
                    output.append(name[0] + '_mask.nii.gz')
            return output
        return None

    def _list_outputs(self):
        return {"output_stack_masks": self.inputs.output_stack_masks}



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
        genfile=True,
        hash_files=False,
        keep_extension=True,
    )

    output_log = File(
        desc="Path to save output log",
        argstr="--output-log %s",
        genfile=True,
        hash_files=False,
        keep_extension=True,
    )



class NesvorRegisterOutputSpec(TraitedSpec):
    """Class for the output for the NeSVoRReg nipype interface.
    Inherits from TraitedSpec.
    """

    output_slices = traits.List(
        traits.File(),
        desc="List of output slices",
    )

    output_json = traits.File(
        desc="The json file saving the inputs and results",
    )

    output_log = traits.File(
        desc="The log file of the registration",
    )


class NesvorRegistration(CommandLine):
    """Class for the NeSVoRReg nipype interface.
    Inherits from CommandLine.

    Calls the singularity container for NeSVoRReg.

    No need to implement _run_interface, as it is inherited from CommandLine and we just need to change the _cmd attribute.

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
                #TODO very hacky, fix
                # extract the full path of the folder
                output = os.path.dirname(self.inputs.input_stacks[0])
                # add a new folder named "slices"
                output = os.path.join(output, "slices")
                # create the folder if it does not exist
                os.makedirs(output, exist_ok=True)
            return output
        if name == "output_json":
            output = self.inputs.output_json
            if not isdefined(output):
                #TODO very hacky, fix
                # extract the full path of the folder
                output = os.path.dirname(self.inputs.input_stacks[0])
                # add a new folder named "slices"
                output = os.path.join(output, "slices")
                # create the folder if it does not exist
                os.makedirs(output, exist_ok=True)
                output = os.path.join(output, "slices.json")
            return output
        if name == "output_log":
            output = self.inputs.output_json
            if not isdefined(output):
                #TODO very hacky, fix
                # extract the full path of the folder
                output = os.path.dirname(self.inputs.input_stacks[0])
                # add a new folder named "slices"
                output = os.path.join(output, "slices")
                # create the folder if it does not exist
                os.makedirs(output, exist_ok=True)
                output = os.path.join(output, "output.log")
            return output

        return None



    def _list_outputs(self):
        return {"output_slices": self.inputs.output_slices,
                "output_json": self.inputs.output_json,
                "output_log": self.inputs.output_log}
        
"""
SVRTK_BOUNTI pipeline using the nipype interface.

TODO:
- Make it an option to use the docker version instead of the singularity one
- Add all the options of the command line interface
- Add the rest of the functions available in the singularity/docker image
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
from typing import Optional, List
from .container import ContainerCommandLine


def copy_T2stacks(T2_stacks):
    import os
    output_dir = os.path.abspath("")
    for s in T2_stacks:
        cmd = "cp {} {}".format(s, output_dir)
        os.system(cmd)
    return output_dir


class SvrtkBountiReconstructionInputSpec(CommandLineInputSpec):

    input_dir = traits.Directory(exists=True,
        desc="input fodler containing the LR stacks",
        argstr="%s",
        mandatory=True,
    )

    output_dir = traits.Directory(
        desc="output directory",
        argstr="%s",
        genfile=True,
    )


class SvrtkBountiReconstructionOutputSpec(TraitedSpec):

    output_dir = traits.Directory(
        desc="output directory",
    )


class SvrtkBountiReconstruction(ContainerCommandLine):

    input_spec = SvrtkBountiReconstructionInputSpec
    output_spec = SvrtkBountiReconstructionOutputSpec

    _cmd = "bash /home/auto-proc-svrtk/scripts/auto-brain-reconstruction.sh"
    _mount_keys = ["input_dir", "output_dir"]

    def __init__(self, pre_command, container_image, **inputs):
        super(SvrtkBountiReconstruction, self).__init__(
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
        if name == "output_dir":
            # Create the output path from the
            # current working directory
            output_dir = os.path.abspath("")
            self.inputs.output_dir = output_dir
            return output_dir

        return

    def _list_outputs(self) -> dict:
        """
        List the outputs of the SvrtkBountiReconstruction.

        Returns
        ----------
        outputs : dict
            Dictionary of outputs.
        """
        outputs = self._outputs().get()
        if isdefined(self.inputs.output_dir):
            outputs["output_dir"] = self.inputs.output_dir
        else:
            print("output_dir not defined"
            )
        print(outputs)
        cmd = "mv /home/tmp_proc {}".format(self.inputs.output_dir)
        os.system(cmd)
        return outputs


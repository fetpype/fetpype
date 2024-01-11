"""
Niftymic pipeline using the nipype interface.

TODO:
-
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


class NiftymicReconstructionInputSpec(CommandLineInputSpec):
    """
    NiftymicReconstructionInputSpec is a class for the input specification for
    the Niftymic nipype interface.
    It inherits from CommandLineInputSpec.

    Attributes
    ----------
    input_stacks:traits.List(File)
        Preprocessed T2 file names
    input_masks:traits.List(File)
        Brain masks for each T2 low-resolution stack given in stacks.
    dir_output:traits.Directory
        The path where the output reconstruction is saved.
    pre_command:
        Command to run niftymic_image (e.g. docker run or singularity run)
    niftymic_image:
        niftymic_image name (e.g. renbem/niftymic:latest)

    TODO:

    """

    # inputs
    input_stacks = traits.List(
        File(exists=True),
        desc="List of input stacks to be processed",
        argstr="--filenames %s",
        mandatory=True,
    )

    input_masks = traits.List(
        File(exists=True),
        desc="List of input masks corresponding to the stacks to be processed",
        argstr="--filenames-masks %s",
        mandatory=True,
    )

    # args
    bias_field_correction = traits.Bool(
        True,
        usedefault=True,
        argstr="--bias-field-correction %d",
        desc="bias field correction",
        mandatory=True,
    )

    isotropic_resolution = traits.Float(
        0.5,
        usedefault=True,
        argstr="--isotropic-resolution %f",
        desc="isotropic resolution",
        mandatory=True,
    )

    # output
    recon_file = traits.File(
        desc="reconstructed file",
        argstr="--output %s",
        genfile=True,
        mandatory=False
    )

    recon_mask_file = traits.File(
        desc="reconstructed mask file",
        mandatory=False
    )

    # pre command and niftymic image
    # these two commands are not used in the command line
    pre_command = traits.Str(
        desc="Pre-command to be run",
        mandatory=True,
    )

    niftymic_image = traits.Str(
        desc="Singularity Niftymic command",
        mandatory=True,
    )


class NiftymicReconstructionOutputSpec(TraitedSpec):
    """
    NesvorReconstructionOutputSpec is a class for the output specification for
    the NeSVoRRec nipype interface.
    It inherits from TraitedSpec.

    Attributes
    ----------
    dir_output : traits.Directory
        The reconstructed image.
    """
    recon_file = traits.File(
        desc="reconstructed file",
        exists=True,
    )

    recon_mask_file = traits.File(
        desc="reconstructed mask_file",
        exists=True,
    )


class NiftymicReconstruction(CommandLine):
    """
    NiftymicReconstruction is a class for the Niftymic nipype interface.
    It inherits from CommandLine.

    This class calls the singularity container for NeSVoRRec. There is no need
    to implement _run_interface,
    as it is inherited from CommandLine and we just need to change the
    _cmd attribute.

    Attributes
    ----------
    _cmd : str
        The command to be run by the singularity container.
    input_spec : NiftymicReconstructionInputSpec
        The input specifications for the NeSVoRRec interface.
    output_spec : NiftymicReconstructionOutputSpec
        The output specifications for the NeSVoRRec interface.
    """

    input_spec = NiftymicReconstructionInputSpec
    output_spec = NiftymicReconstructionOutputSpec

    def __init__(self, **inputs):
        self._cmd = "niftymic_reconstruct_volume"
        super(NiftymicReconstruction, self).__init__(**inputs)

        self._cmd = (
            f"{self.inputs.pre_command} "
            f"{self.inputs.niftymic_image} "
            "niftymic_reconstruct_volume"
            # "niftymic_run_reconstruction_pipeline"
        )

    # Customize how arguments are formatted
    def _format_arg(self, name, trait_spec, value):
        if name == "pre_command":
            return ""  # if the argument is 'pre_command', ignore it
        elif name == "niftymic_image":
            return ""  # if the argument is 'pre_command', ignore it
        return super()._format_arg(name, trait_spec, value)

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
        from nipype.utils.filemanip import split_filename as split_f

        if name == "recon_file":
            recon_file = self.inputs.recon_file
            if not isdefined(recon_file):
                assert 1 <= len(self.inputs.input_stacks), \
                    "Error input stacks should have at least one element"
                path, fname, ext = split_f(self.inputs.input_stacks[0])

                recon_file = os.path.abspath(fname + "_recon" + ext)
            return recon_file

        if name == "recon_mask_file":
            recon_mask_file = self.inputs.recon_mask_file
            if not isdefined(recon_mask_file):
                assert 1 <= len(self.inputs.input_stacks), \
                    "Error input stacks should have at least one element"
                path, fname, ext = split_f(self.inputs.input_stacks[0])

                recon_mask_file = os.path.abspath(fname + "_recon_mask" + ext)
            return recon_mask_file

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
        if isdefined(self.inputs.recon_file):
            outputs["recon_file"] = self.inputs.recon_file
        else:
            outputs["recon_file"] = self._gen_filename("recon_file")

        if isdefined(self.inputs.recon_mask_file):
            outputs["recon_mask_file"] = self.inputs.recon_mask_file
        else:
            outputs["recon_mask_file"] = self._gen_filename("recon_mask_file")

        return outputs


class NiftymicReconstructionPipelineInputSpec(CommandLineInputSpec):
    """
    NiftymicReconstructionInputSpec is a class for the input specification for
    the Niftymic nipype interface.
    It inherits from CommandLineInputSpec.

    Attributes
    ----------
    input_stacks:traits.List(File)
        Preprocessed T2 file names
    input_masks:traits.List(File)
        Brain masks for each T2 low-resolution stack given in stacks.
    dir_output:traits.Directory
        The path where the output reconstruction is saved.
    pre_command:
        Command to run niftymic_image (e.g. docker run or singularity run)
    niftymic_image:
        niftymic_image name (e.g. renbem/niftymic:latest)

    TODO:

    """

    input_stacks = traits.List(File(exists=True),
        desc="List of input stacks to be processed",
        argstr="--filenames %s",
        mandatory=True,
    )

    input_masks = traits.List(File(exists=True),
        desc="List of input masks corresponding to the stacks to be processed",
        argstr="--filenames-masks %s",
        mandatory=True,
    )

    dir_output = traits.Directory(
        desc="Path to save output reconstruction files",
        argstr="--dir-output %s",
        genfile=True,
        hash_files=False,
        mandatory=False,
    )
    # pre command and niftymic image
    # these two commands are not used in the command line
    pre_command = traits.Str(
        desc="Pre-command to be run",
        mandatory=True,
    )

    niftymic_image = traits.Str(
        desc="Singularity Niftymic command",
        mandatory=True,
    )


class NiftymicReconstructionPipelineOutputSpec(TraitedSpec):
    """
    NesvorReconstructionOutputSpec is a class for the output specification for
    the NeSVoRRec nipype interface.
    It inherits from TraitedSpec.

    Attributes
    ----------
    dir_output : traits.Directory
        The reconstructed image.
    """
    dir_output = traits.Directory(
        desc="Path to save output reconstruction files",
        mandatory=True,
    )


class NiftymicReconstructionPipeline(CommandLine):
    """
    NiftymicReconstruction is a class for the Niftymic nipype interface.
    It inherits from CommandLine.

    This class calls the singularity container for NeSVoRRec. There is no need
    to implement _run_interface,
    as it is inherited from CommandLine and we just need to change the
    _cmd attribute.

    Attributes
    ----------
    _cmd : str
        The command to be run by the singularity container.
    input_spec : NiftymicReconstructionInputSpec
        The input specifications for the NeSVoRRec interface.
    output_spec : NiftymicReconstructionOutputSpec
        The output specifications for the NeSVoRRec interface.
    """

    input_spec = NiftymicReconstructionPipelineInputSpec
    output_spec = NiftymicReconstructionPipelineOutputSpec

    def __init__(self, **inputs):
        self._cmd = "niftymic_run_reconstruction_pipeline"
        super(NiftymicReconstruction, self).__init__(**inputs)

        self._cmd = (
            f"{self.inputs.pre_command} "
            f"{self.inputs.niftymic_image} "
            "niftymic_run_reconstruction_pipeline" # "niftymic_run_reconstruction_pipeline"
        )
        # bias field correction was already performed
        self._cmd += " --bias-field-correction 1"
        self._cmd += " --isotropic-resolution 0.5"
        # outliers rejection parameters
        self._cmd += " --run-bias-field-correction 1"
        self._cmd += " --run-diagnostics 0"


    # def _run_interface(self, runtime, correct_return_codes=(0,)):
    #     if "docker" in self.cmdline:
    #         stacks_dir = os.path.commonpath(self.inputs.input_stacks)
    #         stack_masks = os.path.commonpath(self.inputs.stack_masks)
    #         out_dir = os.path.dirname(self._list_outputs()["output_volume"])
    #         new_cmd = self.inputs.pre_command + (
    #             f"-v {stacks_dir}:{stacks_dir} "
    #             f"-v {stack_masks}:{stack_masks} "
    #             f"-v {out_dir}:{out_dir} "
    #             f"{self.inputs.niftymic_image} "
    #             "nesvor reconstruct"
    #         )
    #         self._cmd = new_cmd
    #     super()._run_interface(runtime, correct_return_codes)

    # Customize how arguments are formatted
    def _format_arg(self, name, trait_spec, value):
        if name == "pre_command":
            return ""  # if the argument is 'pre_command', ignore it
        elif name == "niftymic_image":
            return ""  # if the argument is 'pre_command', ignore it
        return super()._format_arg(name, trait_spec, value)

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
        if name == "dir_output":
            dir_output = self.inputs.dir_output
            if not isdefined(dir_output):
                dir_output = os.path.abspath(os.path.join("srr_reconstruction"))
                # cwd = os.environ["PWD"]
                #
                # # add the name of the folder
                # output = os.path.join(cwd, "recon")
                #
                # # create the folder if it does not exist
                os.makedirs(dir_output, exist_ok=True)
                #
                # # add the name of the file
                # dir_outputoutput = os.path.join(output, "recon.nii.gz")

            return dir_output

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
        if isdefined(self.inputs.dir_output):
            outputs["dir_output"] = self.inputs.dir_output
        else:
            outputs["dir_output"] = self._gen_filename("dir_output")
        return outputs


class NiftymicBrainExtractionInputSpec(CommandLineInputSpec):
    """
    Class for the input for the NeSVoRSeg nipype interface.
    Inherits from CommandLineInputSpec.

    Attributes
    ----------
    """
    input_stacks = traits.List(File(exists=True),
        desc="List of input stacks to be processed",
        argstr="--filenames %s",
        mandatory=True,
    )
    input_bmasks = traits.List(File(exists=True),
        desc="List of input masks corresponding to the stacks to be processed",
        argstr="--filenames-masks %s",
        genfile=True,
        mandatory=False,
    )
    # pre command and niftymic image
    # these two commands are not used in the command line
    pre_command = traits.Str(
        desc="Pre-command to be run",
        mandatory=True,
    )

    niftymic_image = traits.Str(
        desc="Singularity Niftymic command",
        mandatory=True,
    )

class NiftymicBrainExtractionOutputSpec(TraitedSpec):
    """
    Class for the output specification for the NeSVoRSeg nipype interface.
    Inherits from TraitedSpec.

    Attributes
    ----------
    """
    output_bmasks = traits.List(File(exists=True),
        desc="List of output brain masks",
        mandatory=True,
    )


class NiftymicBrainExtraction(CommandLine):
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
    input_spec = NiftymicBrainExtractionInputSpec
    output_spec = NiftymicBrainExtractionOutputSpec

    def __init__(self, **inputs):
        self._cmd = "niftymic_segment_fetal_brains"
        super(NiftymicBrainExtraction, self).__init__(**inputs)

        self._cmd = (
            f"{self.inputs.pre_command} "
            f"{self.inputs.niftymic_image} "
            "niftymic_segment_fetal_brains"
        )


    # Customize how arguments are formatted
    def _format_arg(self, name, trait_spec, value):
        if name == "pre_command":
            return ""  # if the argument is 'pre_command', ignore it
        elif name == "niftymic_image":
            return ""  # if the argument is 'pre_command', ignore it
        return super()._format_arg(name, trait_spec, value)

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
        if name == "input_bmasks":
            input_bmasks = self.inputs.input_bmasks
            if not isdefined(input_bmasks):
                # Why do we do [:-7] + .nii.gz?
                input_bmasks = [
                    os.path.abspath(
                        os.path.basename(s)[:-7].replace("_T2w", "_mask") + ".nii.gz",
                    )
                    for s in self.inputs.input_stacks
                ]

            return input_bmasks

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
        if isdefined(self.inputs.input_bmasks):
            outputs["output_bmasks"] = self.inputs.input_bmasks
        else:
            outputs["output_bmasks"] = self._gen_filename("input_bmasks")
        return outputs


def niftymic_recon(stacks, masks, pre_command="", niftymic_image=""):
    """
    Function wrapping niftymic_run_reconstruction_pipeline for use with nipype
    This is a quick and dirty implementation, to be replaced by a proper nipype
    interface in the future.

    Inputs:
        stacks:
            Preprocessed T2 file names
        masks:
            Brain masks for each T2 low-resolution stack given in stacks.
        pre_command:
            Command to run niftymic_image (e.g. docker run or singularity run)
        niftymic_image:
            niftymic_image name (e.g. renbem/niftymic:latest)

    Outputs:
        reconst_dir:
            Directory containing the reconstructed files
    """
    import os

    reconst_dir = os.path.abspath("srr_reconstruction")

    if "docker" in pre_command:
        stacks_dir = os.path.commonpath(stacks)
        masks_dir = os.path.commonpath(masks)
        stacks_docker = " ".join(
            [s.replace(stacks_dir, "/data") for s in stacks]
        )
        bmasks_docker = " ".join(
            [m.replace(masks_dir, "/masks") for m in masks]
        )
        cmd = pre_command
        cmd += (
            f"-v {stacks_dir}:/data "
            f"-v {masks_dir}:/masks "
            f"-v {reconst_dir}:/rec "
            f"{niftymic_image} niftymic_run_reconstruction_pipeline "
            f"--filenames {stacks_docker} "
            f"--filenames-masks {bmasks_docker} "
            "--dir-output /rec "
        )
    elif "singularity" in pre_command:
        stacks = " ".join(stacks)
        masks = " ".join(masks)

        cmd = pre_command + niftymic_image
        cmd += (
            "niftymic_run_reconstruction_pipeline"
            # input stacks
            f" --filenames {stacks}"
            # corresponding masks (previously obtained)
            f" --filenames-masks {masks}"
            # output directory
            f" --dir-output {reconst_dir} "
        )

    else:
        raise ValueError(
            "pre_command must either contain docker or singularity."
        )

    # bias field correction was already performed
    cmd += " --bias-field-correction 1"
    cmd += " --isotropic-resolution 0.5"
    # outliers rejection parameters
    cmd += " --run-bias-field-correction 1"
    cmd += " --run-diagnostics 0"

    print(cmd)

    os.system(cmd)
    return reconst_dir

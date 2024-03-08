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
from .container import ContainerCommandLine

class NiftymicReconstructionInputSpec(CommandLineInputSpec):
    """
    NiftymicReconstructionInputSpec is a class for the input specification for
    the Niftymic nipype interface.
    It inherits from CommandLineInputSpec.

    Attributes
    ----------
    input_stacks: traits.List(File)
        Preprocessed T2 file names
    input_masks: traits.List(File)
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
        0.8,
        usedefault=True,
        argstr="--isotropic-resolution %f",
        desc="isotropic resolution",
        mandatory=True,
    )

    # output (should not be here, right?)
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


class NiftymicReconstruction(ContainerCommandLine):
    """
    NiftymicReconstruction is a class for the Niftymic nipype interface.
    It inherits from ContainerCommandLine.

    This class calls the docker or the singularity container. There is no need
    to implement _run_interface, as it is inherited from ContainerCommandLine and we just need to change the _cmd attribute. Docker mounts are also managed by ContainerCommandLine

    Attributes
    ----------
    _cmd : str
        The command to be run by the  container.
    _mount_keys : list
        List of keys to be mounted on the docker image.
    input_spec : NiftymicReconstructionInputSpec
        The input specifications for the NeSVoRRec interface.
    output_spec : NiftymicReconstructionOutputSpec
        The output specifications for the NeSVoRRec interface.
    Methods
    -------
    _gen_filename(self, name: str) -> str:
        Generates an output filename if not defined.
    _list_outputs(self) -> dict:
        Lists the outputs of the class if not defined.
    """

    input_spec = NiftymicReconstructionInputSpec
    output_spec = NiftymicReconstructionOutputSpec

    _cmd = "niftymic_reconstruct_volume"
    _mount_keys = ["input_stacks", "input_masks"] # folders to be mounted on the container if using docker


    def __init__(self, pre_command, container_image, **inputs):
        super(NiftymicReconstruction, self).__init__(
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
    """

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

    dir_output = traits.Directory(
        desc="Path to save output reconstruction files",
        argstr="--dir-output %s",
        genfile=True,
        hash_files=False,
        mandatory=False,
    )
    # pre command and niftymic image
    # these two commands are not used in the command line
    # pre_command = traits.Str(
    #     desc="Pre-command to be run",
    #     mandatory=True,
    # )

    # niftymic_image = traits.Str(
    #     desc="Singularity Niftymic command",
    #     mandatory=True,
    # )


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


class NiftymicReconstructionPipeline(ContainerCommandLine):
    """
    NiftymicReconstructionPipeline is a class for the Niftymic nipype interface.
    It inherits from ContainerCommandLine.

    This class calls the container for Niftymic reconstruction pipeline. 
    There is no need to implement _run_interface, as it is inherited from ContainerCommandLine and we just need to change the _cmd attribute.

    Attributes
    ----------
    _cmd : str
        The command to be run by the container.
    _mount_keys : list
        List of keys to be mounted on the docker image.
    input_spec : NiftymicReconstructionPipelineInputSpec
        The input specifications for the Niftymic reconstruction pipeline interface.
    output_spec : NiftymicReconstructionPipelineOutputSpec
        The output specifications for the Niftymic reconstruction pipeline interface.

    Methods
    -------
    _gen_filename(self, name: str) -> str:
        Generates an output filename if not defined.
    _list_outputs(self) -> dict:
        Lists the outputs of the class if not defined.
    """

    input_spec = NiftymicReconstructionPipelineInputSpec
    output_spec = NiftymicReconstructionPipelineOutputSpec

    _cmd = "niftymic_run_reconstruction_pipeline"
    _mount_keys = ["input_stacks", "input_masks", "dir_output"]

    def __init__(self, pre_command, container_image, **inputs):
        super(NiftymicReconstructionPipeline, self).__init__(pre_command=pre_command, container_image=container_image, **inputs)

        # TODO: add those parameters as inputs?
        # bias field correction was already performed
        self._cmd += " --bias-field-correction 1"
        self._cmd += " --isotropic-resolution 0.5"
        # outliers rejection parameters
        self._cmd += " --run-bias-field-correction 1"
        self._cmd += " --run-diagnostics 0"


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
                dir_output = os.path.abspath(
                    os.path.join("srr_reconstruction"))
                os.makedirs(dir_output, exist_ok=True)
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
    input_stacks = traits.List(
        File(exists=True),
        desc="List of input stacks to be processed",
        argstr="--filenames %s",
        mandatory=True,
    )

    input_bmasks = traits.List(
        File(exists=True),
        desc="List of input masks corresponding to the stacks to be processed",
        argstr="--filenames-masks %s",
        genfile=True,
        mandatory=False
    )


class NiftymicBrainExtractionOutputSpec(TraitedSpec):
    """
    Class for the output specification for the NeSVoRSeg nipype interface.
    Inherits from TraitedSpec.

    Attributes
    ----------
    output_bmasks : traits.List(File)
        Brain masks for each T2 low-resolution stack given in `input_stacks`.
    """
    output_bmasks = traits.List(
        File(exists=True),
        desc="List of output brain masks",
        mandatory=True
    )


class NiftymicBrainExtraction(ContainerCommandLine):
    """
    Class wrapping `niftymic_segment_fetal_brains` for use with nipype.
    Inherits from `ContainerCommandLine`.

    Attributes
    ----------
    input_spec : NiftymicBrainExtractionInputSpec
        Specification of the input parameters for the brain extraction process.
    output_spec : NiftymicBrainExtractionOutputSpec
        Specification of the output parameters for the brain extraction process.
    _cmd : str
        The command to be run by the container.
    _mount_keys : list
        List of keys to be mounted on the docker image.

    Methods
    -------
    __init__(self, **inputs):
        Initializes the brain extraction process with the given inputs.
    _gen_filename(self, name: str) -> str:
        Generates an output filename if not defined.
    _list_outputs(self) -> dict:
        Lists the outputs of the class.

    Inputs
    ------
    pre_command : str
        Command to run `niftymic_image` (e.g., `docker run` or `singularity run`).
    niftymic_image : str
        `niftymic_image` name (e.g., `renbem/niftymic:latest`).

    Outputs
    -------
    bmasks : List[File]
        Brain masks for each T2 low-resolution stack given in `raw_T2s`.
    """

    input_spec = NiftymicBrainExtractionInputSpec
    output_spec = NiftymicBrainExtractionOutputSpec

    _cmd = "niftymic_segment_fetal_brains"
    _mount_keys = ["input_stacks", "input_bmasks"] # folders to be mounted on the container if using docker

    def __init__(self, pre_command, container_image, **inputs):
        super(NiftymicBrainExtraction, self).__init__(
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
        if name == "input_bmasks":
            input_bmasks = self.inputs.input_bmasks
            if not isdefined(input_bmasks):
                input_bmasks = [
                    os.path.abspath(s.replace("_T2w.nii.gz", "_mask.nii.gz"))
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

    This is an OLD function. It should eventually be deprecated and removed.

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

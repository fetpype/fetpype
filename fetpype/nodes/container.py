import os
from nipype.interfaces.base import (
    CommandLine,
    isdefined,
)


def add_final_space(string):
    """
    Check that there is a space at the end of the string.
    """
    if string.endswith(" "):
        return string
    else:
        return string + " "


class ContainerCommandLine(CommandLine):
    """
    Generic class for calling docker and singularity nodes
    from a unified class. In addition to CommandLine, it
    mounts the input folders on the docker container.
    Inherits from CommandLine.

    Attributes
    ----------
    container_image : str
        Path to the container image.
    _mount_keys : list
        List of keys to be mounted on the container
        (currently, only for docker using -v)
    _mounted : bool
        True if the folders have been mounted on the container.
        (checks if _cmd_prefix has been updated in _pre_run_hook)

    Parameters
    ----------
    pre_command : str
        Command to be executed before the container command.
        (e.g. docker run)
    container_image : str
        Path to the container image.
    **inputs : dict
        Dictionary of inputs to be passed to the nipype interface.)
    """

    _container_image = None
    _mount_keys = []
    _mounted = False

    def __init__(
        self,
        command=None,
        mount_keys=None,
        pre_command=None,
        container_image=None,
        **inputs,
    ):
        super(ContainerCommandLine, self).__init__(command, **inputs)
        self._cmd_prefix = add_final_space(pre_command)
        self._container_image = container_image
        self._mount_keys = mount_keys or getattr(self, "_mount_keys", None)
        self._cmd = f"{self._container_image} " + self._cmd

    def _get_directory(self, entry):
        """
        Get the directory of an entry, to be mounted on docker
        If entry is a list, it returns the common path.
        If entry is a string, it returns the dirname.
        """
        if isinstance(entry, list):
            return os.path.commonpath(entry)
        elif isinstance(entry, str):
            return os.path.dirname(entry)
        else:
            raise TypeError(f"Type {type(entry)} not supported")

    def _get_mount_str(self):
        """
        Build the string for the folders to be mounted on the
        docker image. The folders to be mounted are defined
        in _mount_keys.
        """
        mount_dict = {}

        # Construct the mount dictionary
        for k in self._mount_keys:
            # Get it only if it is in self.inputs
            mount_dict[k] = getattr(self.inputs, k, None)
            if mount_dict[k] is None or not isdefined(mount_dict[k]):
                mount_dict[k] = self._gen_filename(k)
            assert isdefined(mount_dict[k]), f"The variable {k} is not defined"

        # Get the common path for each mount
        print(mount_dict)
        mount_dir_dict = {
            k: self._get_directory(v) for k, v in mount_dict.items()
        }

        # Build a single string to be mounted on docker
        mount_str = " ".join([f"-v {v}:{v}" for v in mount_dir_dict.values()])
        return mount_str

    def _pre_run_hook(self, runtime):
        """
        Executed before _run_interface: if the container
        is a docker image, it mounts the folders on the
        container.
        """
        if "docker" in self.cmdline and not self._mounted:
            self._cmd_prefix += add_final_space(self._get_mount_str())
        print(self.cmdline)
        raise NotImplementedError
        return runtime

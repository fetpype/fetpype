import os
import re


def is_docker(pre_command):
    return "docker" in pre_command


def get_directory(entry):
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


def get_mount_docker(*args):
    """
    Build the string for the folders to be mounted on the
    docker image. The folders to be mounted are defined
    in _mount_keys.
    """
    for arg in args:
        os.makedirs(arg, exist_ok=True)
    return " ".join([f"-v {arg}:{arg}" for arg in args])


def is_valid_cmd(cmd, valid_tags):
    for tag in re.findall(r"\<(.*?)\>", cmd):
        if tag not in valid_tags:
            raise ValueError(f"Invalid tag {tag} in command {cmd}")

    if "docker" in cmd and "<mount>" not in cmd:
        raise ValueError("Docker command must have a <mount> tag")

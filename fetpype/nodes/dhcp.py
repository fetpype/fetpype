"""
Nodes that implement the dHCP pipeline for fetal data.

Version from https://github.com/GerardMJuan/dhcp-structural-pipeline
, which is a fork of the original dataset 
https://github.com/BioMedIA/dhcp-structural-pipeline
with several fixes and changes

The docker image, where everything works "well", is:
https://hub.docker.com/r/gerardmartijuan/dhcp-pipeline-multifact

TODO: specify the changes from one version to another.

"""

def dhcp_segment(T2, mask, gestational_age, pre_command="", dhcp_image=""):
    """ Run the dhcp segmentation pipeline on a single subject.
    The script needs to create the output folders and put the mask there so that the docker image can find it and doesn't run bet. TODO: don't do it that convoluted.
    TODO: Be able to input the number of threads
    """
    import os
    import shutil

    output_dir = os.path.abspath("dhcp_output")
    os.makedirs(output_dir, exist_ok=True)

    # Basename of the T2 file
    recon_file_name = os.path.basename(T2)

    # Copy T2 to output dir    
    shutil.copyfile(
        T2, os.path.join(output_dir, recon_file_name)
    )

    # Copy mask to output dir with the correct name
    os.makedirs(os.path.join(output_dir, "segmentations"), exist_ok=True)

    shutil.copyfile(
        mask,
        os.path.join(
            output_dir,
            "segmentations",
            f"{recon_file_name.replace('.nii.gz', '')}_brain_mask.nii.gz",
        ),
    )
    if "docker" in pre_command:
        cmd = pre_command
        cmd += (
            f"-v {output_dir}:/data "
            f"{dhcp_image} "
            f"/data/{recon_file_name} "
            f"{gestational_age} "
            "-data-dir /data "
            "-t 4 "
            "-c 0 "
            "-seg "
        )

    elif "singularity" in pre_command:
            # Do we need FSL for this pipeline? add in the precommand
        cmd = pre_command + dhcp_image
        cmd += (
            f"/usr/local/src/structural-pipeline/fetal-pipeline.sh " 
            f"{T2} "
            f"{gestational_age} "
            f"-data-dir "
            f"{output_dir} "
            "-t 4 "
            "-c 0 "
            "-seg "
        )

    else:
        raise ValueError(
            "pre_command must either contain docker or singularity."
        )

    print(cmd)

    os.system(cmd)
    return output_dir


def dhcp_surface():
    """
    It calls the same script as dhcp_segment, but with different parameters
    and different input. The input should be the whole folder of the dhcp_seg function.
    """
    print('Not yet implemented!')

    # We assume that the input is the output of dhcp_segment
    # IF not, it will fail. But TODO: warn the user before failing 
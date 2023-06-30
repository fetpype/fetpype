
def niftimic_segment(raw_T2s, pre_command="", niftimic_image=""):

    """ Description: wraps niftimic_segment dirty
    Inputs:

        inputnode:

            raw_T2s:
                T2 raw file names

    Outputs:

            bmasks:
                bmasks
    """

    # TODO
    import os

    output_dir = os.path.abspath("")

    print(output_dir)

    print(pre_command + niftimic_image)

    bmasks = [
        os.path.abspath(os.path.basename(s)[:-7] + ".nii.gz",)
        for s in raw_T2s
    ]
    cmd = pre_command + niftimic_image
    cmd += "niftymic_segment_fetal_brains "
    cmd += "--filenames "
    for s in raw_T2s:
        cmd += s + " "
    cmd += "--filenames-masks "
    for b in bmasks:
        cmd += b + " "
    cmd += "--dir-output "
    cmd += output_dir + " "
    cmd += "--neuroimage-legacy-seg 0 "
    cmd += "--log-config 1"

    print(cmd)
    os.system(cmd)

    print(bmasks)

    for bmask in bmasks:
        print(bmask)
        assert os.path.exists(bmask), "Error, {} does not exists".format(bmask)

    return bmasks


def niftimic_recon(stacks, masks,  pre_command="", niftimic_image=""):

    import os

    reconst_dir = os.path.abspath("srr_reconstruction")

    cmd_os = pre_command + " " + niftimic_image + " "
    cmd_os += "niftymic_run_reconstruction_pipeline"
    # input stacks
    cmd_os += " --filenames "
    for v in stacks:
        cmd_os += v + " "
    # corresponding masks (previously obtained)
    cmd_os += " --filenames-masks "
    for u in masks:
        cmd_os += u + " "
    # output directory
    cmd_os += " --dir-output " + reconst_dir
    # bias field correction was already performed
    cmd_os += " --bias-field-correction 1"
    cmd_os += " --isotropic-resolution 0.5"
    # outliers rejection parameters
    cmd_os += " --run-bias-field-correction 1"
    cmd_os += " --run-diagnostics 0"

    print(cmd_os)

    os.system(cmd_os)
    return reconst_dir

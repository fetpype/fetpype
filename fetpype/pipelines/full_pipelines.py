
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

from fetpype.nodes.niftimic import niftimic_segment


def create_fet_subpipes(name = "full_fet_pipe"):


    """ Description: SPM based segmentation pipeline from T1w and T2w images
    in template space

    Processing steps:

    - wraps niftimic dirty

    Params:

    -

    Inputs:

        inputnode:

            list_T2:
                T2 file names

        arguments:
            name:
                pipeline name (default = "full_spm_subpipes")

    Outputs:

            TODO
    """

    print("Full pipeline name: ", name)

    # Creating pipeline
    full_fet_pipe = pe.Workflow(name=name)

    # Creating input node
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['list_T2']),
        name='inputnode'
    )

    # output node
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['out_outpuf_file']),
        name='outputnode')

    # preprocessing

    #TODO
    niftymic_segment = pe.Node(interface = niu.Function(in_files = ["raw_T2s"], out_files = ["seg_T2s"], function = niftimic_segment), name = "niftymic_segment")

    full_fet_pipe.connect(inputnode, 'list_T2', niftymic_segment, "raw_T2s")

    full_fet_pipe.connect(niftymic_segment, "seg_T2s", outputnode, "out_outpuf_file")
    # connecting


    return full_fet_pipe

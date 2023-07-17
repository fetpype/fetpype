import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe
    from fetpype.nodes.nesvor import (
    NesvorSegmentation,
    NesvorRegistration,
    NesvorReconstruction,
)

nesvor_pype = pe.Workflow(name="test")

mask = pe.Node(NesvorSegmentation(no_augmentation_seg=True), name="mask")

mask.inputs.input_stacks = ['/homedtic/gmarti/DATA/fabian/sub-simu009/ses-01/anat/sub-simu009_ses-01_run-1_T2w.nii.gz', '/homedtic/gmarti/DATA/fabian/sub-simu009/ses-01/anat/sub-simu009_ses-01_run-2_T2w.nii.gz', '/homedtic/gmarti/DATA/fabian/sub-simu009/ses-01/anat/sub-simu009_ses-01_run-3_T2w.nii.gz', '/homedtic/gmarti/DATA/fabian/sub-simu009/ses-01/anat/sub-simu009_ses-01_run-4_T2w.nii.gz', '/homedtic/gmarti/DATA/fabian/sub-simu009/ses-01/anat/sub-simu009_ses-01_run-5_T2w.nii.gz', '/homedtic/gmarti/DATA/fabian/sub-simu009/ses-01/anat/sub-simu009_ses-01_run-6_T2w.nii.gz', '/homedtic/gmarti/DATA/fabian/sub-simu009/ses-01/anat/sub-simu009_ses-01_run-7_T2w.nii.gz']

mask.run()
print(mask.cmdline)
print(mask.outputs)

"""
# registration Node
registration = pe.Node(NesvorRegistration(), name="registration")

nesvor_pype.connect(
    [
        (inputnode, mask, [("stacks", "input_stacks")]),
        (inputnode, registration, [("stacks", "input_stacks")]),
        (mask, registration, [("output_stack_masks", "stack_masks")]),
    ]
)
"""
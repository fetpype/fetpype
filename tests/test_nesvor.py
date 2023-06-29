"""Test nipype nesvor functionality.

TODO: CHange to unit testing
"""

import os
import glob
from nesvor import NesvorSegmentation, NesvorRegistration
from nipype.interfaces.io import BIDSDataGrabber, DataSink
from nipype import Workflow, Node

from nipype import config
config.enable_debug_mode()
  
input_path_BIDS = "/homedtic/gmarti/DATA/ERANEU_BIDS_small/"

# Create a nipype workflow
workflow = Workflow(name="nesvor_workflow", base_dir="/homedtic/gmarti/DATA/nesvor/")

# create an infosource to iterate over the subjects

# BIDS datagrabber
bids_node = Node(BIDSDataGrabber(), name='bids-grabber')
bids_node.inputs.base_dir = input_path_BIDS
bids_node.inputs.subject = '003'

# Define the output as a list of scans with the suffix _T2w.nii.gz
bids_node.inputs.output_query = {'T2w': dict(suffix='T2w', extension='nii.gz')}

# mask Node
mask = Node(NesvorSegmentation(
            no_augmentation_seg=True),
            name="Mask"
            )

# registration Node
registration = Node(NesvorRegistration(), name="Registration")
print(registration.help())
## TODO. Save the output in the output derivative
output_folder = 'derivatives'
datasink = Node(DataSink(base_directory=os.path.join(input_path_BIDS, output_folder),
                         container='nesvor'),  # the name of the sub-folder of base directory
               name='datasink')

# Connect the nodes
# TODO: datasink is not working
workflow.connect([(bids_node, mask, [("T2w", "input_stacks")]),
                  (bids_node, registration, [("T2w", "input_stacks")]),
                  (mask, registration, [("output_stack_masks", "stack_masks")]),
                  (registration, datasink, [("output_slices", "output_slices")]),
                ])

print(workflow.list_node_names())

# Run the nipype interface
workflow.run()


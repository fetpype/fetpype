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
from nipype.interfaces import utility as niu
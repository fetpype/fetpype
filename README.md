#Fetpype

[Documentation](https://fetpype.github.io/fetpype/)

Pipeline for processing MRI acquired in vivo in human fetuses. 

Collaborative effort shared across teams involved in the ERANET project MultiFact.

# Basic principles
- Principal constraint is on the reusability of the pipeline by other teams.
- Efforts shared to develop the skeleton of the pipeline.
- Each team works independently on their new processing tools and when ready for integration in the common pipeline, they provide the wraper corresponding to their new tool in addition to the tool itself as a singularity image.
- Each module ideally would be either a docker/singularity image for easier reproducibility and for running it in a HPC. 
Fetpype is a wrapper calling to docker images (don’t intricate the different code bases)
- use BIDS format for easier input/output across datasets.
Strict and consistent data formatting so that we can easily swap in and out different parts of the pipelines
- Construct intermediary BIDS-datasets after each step + logging
- Fail fast if there is an issue (don’t fail silently)
- Default path + use of configuration files to define different paths (typically a yaml config file could be great).

# List of Nodes available at the present state
- simple data graber (not BIDS)
- denoising with ANTS https://stnava.github.io/ANTs/
- brain extraction and HR volume reconstruction using niftiMIC https://github.com/gift-surg/NiftyMIC
  
# Code maintenance, documentation and improvements
- unitest
  
Test for the formatting of command lines from each node is correct

check that the consequence of a given node on the data written on the disk are appropriate (e.g. LR-QC is expected to exclude some stacks and this exclusion is supposed to be taken into account in the downstream nodes)

check for the proper installation of dependencies

- Documentation
  
Start b extending the present README file and then investigate better options

- Reproducibility tests

Use the simulated data

Run the full pipeline on this dataset across all institutions in order to ensure that we have the exact same results. This might be important for instance to ensure that different versions of docker/singularity images do not influence the results.

Need to implement small quantitative measures to compare across institutions, would be direct one we have implemented the feature extraction nodes.


# Below is our current view of the pipeline we would like to implement in Fetpype
- Data grabber, one for each site/dataset
assume data are organized following BIDS

- Preprocessing I input=set of stacks 
Mask extraction

- Low resolution automated Quality Assessment

slice-wise quality assessment (QA)

Stack-wise QA

- Preprocessing II
  
Denoising

Bias field correction

- 3D High Resolution volume Reconstruction
  
NiftyMIC: docker image currenty working: https://hub.docker.com/repository/docker/gerardmartijuan/niftymic.multifact/general

NeSVoR https://github.com/GerardMJuan/fetpype

SVRTK https://hub.docker.com/r/fetalsvrtk/svrtk new docker from BOUNTI paper, maybe includes reorientation. 

- 3DHR volume QA

- Segmentation
  
NNunet trained on FETA

BOUNTI

other options will be considered

- Segmentation QA

- White and pial Surface extraction
  
adaptation of dHCP pipeline (based on MIRTK recon-neonatal-cortex (https://mirtk.github.io/commands/recon-neonatal-cortex.html))

- Mesh QA

- Surface mapping onto spherical domain
  
tools from MIRTK / dHCP pipeline: https://github.com/amakropoulos/SphericalMesh 

- Inter-individual spherical registration
  
E.Robinson’s MSM as in dHCP / HCP pipelines, i.e. FSL

T.Yeo’s Spherical deamons (matlab, bouuuuu)

H.Lombeart’s Spectral matching (matlab, bouuuuuu)

- Features extraction


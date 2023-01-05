# fetpype
Pipeline for processing MRI acquired in vivo in Human fetus
collaborative effort shared across teams involved in the ERANET project MultiFact.

# Basic principles
- Principal constraint is on the reusability of the pipeline by other teams.
- Efforts shared to develop the skeleton of the pipeline.
- Each team works independently on their new processing tools and when ready for integration in the common pipeline, they provide the wraper corresponding to their new tool in addition to the tool itself as a singularity image. 

# Technical notes
- We base this pipeline on nipype (https://nipy.org/packages/nipype/index.html) because...
- We initiate the development with simple wraps of docker/singularity images, which is clearly not the optimal way of using nipype, but it allows for easier installation/use by other teams.
- We might change this aspect later on, dependening on the feedback of collaborators.

# List of Nodes available at the present state
- simple data graber (not BIDS)
- denoising with ANTS https://stnava.github.io/ANTs/
- brain extraction and HR volume reconstruction using niftiMIC https://github.com/gift-surg/NiftyMIC

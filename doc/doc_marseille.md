This is a documentation file specific to Marseille


# Install:

- generate singularity image from a docker image
singularity pull docker://nomdelimagedockerarecuperer

- for niftymic:
singularity pull docker://gerardmartijuan/niftymic.multifact

- for nesvor
singularity pull docker://junshenxu/nesvor:latest

# special param to run singularity images on GPU
in the .json the –nv serves to use GPU
"pre_command": "singularity exec -B /scratch:/scratch –nv",


# Run pipeline_minimal
- on the simulated data from Lausanne (fabian)
python workflows/pipeline_fet.py -data /scratch/gauzias/data/datasets/fabian/fabian/fabian/ -out /scratch/gauzias/output_sandbox/ -params workflows/params_segment_fet_minimal.json -sub simu010 -ses 01

- on in house test subject
python workflows/pipeline_fet.py -data /scratch/gauzias/data/datasets/test_db/ -out /scratch/gauzias/output_sandbox/ -params workflows/params_segment_fet_minimal.json -sub 0036 -ses 0045
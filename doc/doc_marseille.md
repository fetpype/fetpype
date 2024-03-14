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

# server commands 
- connect to a cluster node with GPU
srun -p kepler -A b219 -t 4-2 --gres=gpu:1 --pty bash -i

- connect to a dev node which enables to git pull/push
srun -p dev -A b219 --pty bash -i

# Run pipeline_minimal
- on the simulated data from Lausanne (fabian)
python workflows/pipeline_fet.py -data /scratch/gauzias/data/datasets/fabian/fabian/fabian/ -out /scratch/gauzias/output_sandbox/ -params workflows/params_segment_fet_minimal.json -sub simu010 -ses 01

- on in house test subject
python workflows/pipeline_fet.py -data /scratch/gauzias/data/datasets/test_db/ -out /scratch/gauzias/output_sandbox/ -params workflows/params_segment_fet_minimal.json -sub 0036 -ses 0045

# test niftymic pipeline
python workflows/pipeline_fet.py -data /scratch/gauzias/data/datasets/test_db/ -out /scratch/gauzias/output_sandbox/ -params workflows/params_niftymic_recon.json -sub 0036 -ses 0045
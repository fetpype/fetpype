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
srun -p volta --gres=gpu:1 --mem=50G -t 2:00:00 -A b219 --pty bash -i


# load the modules
module load userspace/all; module load cuda/11.6; conda activate fetpype; cd /scratch/gauzias/code_gui/fetpype

# Run default pipeline
- on in house test subject
fetpype_run --data /scratch/gauzias/data/test_fetpype/test_db --out /scratch/gauzias/data/test_fetpype/test_db/derivatives/fetpype --config ./configs/sg_marseille.yaml
fetpype_run --data /scratch/gauzias/data/test_fetpype/test_fabian/fabian  --out /scratch/gauzias/data/test_fetpype/test_fabian --config ./configs/sg_marseille.yaml

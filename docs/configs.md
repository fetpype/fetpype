# Config files

Config files are the bread and butter of fetpype. They allow to define how the data should be processed within a container and what output should be returned. They also specify optional parameters that can be modified by the user, without touching at the code. They are based on the [Hydra](https://hydra.cc/docs/intro/) framework, that allows to flexibly parse a hierarchical structure of `.yaml` configs into a unified data structure. 

## The general structure
Fetpype acts as a wrapper around calls to various containers, and uses a limited set of tags in each dedicated node to construct the command that will be called. Config files define the commands that will be called by fetpype. Fetpype starts from a master config located at `configs/default_docker.yaml` (or `default_sg.yaml` for singularity), with the following structure
```yaml
defaults:
  - preprocessing/default # Default preprocessing
  - reconstruction/nesvor # NeSVoR reconstruction -- You can choose between svrtk, nifymic or nesvor
  - segmentation/bounti   # BOUNTI segmentation     
  - _self_
container: "docker"       # Running on docker (other option is singularity)
reconstruction:           # Generic reconstruction arguments
  output_resolution: 0.8  # Target resolution for reconstruction
save_graph: True
```
Each of the `defaults` entries call to other config files, located respectively at `configs/preprocessing/default.yaml`, `configs/reconstruction/nesvor.yaml`, etc.

## Example of a specific config
Let's look at an example of how a specific config is structured. If we open `configs/reconstruction/nesvor.yaml`, we see 

```yaml
pipeline: "nesvor"
docker: 
  cmd: "docker run --gpus '\"device=0\"' <mount> junshenxu/nesvor:v0.5.0 
    nesvor reconstruct 
    --input-stacks <input_stacks> 
    --stack-masks <input_masks> 
    --output-volume <output_volume> 
    --batch-size 4096 
    --n-levels-bias 1"
singularity:
  cmd: "singularity exec --bind <singularity_mount> --nv <singularity_path>/nesvor.sif 
    nesvor reconstruct 
    --input-stacks <input_stacks> 
    --stack-masks <input_masks> 
    --output-volume <output_volume> 
    --batch-size 4096 
    --n-levels-bias 1"
args:
    path_to_output: "nesvor.nii.gz"
```

In this config, we see a common structure that we will find in most of the configs. There is a `docker` and a `singularity` entry that define the command (`cmd`) that fetpype will run. The command has specific tags (marked as `<tag>`) that can be specified. The structure is globally similar for all configs, but specific information on how config files are structured is provided in the [pipelines page](pipelines.md).


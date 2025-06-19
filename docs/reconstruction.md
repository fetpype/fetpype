# Reconstruction

## Available tools
Several state-of-the-art super-resolution reconstruction algorithms have been wrapped and tested in fetpype.

| Algorithm                              | Repository                                               | Docker                                                                            |
| -------------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| NiftyMIC[@ebner_automated_2020]        | <https://github.com/gift-surg/NiftyMIC>  | <https://hub.docker.com/r/renbem/niftymic> |
| SVRTK[@kuklisova-murgasova_reconstruction_2012;@uus2022automated]  |<https://github.com/SVRTK/SVRTK> | <https://hub.docker.com/r/fetalsvrtk/svrtk> |
| NeSVoR[@xu2023nesvor]  | <https://github.com/daviddmc/NeSVoR> | <https://hub.docker.com/r/junshenxu/nesvor> |

## Config structure
Here's a typical structure found in the NeSVoR config. 
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

!!! Note
    All the container runs use the command above and are passed through the function [`run_recon_cmd`](api_nodes.md#fetpype.nodes.reconstruction.run_recon_cmd)

### Tags
There are a limited set of tags that can be used for reconstruction: 

| <div style="width:150px">Command</div> | Description                                               | Comments                                                                            |
| -------------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `<mount>`                              | Where the different folders will be mounted on Docker               | Docker only                                             |
| `<singularity_mount>`                              | Where the different folders will be mounted on Singularity               | Singularity only                                             |
| `<input_stacks>`                       | The list of inputs stacks will be given as arguments      | Mutually exclusive with `<input_dir>`                                               |
| `<input_dir>`                          | The folder that contains the input stacks                 | Mutually exclusive with `<input_stacks>`                                            |
| `<input_masks>`                        | The list of inputs masks will be given as arguments       | Mutually exclusive with `<input_masks_dir>`                                         |
| `<input_masks_dir>`                    | The folder that contains the input masks                  | Mutually exclusive with `<input_masks>`                                             |
| `<output_volume>`                      | The output volume                                         | Mutually exclusive with `<output_dir>`                                              |
| `<output_dir>`                         | The output directory                                      | Mutually exclusive with `<output_volume>`                                           |
| `<input_tp>`                           | The through-plane resolution of input stacks              | Needed for SVRTK - Automatically calculated                                         |
| `<output_res>`                         | The desired voxel resolution for the reconstructed volume | This tag be set in the config file in the field `reconstruction/output_resolution`. |

!!! Note 
    The configs contains an additional variable `path_to_output`. This is needed when only an `<output_dir>` is given to the method. This variable contains the path where the reconstructed volume will be located *relative* to `<output_dir>`.


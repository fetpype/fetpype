# Segmentation

## Available tools
Several state-of-the-art segmentation algorithms have been wrapped and tested in fetpype.

| Algorithm                              | Repository                                               | Docker                                                                            |
| -------------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| BOUNTI[@uus2023bounti]        | <https://github.com/gift-surg/NiftyMIC>  | <https://hub.docker.com/r/renbem/niftymic> |
| dHCP[@makropoulos2018developing]  |<https://github.com/SVRTK/SVRTK> | <https://hub.docker.com/r/fetalsvrtk/svrtk> |


## Config structure
Here's a typical structure found in the BOUNTI config. 
```yaml
pipeline: "bounti"
docker: 
  cmd: "docker run --rm <mount>
    fetalsvrtk/segmentation:general_auto_amd 
    bash /home/auto-proc-svrtk/scripts/auto-brain-bounti-segmentation-fetal.sh 
    <input_dir> <output_dir>"
singularity:
  cmd: "singularity exec -u --bind <singularity_mount> --bind /home/gmarti/tmp:/home/tmp_proc --nv
    <singularity_path>/bounti.sif
    bash /home/auto-proc-svrtk/auto-brain-bounti-segmentation-fetal.sh 
    <input_dir> <output_dir>"
path_to_output: "<basename>-mask-brain_bounti-19.nii.gz"
```

!!! Note
    All the container runs use the command above and are passed through the function [`run_seg_cmd`](api_nodes.md#fetpype.nodes.segmentation.run_seg_cmd)

### Tags
There are a limited set of tags that can be used for reconstruction: 

| <div style="width:150px">Command</div> | Description                                               | Comments                                                                            |
| -------------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `<mount>`                              | Where the different folders will be mounted on Docker               | Docker only                                             |
| `<singularity_mount>`                              | Where the different folders will be mounted on Singularity               | Singularity only                                             |
| `<singularity_path>`                   | The base path of the Singularity image               | Singularity only                                             |

| `<input_stacks>`                       | The list of inputs stacks will be given as arguments      | Mutually exclusive with `<input_dir>`                                               |
| `<input_dir>`                          | The folder that contains the input stacks                 | Mutually exclusive with `<output_dir>`                                              |
| `<output_dir>`                         | The output directory                                      | Mutually exclusive with 


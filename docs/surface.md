
# Surface Extraction
In the surface extraction step, a [segmented](segmentation.md) volume is processed to build a 3D surface of the white matter surface of the brain. This is the last step of fetpype.
# Segmentation

## Available tools
Several state-of-the-art segmentation algorithms have been wrapped and tested in `fetpype`.

| Algorithm                        | Repository                                            | Docker                                                             |
| -------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------ |
| Fetpype surface extraction (`surf_pype`)     | <https://github.com/fetpype/surface_processing>            |  <https://hub.docker.com/r/fetpype/surf_proc>              |
| dHCP[@makropoulos2018developing] | <https://github.com/fetpype/dhcp-structural-pipeline> | <https://hub.docker.com/r/gerardmartijuan/dhcp-pipeline-multifact> |

**⚠️ Disclaimer:** The dHCP pipeline is only available in the dev branch as of now. Surface extraction using the [dHCP structural pipeline](segmentation.md#dhcp-processing-pipeline)[@makropoulos2018developing] can be obtained with the flags `-surf` and `-all`.

## Config structure
Here's a typical structure found in the BOUNTI config. 
```yaml
pipeline: "surf_pype"
docker: 
  cmd: "docker run --rm <mount>
    fetpype/surf_proc:v0.0.2
    generate_mesh -l <labelling_scheme> 
    -s <input_seg> 
    -m <output_surf>"
singularity:
  cmd: "singularity exec --bind <singularity_mount> --home <singularity_home> --nv
    <singularity_path>/macatools/surf_proc.sif
    fetpype/surf_proc:v0.0.2
    generate_mesh -l <labelling_scheme> 
    -s <input_seg> 
    -m <output_surf>"

surface_lh:
    use_scheme: "bounti"
    out_file: "hemi-L_white.surf.gii"
    labelling_scheme:
        bounti: [5, 7, 14, 16]

surface_rh:
    use_scheme: "bounti"
    out_file: "hemi-R_white.surf.gii"
    labelling_scheme:
        bounti: [6, 8, 15, 17]
```


!!! Note
    The surface is computed on each hemisphere separately (`surface_lh` and `surface_rh`). The surface extraction groups together labels in the white matter. For the left hemisphere and BOUNTI labels, it groups the left white matter (5), the left lateral ventricle (7), the left basal ganglia (14) as well as the left thalamus (16). Information on the BOUNTI labelling scheme are available [here](https://gin.g-node.org/kcl_cdb/fetal_brain_mri_atlas).

!!! Note
    All the container runs use the command above and are passed through the function [`run_surf_cmd`](api_nodes.md#fetpype.nodes.surface_extraction.run_surf_cmd)

### Tags
There are a limited set of tags that can be used for reconstruction: 

| <div style="width:150px">Command</div> | Description                                                | Comments                               |
| -------------------------------------- | ---------------------------------------------------------- | -------------------------------------- |
| `<mount>`                              | Where the different folders will be mounted on Docker      | Docker only                            |
| `<singularity_mount>`                  | Where the different folders will be mounted on Singularity | Singularity only                       |
| `<singularity_path>`                   | The base path of the Singularity image                     | Singularity only                       |
| `<singularity_home>`                   | A directory used for temporary files                       | Singularity only                       |
| `<input_seg>`                          | The input segmentation to be used for surface extraction   |   |
| `<labelling_scheme>`                   | List of labels in the <input_seg> to concatenate in order to get the white matter mask of the given hemisphere | |
| `<output_surf>`                        | The output extracted surface                              |  |


--- 



## Available tools

Surface extraction in Fetpype is currenly available using the [dHCP structural pipeline](segmentation.md#dhcp-processing-pipeline)[@makropoulos2018developing], with the flags `-surf` and `-all`.


**Note:** Surface extraction requires prior [reconstruction](reconstruction.md) and gestational age information. Refer to the [dHCP configuration and requirements](segmentation.md#dhcp-processing-pipeline) for more details.

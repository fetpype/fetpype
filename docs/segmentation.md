# Segmentation

## Available tools
Several state-of-the-art segmentation algorithms have been wrapped and tested in fetpype.

| Algorithm                              | Repository                                               | Docker                                                                            |
| -------------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| BOUNTI[@uus2023bounti]        | <https://github.com/gift-surg/NiftyMIC>  | <https://hub.docker.com/r/renbem/niftymic> |
| dHCP[@makropoulos2018developing]  |<https://github.com/SVRTK/SVRTK> | <https://hub.docker.com/r/fetalsvrtk/svrtk> |

**⚠️ Disclaimer:** The dHCP pipeline is only available in the dev branch as of now.

The version of the algorithm used in fetpype is the one available on the Docker Hub, which have some changes to the original code. The repository is available at <https://github.com/fetpype/dhcp-structural-pipeline>.

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
  cmd: "singularity exec -u --bind <singularity_mount> --bind <singularity_home>:/home/tmp_proc --nv
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
| `<singularity_home>`                   | A directory used for temporary files               | Singularity only                                             |
| `<input_stacks>`                       | The list of inputs stacks will be given as arguments      | Mutually exclusive with `<input_dir>`                                               |
| `<input_dir>`                          | The folder that contains the input stacks                 | Mutually exclusive with `<output_dir>`                                              |
| `<output_dir>`                         | The output directory                                      | Mutually exclusive with 

## dHCP processing pipeline 

The dHCP pipeline presents some particularities compared to the BOUNTI implementation.

### Gestational Age Requirement

The dHCP pipeline requires gestational age information, which can be provided through the `participants.tsv` file in the root of the BIDS dataset:

```tsv
participant_id    gestational_age
sub-01           28.5
sub-02           32.1
sub-03           25.8
```

### Processing Stages

You can choose to run only the segmentation, the surface reconstruction, or both. The default is to run both. The following options are available, and you should add them to the "cmd" field of the configuration file:

**`-seg` (Segmentation only):**

**`-surf` (Surface reconstruction):**

**`-all` (Complete Processing):**

### Known dHCP issues

The pipeline has been shown to fail in specific systems. We are still investigating the cause of this issue, but if the pipeline fails with the following error in logs/<image_name>-tissue-em-err.log:

```
10%...Error: draw-em command returned non-zero exit status -8
```

Try to run the pipeline in a different system or, if you are in an HPC, in a different node. If the problem persists, please open an issue on the [GitHub repository](https://github.com/gerardmartijuan/dhcp-pipeline-multifact/issues) with the characteristics of the system you are using.


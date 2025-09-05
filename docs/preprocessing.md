# Preprocessing
Pre-processing starts from multiple T2-weighted stacks and processed each stack individually to prepare them for [super-resolution reconstruction](reconstruction.md).

## Available tools
Fetpype pre-processes the data in the following order. 
---

Data Loading (→ **Brain extraction)** → [Resolution checks](api_nodes.md#fetpype.nodes.preprocessing.CheckAffineResStacksAndMasks) → [Cropping](api_nodes.md#fetpype.nodes.preprocessing.CropStacksAndMasks) → **Denoising** 
→ **Bias field correction** → [Output checks](api_nodes.md#fetpype.nodes.preprocessing.CheckAndSortStacksAndMasks)

---

The three steps in boldface are run from a container. 

!!! Note
    All the container runs use the command below and are passed through the function [`run_prepro_cmd`](api_nodes.md#fetpype.nodes.preprocessing.run_prepro_cmd)
## Config structure

The config file is structured as follows:
```yaml
brain_extraction:
  docker:
    cmd: "docker run --gpus all <mount> thsanchez/fetpype_utils:latest run_brain_extraction 
      --input_stacks <input_stacks> 
      --output_masks <output_masks> 
      --method fet_bet"
  singularity:
    cmd: "singularity run --bind <singularity_mount> --nv
      <singularity_path>/fetpype_utils.sif
      run_brain_extraction
      --input_stacks <input_stacks> 
      --output_masks <output_masks> --method monaifbs"

check_stacks_and_masks:
  enabled: true

denoising:
  enabled: true
  docker:
    cmd: "docker run <mount> thsanchez/fetpype_utils:latest run_denoising 
      --input_stacks <input_stacks> 
      --output_stacks <output_stacks>"
  singularity:
    cmd: "singularity run --bind <singularity_mount>
      <singularity_path>/fetpype_utils.sif
      run_denoising
      --input_stacks <input_stacks> 
      --output_stacks <output_stacks>"
cropping:
  enabled: true
  
bias_correction:
  enabled: true
  docker:
    cmd: "docker run <mount> thsanchez/fetpype_utils:latest run_bias_field_correction 
      --input_stacks <input_stacks> 
      --input_masks <input_masks> 
      --output_stacks <output_stacks>"
  singularity:
    cmd: "singularity run --bind <singularity_mount>
      <singularity_path>/fetpype_utils.sif
      run_bias_field_correction
      --input_stacks <input_stacks> 
      --input_masks <input_masks> 
      --output_stacks <output_stacks>"
```
!!! Note 
    - Each pre-processing step that can be disabled has a boolean entry `enabled: true` that can be set to false.
    - The steps that rely on a container are set with a list of valid tags

### Tags


There are a limited set of tags that can be used for preprocessing: 

| <div style="width:150px">Command</div> | Description                                               | Comments                                                                            |
| -------------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `<mount>`                              | Where the different folders will be mounted on Docker               | Docker only                                             |
| `<singularity_mount>`                  | Where the different folders will be mounted on Singularity               | Singularity only                                             |
| `<singularity_path>`                   | The base path of the Singularity image               | Singularity only                                             |
| `<input_stacks>`                       | The list of inputs stacks will be given as arguments      | Mutually exclusive with `<input_dir>`                                               |
| `<input_masks>`                        | The list of inputs masks will be given as arguments       | Mutually exclusive with `<input_masks_dir>`                                         |
| `<output_stacks>`                      | The list of output stacks                                         |                                               |
| `<output_masks>`                       | The list of output masks                                   |                                            |


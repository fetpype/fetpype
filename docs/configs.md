# Config files

Config files are the bread and butter of fetpype. They allow to define how the data should be processed within a container and what output should be returned. They also specify optional parameters that can be modified by the user, without touching at the code.

## Calls to docker and singularity containers
Fetpype acts as a wrapper around calls to various containers, and uses a limited set of tags in each dedicated node to construct the command that will be called.

## Reconstruction configs
The reconstruction algorithms used are described in greater depth in their [dedicated page](reconstruction.md). Here, we look at an example of how the config file of niftymic (in `configs/reconstruction/niftymic.yaml`) is structured.

This is how the config file looks.
```
pipeline: "niftymic"
docker: 
  cmd: "docker run --gpus '\"device=0\"' <mount> renbem/niftymic 
    niftymic_run_reconstruction_pipeline
    --filenames <input_stacks>
    --filenames-masks <input_masks>
    --dir-output <output_dir>"
singularity:
  cmd: null
path_to_output: "recon_template_space/srr_template.nii.gz"
```

The structuring of the docker call features: 

- A set of tags: `<mount>`, `<input_stacks>`, `<input_masks>`, ` <output_dir>`
- The bulk of the call to the reconstruction pipeline of niftymic.

### Tags
There are a limited set of tags that can be used for reconstruction: 

| <div style="width:150px">Command</div> | Description                                               | Comments                                                                            |
| -------------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `<mount>`                              | Where the different folders will be mounted               | Docker only (not needed in singularity)                                             |
| `<input_stacks>`                       | The list of inputs stacks will be given as arguments      | Mutually exclusive with `<input_dir>`                                               |
| `<input_dir>`                          | The folder that contains the input stacks                 | Mutually exclusive with `<input_stacks>`                                            |
| `<input_masks>`                        | The list of inputs masks will be given as arguments       | Mutually exclusive with `<input_masks_dir>`                                         |
| `<input_masks_dir>`                    | The folder that contains the input masks                  | Mutually exclusive with `<input_masks>`                                             |
| `<output_volume>`                      | The output volume                                         | Mutually exclusive with `<output_dir>`                                              |
| `<output_dir>`                         | The output directory                                      | Mutually exclusive with `<output_volume>`                                           |
| `<input_tp>`                           | The through-plane resolution of input stacks              | Needed for SVRTK - Automatically calculated                                         |
| `<output_res>`                         | The desired voxel resolution for the reconstructed volume | This tag be set in the config file in the field `reconstruction/output_resolution`. |

!!! Note 
    The NiftyMIC config contains an additional variable `path_to_output`. This is needed when only an `<output_dir>` is given to the method. This variable contains the path where the reconstructed volume will be located *relative* to `<output_dir>`.



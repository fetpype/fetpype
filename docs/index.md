# Fetpype
## About
Fetpype is a library that aims at facilitating the analysis of fetal brain MRI by integrating the variety of tools commonly used in processing pipelines. Starting from clinical acquisition of fetal brain MRI (T2-weighted fast spin echo sequences), it performs [pre-processing](preprocessing.md), [reconstruction](reconstruction.md), [segmentation](segmentation.md) and [surface extraction](surface.md).

![Fetpype diagram](media/fetpype_illustration.png)

## The tool
Fetpype aims at integrating a variety of existing tools, available as docker containers into a single, easy to use interface.  It relies on three main components:

- Standardized data formatting following the [BIDS](https://bids.neuroimaging.io/index.html) (Brain Imaging Data Structure) convention.
- Integration of containerized methods using Docker or Singularity.
- Chaining of data calls using [Nipype](https://nipype.readthedocs.io/en/latest/), a library for robust integration of heterogeneous neuroimaging pipelines.
- Simple yaml configuration files generated using [Hydra](https://hydra.cc/docs/intro/).

![BIDS, containers, Nipype and hydra](media/bids_container_nipype_hydra.png)

## Quick start guide
### Installation
Clone the latest version of the fetpype repository
```
git clone https://github.com/fetpype/fetpype
```

Within your desired python environment, install fetpype
```
pip install -e .
```

### Running your first pipeline
#### Data formatting
Start with a BIDS-formatted dataset containing multiple stacks of low-resolution T2-weighted fetal brain MRI. A BIDS formatted folder should look as follows

```
sub-01
    [ses-01]
        anat
            sub-01_[ses-01]_run-1_T2w.nii.gz
            sub-01_[ses-01]_run-2_T2w.nii.gz
            ...
            sub-01_[ses-01]_run-N_T2w.nii.gz
sub-myname
    [ses-01]
        anat
            sub-myname_[ses-01]_run-1_T2w.nii.gz
            sub-myname_[ses-01]_run-2_T2w.nii.gz
            sub-myname_[ses-01]_run-6_T2w.nii.gz
            sub-myname_[ses-01]_run-7_T2w.nii.gz
    [ses-02]
            sub-myname_[ses-01]_run-1_T2w.nii.gz
            sub-myname_[ses-01]_run-2_T2w.nii.gz
            sub-myname_[ses-01]_run-3_T2w.nii.gz
```


Here, [ses-XX] is an optional tag/folder level. The `anat` folder will contain the different runs, which are the different stacks acquired for a given subject. More information about BIDS formatting is available [here](https://bids.neuroimaging.io/index.html).

#### Choose what you will run
The pipeline that will be run is defined by a structure of config files. A default pipeline, featuring pre-processing (mask extraction, denoising, cropping and masks), reconstruction (using NeSVoR [REF]) and segmentation (using BOUNTI [REF]) is defined by the following config file.

It starts by a master config located at `configs/default.yaml` with the following structure
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
This config defines a pipeline that will run the default preprocessing step (defined in `configs/preprocessing/default.yaml`), the NeSVoR reconstruction pipeline (defined in `configs/reconstruction/nesvor.yaml`) followed by the BOUNTI segmentation pipeline (defined in `configs/preprocessing/bounti.yaml`). Hydra will go in the corresponding folder and load the files to create a global config defined in a nested manner. Changing the pipeline that you want to run is as easy as changing the reconstruction pipeline from `nesvor` to `niftymic`. 

The details of the configs, the attributes and methods implemented is available [in this page](methods.md).

#### Just run it!
Once you chose the pipeline that you are going to run, you can then run it by calling 
```
fetpype_run --data <THE_PATH_TO_YOUR_DATA> --out <THE_PATH_TO_YOUR_DATA>/derivatives/fetpype
```

Additional options are available when calling `fetpype_run --help`. Then just wait and see your results! 

#### While you're waiting for the results
Feel free to explore how fetpype works and what it can do!

- [Output data formatting](output_data.md)
- [Running parts of the pipeline](run_parts.md)
- [How can I include my method in fetpype?](contributing.md)


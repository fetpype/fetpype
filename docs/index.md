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
Clone the latest version of the fetpype repository:
```
git clone https://github.com/fetpype/fetpype
```

Within your desired python environment, install fetpype
```
pip install -e .
```

### Running your first pipeline
Start with a BIDS-formatted dataset containing multiple stacks of low-resolution T2-weighted fetal brain MRI. A BIDS formatted folder should look as follows:


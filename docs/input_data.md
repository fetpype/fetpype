# BIDS Input Data Preparation
This guide explains how to prepare your fetal brain MRI data in BIDS (Brain Imaging Data Structure) format for use with Fetpype. 

## Overview 
Fetpype expects input data to follow the BIDS specification for neuroimaging datasets. This standardized format ensures reproducibility, facilitates data sharing, and enables automatic processing pipeline execution.

## BIDS Structure

The BIDS structure is as follows:

```
dataset/
├── dataset_description.json           # Dataset metadata (required)
├── participants.tsv                   # Subject information (required for dHCP)
├── README                             # Dataset description (recommended)
├── CHANGES                            # Version history (recommended)
└── sub-<subject_id>/                  # Subject directories
    └── [ses-<session_id>/]            # Session directories (optional)
        └── anat/                      # Anatomical data directory
            ├── sub-<subject_id>[_ses-<session_id>][_acq-<acquisition>]_run-<run_number>_T2w.nii.gz
            ├── sub-<subject_id>[_ses-<session_id>][_acq-<acquisition>]_run-<run_number>_T2w.nii.gz
            ├── sub-<subject_id>[_ses-<session_id>][_acq-<acquisition>]_run-<run_number>_T2w.nii.gz
            └── ...
```

## Naming Conventions

The naming convention for the files is as follows:

```
sub-<subject_id>[_ses-<session_id>][_acq-<acquisition>]_run-<run_number>_T2w.nii.gz
```

The following entities are supported:

- `sub-<subject_id>`: Subject identifier
- `ses-<session_id>`: Session identifier
- `acq-<acquisition>`: Acquisition identifier
- `run-<run_number>`: Run number

## DICOM to BIDS Conversion

There are several tools that can be used to convert DICOM to BIDS. We recommend using [dcm2bids](https://github.com/dcm2bids/dcm2bids). Other options are to use [dcm2niix](https://github.com/rordenlab/dcm2niix) to create the nifti files and then convert the files to BIDS
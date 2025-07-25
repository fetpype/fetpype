# Output Data Structure

Fetpype organizes all processed data following the [BIDS (Brain Imaging Data Structure)](https://bids.neuroimaging.io/index.html) derivatives convention. This standardized organization ensures that your results are easily shareable, reproducible, and compatible with other neuroimaging analysis tools.

To understand how to transform your raw data into the BIDS structure that Fetpype expects, please refer to this guide: [Input Data Structure](input_data.md).

## Overall Structure

Fetpype creates a derivatives directory structure that mirrors your input BIDS dataset but contains processed data instead of raw acquisitions. The structure is as follows:

```
your_project/
├── sub-01/                          # Raw BIDS data (input)
│   └── ses-01/
│       └── anat/
│           ├── sub-01_ses-01_run-1_T2w.nii.gz
│           ├── sub-01_ses-01_run-2_T2w.nii.gz
│           └── sub-01_ses-01_run-3_T2w.nii.gz
└── derivatives/                     # Processed data (output)
    ├── preprocessing/               # Intermediate preprocessing outputs
    ├── nesvor/                      # Reconstruction outputs  
    ├── bounti/                      # Segmentation outputs
    └── nesvor_bounti/               # Combined pipeline outputs
```

Each derivatives subdirectory contains:

- `dataset_description.json`: Metadata about the processing pipeline
- Subject directories: Organized following BIDS conventions

## The DataSink Module

The BIDS DataSink handles the organization and formatting of pipeline outputs according to BIDS conventions. It ensures that all processed data is properly structured and named.

The BIDS DataSink automatically organizes pipeline outputs into the standard BIDS derivatives structure:

```
derivatives/
├── <pipeline_name>/
│   ├── dataset_description.json
│   └── sub-<subject>/
│       └── [ses-<session>/]
│           └── anat/
│               └── sub-<subject>_[ses-<session>]_[rec-<reconstruction>]_[seg-<segmentation>]_[desc-<description>]_<suffix>.nii.gz
```

### File Naming Convention

The DataSink applies transformations to convert Nipype working directory paths into BIDS-compliant names:

| Input (Nipype working dir) | Output (BIDS derivatives) |
|----------------------------|---------------------------|
| `preprocessing_wf/_session_01_subject_sub-01/denoise_wf/_denoising/sub-01_ses-01_run-1_T2w_noise_corrected.nii.gz` | `sub-01/ses-01/anat/sub-01_ses-01_run-1_desc-denoised_T2w.nii.gz` |
| `nesvor_pipeline_wf/_session_02_subject_sub-01/recon_node/recon.nii.gz` | `sub-01/ses-02/anat/sub-01_ses-02_rec-nesvor_T2w.nii.gz` |
| `segmentation_wf/_session_01_subject_sub-01/seg_node/input_srr-mask-brain_bounti-19.nii.gz` | `sub-01/ses-01/anat/sub-01_ses-01_rec-nesvor_seg-bounti_dseg.nii.gz` |


## Example of integration with pipelines

The DataSink is automatically integrated into Fetpype workflows:

```python
# In pipeline creation
datasink = create_bids_datasink(
    out_dir=output_directory,
    pipeline_name=get_pipeline_name(cfg),
    strip_dir=main_workflow.base_dir,
    rec_label=cfg.reconstruction.pipeline,
    seg_label=cfg.segmentation.pipeline
)

# Connect pipeline outputs to datasink
main_workflow.connect(
    reconstruction_node, "output_volume", 
    datasink, "@reconstruction"
)
```

## BIDS Entity Explanation
Fetpype uses standard BIDS entities to describe the processed data:

### Core Entities

- `sub-XX`: Subject identifier (matches input data)
- `ses-XX`: Session identifier (matches input data, omitted if no sessions)
- `run-X`: Run number (from original stacks, preserved in preprocessing)

### Processing Entities

- `rec-METHOD`: Reconstruction method used (e.g., rec-nesvor, rec-niftymic, rec-svrtk)
- `seg-METHOD`: Segmentation method used (e.g., seg-bounti, seg-dhcp)
- `desc-DESCRIPTION`: Processing description (e.g., desc-denoised, desc-cropped)

### File Suffixes

- `T2w`: Reconstructed T2-weighted volume
- `dseg`: Discrete segmentation (labeled volume)
- `mask`: Binary mask
- `surf.gii`: Surface mesh (GIFTI format)
- `shape.gii`: Surface metric data (GIFTI format)


## Possible issues
If your Fetpype pipeline finishes successfully but you don't find any outputs in the derivatives/ folder, this typically indicates a DataSink organization error.

### What to Do

1. Check the Nipype working directory: Your processed files are likely still there, just not properly organized. Look in:

```
nipype/                          # Or your specified --nipype_dir
└── pipeline_name_wf/
    └── _session_XX_subject_XX/
        └── [various_processing_nodes]/
            └── [your_actual_results]
```

2. Locate your results: The actual processed volumes and segmentations will be in the individual node directories within the Nipype working directory.

3. Check the naming of your raw files: This issue could be caused by your files having names that don't match the expected BIDS format by the DataSink, preventing it from working correctly. 

**Common scenarios that cause DataSink issues:**

- Non-standard subject/session naming in your input BIDS dataset
- Special characters in filenames or paths
- Unexpected file extensions or naming conventions
- Missing session information when sessions are expected (or vice versa)

If everything looks correct, please add an issue on the [GitHub repository](https://github.com/fetpype/fetpype/issues) with the following information:

- Your input BIDS directory structure (subject/session naming).
- The command you used to run Fetpype.
- The configuration file used.
- An example of the file paths in your Nipype working directory.
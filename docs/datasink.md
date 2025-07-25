
# DataSink module

The DataSink module in fetpype is responsible for organizing and renaming pipeline outputs from the nipype default workflow into BIDS-compliant directory structures. This document provides a comprehensive guide on how the DataSink works, and how to use it correctly.

## Overview

Fetpype uses Nipype's `DataSink` interface wrapped in a custom function `create_bids_datasink()` to automatically organize outputs according to BIDS conventions. The system handles complex file renaming through regex substitutions and ensures outputs are properly structured for downstream analysis. For a more detailed explanation of the DataSink module, see the [Nipype documentation](https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.io.html#datasink) or the [nipype-tutorial](https://miykael.github.io/nipype_tutorial/notebooks/basic_data_output.html) on DataSink.

## Core Architecture

### Main Function: `create_bids_datasink()`

Located in `fetpype/utils/utils_bids.py`, this function creates a configured DataSink node:

```python
def create_bids_datasink(
    out_dir,           # Base output directory
    pipeline_name,     # Name of the pipeline (e.g., 'nesvor_bounti')
    strip_dir,         # Nipype working directory path to strip
    datatype="anat",   # BIDS datatype
    name=None,         # Node name (auto-generated if None)
    rec_label=None,    # Reconstruction label (e.g., 'nesvor')
    seg_label=None,    # Segmentation label (e.g., 'bounti')
    desc_label=None,   # Description label (e.g., 'denoised')
    custom_subs=None,  # Custom simple substitutions
    custom_regex_subs=None  # Custom regex substitutions
)
```

## Directory Structure

The DataSink module default behavior organizes outputs into the following structure:

```
<out_dir>/
├── sub-<ID>/
│   ├── [ses-<ID>/]
│   │   └── anat/
│   │       ├── sub-<ID>_[ses-<ID>]_desc-<label>_T2w.nii.gz
│   │       ├── sub-<ID>_[ses-<ID>]_rec-<method>_T2w.nii.gz
│   │       └── sub-<ID>_[ses-<ID>]_rec-<method>_seg-<method>_dseg.nii.gz
└── dataset_description.json
```

## Regex Substitution Rules

The DataSink applies different rules based on pipeline context:

### Rule 1: Preprocessing Stacks (Denoised)
**Trigger**: `pipeline_name == "preprocessing"` and `desc_label == "denoised"`

```regex
Input:  /output/preprocessing_wf/_session_01_subject_sub-01/denoise_wf/_denoising/sub-01_ses-01_run-1_T2w_noise_corrected.nii.gz
Output: /output/sub-01/ses-01/anat/sub-01_ses-01_run-1_desc-denoised_T2w.nii.gz
```

### Rule 2: Preprocessing Masks (Cropped)
**Trigger**: `pipeline_name == "preprocessing"` and `desc_label == "cropped"`

```regex
Input:  /output/preprocessing_wf/_session_01_subject_sub-01/crop_wf/_cropping/sub-01_ses-01_run-1_mask.nii
Output: /output/sub-01/ses-01/anat/sub-01_ses-01_run-1_desc-cropped_mask.nii
```

### Rule 3: Reconstruction Output
**Trigger**: `rec_label` is set and `seg_label` is None

```regex
Input:  /output/nesvor_pipeline_wf/_session_02_subject_sub-01/recon_node/recon.nii.gz
Output: /output/sub-01/ses-02/anat/sub-01_ses-02_rec-nesvor_T2w.nii.gz
```

### Rule 4: Segmentation Output (BOUNTI)
**Trigger**: Both `seg_label` and `rec_label` are set

```regex
Input:  /output/segmentation_wf/_session_01_subject_sub-01/seg_node/input_srr-mask-brain_bounti-19.nii.gz
Output: /output/sub-01/ses-01/anat/sub-01_ses-01_rec-nesvor_seg-bounti_dseg.nii.gz
```

### Rule 5: Segmentation Output (dHCP)
**Trigger**: `seg_label == "dhcp"`

```regex
Input:  /output/segmentation_wf/_session_01_subject_sub-01/dhcp_node/
Output: /output/sub-01/ses-01/anat/sub-01_ses-01_dhcp/
```

### Cleanup Rules
Applied to all outputs:

- `sub-sub-` → `sub-` (fix doubled prefixes)
- `ses-ses-` → `ses-` (fix doubled prefixes)  
- `_+` → `_` (multiple underscores to single)
- `//+` → `/` (fix double slashes)
- `_ses-None` → `` (remove None sessions)
- `(\.nii\.gz)\1+$` → `\1` (fix repeated extensions)

## Usage Examples

### Basic Reconstruction DataSink

```python
from fetpype.utils.utils_bids import create_bids_datasink

datasink = create_bids_datasink(
    out_dir="/path/to/derivatives",
    pipeline_name="nesvor",
    strip_dir="/path/to/nipype/workdir",
    rec_label="nesvor"
)

# Connect in workflow
workflow.connect(recon_node, "output", datasink, "@nesvor")
```

### Preprocessing DataSink

```python
# For denoised stacks
denoised_datasink = create_bids_datasink(
    out_dir="/path/to/derivatives/preprocessing",
    pipeline_name="preprocessing",
    strip_dir="/path/to/nipype/workdir",
    desc_label="denoised"
)

# For cropped masks  
cropped_datasink = create_bids_datasink(
    out_dir="/path/to/derivatives/preprocessing",
    pipeline_name="preprocessing", 
    strip_dir="/path/to/nipype/workdir",
    desc_label="cropped"
)
```

### Segmentation DataSink

```python
seg_datasink = create_bids_datasink(
    out_dir="/path/to/derivatives",
    pipeline_name="nesvor_bounti",
    strip_dir="/path/to/nipype/workdir", 
    rec_label="nesvor",
    seg_label="bounti"
)
```

## Integration in Workflows

### Connecting Outputs

The DataSink uses Nipype's connection syntax with `@` prefix for container naming:

```python
# For single outputs
workflow.connect(node, "output", datasink, "@pipeline_name")

# For multiple outputs  
workflow.connect(node, "output1", datasink, "@output1")
workflow.connect(node, "output2", datasink, "@output2")
```

### Workflow Examples

From `fetpype/workflows/pipeline_fet.py`:

```python
# Reconstruction datasink
recon_datasink = create_bids_datasink(
    out_dir=out_dir,
    pipeline_name=pipeline_name,
    strip_dir=main_workflow.base_dir,
    name="final_recon_datasink",
    rec_label=cfg.reconstruction.pipeline,
)

workflow.connect(
    fet_pipe, "outputnode.output_srr", 
    recon_datasink, f"@{pipeline_name}"
)
```

## Best Practices

### 1. Always Set strip_dir
The `strip_dir` parameter is mandatory and should point to the Nipype base working directory:

```python
# Correct
strip_dir = main_workflow.base_dir

# Incorrect - will raise ValueError
strip_dir = None
```

### 2. Use Appropriate Labels
Choose labels that reflect the actual processing method:

```python
# Good
rec_label = cfg.reconstruction.pipeline  # "nesvor", "niftymic", etc.
seg_label = cfg.segmentation.pipeline    # "bounti", "dhcp", etc.

# Avoid
rec_label = "reconstruction"  # Too generic
```

### 3. Pipeline Name Conventions
Pipeline names should be descriptive and match the processing chain:

```python
# For full pipeline
pipeline_name = "nesvor_bounti"

# For single steps  
pipeline_name = "preprocessing"
pipeline_name = "nesvor"
```

### 4. Custom Substitutions
Add custom substitutions for specialized file patterns, according to the output names and folders of your custom node:

```python
custom_regex_subs = [
    (r"_custom_suffix", ""),
    (r"temp_", "")
]

datasink = create_bids_datasink(
    ...,
    custom_regex_subs=custom_regex_subs
)
```

## Advanced Usage

### Custom DataSink for New Pipelines

When adding a new pipeline to fetpype:

1. **Determine file patterns**: Understand what your pipeline outputs.
2. **Design BIDS naming**: Choose appropriate BIDS entities.
3. **Create regex rules**: Write patterns to transform paths.
4. **Test thoroughly**: Use unit tests to verify behavior

Example for a new "mymethod" pipeline:

```python
# Add to create_bids_datasink function
if pipeline_name == "mymethod" and rec_label:
    regex_subs.append((
        rf"^{escaped_bids_derivatives_root}/.*mymethod.*/"
        rf"([^/]+)_output(\.nii\.gz|\.nii)$",
        rf"{bids_derivatives_root}/sub-\1/anat/"
        rf"sub-\1_rec-mymethod_T2w\2"
    ))
```

### Multiple DataSinks in One Workflow

For complex pipelines, use multiple DataSinks:

```python
# Primary outputs
main_datasink = create_bids_datasink(...)

# Intermediate outputs  
intermediate_datasink = create_bids_datasink(
    out_dir=intermediate_dir,
    ...
)

# QC outputs
qc_datasink = create_bids_datasink(
    out_dir=qc_dir,
    ...
)
```

## Testing DataSink Configuration

Always test your DataSink configuration prior to a pull request. This is a test example:

```python
def test_my_datasink(mock_output_dir, mock_nipype_wf_dir):
    ds = create_bids_datasink(
        out_dir=mock_output_dir,
        pipeline_name="mymethod",
        strip_dir=mock_nipype_wf_dir,
        rec_label="mymethod"
    )
    
    # Test regex substitutions
    regex_subs = ds.inputs.regexp_substitutions
    
    test_path = f"{mock_output_dir}/mymethod_wf/_session_01_subject_sub-01/output.nii.gz"
    expected = f"{mock_output_dir}/sub-01/ses-01/anat/sub-01_ses-01_rec-mymethod_T2w.nii.gz"
    
    result = apply_regex_subs(test_path, regex_subs)
    assert result == expected
```
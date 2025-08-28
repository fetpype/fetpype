# Output Data Structure

Fetpype organizes all processed data following the [BIDS (Brain Imaging Data Structure)](https://bids.neuroimaging.io/index.html) derivatives convention. This ensures your results are shareable, reproducible, and compatible with other neuroimaging tools.

For transforming raw data into the BIDS structure Fetpype expects, see: [Input Data Structure](input_data.md).

## The DataSink Module

Fetpype uses a custom DataSink (see `create_bids_datasink` in `fetpype/utils/utils_bids.py`) to organize and rename pipeline outputs into BIDS-compliant structures. It wraps Nipype's DataSink and applies regex substitutions to ensure outputs are properly named and structured for downstream analysis. For a more detailed explanation of the DataSink module, see the [Nipype documentation](https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.io.html#datasink) or the [nipype-tutorial](https://miykael.github.io/nipype_tutorial/notebooks/basic_data_output.html) on DataSink.

### How DataSink Works

- **Input:** Nipype working directory outputs (often with non-BIDS names)
- **Processing:** Applies a set of regex and simple substitutions to transform paths and filenames into BIDS-compliant outputs
- **Output:** Files organized in the BIDS derivatives structure, with correct naming and metadata

### Example Output Structure

```
derivatives/
├── <pipeline_name>/
│   ├── dataset_description.json
│   └── sub-<subject>/
│       └── [ses-<session>/]
│           └── anat/
│               └── sub-<subject>_[ses-<session>]_[rec-<reconstruction>]_[seg-<segmentation>]_[surf-surface]_[desc-<description>]_<suffix>.nii.gz
```

### File Naming Convention

| Input (Nipype working dir) | Output (BIDS derivatives) |
|----------------------------|---------------------------|
| `preprocessing_wf/_session_01_subject_sub-01/denoise_wf/_denoising/sub-01_ses-01_run-1_T2w_noise_corrected.nii.gz` | `sub-01/ses-01/anat/sub-01_ses-01_run-1_desc-denoised_T2w.nii.gz` |
| `nesvor_pipeline_wf/_session_02_subject_sub-01/recon_node/recon.nii.gz` | `sub-01/ses-02/anat/sub-01_ses-02_rec-nesvor_T2w.nii.gz` |
| `segmentation_wf/_session_01_subject_sub-01/seg_node/input_srr-mask-brain_bounti-19.nii.gz` | `sub-01/ses-01/anat/sub-01_ses-01_rec-nesvor_seg-bounti_dseg.nii.gz` |
| `surface_wf/_session_01_subject_sub-01/seg_node/surf.gii` | `sub-01/ses-01/anat/sub-01_ses-01_rec-nesvor_seg-bounti_surf-surface-surf.gii` |

### Core BIDS Entities

- `sub-XX`: Subject identifier
- `ses-XX`: Session identifier (omitted if no sessions)
- `run-X`: Run number (from original stacks, preserved in preprocessing)
- `rec-METHOD`: Reconstruction method (e.g., rec-nesvor)
- `seg-METHOD`: Segmentation method (e.g., seg-bounti)
- `surf-METHOD`: Surface extraction method (e.g., surf-surface)
- `desc-DESCRIPTION`: Processing description (e.g., desc-denoised)
- Suffixes: `T2w`, `dseg`, `mask`, `surf.gii`, `shape.gii`

## DataSink Regex and Substitution Rules

The DataSink applies context-specific regex rules to convert Nipype outputs to BIDS-compliant names. Some examples of rules that are in use for various pipelines:

- **Preprocessing (denoised):**
  - Input: .../denoise_wf/.../sub-01_ses-01_run-1_T2w_noise_corrected.nii.gz
  - Output: sub-01/ses-01/anat/sub-01_ses-01_run-1_desc-denoised_T2w.nii.gz
- **Preprocessing (cropped):**
  - Input: .../crop_wf/.../sub-01_ses-01_run-1_mask.nii
  - Output: sub-01/ses-01/anat/sub-01_ses-01_run-1_desc-cropped_mask.nii
- **Reconstruction:**
  - Input: .../recon_node/recon.nii.gz
  - Output: sub-01/ses-02/anat/sub-01_ses-02_rec-nesvor_T2w.nii.gz
- **Segmentation:**
  - Input: .../seg_node/input_srr-mask-brain_bounti-19.nii.gz
  - Output: sub-01/ses-01/anat/sub-01_ses-01_rec-nesvor_seg-bounti_dseg.nii.gz
- **Surface extraction:**
  - Input: .../surf_node/surf.gii
  - Output: sub-01/ses-01/anat/sub-01_ses-01_rec-nesvor_seg-bounti_surf-surface_surf.gii

**Cleanup rules** (applied to all outputs):
- Remove doubled prefixes (e.g., `sub-sub-` → `sub-`)
- Collapse multiple underscores or slashes
- Remove `None` session labels
- Fix repeated extensions (e.g., `.nii.gz.gz` → `.nii.gz`)

### Customization

You can add custom substitutions for specialized file patterns using the `custom_subs` and `custom_regex_subs` arguments to `create_bids_datasink`.

Example:
```python
custom_regex_subs = [
    (r"_custom_suffix", ""),
    (r"temp_", "")
]
datasink = create_bids_datasink(
    ..., custom_regex_subs=custom_regex_subs
)
```

## Example: Integrating DataSink in a Pipeline

```python
from fetpype.utils.utils_bids import create_bids_datasink

datasink = create_bids_datasink(
    out_dir="/path/to/derivatives",
    pipeline_name="nesvor_bounti",
    strip_dir="/path/to/nipype/workdir",
    rec_label="nesvor",
    seg_label="bounti"
)

workflow.connect(
    node, "output", datasink, "@nesvor_bounti"
)
```

## Best Practices

- **Always set `strip_dir`:** This should point to the Nipype base working directory. If not set, DataSink will raise an error.
- **Use descriptive labels:** For `rec_label`, `seg_label`, `surf_label`, and `desc_label`, use values that reflect the actual processing method (e.g., `nesvor`, `bounti`, `surface`, `denoised`).
- **Pipeline names:** Should match the processing chain (e.g., `nesvor_bounti_surface`, `preprocessing`).
- **Test your DataSink configuration:** Use unit tests or inspect outputs to ensure correct organization and naming.

## Troubleshooting

If your pipeline finishes but you don't see outputs in `derivatives/`, check:
- The Nipype working directory for your results (they may not have been moved/renamed correctly).
- That your input BIDS dataset uses standard subject/session naming.
- That there are no special characters or unexpected extensions in your filenames.
- That session information is present/absent as expected.

If issues persist, please open an issue on [GitHub](https://github.com/fetpype/fetpype/issues) with:
- Your input BIDS directory structure.
- The command and config file used.
- Example file paths from your Nipype working directory.
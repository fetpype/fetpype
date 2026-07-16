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
│               ├── sub-<subject>_[ses-<session>]_[rec-<reconstruction>]_[seg-<segmentation>]_[desc-<description>]_<suffix>.nii.gz
│               ├── sub-<subject>_[ses-<session>]_[rec-<reconstruction>]_[seg-<segmentation>]_hemi-L_white.surf.gii
│               └── sub-<subject>_[ses-<session>]_[rec-<reconstruction>]_[seg-<segmentation>]_hemi-R_white.surf.gii
```

### File Naming Convention

| Input (Nipype working dir) | Output (BIDS derivatives) |
|----------------------------|---------------------------|
| `nesvor_bounti_surfpype/full_pipeline/Preprocessing/_session_01_subject_sub-01/denoise_wf/_denoising/sub-01_ses-01_run-1_T2w_noise_corrected.nii.gz` | `sub-01/ses-01/anat/sub-01_ses-01_run-1_desc-denoised_T2w.nii.gz` |
| `nesvor_bounti_surfpype/full_pipeline/Reconstruction/_session_01_subject_sub-01/nesvor/recon/recon.nii.gz` | `sub-01/ses-01/anat/sub-01_ses-01_rec-nesvor_T2w.nii.gz` |
| `nesvor_bounti_surfpype/full_pipeline/Segmentation/_session_01_subject_sub-01/bounti/seg/out/input_srr-mask-brain_bounti-19.nii.gz` | `sub-01/ses-01/anat/sub-01_ses-01_rec-nesvor_seg-bounti_dseg.nii.gz` |
| `nesvor_bounti_surfpype/full_pipeline/SurfaceExtraction/_session_01_subject_sub-01/surf_lh/surf/out/hemi-L_white.surf.gii` | `sub-01/ses-01/anat/sub-01_ses-01_rec-nesvor_seg-bounti_hemi-L_white.surf.gii` |
| `nesvor_bounti_surfpype/full_pipeline/SurfaceExtraction/_session_01_subject_sub-01/surf_rh/surf/out/hemi-R_white.surf.gii` | `sub-01/ses-01/anat/sub-01_ses-01_rec-nesvor_seg-bounti_hemi-R_white.surf.gii` |

### Core BIDS Entities

- `sub-XX`: Subject identifier
- `ses-XX`: Session identifier (omitted if no sessions)
- `run-X`: Run number (from original stacks, preserved in preprocessing)
- `rec-<method>`: Reconstruction method (e.g., rec-nesvor)
- `seg-<method>`: Segmentation method (e.g., seg-bounti)
- `hemi-L` / `hemi-R`: Hemisphere (left and right), used for surface outputs
- `desc-<description>`: Processing description (e.g., desc-denoised)
- Suffixes: `T2w`, `dseg`, `mask`, `white.surf.gii`

## DataSink Regex and Substitution Rules

All rules extract the subject and session identifiers from the Nipype working directory path (via the `_session_X_subject_Y` segments that Nipype inserts automatically) and use them to construct the BIDS output path. Which rules are active depends on the pipeline stage and the labels passed to `create_bids_datasink`.

### Preprocessing rules

These rules are active only when `pipeline_name == "preprocessing"`.

**Denoised stacks** (`desc_label="denoised"`): Matches files ending in `_T2w_noise_corrected.nii[.gz]` within any `_denoising` subdirectory. Preserves the subject, session, and run identifiers from the filename.

  - Input: `.../Preprocessing/_session_01_subject_sub-01/_denoising/sub-01_ses-01_run-1_T2w_noise_corrected.nii.gz`
  - Output: `sub-01/ses-01/anat/sub-01_ses-01_run-1_desc-denoised_T2w.nii.gz`

### Full-pipeline rules

These rules are active for the reconstruction, segmentation, and surface pipelines.

**Reconstruction** (`rec_label` set, no `seg_label`): Any `.nii[.gz]` file under the subject/session path is renamed, discarding the original filename and tagging the result with the reconstruction method label.

  - Input: `.../nesvor/recon/recon.nii.gz`
  - Output: `sub-01/ses-01/anat/sub-01_ses-01_rec-nesvor_T2w.nii.gz`

**Segmentation** (`rec_label` and `seg_label` both set): Matches the BOUNTI output by its fixed filename `input_srr-mask-brain_bounti-19.nii[.gz]` and tags it with both the reconstruction and segmentation method labels.

  - Input: `.../bounti/seg/out/input_srr-mask-brain_bounti-19.nii.gz`
  - Output: `sub-01/ses-01/anat/sub-01_ses-01_rec-nesvor_seg-bounti_dseg.nii.gz`

**Surface extraction** (`surf_label` set): Any `.gii` or `.stl` file keeps its original filename stem as the BIDS suffix, prefixed with the reconstruction and segmentation labels when available. One file is produced per hemisphere:

Left hemisphere:

  - Input: `.../surf_lh/surf/out/hemi-L_white.surf.gii`
  - Output: `sub-01/ses-01/anat/sub-01_ses-01_rec-nesvor_seg-bounti_hemi-L_white.surf.gii`
  
Right hemisphere:

  - Input: `.../surf_rh/surf/out/hemi-R_white.surf.gii`
  - Output: `sub-01/ses-01/anat/sub-01_ses-01_rec-nesvor_seg-bounti_hemi-R_white.surf.gii`

### Cleanup rules

Applied to all outputs after the above rules:

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
    pipeline_name="nesvor_bounti_surfpype",
    strip_dir="/path/to/nipype/workdir",
    rec_label="nesvor",
    seg_label="bounti",
    surf_label="surfpype"
)

workflow.connect(
    node, "output", datasink, "@nesvor_bounti_surfpype"
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
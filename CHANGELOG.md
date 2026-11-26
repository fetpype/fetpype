# Changelog

All notable changes to fetpype are documented here. Releases follow [semantic versioning](https://semver.org/): see the [contributing guide](https://fetpype.github.io/fetpype/contributing/#updating-the-changelog) for how to update it.

## [Unreleased]

## [2.0.0] - 2026-10-08

### Added
- **Breaking:** Added a new brain mask dilation step brain extraction, and this is enabled by default. This changes input for reconstruction, and therefore the downstream results. Dilated masks are saved as `*_dilated_mask*`. Custom preprocessing configs must now include a `mask_dilation` section. A user should set `mask_dilation.enabled: false` to keep the behaviour like the previous versions of `fetpype`.
- Added an automated release control.

### Added
- Support for the BIDS `acq-` (acquisition) entity in input file names.
- Documentation for running fetpype with Singularity, including notes for mesocentre users.

## [1.1.0] - 2026-07-24

### Added
- Bias field correction and intensity clipping as post-processing options.
- FetalSynthSeg as an alternative segmentation method to BOUNTI.

## [1.0.1] - 2026-05-19

Post-JOSS review release.

### Added
- The JOSS paper in the repository.
- A small toy dataset in `test_data` to help users try fetpype out.

### Changed
- Added a tutorial, substantially revised the documentation, and clarified system dependencies.
- `pytest` is now a dev dependency.

### Fixed
- Indexing failing after the `nipype_dir` was created inside the `data_dir`.
- `--masks` in `fetpype_run` leading to errors due to wrong workflow connections.

## [1.0.0] - 2025-10-09

First full release of fetpype, featuring the full processing pipeline.

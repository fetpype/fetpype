# tests/conftest.py
# -*- coding: utf-8 -*-
import pytest
import os
import shutil
import json
from pathlib import Path

@pytest.fixture(scope="function") # Use "function" scope for clean state per test
def mock_bids_root(tmp_path_factory):
    """Creates a mock BIDS dataset in a temporary directory within tests/."""

    # Get the root directory of the project (assuming conftest.py is in tests/)
    project_root = Path(__file__).parent.parent
    test_tmp_dir = project_root / "tests" / "tmp_test_data"
    test_tmp_dir.mkdir(exist_ok=True)

    # Create a unique directory for this specific test run within tests/tmp_test_data
    bids_root = test_tmp_dir / f"mock_bids_{os.urandom(4).hex()}"
    bids_root.mkdir(parents=True, exist_ok=True)
    print(f"Creating mock BIDS dataset at: {bids_root}")

    # --- Create dataset_description.json ---
    dataset_desc = {
        "Name": "Mock BIDS Dataset",
        "BIDSVersion": "1.6.0",
        "Authors": ["Test Generator"],
    }
    with open(bids_root / "dataset_description.json", "w") as f:
        json.dump(dataset_desc, f, indent=2)

    files_to_create = [
        "sub-01/ses-01/anat/sub-01_ses-01_T2w.nii.gz",
        "sub-01/ses-01/anat/sub-01_ses-01_acq-fast_T2w.nii.gz",
        "sub-01/ses-02/anat/sub-01_ses-02_T2w.nii.gz",
        "sub-02/anat/sub-02_T2w.nii.gz",
        "sub-02/anat/sub-02_acq-slow_T2w.nii.gz",
        "sub-03/ses-01/anat/sub-03_ses-01_acq-fast_T2w.nii.gz",
    ]

    for file_rel_path in files_to_create:
        file_path = bids_root / file_rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch() # Create empty file

    # --- Create a dummy derivative ---
    deriv_root = bids_root / "derivatives" / "fmriprep"
    deriv_root.mkdir(parents=True, exist_ok=True) # Ensure deriv root exists

    deriv_dataset_desc = {
        "Name": "Mock Derivative Dataset",
        "BIDSVersion": "1.6.0",
        "GeneratedBy": [
            {
                "Name": "MockPipeline",
                "Version": "1.0.0"
            }
        ],
        "PipelineDescription": {
            "Name": "MockPipeline"
        }
    }
    with open(deriv_root / "dataset_description.json", "w") as f:
        json.dump(deriv_dataset_desc, f, indent=2)

    deriv_files = [
        "sub-01/ses-01/anat/sub-01_ses-01_desc-preproc_T2w.nii.gz",
        "sub-02/anat/sub-02_desc-preproc_T2w.nii.gz",
    ]
    for file_rel_path in deriv_files:
        file_path = deriv_root / file_rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()

    yield bids_root # Provide the path to the test

    # --- Teardown ---
    print(f"Removing mock BIDS dataset at: {bids_root}")
    try:
        shutil.rmtree(bids_root)
    except OSError as e:
        print(f"Error removing directory {bids_root}: {e}")

@pytest.fixture(scope="function")
def mock_nipype_wf_dir(tmp_path_factory):
    # Use pytest's tmp_path_factory for simplicity and robust cleanup
    wf_base = tmp_path_factory.mktemp("nipype_wf")
    print(f"Creating mock Nipype WF base dir at: {wf_base}")
    yield str(wf_base) # Pass the path as a string, like real usage
    print(f"Mock Nipype WF base dir {wf_base} will be cleaned up by pytest.")
    # No explicit shutil needed when using tmp_path_factory


@pytest.fixture(scope="function")
def mock_output_dir(tmp_path_factory):
    # Use pytest's tmp_path_factory
    out_base = tmp_path_factory.mktemp("output")
    print(f"Creating mock output dir at: {out_base}")
    yield str(out_base)
    print(f"Mock output dir {out_base} will be cleaned up by pytest.")
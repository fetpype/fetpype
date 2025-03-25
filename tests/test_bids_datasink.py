import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
import nibabel as nib
import numpy as np
import nipype.pipeline.engine as pe
from nipype.interfaces.base import Bunch
from fetpype.utils.utils_bids import create_description_file

# Add parent directory to path to properly import fetpype
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fetpype.utils.utils_bids import create_datasource, create_bids_datasink


# Helper functions for creating mock BIDS datasets
def create_mock_bids_dataset(base_dir, subjects, sessions=None, acquisitions=None):
    """Create a mock BIDS dataset for testing.
    
    Parameters
    ----------
    base_dir : str
        Directory where the mock dataset will be created
    subjects : list
        List of subject IDs
    sessions : list, optional
        List of session IDs
    acquisitions : list, optional
        List of acquisition types
        
    Returns
    -------
    str
        Path to the created mock dataset
    """
    bids_dir = os.path.join(base_dir, "mock_bids_dataset")
    os.makedirs(bids_dir, exist_ok=True)
    
    # Create dataset_description.json
    create_description_file(bids_dir, "mock_dataset")
    
    # Create mock data
    for sub in subjects:
        sub_dir = os.path.join(bids_dir, f"sub-{sub}")
        
        if sessions:
            for ses in sessions:
                ses_dir = os.path.join(sub_dir, f"ses-{ses}")
                anat_dir = os.path.join(ses_dir, "anat")
                os.makedirs(anat_dir, exist_ok=True)
                
                # Create a simple NIfTI file with acquisition if specified
                if acquisitions:
                    for acq in acquisitions:
                        create_mock_nifti(
                            os.path.join(anat_dir, f"sub-{sub}_ses-{ses}_acq-{acq}_T2w.nii.gz")
                        )
                else:
                    create_mock_nifti(
                        os.path.join(anat_dir, f"sub-{sub}_ses-{ses}_T2w.nii.gz")
                    )
        else:
            # No sessions
            anat_dir = os.path.join(sub_dir, "anat")
            os.makedirs(anat_dir, exist_ok=True)
            
            # Create a simple NIfTI file with acquisition if specified
            if acquisitions:
                for acq in acquisitions:
                    create_mock_nifti(
                        os.path.join(anat_dir, f"sub-{sub}_acq-{acq}_T2w.nii.gz")
                    )
            else:
                create_mock_nifti(
                    os.path.join(anat_dir, f"sub-{sub}_T2w.nii.gz")
                )
    
    return bids_dir


def create_mock_derivatives(bids_dir, pipeline_name, subjects, sessions=None):
    """Create a mock derivatives folder within a BIDS dataset.
    
    Parameters
    ----------
    bids_dir : str
        Path to the BIDS dataset
    pipeline_name : str
        Name of the pipeline for the derivatives folder
    subjects : list
        List of subject IDs
    sessions : list, optional
        List of session IDs
        
    Returns
    -------
    str
        Path to the created derivatives folder
    """
    deriv_dir = os.path.join(bids_dir, "derivatives", pipeline_name)
    os.makedirs(deriv_dir, exist_ok=True)
    
    # Create dataset_description.json
    create_description_file(deriv_dir, pipeline_name)
    
    # Create mock data
    for sub in subjects:
        sub_dir = os.path.join(deriv_dir, f"sub-{sub}")
        
        if sessions:
            for ses in sessions:
                ses_dir = os.path.join(sub_dir, f"ses-{ses}")
                anat_dir = os.path.join(ses_dir, "anat")
                os.makedirs(anat_dir, exist_ok=True)
                
                # Create derivatives
                create_mock_nifti(
                    os.path.join(anat_dir, f"sub-{sub}_ses-{ses}_rec-{pipeline_name}_T2w.nii.gz")
                )
                create_mock_nifti(
                    os.path.join(anat_dir, f"sub-{sub}_ses-{ses}_rec-{pipeline_name}_mask.nii.gz")
                )
        else:
            # No sessions
            anat_dir = os.path.join(sub_dir, "anat")
            os.makedirs(anat_dir, exist_ok=True)
            
            # Create derivatives
            create_mock_nifti(
                os.path.join(anat_dir, f"sub-{sub}_rec-{pipeline_name}_T2w.nii.gz")
            )
            create_mock_nifti(
                os.path.join(anat_dir, f"sub-{sub}_rec-{pipeline_name}_mask.nii.gz")
            )
    
    return deriv_dir


def create_mock_nifti(filepath):
    """Create a small mock NIfTI file for testing.
    
    Parameters
    ----------
    filepath : str
        Path where the NIfTI file will be saved
    """
    # Create a small 3D array
    data = np.zeros((10, 10, 10), dtype=np.int16)
    data[3:7, 3:7, 3:7] = 1  # A small cube in the middle
    
    # Create and save the NIfTI file
    img = nib.Nifti1Image(data, np.eye(4))
    nib.save(img, filepath)


# Fixture for temporary directory
@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing and clean up afterwards."""
    tmp_dir = tempfile.mkdtemp(dir=os.getcwd())
    print(f"Created temporary directory: {tmp_dir}")
    yield tmp_dir
    # shutil.rmtree(tmp_dir)


# Tests for create_datasource
def test_create_datasource_all_subjects(temp_dir):
    """Test create_datasource with no filters (all subjects).
    
    This test verifies that create_datasource correctly finds all subjects
    and sessions in a BIDS dataset when no filters are applied.
    """
    # Create mock dataset with 3 subjects, 2 sessions each
    subjects = ["01", "02", "03"]
    sessions = ["01", "02"]
    
    bids_dir = create_mock_bids_dataset(temp_dir, subjects, sessions)
    
    # Define output query for T2w images
    output_query = {
        "stacks": {
            "datatype": "anat",
            "suffix": "T2w",
            "extension": ["nii", ".nii.gz"],
        }
    }
    
    # Create datasource without filters (all subjects)
    datasource = create_datasource(output_query, bids_dir)
    
    # Validate iterables
    iterables = datasource.iterables
    assert len(iterables) == 2
    assert iterables[0] == ("subject", "session", "acquisition")
    
    # Should have 6 combinations (3 subjects x 2 sessions)
    assert len(iterables[1]) == 6
    
    # Check that all expected combinations are present
    expected_combinations = []
    for sub in subjects:
        for ses in sessions:
            expected_combinations.append((sub, ses, None))
    
    for combo in expected_combinations:
        assert combo in iterables[1]


def test_create_datasource_specific_subjects(temp_dir):
    """Test create_datasource with specific subject filters.
    
    This test verifies that create_datasource correctly filters subjects
    when a list of subjects is provided.
    """
    # Create mock dataset with 3 subjects, 2 sessions each
    subjects = ["01", "02", "03"]
    sessions = ["01", "02"]
    
    bids_dir = create_mock_bids_dataset(temp_dir, subjects, sessions)
    
    # Define output query for T2w images
    output_query = {
        "stacks": {
            "datatype": "anat",
            "suffix": "T2w",
            "extension": ["nii", ".nii.gz"],
        }
    }
    
    # Create datasource with specific subject filter
    filter_subjects = ["01", "03"]
    datasource = create_datasource(output_query, bids_dir, subjects=filter_subjects)
    
    # Validate iterables
    iterables = datasource.iterables
    assert len(iterables) == 2
    assert iterables[0] == ("subject", "session", "acquisition")
    
    # Should have 4 combinations (2 subjects x 2 sessions)
    assert len(iterables[1]) == 4
    
    # Check that only the filtered combinations are present
    expected_combinations = []
    for sub in filter_subjects:
        for ses in sessions:
            expected_combinations.append((sub, ses, None))
    
    for combo in expected_combinations:
        assert combo in iterables[1]
    
    # Check that filtered out subjects are not present
    for ses in sessions:
        assert ("02", ses, None) not in iterables[1]


def test_create_datasource_with_acquisitions(temp_dir):
    """Test create_datasource with acquisitions.
    
    This test verifies that create_datasource correctly handles acquisitions
    when they are present in the dataset and filters.
    """
    # Create mock dataset with acquisitions
    subjects = ["01", "02"]
    sessions = ["01"]
    acquisitions = ["haste", "tru"]
    
    bids_dir = create_mock_bids_dataset(temp_dir, subjects, sessions, acquisitions)
    
    # Define output query for T2w images
    output_query = {
        "stacks": {
            "datatype": "anat",
            "suffix": "T2w",
            "extension": ["nii", ".nii.gz"],
        }
    }
    
    # Create datasource with specific acquisition filter
    filter_acquisitions = ["haste"]
    datasource = create_datasource(
        output_query, bids_dir, acquisitions=filter_acquisitions
    )
    
    # Validate iterables
    iterables = datasource.iterables
    assert len(iterables) == 2
    assert iterables[0] == ("subject", "session", "acquisition")
    
    # Should have 2 combinations (2 subjects x 1 session x 1 acquisition)
    assert len(iterables[1]) == 2
    
    # Check that only the filtered combinations are present
    expected_combinations = [
        ("01", "01", "haste"),
        ("02", "01", "haste")
    ]
    
    for combo in expected_combinations:
        assert combo in iterables[1]
    
    # Check that filtered out acquisitions are not present
    assert ("01", "01", "tru") not in iterables[1]
    assert ("02", "01", "tru") not in iterables[1]


def test_create_datasource_with_derivatives(temp_dir):
    """Test create_datasource with derivatives index.
    
    This test verifies that create_datasource correctly finds and indexes
    derivative data when index_derivative=True.
    """
    # Create mock dataset
    subjects = ["01", "02"]
    sessions = ["01"]
    
    bids_dir = create_mock_bids_dataset(temp_dir, subjects, sessions)
    
    # Create mock derivatives
    pipeline_name = "nesvor"
    create_mock_derivatives(bids_dir, pipeline_name, subjects, sessions)
    
    # Define output query for derivatives
    output_query = {
        "T2": {
            "datatype": "anat",
            "suffix": "T2w",
            "scope": pipeline_name,
            "extension": ["nii", ".nii.gz"],
        },
        "mask": {
            "datatype": "anat",
            "suffix": "mask",
            "scope": pipeline_name,
            "extension": ["nii", ".nii.gz"],
        }
    }
    
    # Create datasource with derivatives index
    datasource = create_datasource(
        output_query, bids_dir, subjects=subjects, sessions=sessions, 
        index_derivative=True, derivative=pipeline_name
    )
    
    # Validate iterables
    iterables = datasource.iterables
    assert len(iterables) == 2
    assert iterables[0] == ("subject", "session", "acquisition")
    
    # Should have 2 combinations (2 subjects x 1 session)
    assert len(iterables[1]) == 2
    
    # Check base_dir and index_derivatives settings
    assert datasource.inputs.base_dir == bids_dir
    assert datasource.inputs.index_derivatives == True
    
    # Check output_query
    assert datasource.inputs.output_query == output_query


def test_create_datasource_nonexistent_subject(temp_dir):
    """Test create_datasource with a non-existent subject.
    
    This test verifies that create_datasource handles non-existent subjects
    gracefully, excluding them from the iterables without error.
    """
    # Create mock dataset
    subjects = ["01", "02"]
    sessions = ["01"]
    
    bids_dir = create_mock_bids_dataset(temp_dir, subjects, sessions)
    
    # Define output query
    output_query = {
        "stacks": {
            "datatype": "anat",
            "suffix": "T2w",
            "extension": ["nii", ".nii.gz"],
        }
    }
    
    # Create datasource with non-existent subject
    filter_subjects = ["01", "03"]  # 03 doesn't exist
    
    # This should warn but not error
    datasource = create_datasource(
        output_query, bids_dir, subjects=filter_subjects
    )
    
    # Validate iterables - should only include existing subjects
    iterables = datasource.iterables
    assert len(iterables) == 2
    
    # Should only have combinations for subject 01
    expected_combinations = [("01", "01", None)]
    
    for combo in expected_combinations:
        assert combo in iterables[1]
    
    # Check that non-existent subject is not in iterables
    for ses in sessions:
        assert ("03", ses, None) not in iterables[1]


# Tests for create_bids_datasink
def test_create_bids_datasink_reconstruction(temp_dir):
    """Test create_bids_datasink for reconstruction step.
    
    This test verifies that create_bids_datasink correctly configures
    substitutions for reconstruction outputs in BIDS format.
    """
    # Create mock dataset
    subjects = ["01", "02"]
    sessions = ["01"]
    
    bids_dir = create_mock_bids_dataset(temp_dir, subjects, sessions)
    
    # Create datasink for reconstruction
    pipeline_name = "nesvor"
    datasink = create_bids_datasink(
        data_dir=bids_dir,
        pipeline_name=pipeline_name,
        step_name="reconstruction",
        subjects=subjects,
        sessions=sessions,
        name="recon_datasink",
        recon_method=pipeline_name
    )
    
    # Check that the datasink is properly configured
    assert isinstance(datasink, pe.Node)
    assert datasink.name == "recon_datasink"
    
    # Check substitutions for proper BIDS formatting
    subs = datasink.inputs.substitutions
    
    # Should have substitutions for each subject/session combination
    for sub in subjects:
        for ses in sessions:
            # Check for subject/session path mapping
            sub_ses_path = f"sub-{sub}/ses-{ses}/anat/sub-{sub}_ses-{ses}"
            assert any(sub_ses_path in s[1] for s in subs)
    
    # Check for proper file suffixes
    assert any(f"_rec-{pipeline_name}_T2w.nii.gz" in s[1] for s in subs)


def test_create_bids_datasink_segmentation(temp_dir):
    """Test create_bids_datasink for segmentation step.
    
    This test verifies that create_bids_datasink correctly configures
    substitutions for segmentation outputs in BIDS format.
    """
    # Create mock dataset
    subjects = ["01"]
    sessions = ["01"]
    
    bids_dir = create_mock_bids_dataset(temp_dir, subjects, sessions)
    
    # Create datasink for segmentation
    recon_method = "nesvor"
    seg_method = "bounti"
    datasink = create_bids_datasink(
        data_dir=bids_dir,
        pipeline_name=recon_method,
        step_name="segmentation",
        subjects=subjects,
        sessions=sessions,
        name="seg_datasink",
        recon_method=recon_method,
        seg_method=seg_method
    )
    
    # Check that the datasink is properly configured
    assert isinstance(datasink, pe.Node)
    assert datasink.name == "seg_datasink"
    
    # Check substitutions for proper BIDS formatting
    subs = datasink.inputs.substitutions
    
    # Should have substitutions for each subject/session combination
    for sub in subjects:
        for ses in sessions:
            # Check for subject/session path mapping
            sub_ses_path = f"sub-{sub}/ses-{ses}/anat/sub-{sub}_ses-{ses}"
            assert any(sub_ses_path in s[1] for s in subs)
    
    # Check for proper file suffixes for segmentation
    assert any(f"_rec-{recon_method}_seg-{seg_method}_dseg.nii.gz" in s[1] for s in subs)
    assert any(f"_rec-{recon_method}_seg-{seg_method}_labels.nii.gz" in s[1] for s in subs)


def test_create_bids_datasink_without_sessions(temp_dir):
    """Test create_bids_datasink without sessions.
    
    This test verifies that create_bids_datasink correctly handles datasets
    without sessions, maintaining proper BIDS format.
    """
    # Create mock dataset without sessions
    subjects = ["01", "02"]
    
    bids_dir = create_mock_bids_dataset(temp_dir, subjects)
    
    # Create datasink for reconstruction
    pipeline_name = "nesvor"
    datasink = create_bids_datasink(
        data_dir=bids_dir,
        pipeline_name=pipeline_name,
        step_name="reconstruction",
        subjects=subjects,
        name="recon_datasink",
        recon_method=pipeline_name
    )
    
    # Check substitutions for proper BIDS formatting
    subs = datasink.inputs.substitutions
    
    # Should have substitutions for each subject (no sessions)
    for sub in subjects:
        # Check for subject path mapping
        sub_path = f"sub-{sub}/anat/sub-{sub}"
        assert any(sub_path in s[1] for s in subs)
    
    # Check for proper file suffixes
    assert any(f"_rec-{pipeline_name}_T2w.nii.gz" in s[1] for s in subs)


def test_create_bids_datasink_preprocessing(temp_dir):
    """Test create_bids_datasink for preprocessing step.
    
    This test verifies that create_bids_datasink correctly configures
    substitutions for preprocessing outputs in BIDS format.
    """
    # Create mock dataset
    subjects = ["01"]
    sessions = ["01"]
    
    bids_dir = create_mock_bids_dataset(temp_dir, subjects, sessions)
    
    # Create datasink for preprocessing
    pipeline_name = "nesvor"
    datasink = create_bids_datasink(
        data_dir=bids_dir,
        pipeline_name=pipeline_name,
        step_name="preprocessing",
        subjects=subjects,
        sessions=sessions,
        name="preproc_datasink",
        recon_method=pipeline_name
    )
    
    # Check that the datasink is properly configured
    assert isinstance(datasink, pe.Node)
    assert datasink.name == "preproc_datasink"
    
    # Check substitutions for proper BIDS formatting
    subs = datasink.inputs.substitutions
    
    # For preprocessing, check for stacks and masks mappings
    assert any("stacks" in s[0] for s in subs)
    assert any("masks" in s[0] for s in subs)
    
    # Should map to subject/session/anat paths
    for sub in subjects:
        for ses in sessions:
            sub_ses_path = f"sub-{sub}/ses-{ses}/anat"
            assert any(sub_ses_path in s[1] for s in subs)


def test_bids_datasink_regexp_substitutions(temp_dir):
    """Test regex substitutions in create_bids_datasink.
    
    This test verifies that create_bids_datasink correctly configures
    regular expression substitutions for proper BIDS formatting.
    """
    # Create mock dataset
    subjects = ["01"]
    sessions = ["01"]
    
    bids_dir = create_mock_bids_dataset(temp_dir, subjects, sessions)
    
    # Create datasink
    pipeline_name = "nesvor"
    datasink = create_bids_datasink(
        data_dir=bids_dir,
        pipeline_name=pipeline_name,
        step_name="reconstruction",
        subjects=subjects,
        sessions=sessions,
        name="recon_datasink",
        recon_method=pipeline_name
    )
    
    # Check regex substitutions
    regex_subs = datasink.inputs.regexp_substitutions
    
    # Should handle double underscores
    assert any(r[0] == r"__+" for r in regex_subs)
    
    # Should fix file extensions if needed
    assert any(r"(\.nii\.gz)\.nii\.gz" in r[0] for r in regex_subs)
    
    # Should handle subject/session patterns in filenames
    assert any(r"(sub-[^/]+)/(ses-[^/]+)/(anat)/.*?(sub-[^/]+)_(ses-[^/]+)(.*\.nii\.gz)" in r[0] for r in regex_subs)


# Test utility functions
def test_mock_bids_dataset_creation(temp_dir):
    """Test that the mock BIDS dataset is created correctly.
    
    This test verifies that our mock dataset creation utility correctly
    creates a valid BIDS dataset structure.
    """
    # Create mock dataset
    subjects = ["01", "02"]
    sessions = ["01", "02"]
    acquisitions = ["haste"]
    
    bids_dir = create_mock_bids_dataset(temp_dir, subjects, sessions, acquisitions)
    
    # Check directory structure
    assert os.path.exists(bids_dir)
    assert os.path.exists(os.path.join(bids_dir, "dataset_description.json"))
    
    # Check subject directories
    for sub in subjects:
        sub_dir = os.path.join(bids_dir, f"sub-{sub}")
        assert os.path.exists(sub_dir)
        
        # Check session directories
        for ses in sessions:
            ses_dir = os.path.join(sub_dir, f"ses-{ses}")
            assert os.path.exists(ses_dir)
            
            # Check anat directory
            anat_dir = os.path.join(ses_dir, "anat")
            assert os.path.exists(anat_dir)
            
            # Check T2w files with acquisitions
            for acq in acquisitions:
                t2w_file = os.path.join(anat_dir, f"sub-{sub}_ses-{ses}_acq-{acq}_T2w.nii.gz")
                assert os.path.exists(t2w_file)
                
                # Check that the file is a valid NIfTI
                img = nib.load(t2w_file)
                assert img.shape == (10, 10, 10)


def test_mock_derivatives_creation(temp_dir):
    """Test that the mock derivatives are created correctly.
    
    This test verifies that our mock derivatives creation utility correctly
    creates a valid BIDS derivatives structure.
    """
    # Create mock dataset
    subjects = ["01"]
    sessions = ["01"]
    
    bids_dir = create_mock_bids_dataset(temp_dir, subjects, sessions)
    
    # Create mock derivatives
    pipeline_name = "nesvor"
    deriv_dir = create_mock_derivatives(bids_dir, pipeline_name, subjects, sessions)
    
    # Check directory structure
    assert os.path.exists(deriv_dir)
    assert os.path.exists(os.path.join(deriv_dir, "dataset_description.json"))
    
    # Check derivative files
    for sub in subjects:
        for ses in sessions:
            # Check derivative T2w and mask files
            t2w_file = os.path.join(
                deriv_dir, f"sub-{sub}", f"ses-{ses}", "anat",
                f"sub-{sub}_ses-{ses}_rec-{pipeline_name}_T2w.nii.gz"
            )
            mask_file = os.path.join(
                deriv_dir, f"sub-{sub}", f"ses-{ses}", "anat",
                f"sub-{sub}_ses-{ses}_rec-{pipeline_name}_mask.nii.gz"
            )
            
            assert os.path.exists(t2w_file)
            assert os.path.exists(mask_file)
            
            # Check that the files are valid NIfTIs
            assert nib.load(t2w_file).shape == (10, 10, 10)
            assert nib.load(mask_file).shape == (10, 10, 10)
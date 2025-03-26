# tests/test_utils_bids.py
import pytest
import re
from pathlib import Path # Import Path
import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio

# Adjust import path if necessary
try:
    from fetpype.utils.utils_bids import create_datasource, create_bids_datasink
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from fetpype.utils.utils_bids import create_datasource, create_bids_datasink


# --- Tests for create_datasource ---
# test_create_datasource_node_creation remains the same - PASSED

def test_create_datasource_default_iterables(mock_bids_root):
    """Test default iterable generation (all subs, ses, acq)."""
    output_query = {'T2w': {'datatype': 'anat', 'suffix': 'T2w'}}
    node = create_datasource(output_query, str(mock_bids_root))

    expected_iterable_name = ("subject", "session", "acquisition")
    # --- EXPECT BARE IDs ---
    expected_iterables_list_tuples = [
        ('01', '01', None),   # sub-01/ses-01 has file w/o acq
        ('01', '01', 'fast'), # sub-01/ses-01 has file w acq='fast'
        ('01', '02', None),   # sub-01/ses-02 has file w/o acq
        ('02', None, None),   # sub-02 has file w/o ses or acq
        ('02', None, 'slow'), # sub-02 has file w/o ses, w acq='slow'
        ('03', '01', 'fast'), # sub-03/ses-01 has file w acq='fast' (no non-acq file)
    ]
    # Sort for comparison robustness
    expected_iterables_list_tuples.sort()


    assert hasattr(node, 'iterables')
    iterables_names, iterables_values = node.iterables
    # Sort actual values too
    iterables_values.sort()

    assert iterables_names == expected_iterable_name
    assert iterables_values == expected_iterables_list_tuples


def test_create_datasource_specify_subjects(mock_bids_root):
    """Test providing a specific list of subjects."""
    output_query = {'T2w': {'datatype': 'anat', 'suffix': 'T2w'}}
    subjects = ['sub-01', 'sub-03'] # User provides full ID
    node = create_datasource(output_query, str(mock_bids_root), subjects=subjects)

    # --- EXPECT BARE IDs --- based on combinations for sub-01 and sub-03
    expected_iterables_list_tuples = [
        ('01', '01', None),
        ('01', '01', 'fast'),
        ('01', '02', None),
        # sub-02 skipped
        ('03', '01', 'fast'),
    ]
    expected_iterables_list_tuples.sort()

    _, iterables_values = node.iterables
    iterables_values.sort()
    assert iterables_values == expected_iterables_list_tuples

def test_create_datasource_specify_sessions(mock_bids_root):
    """Test providing a specific list of sessions."""
    output_query = {'T2w': {'datatype': 'anat', 'suffix': 'T2w'}}
    sessions = ['01'] # User provides bare ID
    node = create_datasource(output_query, str(mock_bids_root), sessions=sessions)

    # Expected: Apply ses='01' to all layout subjects ('01', '02', '03')
    # Get acqs for each combination or use [None]
    # Sub-01, Ses-01: layout_acqs=['fast'] -> ('01', '01', 'fast')
    # Sub-02: has no ses-01 in layout.
    #   Sub-02, Ses-01: layout_acqs=[] -> ('02', '01', None) # Warning printed
    # Sub-03, Ses-01: layout_acqs=['fast'] -> ('03', '01', 'fast')
    # --- EXPECT BARE IDs ---
    expected_iterables_list_tuples = [
        ('01', '01', 'fast'),
        ('02', '01', None), # Warning expected: Session 01 not found for subject 02
        ('03', '01', 'fast'),
    ]
    expected_iterables_list_tuples.sort()

    _, iterables_values = node.iterables
    iterables_values.sort()
    assert iterables_values == expected_iterables_list_tuples

def test_create_datasource_specify_acquisitions(mock_bids_root):
    """Test providing a specific list of acquisitions."""
    output_query = {'T2w': {'datatype': 'anat', 'suffix': 'T2w'}}
    acquisitions = ['fast', None] # User provides bare IDs/None
    node = create_datasource(output_query, str(mock_bids_root), acquisitions=acquisitions)

    # Expected: Apply acq=['fast', None] to all default sub/ses combinations
    # Sub-01, Ses-01: layout_acqs=['fast']. Iterate 'fast' (ok). Iterate None (warning). -> ('01', '01', 'fast'), ('01', '01', None)
    # Sub-01, Ses-02: layout_acqs=[]. Iterate 'fast' (warning). Iterate None (ok). -> ('01', '02', 'fast'), ('01', '02', None)
    # Sub-02, Ses=None: layout_acqs=['slow']. Iterate 'fast' (warning). Iterate None (ok). -> ('02', None, 'fast'), ('02', None, None)
    # Sub-03, Ses-01: layout_acqs=['fast']. Iterate 'fast' (ok). Iterate None (warning). -> ('03', '01', 'fast'), ('03', '01', None)
    # --- EXPECT BARE IDs ---
    expected_iterables_list_tuples = [
        ('01', '01', 'fast'),
        ('01', '01', None),   # Warning expected: Acq None not found
        ('01', '02', 'fast'), # Warning expected: Acq fast not found
        ('01', '02', None),
        ('02', None, 'fast'), # Warning expected: Acq fast not found
        ('02', None, None),
        ('03', '01', 'fast'),
        ('03', '01', None),   # Warning expected: Acq None not found
    ]
    expected_iterables_list_tuples.sort()

    _, iterables_values = node.iterables
    iterables_values.sort()
    assert iterables_values == expected_iterables_list_tuples

def test_create_datasource_specify_all(mock_bids_root):
    """Test providing subjects, sessions, and acquisitions."""
    output_query = {'T2w': {'datatype': 'anat', 'suffix': 'T2w'}}
    subjects = ['sub-01', 'sub-99'] # sub-99 doesn't exist
    sessions = ['01', '03']        # 03 doesn't exist for sub-01
    acquisitions = ['fast', 'other'] # other doesn't exist

    node = create_datasource(
        output_query,
        str(mock_bids_root),
        subjects=subjects,
        sessions=sessions,
        acquisitions=acquisitions
    )

    # Expected: Iterate combinations based on input lists. Check against layout.
    # Sub='01' (from 'sub-01')
    #   Ses='01': layout_acqs=['fast']
    #     Acq='fast' (ok) -> ('01', '01', 'fast')
    #     Acq='other' (warning) -> ('01', '01', 'other')
    #   Ses='03' (warning): layout_acqs=[]
    #     Acq='fast' (warning) -> ('01', '03', 'fast')
    #     Acq='other' (warning) -> ('01', '03', 'other')
    # Sub='99' (from 'sub-99') (warning: not in layout)
    #   Ses='01' (warning): layout_acqs=[]
    #     Acq='fast' (warning) -> ('99', '01', 'fast')
    #     Acq='other' (warning) -> ('99', '01', 'other')
    #   Ses='03' (warning): layout_acqs=[]
    #     Acq='fast' (warning) -> ('99', '03', 'fast')
    #     Acq='other' (warning) -> ('99', '03', 'other')
    # --- EXPECT BARE IDs ---
    expected_iterables_list_tuples = [
        ('01', '01', 'fast'),
        ('01', '01', 'other'),
        ('01', '03', 'fast'),
        ('01', '03', 'other'),
        ('99', '01', 'fast'),
        ('99', '01', 'other'),
        ('99', '03', 'fast'),
        ('99', '03', 'other'),
    ]
    expected_iterables_list_tuples.sort()

    _, iterables_values = node.iterables
    iterables_values.sort()
    assert iterables_values == expected_iterables_list_tuples


def test_create_datasource_derivatives(mock_bids_root):
    """Test using index_derivative (iterables should reflect raw dataset entities)."""
    # Add dataset_description.json to derivatives in fixture!
    deriv_desc = {"Name": "fmriprep derivative", "BIDSVersion": "1.6.0", "GeneratedBy": [{"Name": "fmriprep"}]}
    deriv_dir = mock_bids_root / "derivatives" / "fmriprep"
    import json
    with open(deriv_dir / "dataset_description.json", "w") as f:
        json.dump(deriv_desc, f)


    output_query = {'preproc': {'datatype': 'anat', 'desc': 'preproc'}}
    node = create_datasource(
        output_query,
        str(mock_bids_root),
        index_derivative=True, # Important!
    )

    expected_iterable_name = ("subject", "session", "acquisition")
    # Expect same iterables as default, based on RAW structure entities
    # --- EXPECT BARE IDs ---
    expected_iterables_list_tuples = [
        ('01', '01', None),
        ('01', '01', 'fast'),
        ('01', '02', None),
        ('02', None, None),
        ('02', None, 'slow'),
        ('03', '01', 'fast'),
    ]
    expected_iterables_list_tuples.sort()


    assert hasattr(node, 'iterables')
    iterables_names, iterables_values = node.iterables
    iterables_values.sort()

    assert iterables_names == expected_iterable_name
    assert iterables_values == expected_iterables_list_tuples
    assert node.inputs.index_derivatives is True # Check input propagation


# --- Tests for create_bids_datasink ---

def test_create_datasink_node_creation(mock_output_dir, mock_nipype_wf_dir):
    """Test basic node creation and input propagation."""
    out_dir = mock_output_dir
    pipeline_name = "my_pipeline"
    strip_dir = mock_nipype_wf_dir

    ds = create_bids_datasink(out_dir, pipeline_name, strip_dir)

    assert isinstance(ds, pe.Node)
    assert isinstance(ds.interface, nio.DataSink)
    assert ds.inputs.base_directory == out_dir
    assert ds.inputs.strip_dir == strip_dir
    assert ds.inputs.parameterization is True
    assert ds.name == f"{pipeline_name}_datasink" # Default name

def test_create_datasink_missing_strip_dir(mock_output_dir):
    """Test ValueError if strip_dir is missing."""
    with pytest.raises(ValueError, match="`strip_dir` .* required"):
        create_bids_datasink(mock_output_dir, "some_pipeline", strip_dir=None)
    with pytest.raises(ValueError, match="`strip_dir` .* required"):
        create_bids_datasink(mock_output_dir, "some_pipeline", strip_dir="")

# --- Tests simulating regex application ---

def apply_regex_subs(path_in, regex_subs):
    """Helper function to apply a list of regex substitutions."""
    path_out = path_in
    for pattern, replacement in regex_subs:
        path_out = re.sub(pattern, replacement, path_out)
    return path_out

def test_datasink_regex_simulation_preprocessing_denoised(mock_output_dir, mock_nipype_wf_dir):
    """Simulate renaming for preprocessing denoised file."""
    ds = create_bids_datasink(
        out_dir=mock_output_dir,
        pipeline_name="preprocessing",
        strip_dir=mock_nipype_wf_dir,
        desc_label="denoised",
        datatype="anat"
    )
    regex_subs = ds.inputs.regexp_substitutions

    in_path = f"{mock_output_dir}/_orig_filename_sub-01_ses-01_T2w.nii.gz/_session_01_subject_sub-01/denoise_wf/_denoising/sub-01_ses-01_T2w_noise_corrected.nii.gz"
    # EXPECTED FINAL PATH (after sub-sub- fix if any, etc.)
    expected_path = f"{mock_output_dir}/sub-01/ses-01/anat/sub-01_ses-01_T2w_desc-denoised_T2w.nii.gz"

    result_path = apply_regex_subs(in_path, regex_subs)
    assert result_path == expected_path

def test_datasink_regex_simulation_preprocessing_cropped(mock_output_dir, mock_nipype_wf_dir):
    """Simulate renaming for preprocessing cropped mask file."""
    ds = create_bids_datasink(
        out_dir=mock_output_dir,
        pipeline_name="preprocessing",
        strip_dir=mock_nipype_wf_dir,
        desc_label="cropped",
        datatype="anat"
    )
    regex_subs = ds.inputs.regexp_substitutions

    in_path = f"{mock_output_dir}/some_node/_session_01_subject_sub-01/crop_wf/_cropping/sub-01_ses-01_run-1_mask.nii"
    # EXPECTED FINAL PATH (keeps full base name from group \4, applies sub-sub fix)
    expected_path = f"{mock_output_dir}/sub-01/ses-01/anat/sub-01_ses-01_run-1_desc-cropped_mask.nii"

    result_path = apply_regex_subs(in_path, regex_subs)
    assert result_path == expected_path


def test_datasink_regex_simulation_reconstruction(mock_output_dir, mock_nipype_wf_dir):
    """Simulate renaming for reconstruction file."""
    ds = create_bids_datasink(
        out_dir=mock_output_dir,
        pipeline_name="nesvor",
        strip_dir=mock_nipype_wf_dir,
        rec_label="nesvor",
        datatype="anat"
    )
    regex_subs = ds.inputs.regexp_substitutions

    # Test with session
    in_path_ses = f"{mock_output_dir}/_session_02_subject_sub-01/recon_node/recon.nii.gz"
    # EXPECTED FINAL PATH (cleaned)
    expected_path_ses_cleaned = f"{mock_output_dir}/sub-01/ses-02/anat/sub-01_ses-02_rec-nesvor_T2w.nii.gz"
    result_path_ses = apply_regex_subs(in_path_ses, regex_subs)
    assert result_path_ses == expected_path_ses_cleaned

    # Test without session
    in_path_no_ses = f"{mock_output_dir}/_session_None_subject_sub-02/recon_node/recon.nii.gz"
    # EXPECTED FINAL PATH (cleaned, including _ses-None removal)
    expected_path_no_ses_cleaned = f"{mock_output_dir}/sub-02/anat/sub-02_rec-nesvor_T2w.nii.gz"
    result_path_no_ses = apply_regex_subs(in_path_no_ses, regex_subs)
    assert result_path_no_ses == expected_path_no_ses_cleaned

def test_datasink_regex_simulation_segmentation(mock_output_dir, mock_nipype_wf_dir):
    """Simulate renaming for segmentation file."""
    ds = create_bids_datasink(
        out_dir=mock_output_dir,
        pipeline_name="nesvor_bounti",
        strip_dir=mock_nipype_wf_dir,
        rec_label="nesvor",
        seg_label="bounti",
        datatype="anat"
    )
    regex_subs = ds.inputs.regexp_substitutions

    in_path = f"{mock_output_dir}/_session_01_subject_sub-01/seg_node/input_srr-mask-brain_bounti-19.nii.gz"
    # EXPECTED FINAL PATH (cleaned)
    expected_path = f"{mock_output_dir}/sub-01/ses-01/anat/sub-01_ses-01_rec-nesvor_seg-bounti_dseg.nii.gz"

    result_path = apply_regex_subs(in_path, regex_subs)
    assert result_path == expected_path

def test_datasink_regex_simulation_cleanup(mock_output_dir, mock_nipype_wf_dir):
    """Simulate only the cleanup rules."""
    ds = create_bids_datasink(
        out_dir=mock_output_dir,
        pipeline_name="cleanup_test",
        strip_dir=mock_nipype_wf_dir,
    )
    regex_subs = ds.inputs.regexp_substitutions # Contains only defaults (now fixed)

    # Test various cleanup scenarios
    assert apply_regex_subs("path///with__multiple///slashes_and__underscores.", regex_subs) == "path/with_multiple/slashes_and_underscores."
    assert apply_regex_subs("path/with_underscore_before_slash/_test", regex_subs) == "path/with_underscore_before_slash/test"
    # This one should now pass with the fixed rule
    assert apply_regex_subs("filename_before_dot_.nii.gz", regex_subs) == "filename_before_dot.nii.gz"
    assert apply_regex_subs("sub-01_ses-None_T2w.nii.gz", regex_subs) == "sub-01_T2w.nii.gz"
    # Test the /ses-None/ case
    assert apply_regex_subs("sub-01/ses-None/anat/file.nii", regex_subs) == "sub-01/anat/file.nii"
    assert apply_regex_subs("file.nii.nii", regex_subs) == "file.nii"
    assert apply_regex_subs("file.nii.gz.nii.gz", regex_subs) == "file.nii.gz"
    assert apply_regex_subs("path/with/trailing/slash/", regex_subs) == "path/with/trailing/slash"
    assert apply_regex_subs("multiple---hyphens", regex_subs) == "multiple-hyphens"
    # Test sub-sub / ses-ses cleanup
    assert apply_regex_subs("sub-sub-01/ses-ses-01/anat/sub-sub-01.nii", regex_subs) == "sub-01/ses-01/anat/sub-01.nii"
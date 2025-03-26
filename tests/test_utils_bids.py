# tests/test_utils_bids.py
import pytest
import re
import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
from fetpype.utils.utils_bids import create_datasource, create_bids_datasink


# --- Tests for create_datasource ---
def test_create_datasource_node_creation(mock_bids_root):
    """Test if the function returns a Nipype Node."""
    output_query = {'T2w': {'datatype': 'anat', 'suffix': 'T2w'}}
    node = create_datasource(output_query, str(mock_bids_root))
    assert isinstance(node, pe.Node)
    assert isinstance(node.interface, nio.BIDSDataGrabber)
    assert node.inputs.base_dir == str(mock_bids_root)
    assert node.inputs.output_query == output_query
    assert node.name == "bids_datasource" # Default name

def test_create_datasource_default_iterables(mock_bids_root):
    """Test default iterable generation (all subs, ses, acq)."""
    output_query = {'T2w': {'datatype': 'anat', 'suffix': 'T2w'}}
    node = create_datasource(output_query, str(mock_bids_root))

    expected_iterable_name = ("subject", "session", "acquisition")
    expected_iterables_list_tuples = [
        ('sub-01', '01', 'fast'),
        ('sub-01', '02', None),
        ('sub-02', None, 'slow'),
        ('sub-03', '01', 'fast'),
    ]

    assert hasattr(node, 'iterables')
    # Nipype stores iterables as (name_tuple, value_list)
    iterables_names, iterables_values = node.iterables
    assert iterables_names == expected_iterable_name
    # Convert to sets for comparison as order might not be guaranteed, although the code produces a specific order.
    # Let's stick to list comparison first, assuming deterministic order.
    assert iterables_values == expected_iterables_list_tuples


def test_create_datasource_specify_subjects(mock_bids_root):
    """Test providing a specific list of subjects."""
    output_query = {'T2w': {'datatype': 'anat', 'suffix': 'T2w'}}
    subjects = ['sub-01', 'sub-03']
    node = create_datasource(output_query, str(mock_bids_root), subjects=subjects)

    expected_iterables_list_tuples = [
        ('sub-01', '01', 'fast'),
        ('sub-01', '02', None),
        # sub-02 skipped
        ('sub-03', '01', 'fast'),
    ]
    _, iterables_values = node.iterables
    assert iterables_values == expected_iterables_list_tuples

def test_create_datasource_specify_sessions(mock_bids_root):
    """Test providing a specific list of sessions."""
    output_query = {'T2w': {'datatype': 'anat', 'suffix': 'T2w'}}
    # Note: This applies the session list to *all* subjects found/specified.
    sessions = ['01']
    node = create_datasource(output_query, str(mock_bids_root), sessions=sessions)

    expected_iterables_list_tuples = [
        ('sub-01', '01', 'fast'),
        ('sub-02', '01', None), # Will print warning in function: "Session 01 was not found for subject sub-02"
        ('sub-03', '01', 'fast'),
    ]
    _, iterables_values = node.iterables
    assert iterables_values == expected_iterables_list_tuples

def test_create_datasource_specify_acquisitions(mock_bids_root):
    """Test providing a specific list of acquisitions."""
    output_query = {'T2w': {'datatype': 'anat', 'suffix': 'T2w'}}
    # Note: This applies the acq list to *all* subjects/sessions found/specified.
    acquisitions = ['fast', None] # Test specifying None explicitly
    node = create_datasource(output_query, str(mock_bids_root), acquisitions=acquisitions)

    # Let's re-trace with the code's acq check: `if acq is not None and acq not in existing_acq:` -> prints warning, but still adds tuple!
    # Refined Expectation:
    expected_iterables_list_tuples = [
        ('sub-01', '01', 'fast'), # acq=fast exists
        ('sub-01', '01', None),   # acq=None does not exist explicitly (warning)
        ('sub-01', '02', 'fast'), # acq=fast does not exist (warning)
        ('sub-01', '02', None),   # acq=None exists implicitly
        ('sub-02', None, 'fast'), # acq=fast does not exist (warning)
        ('sub-02', None, None),   # acq=None exists implicitly
        ('sub-03', '01', 'fast'), # acq=fast exists
        ('sub-03', '01', None),   # acq=None does not exist explicitly (warning)
    ]

    _, iterables_values = node.iterables
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

    expected_iterables_list_tuples = [
        ('sub-01', '01', 'fast'),
        ('sub-01', '01', 'other'),
        ('sub-01', '03', 'fast'),
        ('sub-01', '03', 'other'),
        ('sub-99', '01', 'fast'),
        ('sub-99', '01', 'other'),
        ('sub-99', '03', 'fast'),
        ('sub-99', '03', 'other'),
    ]
    _, iterables_values = node.iterables
    assert iterables_values == expected_iterables_list_tuples


def test_create_datasource_derivatives(mock_bids_root):
    """Test using index_derivative (though function logic barely uses it for iterables)."""
    output_query = {'preproc': {'datatype': 'anat', 'desc': 'preproc'}}
    # We need to point data_dir to the raw dataset, BIDSLayout handles derivatives path
    node = create_datasource(
        output_query,
        str(mock_bids_root),
        index_derivative=True, # Important!
        # derivative='fmriprep' # This input is commented out in the function
    )

    expected_iterable_name = ("subject", "session", "acquisition")
    expected_iterables_list_tuples = [
        ('sub-01', '01', 'fast'),
        ('sub-01', '02', None),
        ('sub-02', None, 'slow'),
        ('sub-03', '01', 'fast'),
    ]

    assert hasattr(node, 'iterables')
    iterables_names, iterables_values = node.iterables
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
        strip_dir=mock_nipype_wf_dir, # This is only used by DataSink itself, not needed for simulation
        desc_label="denoised",
        datatype="anat"
    )
    regex_subs = ds.inputs.regexp_substitutions

    # Example path mimicking Nipype output within the base output dir
    # Note: Real paths would have the strip_dir prefix, but the regex patterns start matching
    # from the base_directory (out_dir) passed to datasink.
    in_path = f"{mock_output_dir}/_orig_filename_sub-01_ses-01_T2w.nii.gz/_session_01_subject_sub-01/denoise_wf/_denoising/sub-01_ses-01_T2w_noise_corrected.nii.gz"
    expected_path = f"{mock_output_dir}/sub-01/ses-01/anat/sub-01_ses-01_desc-denoised_T2w.nii.gz" # sub-sub fixed by cleanup

    # Simulate the full chain including cleanup
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
    expected_path = f"{mock_output_dir}/sub-01/ses-01/anat/sub-01_run-1_desc-cropped_mask.nii"

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
    expected_path_ses = f"{mock_output_dir}/sub-sub-01/ses-02/anat/sub-sub-01_ses-02_rec-nesvor_T2w.nii.gz"
    result_path_ses = apply_regex_subs(in_path_ses, regex_subs)
    expected_path_ses_cleaned = expected_path_ses.replace("sub-sub-", "sub-")
    assert result_path_ses == expected_path_ses_cleaned

    # Test without session (assuming _session_None pattern if generated by upstream)
    # The current regex might require _session_ explicitly. Let's test that path.
    # If upstream node folder is just _subject_sub-02, the recon regex won't match.
    # Let's assume upstream creates _session_None_subject_sub-02
    in_path_no_ses = f"{mock_output_dir}/_session_None_subject_sub-02/recon_node/recon.nii.gz"
    expected_path_no_ses = f"{mock_output_dir}/sub-02/anat/sub-02_ses-None_rec-nesvor_T2w.nii.gz"
    result_path_no_ses = apply_regex_subs(in_path_no_ses, regex_subs)

    assert result_path_no_ses == expected_path_no_ses

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
    regex_subs = ds.inputs.regexp_substitutions # Contains only defaults

    # Test various cleanup scenarios
    assert apply_regex_subs("path///with__multiple///slashes_and__underscores.", regex_subs) == "path/with_multiple/slashes_and_underscores."
    assert apply_regex_subs("path/with_underscore_before_slash/_test", regex_subs) == "path/with_underscore_before_slash/test"
    assert apply_regex_subs("filename_before_dot_.nii.gz", regex_subs) == "filename_before_dot.nii.gz"
    assert apply_regex_subs("sub-01_ses-None_T2w.nii.gz", regex_subs) == "sub-01_T2w.nii.gz"
    assert apply_regex_subs("file.nii.nii", regex_subs) == "file.nii"
    assert apply_regex_subs("file.nii.gz.nii.gz", regex_subs) == "file.nii.gz"
    assert apply_regex_subs("path/with/trailing/slash/", regex_subs) == "path/with/trailing/slash"
    assert apply_regex_subs("multiple---hyphens", regex_subs) == "multiple-hyphens"
import pytest
import re
import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio

from fetpype.utils.utils_bids import create_bids_datasink


# Helper for sorting lists containing None
def sort_key(item):
    # Treat None as an empty string for sorting purposes
    return tuple(
        "" if x is None else str(x) for x in item
    )  # Ensure all are strings or comparable


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
    assert ds.name == f"{pipeline_name}_datasink"


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


def test_datasink_regex_simulation_preprocessing_denoised(
    mock_output_dir, mock_nipype_wf_dir
):
    """Simulate renaming for preprocessing denoised file."""
    ds = create_bids_datasink(
        out_dir=mock_output_dir,
        pipeline_name="preprocessing",
        strip_dir=mock_nipype_wf_dir,
        desc_label="denoised",
        datatype="anat",
    )
    regex_subs = ds.inputs.regexp_substitutions

    # Test with session
    in_path = (
        f"{mock_output_dir}/preprocessing_wf/_session_01_subject_01_sub-01/"
        "denoise_wf/_denoising/sub-01_ses-01_run-1_T2w_noise_corrected.nii.gz"
    )

    expected_path = (
        f"{mock_output_dir}/sub-01_sub-01/ses-01/anat/"
        "sub-01_ses-01_run-1_desc-denoised_T2w.nii.gz"
    )

    result_path = apply_regex_subs(in_path, regex_subs)
    assert result_path == expected_path

    # Test without session
    in_path_no_ses = (
        f"{mock_output_dir}/preprocessing_wf/_subject_345MV11/"
        "denoise_wf/_denoising/sub-345MV11_run-1_T2w_noise_corrected.nii.gz"
    )
    expected_path_no_ses = (
        f"{mock_output_dir}/sub-345MV11/anat/"
        "sub-345MV11_run-1_desc-denoised_T2w.nii.gz"
    )
    result_path_no_ses = apply_regex_subs(in_path_no_ses, regex_subs)
    assert result_path_no_ses == expected_path_no_ses
    
    # Test with acquisition and with session
    in_path_ses_acq = (
        f"{mock_output_dir}/preprocessing_wf/"
        "_acquisition_trufi_session_12_subject_85/"
        "denoise_wf/_denoising/sub-85_ses-12_acq-trufi_run-1_T2w_noise_corrected.nii.gz"
    )
    expected_path_ses_acq = (
        f"{mock_output_dir}/sub-85/ses-12/anat/"
        "sub-85_ses-12_acq-trufi_run-1_desc-denoised_T2w.nii.gz"
    )
    result_path_ses_acq = apply_regex_subs(in_path_ses_acq, regex_subs)
    assert result_path_ses_acq == expected_path_ses_acq
    
    # Test with acquisition and without session
    in_path_no_ses_acq = (
        f"{mock_output_dir}/preprocessing_wf/"
        "_acquisition_36_subject_XPWZ/"
        "denoise_wf/_denoising/sub-XPWZ_acq-36_run-1_T2w_noise_corrected.nii.gz"
    )
    expected_path_no_ses_acq = (
        f"{mock_output_dir}/sub-XPWZ/anat/"
        "sub-XPWZ_acq-36_run-1_desc-denoised_T2w.nii.gz"
    )
    result_path_no_ses_acq = apply_regex_subs(in_path_no_ses_acq, regex_subs)
    assert result_path_no_ses_acq == expected_path_no_ses_acq


def test_datasink_regex_simulation_preprocessing_cropped(
    mock_output_dir, mock_nipype_wf_dir
):
    """Simulate renaming for preprocessing cropped mask file."""
    ds = create_bids_datasink(
        out_dir=mock_output_dir,    
        pipeline_name="preprocessing",
        strip_dir=mock_nipype_wf_dir,
        desc_label="cropped",
        datatype="anat",
    )
    regex_subs = ds.inputs.regexp_substitutions

    # Test with session
    in_path = (
        f"{mock_output_dir}/preprocessing_wf/_session_01_subject_sub-01/"
        "crop_wf/_cropping/sub-01_ses-01_run-1_mask.nii"
    )
    expected_path = (
        f"{mock_output_dir}/sub-01/ses-01/anat/"
        "sub-01_ses-01_run-1_desc-cropped_mask.nii"
    )

    result_path = apply_regex_subs(in_path, regex_subs)
    assert result_path == expected_path

    # Test without session
    in_path_no_ses = (
        f"{mock_output_dir}/preprocessing_wf/_subject_33PJ7/"
        "crop_wf/_cropping/sub-33PJ7_run-1_mask.nii"
    )
    expected_path_no_ses = (
        f"{mock_output_dir}/sub-33PJ7/anat/"
        "sub-33PJ7_run-1_desc-cropped_mask.nii"
    )
    result_path_no_ses = apply_regex_subs(in_path_no_ses, regex_subs)
    assert result_path_no_ses == expected_path_no_ses

    # Test with acquisition and with session
    in_path_ses_acq = (
        f"{mock_output_dir}/preprocessing_wf/"
        "_acquisition_haste_session_66_subject_sub-27/"
        "crop_wf/_cropping/sub-27_ses-66_acq-haste_run-1_mask.nii"
    )
    expected_path_ses_acq = (
        f"{mock_output_dir}/sub-27/ses-66/anat/"
        "sub-27_ses-66_acq-haste_run-1_desc-cropped_mask.nii"
    )
    result_path_ses_acq = apply_regex_subs(in_path_ses_acq, regex_subs)
    assert result_path_ses_acq == expected_path_ses_acq

    # Test with acquisition and without session
    in_path_no_ses_acq = (
        f"{mock_output_dir}/preprocessing_wf/"
         "_acquisition_22_subject_0027/"
         "crop_wf/_cropping/sub-0027_acq-22_run-1_mask.nii"
    )
    expected_path_no_ses_acq = (
        f"{mock_output_dir}/sub-0027/anat/"
        "sub-0027_acq-22_run-1_desc-cropped_mask.nii"
    )
    result_path_no_ses_acq = apply_regex_subs(in_path_no_ses_acq, regex_subs)
    assert result_path_no_ses_acq == expected_path_no_ses_acq



def test_datasink_regex_simulation_reconstruction(
    mock_output_dir, mock_nipype_wf_dir
):
    """Simulate renaming for reconstruction file."""
    ds = create_bids_datasink(
        out_dir=mock_output_dir,
        pipeline_name="nesvor",  # This means Rule 3 is active
        strip_dir=mock_nipype_wf_dir,
        rec_label="nesvor",
        datatype="anat",
    )
    regex_subs = ds.inputs.regexp_substitutions

    # Test with session
    in_path_ses = (
        f"{mock_output_dir}/nesvor_pipeline_wf/"
        "_session_02_subject_sub-01/recon_node/recon.nii.gz"
    )
    expected_path_ses_cleaned = (
        f"{mock_output_dir}/sub-01/ses-02/anat/"
        "sub-01_ses-02_rec-nesvor_T2w.nii.gz"
    )
    result_path_ses = apply_regex_subs(in_path_ses, regex_subs)
    assert result_path_ses == expected_path_ses_cleaned

    # Test without session
    in_path_no_ses = (
        f"{mock_output_dir}/nesvor_pipeline_wf/_session_None_subject_sub-02/"
        "recon_node/recon.nii.gz"
    )
    # Expected path after substitutions (Rule 3 + cleanup rules in function)
    expected_path_no_ses_cleaned = (
        f"{mock_output_dir}/sub-02/ses-None/anat/sub-02_rec-nesvor_T2w.nii.gz"
    )
    result_path_no_ses = apply_regex_subs(in_path_no_ses, regex_subs)
    assert result_path_no_ses == expected_path_no_ses_cleaned

    # Test with acquisition and with session
    in_path_ses_acq = (
        f"{mock_output_dir}/nesvor_pipeline_wf/"
        "_acquisition_522_session_36_subject_55/recon_node/recon.nii.gz"
    )
    expected_path_ses_acq = (
        f"{mock_output_dir}/sub-55/ses-36/anat/sub-55_ses-36_acq-522_rec-nesvor_T2w.nii.gz"
    )
    result_path_ses_acq = apply_regex_subs(in_path_ses_acq, regex_subs)
    assert result_path_ses_acq == expected_path_ses_acq

    # Test with acquisition and without session
    in_path_no_ses_acq = (
        f"{mock_output_dir}/nesvor_pipeline_wf/"
        "_acquisition_haste_subject_CX5/recon_node/recon.nii.gz"
    )
    expected_path_no_ses_acq = (
        f"{mock_output_dir}/sub-CX5/anat/sub-CX5_acq-haste_rec-nesvor_T2w.nii.gz"
    )
    result_path_no_ses_acq = apply_regex_subs(in_path_no_ses_acq, regex_subs)
    assert result_path_no_ses_acq == expected_path_no_ses_acq


def test_datasink_regex_simulation_segmentation(
    mock_output_dir, mock_nipype_wf_dir
):
    """Simulate renaming for segmentation file."""
    ds = create_bids_datasink(
        out_dir=mock_output_dir,
        pipeline_name="nesvor_bounti",  # This means Rule 4 is active
        strip_dir=mock_nipype_wf_dir,
        rec_label="nesvor",
        seg_label="bounti",
        datatype="anat",
    )
    regex_subs = ds.inputs.regexp_substitutions

    # Test with session
    in_path = (
        f"{mock_output_dir}/segmentation_wf/_session_01_subject_sub-01/"
        "seg_node/input_srr-mask-brain_bounti-19.nii.gz"
    )
    expected_path = (
        f"{mock_output_dir}/sub-01/ses-01/anat/"
        "sub-01_ses-01_rec-nesvor_seg-bounti_dseg.nii.gz"
    )

    result_path = apply_regex_subs(in_path, regex_subs)
    assert result_path == expected_path

    # Test without session
    in_path_no_ses = (
        f"{mock_output_dir}/segmentation_wf/_subject_MV1/"
        "seg_node/input_srr-mask-brain_bounti-19.nii.gz"
    )
    expected_path_no_ses = (
        f"{mock_output_dir}/sub-MV1/anat/"
        "sub-MV1_rec-nesvor_seg-bounti_dseg.nii.gz"
    )
    result_path_no_ses = apply_regex_subs(in_path_no_ses, regex_subs)
    assert result_path_no_ses == expected_path_no_ses

    # Test with acquisition and with session
    in_path_ses_acq = (
        f"{mock_output_dir}/segmentation_wf/"
        "_acquisition_trufi_session_33_subject_687/"
        "seg_node/input_srr-mask-brain_bounti-19.nii.gz"
    )
    expected_path_ses_acq = (
        f"{mock_output_dir}/sub-687/ses-33/anat/"
        "sub-687_ses-33_acq-trufi_rec-nesvor_seg-bounti_dseg.nii.gz"
    )
    result_path_ses_acq = apply_regex_subs(in_path_ses_acq, regex_subs)
    assert result_path_ses_acq == expected_path_ses_acq
    
    # Test with acquisition and without session
    in_path_no_ses_acq = (
        f"{mock_output_dir}/segmentation_wf/" 
        "_acquisition_35_subject_sub-M23CXX21/"
        "seg_node/input_srr-mask-brain_bounti-19.nii.gz"
    )
    expected_path_no_ses_acq = (
        f"{mock_output_dir}/sub-M23CXX21/anat/"
        "sub-M23CXX21_acq-35_rec-nesvor_seg-bounti_dseg.nii.gz"
    )
    result_path_no_ses_acq = apply_regex_subs(in_path_no_ses_acq, regex_subs)
    assert result_path_no_ses_acq == expected_path_no_ses_acq


def test_datasink_regex_simulation_cleanup(
    mock_output_dir, mock_nipype_wf_dir
):
    """Simulate only the cleanup rules."""
    ds = create_bids_datasink(
        out_dir=mock_output_dir,
        pipeline_name="cleanup_test",  # Name doesn't trigger special rules
        strip_dir=mock_nipype_wf_dir,
    )
    regex_subs = ds.inputs.regexp_substitutions

    # Test various cleanup scenarios
    assert (
        apply_regex_subs(
            "path///with__multiple///slashes_and__underscores.", regex_subs
        )
        == "path/with_multiple/slashes_and_underscores."
    )
    assert (
        apply_regex_subs("path/with_underscore_before_slash/_test", regex_subs)
        == "path/with_underscore_before_slash/test"
    )
    assert (
        apply_regex_subs("sub-01_ses-None_T2w.nii.gz", regex_subs)
        == "sub-01_T2w.nii.gz"
    )
    # Test the /ses-None/ case
    # NO rule exists to clean this up in the function
    assert (
        apply_regex_subs("sub-01/ses-None/anat/file.nii", regex_subs)
        == "sub-01/ses-None/anat/file.nii"
    )
    assert apply_regex_subs("file.nii.nii", regex_subs) == "file.nii"
    assert apply_regex_subs("file.nii.gz.nii.gz", regex_subs) == "file.nii.gz"
    assert (
        apply_regex_subs("path/with/trailing/slash/", regex_subs)
        == "path/with/trailing/slash"
    )
    assert (
        apply_regex_subs("multiple---hyphens", regex_subs)
        == "multiple-hyphens"
    )
    # Test sub-sub / ses-ses cleanup
    assert (
        apply_regex_subs(
            "sub-sub-01/ses-ses-01/anat/sub-sub-01.nii", regex_subs
        )
        == "sub-01/ses-01/anat/sub-01.nii"
    )
    # Test acq-acq cleanup
    assert (
            apply_regex_subs(
                "sub-sub-12MC3/anat/sub-sub-12MC3_acq-acq-trufi.nii", regex_subs
            )
            == "sub-12MC3/anat/sub-12MC3_acq-trufi.nii"
        )
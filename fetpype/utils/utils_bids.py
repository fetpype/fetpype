import os.path as op

import json
import os
from bids.layout import BIDSLayout

import nipype.interfaces.io as nio
import nipype.pipeline.engine as pe
from omegaconf import OmegaConf
import re


def create_datasource(
    output_query,
    data_dir,
    nipype_dir,
    subjects=None,
    sessions=None,
    acquisitions=None,
    derivative=None,
    name="bids_datasource",
    extra_derivatives=None,
    save_db=False,
):
    """Create a datasource node that have iterables following BIDS format.
    By default, from a BIDSLayout, lists all the subjects (`<sub>`),
    finds their session numbers (`<ses>`, if any) and their acquisition
    type (`<acq>`, if any), and builds an iterable of tuples
    (sub, ses, acq) with all valid combinations.

    If a list of subjects/sessions/acquisitions is provided, the
    BIDSLayout is not queried and the provided
    subjects/sessions/acquisitions are used as is.

    If derivative is not None, the BIDSLayout will be queried for
    the specified derivative.

    For example, if provided with subjects=["sub01", "sub02"],
    sessions=["01"], acq=["haste", "tru"], the datagrabber will
    attempt at retrieving all of the following combinations:
    ```
    [("sub01", "01", "haste"), ("sub01", "01","tru"),
     ("sub02", "01", "haste"), ("sub02", "01","tru")]
    ```

    Args:
        output_query (dict): A dictionary specifying the output query
            for the BIDSDataGrabber.
        data_dir (str): The base directory of the BIDS dataset.
        subjects (list, optional): List of subject IDs to include.
            If None, all subjects in the dataset are included.
        sessions (list, optional): List of session IDs to include.
            If None, all sessions for each subject are included.
        acquisitions (list, optional): List of acquisition types to include.
            If None, all acquisitions for each subject/session are included.
        derivative (str, optional): The name of the derivative to query.
            If None, no derivative is queried.
        name (str, optional): Name for the datasource node. Defaults to
                            "bids_datasource".
        extra_derivatives (list or str, optional): Additional
            derivatives to include. If provided, these will be
            added to the BIDSDataGrabber.
    Returns:
        pe.Node: A configured BIDSDataGrabber node that retrieves data
        according to the specified parameters.
    """

    bids_datasource = pe.Node(
        interface=nio.BIDSDataGrabber(),
        name=name,
        synchronize=True,
    )

    bids_datasource.inputs.base_dir = data_dir
    if extra_derivatives is not None:
        bids_datasource.inputs.index_derivatives = True
        if isinstance(extra_derivatives, str):
            extra_derivatives = [extra_derivatives]
        bids_datasource.inputs.extra_derivatives = extra_derivatives
    bids_datasource.inputs.output_query = output_query

    layout = BIDSLayout(data_dir, validate=False)

    # Needed as the layout uses validate which
    # does not work with our segmentation files.

    if save_db:
        layout_db = os.path.join(nipype_dir, "layout_db")
        if os.path.exists(layout_db):
            os.remove(os.path.join(layout_db, "layout_index.sqlite"))
        layout.save(layout_db)

        bids_datasource.inputs.load_layout = layout_db

    # Verbose
    print("BIDS layout:", layout)
    print("\t", layout.get_subjects())
    print("\t", layout.get_sessions())
    iterables = [("subject", "session", "acquisition"), []]

    existing_sub = layout.get_subjects()
    if subjects is None:
        subjects = existing_sub

    for sub in subjects:
        if sub not in existing_sub:
            raise ValueError(
                f"Requested subject {sub} was not found in the " f"folder {data_dir}."
            )

        existing_ses = layout.get_sessions(subject=sub)
        if sessions is None:
            sessions_subj = existing_ses
        else:
            sessions_subj = sessions
        # If no sessions are found, it is possible that there is no session.
        sessions_subj = [None] if len(sessions_subj) == 0 else sessions_subj
        for ses in sessions_subj:
            if ses is not None and ses not in existing_ses:
                print(f"WARNING: Session {ses} was not found for subject {sub}.")
            existing_acq = layout.get_acquisition(subject=sub, session=ses)
            if acquisitions is None:
                acquisitions_subj = existing_acq
            else:
                acquisitions_subj = acquisitions
            # If there is no acquisition found, maybe the acquisition
            # tag was not specified.
            acquisitions_subj = (
                [None] if len(acquisitions_subj) == 0 else acquisitions_subj
            )
            for acq in acquisitions_subj:
                if acq is not None and acq not in existing_acq:
                    print(
                        f"WARNING: Acquisition {acq} was not found for "
                        f"subject {sub} session {ses}."
                    )

                iterables[1] += [(sub, ses, acq)]

    bids_datasource.iterables = iterables

    return bids_datasource


def create_bids_datasink(
    out_dir,
    pipeline_name,
    strip_dir,
    datatype="anat",
    name=None,
    rec_label=None,
    seg_label=None,
    surf_label=None,
    desc_label=None,
    custom_subs=None,
    custom_regex_subs=None,
):
    """
    Creates a BIDS-compatible datasink using parameterization and
    regex substitutions.
    Organizes outputs into:
    <out_dir>/derivatives/<pipeline_name>/sub-<ID>/[ses-<ID>/]
    <datatype>/<BIDS_filename>
    """
    if not strip_dir:
        raise ValueError("`strip_dir` (Nipype work dir base path) is required.")
    if name is None:
        name = f"{pipeline_name}_datasink"

    datasink = pe.Node(
        nio.DataSink(
            base_directory=out_dir, parameterization=True, strip_dir=strip_dir
        ),
        name=name,
    )

    regex_subs = []

    bids_derivatives_root = out_dir  # we already pass the bids derivatives
    escaped_bids_derivatives_root = re.escape(out_dir)

    if pipeline_name == "preprocessing":
        # ** Rule 1: Preprocessing Stacks (Denoised) **
        if desc_label == "denoised":
            # with session
            regex_subs.append(
                (
                    (
                        rf"^{escaped_bids_derivatives_root}/"
                        rf".*?_?session_([^/]+)"
                        rf"_subject_([^/]+).*?/?_denoising.*/"
                        rf"(sub-[^_]+_ses-[^_]+(?:_run-\d+))?"
                        rf"_T2w_noise_corrected(\.nii(?:\.gz)?)$"
                    ),
                    (
                        rf"{bids_derivatives_root}/sub-\2/ses-\1/{datatype}"
                        rf"/\3_desc-denoised_T2w\4"
                    ),
                )
            )
            # without session
            regex_subs.append(
                (
                    (
                        rf"^{escaped_bids_derivatives_root}/"
                        rf"(?!.*?_?session_[^/]+).*?_?subject_([^/]+).*?/"
                        rf"?_denoising.*/"
                        rf"(sub-[^_]+(?:_run-\d+)?)?_?"
                        rf"T2w_noise_corrected(\.nii(?:\.gz)?)$"
                    ),
                    (
                        rf"{bids_derivatives_root}/sub-\1/{datatype}"
                        rf"/\2_desc-denoised_T2w\3"
                    ),
                )
            )

        # ** Rule 2: Preprocessing Masks (Cropped) **
        if desc_label == "cropped":
            # with session
            regex_subs.append(
                (
                    (
                        rf"^{escaped_bids_derivatives_root}/.*?_session_"
                        rf"([^/]+)_subject_([^/]+).*/?_cropping.*/"
                        rf"(sub-[^_]+_ses-[^_]+(?:_run-\d+)?)_"
                        rf"mask(\.nii(?:\.gz)?)$"
                    ),
                    (
                        rf"{bids_derivatives_root}/sub-\2/ses-\1/{datatype}"
                        rf"/\3_desc-cropped_mask\4"
                    ),
                )
            )
            # without session
            regex_subs.append(
                (
                    (
                        rf"^{escaped_bids_derivatives_root}/"
                        rf"(?!.*?_session_[^/]+).*?_subject_"
                        rf"([^/]+).*/?_cropping.*/"
                        rf"(sub-[^_]+(?:_run-\d+)?)_mask(\.nii(?:\.gz)?)$"
                    ),
                    (
                        rf"{bids_derivatives_root}/sub-\1/{datatype}"
                        rf"/\2_desc-cropped_mask\3"
                    ),
                )
            )

    # ** Rule 3: Reconstruction Output **
    if rec_label and not seg_label and pipeline_name != "preprocessing":
        # with session
        regex_subs.append(
            (
                (
                    rf"^{escaped_bids_derivatives_root}/.*?_?session_([^/]+)"
                    rf"_subject_([^/]+).*/(?:[^/]+)(\.nii(?:\.gz)?)$"
                ),
                (
                    rf"{bids_derivatives_root}/sub-\2/ses-\1/"
                    rf"{datatype}/sub-\2_ses-\1_rec-{rec_label}_T2w\3"
                ),
            )
        )
        # without session
        regex_subs.append(
            (
                (
                    rf"^{escaped_bids_derivatives_root}/(?!.*?_?session_[^/]+)"
                    rf".*?_?subject_"
                    rf"([^/]+).*/(?:[^/]+)(\.nii(?:\.gz)?)$"
                ),
                (
                    rf"{bids_derivatives_root}/sub-\1/"
                    rf"{datatype}/sub-\1_rec-{rec_label}_T2w\2"
                ),
            )
        )

    # ** Rule 4: Segmentation Output **
    if seg_label and rec_label and pipeline_name != "preprocessing":
        # with session
        regex_subs.append(
            (
                (
                    rf"^{escaped_bids_derivatives_root}/"
                    rf".*?_?session_([^/]+)_subject_([^/]+).*/"
                    rf"input_srr-mask-brain_bounti-19(\.nii(?:\.gz)?)$"
                ),
                (
                    rf"{bids_derivatives_root}/sub-\2/ses-\1/{datatype}/"
                    rf"sub-\2_ses-\1_rec-{rec_label}_seg-{seg_label}_dseg\3"
                ),
            )
        )
        # without session
        regex_subs.append(
            (
                (
                    rf"^{escaped_bids_derivatives_root}/(?!.*?_?session_[^/]+)"
                    rf".*?_?subject_([^/]+).*/"
                    rf"input_srr-mask-brain_bounti-19(\.nii(?:\.gz)?)$"
                ),
                (
                    rf"{bids_derivatives_root}/sub-\1/{datatype}/"
                    rf"sub-\1_rec-{rec_label}_seg-{seg_label}_dseg\2"
                ),
            )
        )
    # ** Rule 4.5: Segmentation Output FetalSynthSeg **
    if seg_label == "fetalsynthseg" and rec_label and pipeline_name != "preprocessing":
        # with session
        regex_subs.append(
            (
                (
                    rf"^{escaped_bids_derivatives_root}/"
                    rf".*?_?session_([^/]+)_subject_([^/]+).*/"
                    rf"seg-drifts_pred(\.nii(?:\.gz)?)$"
                ),
                (
                    rf"{bids_derivatives_root}/sub-\2/ses-\1/{datatype}/"
                    rf"sub-\2_ses-\1_rec-{rec_label}_seg-{seg_label}_dseg\3"
                ),
            )
        )
        # without session
        regex_subs.append(
            (
                (
                    rf"^{escaped_bids_derivatives_root}/(?!.*?_?session_[^/]+)"
                    rf".*?_?subject_([^/]+).*/"
                    rf"seg-drifts_pred(\.nii(?:\.gz)?)$"
                ),
                (
                    rf"{bids_derivatives_root}/sub-\1/{datatype}/"
                    rf"sub-\1_rec-{rec_label}_seg-{seg_label}_dseg\2"
                ),
            )
        )
    # ** Rule 5: Surface outputs (.gii) **
    if surf_label:
        label = f"_rec-{rec_label}" if rec_label else ""
        label += f"_seg-{seg_label}" if seg_label else ""
        # with session
        regex_subs.append(
            (
                (
                    rf"^{escaped_bids_derivatives_root}/"
                    rf".*?_?session_([^/]+)_subject_([^/]+).*/"
                    rf"([^/]+)\.gii$"
                ),
                (
                    rf"{bids_derivatives_root}/sub-\2/ses-\1/{datatype}/"
                    rf"sub-\2_ses-\1{label}_\3.gii"
                ),
            )
        )
        # without session
        regex_subs.append(
            (
                (
                    rf"^{escaped_bids_derivatives_root}/(?!.*?_?session_[^/]+)"
                    rf".*?_?subject_([^/]+).*/"
                    rf"([^/]+)\.gii$"
                ),
                (
                    rf"{bids_derivatives_root}/sub-\1/{datatype}/"
                    rf"sub-\1{label}_\2.gii"
                ),
            )
        )

        # ** Rule 6: Surface outputs (.stl) **
        # with session
        regex_subs.append(
            (
                (
                    rf"^{escaped_bids_derivatives_root}/"
                    rf".*?_?session_([^/]+)_subject_([^/]+).*/"
                    rf"([^/]+)\.stl$"
                ),
                (
                    rf"{bids_derivatives_root}/sub-\2/ses-\1/{datatype}/"
                    rf"sub-\2_ses-\1{label}_\3.stl"
                ),
            )
        )
        # without session
        regex_subs.append(
            (
                (
                    rf"^{escaped_bids_derivatives_root}/(?!.*?_?session_[^/]+)"
                    rf".*?_?subject_([^/]+).*/"
                    rf"([^/]+)\.stl$"
                ),
                (
                    rf"{bids_derivatives_root}/sub-\1/{datatype}/"
                    rf"sub-\1{label}_\2.stl"
                ),
            )
        )

    # --- Generic cleanup rules (unchanged, but keep them
    # after the mapping rules) ---
    regex_subs.extend(
        [
            (r"sub-sub-", r"sub-"),
            (r"ses-ses-", r"ses-"),
            (r"_+", "_"),
            (r"(/)_", r"\1"),
            (r"(_)\.", r"\."),
            (r"-+", "-"),
            (r"//+", "/"),
            (r"[\\/]$", ""),
            (r"_ses-None", ""),  # in case something injected a None
            (r"(\.nii\.gz)\1+$", r"\1"),
            (r"(\.nii)\1+$", r"\1"),
        ]
    )

    # Add custom regex substitutions
    if custom_regex_subs:
        regex_subs.extend(custom_regex_subs)

    datasink.inputs.regexp_substitutions = regex_subs

    # Add custom simple substitutions
    final_subs = []
    if custom_subs:
        final_subs.extend(custom_subs)
    datasink.inputs.substitutions = final_subs

    return datasink


def create_datasink(iterables, name="output", params_subs={}, params_regex_subs={}):
    """
    Deprecated. Creates a data sink node for reformatting and organizing
    relevant outputs.

    From: https://github.com/Macatools/macapype (adapted)

    Args:
        iterables (list or tuple): A collection of iterables, containing
                                   subject and session information.
        name (str, optional): The name for the data sink container.
                              Defaults to "output".
        params_subs (dict, optional): A dictionary of parameter substitutions
                                      to apply to output paths. Defaults to
                                      an empty dictionary.
        params_regex_subs (dict, optional): A dictionary of regular
                                            expression-based substitutions
                                            to apply to output paths.
                                            Defaults to an empty dictionary.

    Returns:
        pe.Node: A Pipeline Engine Node representing the configured datasink.
    """

    print("Datasink name: ", name)

    # Create the datasink node
    datasink = pe.Node(nio.DataSink(), name=name)

    # Generate subject folders with session and subject information
    subjFolders = [
        (
            "_acquisition_%s_session_%s_subject_%s" % (acq, ses, sub),
            "sub-%s/ses-%s/anat" % (sub, ses),
        )
        for (sub, ses, acq) in iterables[1]  # doublecheck
    ]

    print("subjFolders: ", subjFolders)

    # Load parameter substitutions from the 'subs.json' file
    json_subs = op.join(op.dirname(op.abspath(__file__)), "subs.json")
    dict_subs = json.load(open(json_subs, encoding="utf-8"))
    dict_subs.update(params_subs)  # Override with any provided substitutions

    subs = [(key, value) for key, value in dict_subs.items()]
    subjFolders.extend(subs)  # Add parameter substitutions to folders

    datasink.inputs.substitutions = subjFolders

    # Load regex-based substitutions from the 'regex_subs.json' file
    json_regex_subs = op.join(op.dirname(op.abspath(__file__)), "regex_subs.json")
    dict_regex_subs = json.load(open(json_regex_subs, encoding="utf-8"))

    # Update with provided regex substitutions
    dict_regex_subs.update(params_regex_subs)

    regex_subs = [(key, value) for key, value in dict_regex_subs.items()]
    datasink.inputs.regexp_substitutions = regex_subs

    return datasink


def get_gestational_age(bids_dir, T2):
    """
    Retrieve the gestational age for a specific subject from a BIDS dataset.

    Args:
        bids_dir : The file path to the root of the BIDS dataset,
            which must contain a 'participants.tsv' file.
        T2 : The path of the image. We can get the subject id from there if
            it follows a BIDS format.
    Returns:
        gestational_age : The gestational age of the subject.

    """
    import pandas as pd
    import os

    participants_path = f"{bids_dir}/participants.tsv"

    try:
        df = pd.read_csv(participants_path, delimiter="\t")
    except FileNotFoundError:
        raise FileNotFoundError(f"participants.tsv not found in {bids_dir}")

    # TODO This T2[0] not really clean
    subject_id = os.path.basename(T2).split("_")[0]
    try:
        gestational_age = df.loc[
            df["participant_id"] == f"{subject_id}", "gestational_age"
        ].values[0]
    except KeyError:
        raise KeyError("Column 'gestational_age' not found in participants.tsv")
    except IndexError:
        raise IndexError(f"Subject sub-{subject_id} not found in participants.tsv")

    return gestational_age


def create_description_file(out_dir, algo, prev_desc=None, cfg=None):
    """Create a dataset_description.json file in the derivatives folder.
    TODO: should look for the extra parameters and also add them

    Args:
        args : Dictionary containing the arguments passed to the script.
        container_type : Type of container used to run the algorithm.
    """
    if not os.path.exists(os.path.join(out_dir, "dataset_description.json")):
        description = {
            "Name": algo,
            "Version": "1.0",
            "BIDSVersion": "1.7.0",
            "PipelineDescription": {
                "Name": algo,
            },
            "GeneratedBy": [
                {
                    "Name": algo,
                }
            ],
        }

        if prev_desc is not None:
            with open(prev_desc, "r") as f:
                prev_desc = json.load(f)
                description["GeneratedBy"].append({"Name": prev_desc["Name"]})
        if cfg is not None:
            description["Config"] = OmegaConf.to_container(cfg, resolve=True)
        with open(
            os.path.join(
                out_dir,
                "dataset_description.json",
            ),
            "w",
            encoding="utf-8",
        ) as outfile:
            json.dump(description, outfile, indent=4)

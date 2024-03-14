import os.path as op

import json
import os
from bids.layout import BIDSLayout

import nipype.interfaces.io as nio
import nipype.pipeline.engine as pe


def create_datasource(
    output_query,
    data_dir,
    subjects=None,
    sessions=None,
    acquisitions=None,
    index_derivative=False,
    derivative=None,
):
    """Create a datasource node that have iterables following BIDS format.
    By default, from a BIDSLayout, lists all the subjects (<sub>),
    finds their session numbers (<ses>, if any) and their acquisition
    type (<acq>, if any), and builds an iterable of tuples
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
    """

    bids_datasource = pe.Node(
        interface=nio.BIDSDataGrabber(),
        name="bids_datasource",
        synchronize=True,
    )

    bids_datasource.inputs.base_dir = data_dir
    bids_datasource.inputs.index_derivatives = index_derivative
    bids_datasource.inputs.output_query = output_query

    # If a derivative is specified, we need to go to the derivatives
    # if not, problems with acquisition
    # if derivative is not None:
    #     data_dir = op.join(data_dir, "derivatives", derivative)

    layout = BIDSLayout(data_dir, derivatives=index_derivative)

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
            print(f"Subject {sub} was not found.")

        existing_ses = layout.get_sessions(subject=sub)
        if sessions is None:
            sessions = existing_ses

        # If no sessions are found, it is possible that there is no session.
        sessions = [None] if len(sessions) == 0 else sessions
        for ses in sessions:
            if ses is not None and ses not in existing_ses:
                print(
                    f"WARNING: Session {ses} was not found for subject {sub}."
                )
            existing_acq = layout.get_acquisition(subject=sub, session=ses)
            if acquisitions is None:
                acquisitions = existing_acq

            # If there is no acquisition found, maybe the acquisition
            # tag was not specified.
            acquisitions = [None] if len(acquisitions) == 0 else acquisitions
            for acq in acquisitions:
                if acq is not None and acq not in existing_acq:
                    print(
                        f"WARNING: Acquisition {acq} was not found for "
                        f"subject {sub} session {ses}."
                    )

                iterables[1] += [(sub, ses, acq)]

    bids_datasource.iterables = iterables
    return bids_datasource


def create_datasink(
    iterables, name="output", params_subs={}, params_regex_subs={}
):
    """
    Creates a data sink node for reformatting and organizing relevant outputs.

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
            "_acquisition_haste_session_%s_subject_%s" % (ses, sub),
            "sub-%s/ses-%s/anat" % (sub, ses),
        )
        for (sub, ses, _) in iterables[1]  # doublecheck
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
    json_regex_subs = op.join(
        op.dirname(op.abspath(__file__)), "regex_subs.json"
    )
    dict_regex_subs = json.load(open(json_regex_subs, encoding="utf-8"))

    # Update with provided regex substitutions
    dict_regex_subs.update(params_regex_subs)

    regex_subs = [(key, value) for key, value in dict_regex_subs.items()]
    datasink.inputs.regexp_substitutions = regex_subs

    return datasink


def get_gestational_age(bids_dir, T2):
    """
    Retrieve the gestational age for a specific subject from a BIDS dataset.

    Parameters
    ----------
    bids_dir : str
        The file path to the root of the BIDS dataset,
        which must contain a 'participants.tsv' file.
    T2 : str
        The path of the image. We can get the subject id from there if
        it follows a BIDS format.

    Returns
    -------
    float
        The gestational age of the subject.

    Raises
    ------
    FileNotFoundError
        If the 'participants.tsv' file is not found
        in the specified BIDS directory.
    KeyError
        If the 'gestational_age' column is
        not found in the 'participants.tsv' file.
    IndexError
        If the specified subject ID is not
        found in the 'participants.tsv' file.
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
        raise KeyError(
            "Column 'gestational_age' not found in participants.tsv"
        )
    except IndexError:
        raise IndexError(
            f"Subject sub-{subject_id} not found in participants.tsv"
        )

    return gestational_age


def create_description_file(recon_dir, algorithm):
    """Create a dataset_description.json file in the derivatives folder.

    Parameters
    ----------
    args : dictionary
        Dictionary containing the arguments passed to the script.
    container_type : string
        Type of container used to run the algorithm.

    TODO: should look for the extra parameters and also add them
    """
    if not os.path.exists(os.path.join(recon_dir, "dataset_description.json")):
        description = {
            "Name": algorithm,
            "Version": "1.0",
            "BIDSVersion": "1.7.0",
            "PipelineDescription": {
                "Name": algorithm,
            },
            "GeneratedBy": [
                {
                    "Name": algorithm,
                }
            ],
        }
        with open(
            os.path.join(
                recon_dir,
                "dataset_description.json",
            ),
            "w",
            encoding="utf-8",
        ) as outfile:
            json.dump(description, outfile)

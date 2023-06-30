import os.path as op

import json

from bids.layout import BIDSLayout

import nipype.interfaces.io as nio
import nipype.pipeline.engine as pe


def create_datasource(
    output_query, data_dir, subjects=None, sessions=None, acquisitions=None
):
    """Create a datasource node that have iterables following BIDS format.
    By default, from a BIDSLayout, lists all the subjects (<sub>),
    finds their session numbers (<ses>, if any) and their acquisition
    type (<acq>, if any), and builds an iterable of tuples
    (sub, ses, acq) with all valid combinations.

    If a list of subjects/sessions/acquisitions is provided, the
    BIDSLayout is not queried and the provided
    subjects/sessions/acquisitions are used as is.

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
    bids_datasource.inputs.output_query = output_query

    layout = BIDSLayout(data_dir)

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

    print(iterables)

    bids_datasource.iterables = iterables
    return bids_datasource


def create_datasink(
    iterables, name="output", params_subs={}, params_regex_subs={}
):
    """
    Description: reformating relevant outputs
    """

    print("Datasink name: ", name)

    datasink = pe.Node(nio.DataSink(container=name), name="datasink")

    subjFolders = [
        (
            "_session_%s_subject_%s" % (ses, sub),
            "sub-%s/ses-%s/anat" % (sub, ses),
        )
        for ses in iterables[1][1]
        for sub in iterables[0][1]
    ]

    # subs
    json_subs = op.join(op.dirname(op.abspath(__file__)), "subs.json")

    dict_subs = json.load(open(json_subs))

    dict_subs.update(params_subs)

    print(dict_subs)

    subs = [(key, value) for key, value in dict_subs.items()]

    subjFolders.extend(subs)

    print(subjFolders)

    datasink.inputs.substitutions = subjFolders

    # regex_subs
    json_regex_subs = op.join(
        op.dirname(op.abspath(__file__)), "regex_subs.json"
    )

    dict_regex_subs = json.load(open(json_regex_subs))

    dict_regex_subs.update(params_regex_subs)

    regex_subs = [(key, value) for key, value in dict_regex_subs.items()]

    datasink.inputs.regexp_substitutions = regex_subs

    return datasink

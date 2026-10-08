"""Integration test: run the full pipeline on test_data.

This runs the containers (Docker or Singularity, depending on the config) and
needs a GPU, so it is skipped unless pytest is called with --integration:

    pytest tests/integration --integration [--integration-config my_cfg.yaml]

Use scripts/run_integration.sh to also report the result on GitHub.
"""
import shutil
import subprocess
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from fetpype.workflows.utils import get_pipeline_name, init_and_load_cfg

pytestmark = pytest.mark.integration

TEST_DATA = Path(__file__).parents[2] / "test_data"
SUBJECT, SESSION = "sub-simu001", "ses-01"
TIMEOUT = 4 * 3600  # seconds


def test_full_pipeline(tmp_path, integration_config):
    """Run every step, including brain extraction and mask dilation (the
    masks provided in test_data are not used)."""
    data = tmp_path / "data"
    shutil.copytree(TEST_DATA, data)
    out = tmp_path / "out"
    cmd = [
        "fetpype_run",
        "--data", str(data),
        "--out", str(out),
        "--config", integration_config,
        "--nprocs", "4",
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
    log = tmp_path / "fetpype_run.log"
    log.write_text(proc.stdout + proc.stderr)
    assert proc.returncode == 0, (
        f"fetpype_run failed, see {log}:\n{proc.stderr[-3000:]}"
    )

    # The final outputs are named after the methods used in the config.
    cfg = init_and_load_cfg(integration_config)
    rec = cfg.reconstruction.pipeline
    seg = cfg.segmentation.pipeline
    anat = (
        out / "derivatives" / get_pipeline_name(cfg) / SUBJECT / SESSION
        / "anat"
    )
    prefix = f"{SUBJECT}_{SESSION}_rec-{rec}"

    srr = nib.load(anat / f"{prefix}_T2w.nii.gz")
    assert srr.ndim == 3, "The reconstruction should be a 3D volume"
    assert np.any(srr.get_fdata()), "The reconstruction is empty"

    dseg = nib.load(anat / f"{prefix}_seg-{seg}_dseg.nii.gz")
    assert dseg.shape[:3] == srr.shape, (
        "The segmentation should match the reconstruction"
    )
    assert len(np.unique(dseg.get_fdata())) > 2, (
        "The segmentation should contain several tissue labels"
    )

    for hemi in "LR":
        surf_name = f"{prefix}_seg-{seg}_hemi-{hemi}_white.surf.gii"
        surf = nib.load(anat / surf_name)
        assert len(surf.darrays[0].data) > 1000, (
            f"The hemi-{hemi} surface should be a full mesh"
        )

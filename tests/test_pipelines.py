import os.path as op

from pathlib import Path
from fetpype.pipelines.full_pipeline import (create_full_pipeline, create_rec_pipeline, create_seg_pipeline)
from hydra import initialize, compose
from fetpype.workflows.utils import (
    init_and_load_cfg,
)



# 1. initialize will add config_path the config search path within the context
# 2. The module with your configs should be importable.
#    it needs to have a __init__.py (can be empty).
# 3. THe config path is relative to the file calling initialize (this file)


def test_create_full_pipeline(mock_output_dir):

    cfg = init_and_load_cfg(
        "configs/default.yaml"
    )

    pipeline_fet = create_full_pipeline(
        cfg,
        name="test_create_full_pipeline",
    )
    pipeline_fet.base_dir = mock_output_dir
    pipeline_fet.write_graph(
        graph2use="colored",
        format="png",
        simple_form=True,
    )
    assert op.exists(
        op.join(mock_output_dir, "test_create_full_pipeline", "graph.png")
    )


def test_create_rec_pipeline(mock_output_dir):

    cfg = init_and_load_cfg(
        "configs/default.yaml"
    )

    pipeline_fet = create_rec_pipeline(
        cfg,
        name="test_create_rec_pipeline",
    )
    pipeline_fet.base_dir = mock_output_dir
    pipeline_fet.write_graph(
        graph2use="colored",
        format="png",
        simple_form=True,
    )
    assert op.exists(
        op.join(mock_output_dir, "test_create_rec_pipeline", "graph.png")
    )

def test_create_seg_pipeline(mock_output_dir):

    cfg = init_and_load_cfg(
        "configs/default.yaml"
    )

    pipeline_fet = create_rec_pipeline(
        cfg,
        name="test_create_seg_pipeline",
    )
    pipeline_fet.base_dir = mock_output_dir
    pipeline_fet.write_graph(
        graph2use="colored",
        format="png",
        simple_form=True,
    )
    assert op.exists(
        op.join(mock_output_dir, "test_create_seg_pipeline", "graph.png")
    )

if __name__ == "__main__":
    test_create_subpipes_no_args

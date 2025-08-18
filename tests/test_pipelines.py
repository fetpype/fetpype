import os.path as op
from fetpype.pipelines.full_pipeline import (
    create_full_pipeline,
    create_rec_pipeline,
    create_seg_pipeline,
)
from fetpype.workflows.utils import (
    init_and_load_cfg,
)
import pytest
import itertools

# 1. initialize will add config_path the config search path within the context
# 2. The module with your configs should be importable.
#    it needs to have a __init__.py (can be empty).
# 3. THe config path is relative to the file calling initialize (this file)


# Define options
pipelines = [create_full_pipeline, create_rec_pipeline, create_seg_pipeline]
recon_methods = ["niftymic", "nesvor", "svrtk"]


@pytest.mark.parametrize("sr_method", recon_methods)
def test_read_config(generate_config, sr_method):
    cfg = generate_config(sr_method, "bounti", "surface")
    cfg = init_and_load_cfg(cfg)
    assert cfg["reconstruction"]["pipeline"] == sr_method
    assert cfg["segmentation"]["pipeline"] == "bounti"
    assert cfg["surface"]["pipeline"] == "surface"


load_masks = [True, False]
test_cases = list(itertools.product(pipelines, recon_methods, load_masks))


@pytest.mark.parametrize(
    "pipeline, sr_method, load_masks",
    test_cases,
    ids=[
        f"pipelines-{str(x[0].__name__)}_sr-{x[1]}_loadMask-{x[2]}"
        for x in test_cases
    ],
)
def test_create_full_pipelines(
    generate_config, mock_output_dir, pipeline, sr_method, load_masks
):
    cfg = generate_config(sr_method, "bounti", "surface")
    cfg = init_and_load_cfg(cfg)

    name = "test_" + str(pipeline.__name__)
    if "seg" in pipeline.__name__:
        pipeline_fet = pipeline(
            cfg,
            name=name,
        )
    else:
        pipeline_fet = pipeline(
            cfg,
            load_masks=load_masks,
            name=name,
        )
    pipeline_fet.base_dir = mock_output_dir
    pipeline_fet.write_graph(
        graph2use="colored",
        format="png",
        simple_form=True,
    )
    assert op.exists(op.join(mock_output_dir, name, "graph.png"))

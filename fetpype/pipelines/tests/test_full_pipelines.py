import os.path as op

from pathlib import Path
from fetpype.utils.utils_tests import make_tmp_dir
from fetpype.pipelines.full_pipeline import create_fet_subpipes
from hydra import initialize, compose

cwd = Path.cwd()
data_path = make_tmp_dir()


# 1. initialize will add config_path the config search path within the context
# 2. The module with your configs should be importable.
#    it needs to have a __init__.py (can be empty).
# 3. THe config path is relative to the file calling initialize (this file)
def test_create_subpipes_no_args() -> None:
    with initialize(version_base=None, config_path="../../../configs/"):
        cfg = compose(config_name="default.yaml")
    pipeline_fet = create_fet_subpipes(
        cfg, name="test_create_subpipes_no_args"
    )
    pipeline_fet.base_dir = data_path
    pipeline_fet.write_graph(
        graph2use="colored",
        format="png",
        simple_form=True,
    )
    assert op.exists(
        op.join(data_path, "test_create_subpipes_no_args", "graph.png")
    )


# def test_create_minimal_subpipes_no_args():

#     params = {
#         "general": {
#             "pipeline": "minimal",
#             "pre_command": "docker run ",
#             "niftymic_image": "renbem/niftymic:v0.9 ",
#             "no_graph": False,
#         }
#     }

#     # running workflow
#     pipeline_fet = create_minimal_subpipes(
#         params=params, name="test_create_minimal_subpipes_no_args"
#     )

#     pipeline_fet.write_graph(graph2use="colored")

#     assert op.exists(
#         op.join(data_path, "test_create_minimal_subpipes_no_args", "graph.png")
#     )


if __name__ == "__main__":
    test_create_subpipes_no_args

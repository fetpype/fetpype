import os.path as op

from pathlib import Path

from fetpype.utils.utils_tests import make_tmp_dir

from fetpype.pipelines.full_pipelines import create_minimal_subpipes

cwd = Path.cwd()
data_path = make_tmp_dir()


def test_create_minimal_subpipes_no_args():

    params = {
        "general":
        {
            "pipeline": "minimal",
            "pre_command": "docker run ",
            "niftymic_image": "renbem/niftymic:v0.9 ",
            "no_graph": false
        }
    }

    # running workflow
    pipeline_fet = create_minimal_subpipes(
        params=params, name="test_create_minimal_subpipes_no_args")

    pipeline_fet.base_dir = data_path

    pipeline_fet.write_graph(graph2use="colored")

    assert op.exists(
        op.join(data_path, "test_create_minimal_subpipes_no_args",
                "graph.png"))

if __name__ == '__main__':
    test_create_minimal_subpipes_no_args

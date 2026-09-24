import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
KAGGLE = ROOT / "kaggle"
NOTEBOOK = KAGGLE / "satreg-gpu-benchmark.ipynb"


def code_cells():
    cells = json.loads(NOTEBOOK.read_text())["cells"]
    return [cell for cell in cells if cell["cell_type"] == "code"]


def test_notebook_is_committed_as_python_without_outputs():
    for cell in code_cells():
        assert cell["outputs"] == []
        assert cell["execution_count"] is None
        ast.parse("".join(cell["source"]))


def test_notebook_runs_a_run_config_of_the_repository():
    source = "".join("".join(cell["source"]) for cell in code_cells())

    config = re.search(r'^CONFIG = "(.+)"$', source, re.MULTILINE).group(1)

    assert (ROOT / config).is_file()


def test_kernel_metadata_asks_for_a_gpu_and_the_internet():
    metadata = json.loads((KAGGLE / "kernel-metadata.json").read_text())

    assert (KAGGLE / metadata["code_file"]).resolve() == NOTEBOOK.resolve()
    assert metadata["kernel_type"] == "notebook"
    assert metadata["enable_gpu"] is True
    # To clone the repository, install the extras and fetch chips and weights.
    assert metadata["enable_internet"] is True
    assert metadata["is_private"] is True


def test_no_credentials_in_the_kaggle_files():
    # GitHub tokens, the key of a kaggle.json, Kaggle API tokens.
    credential = re.compile(r'gh[pousr]_\w{20}|github_pat_|"key"\s*:|KGAT_')

    for path in KAGGLE.iterdir():
        assert not credential.search(path.read_text()), path

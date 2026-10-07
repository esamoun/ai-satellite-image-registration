import ast
import json
import re
from pathlib import Path

import pytest

from satreg.cli import _parser
from satreg.train import load_train_config

ROOT = Path(__file__).parents[1]
KAGGLE = ROOT / "kaggle"
NOTEBOOK = KAGGLE / "satreg-gpu-benchmark.ipynb"
TRAINING = KAGGLE / "satreg-train.ipynb"
NOTEBOOKS = pytest.mark.parametrize("notebook", [NOTEBOOK, TRAINING], ids=str)


def code_cells(notebook):
    cells = json.loads(notebook.read_text())["cells"]
    return [cell for cell in cells if cell["cell_type"] == "code"]


def source(notebook):
    return "\n".join("".join(cell["source"]) for cell in code_cells(notebook))


def config(notebook):
    found = re.search(r'^CONFIG = "(.+)"$', source(notebook), re.MULTILINE)
    return ROOT / found.group(1)


@NOTEBOOKS
def test_notebook_is_committed_as_python_without_outputs(notebook):
    for cell in code_cells(notebook):
        assert cell["outputs"] == []
        assert cell["execution_count"] is None
        ast.parse("".join(cell["source"]))


@NOTEBOOKS
def test_notebook_runs_a_run_config_of_the_repository(notebook):
    assert config(notebook).is_file()


def test_the_training_notebook_runs_trainings_the_command_accepts():
    parameters = ast.parse("".join(code_cells(TRAINING)[0]["source"]))
    runs = next(
        ast.literal_eval(node.value)
        for node in parameters.body
        if isinstance(node, ast.Assign) and node.targets[0].id == "RUNS"
    )

    assert len(runs) == 3
    for options in runs.values():
        _parser().parse_args(["train", *options])
    # The run the notebook times is on the GPU, on new pairs, and validates.
    run = load_train_config(config(TRAINING))
    assert (run.device, run.n_pairs) == ("cuda", 0)
    assert run.validate_every and run.workers
    assert run.steps % run.validate_every == 0


def test_the_training_notebook_names_no_kaggle_account():
    # The chips dataset is found by its content, whoever owns it.
    assert 'INPUT.rglob("chips.json")' in source(TRAINING)
    assert not re.search(r"/kaggle/input/\w", source(TRAINING))


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

    paths = list(KAGGLE.iterdir())
    assert TRAINING in paths
    for path in paths:
        assert not credential.search(path.read_text()), path


def test_the_benchmark_notebook_fetches_the_fine_tuned_weights_before_the_run():
    code = source(NOTEBOOK)

    assert code.index('"fetch-weights"') < code.index('"benchmark"')
    _parser().parse_args(["fetch-weights"])
    # The token reaches the command through the environment, and is dropped
    # before the benchmark, which reads the cache.
    assert 'env["GITHUB_TOKEN"] = token' in code
    assert code.index("del token") < code.index('"benchmark"')

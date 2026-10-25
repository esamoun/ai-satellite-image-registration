"""What the container image is made of: the benchmark chip it carries, the
small benchmark it runs and what the Dockerfile copies. Building it and running
it are CI's job (`make container-image`, `make container-image-try`)."""

import hashlib
import json
import re
import tomllib
from pathlib import Path

import rasterio

from satreg.cli import load_run_config, main
from satreg.ingest import cache_path
from satreg.methods import load_methods
from satreg.methods.arosics import Arosics
from satreg.methods.lightglue import LightGlue
from satreg.methods.raft import Raft
from satreg.methods.raft_onnx import RaftOnnx
from satreg.methods.roma import Roma
from satreg.sites import load_sites
from satreg.weights import RELEASED_ONNX, REPOSITORY, WEIGHTS_TERMS

ROOT = Path(__file__).parents[1]
CONFIGS = ROOT / "configs"
CONFIG = CONFIGS / "container-image.toml"

# What the Dockerfile copies to `data/` in the container image.
DATA = ROOT / "docker" / "data"

# The scene the published figures of Beauce were made on, and the chip
# `satreg fetch` cut from it on the M1.
SCENE = "S2B_T31UCP_20250701T110241_L2A"
CHIP_SHA256 = "acce2a314f97121f2590245bf6e4159e88a24d8d83af23f0df0753fa61e7a283"


def committed_chip() -> Path:
    """Where `satreg benchmark` looks for Beauce's chip in the container image."""
    config = load_sites(CONFIGS / "sites.toml")
    return cache_path(config.sites["beauce"], config.catalogue, DATA)


def copied_sources() -> list[list[str]]:
    """The sources of each COPY of the Dockerfile: every argument but the last."""
    return [
        line.split()[1:-1]
        for line in (ROOT / "Dockerfile").read_text().splitlines()
        if line.startswith("COPY ")
    ]


def test_the_committed_chip_is_the_file_the_benchmark_looks_for():
    chip = committed_chip()

    assert chip.is_file(), (
        f"{chip.relative_to(ROOT)} is not committed: Beauce's entry in "
        "configs/sites.toml changed, and the container image would ask the "
        "catalogue for a chip with no network"
    )
    assert [path.name for path in DATA.rglob("*.tif")] == [chip.name]


def test_the_committed_chip_is_the_scene_of_the_published_figures():
    chip = committed_chip()
    manifest = json.loads((ROOT / "examples" / "manifest.json").read_text())
    shown = {pair["scene"] for pair in manifest["pairs"] if pair["site"] == "beauce"}

    assert hashlib.sha256(chip.read_bytes()).hexdigest() == CHIP_SHA256
    with rasterio.open(chip) as src:
        assert src.tags()["item_id"] == SCENE
        assert src.shape == (1024, 1024)
    assert shown == {SCENE}
    assert "Copernicus Sentinel data 2025" in (DATA / "README.md").read_text()


def test_the_small_benchmark_is_beauce_translations_clean_and_hard_on_20_pairs():
    options = load_run_config(CONFIG)

    assert options["sites"] == ["beauce"]
    assert options["scenarios"] == ["translation"]
    assert options["degradations"] == ["clean", "hard"]
    assert (options["pairs"], options["size"], options["seed"]) == (20, 256, 0)
    assert "allow_held_out" not in options


def test_no_method_of_the_small_benchmark_needs_pytorch_or_arosics():
    methods = load_methods(CONFIGS / "methods.toml")

    for name in load_run_config(CONFIG)["methods"]:
        assert not isinstance(methods[name], (Arosics, LightGlue, Raft, Roma)), name


def test_the_small_benchmark_runs_every_released_onnx_file_and_no_other():
    methods = load_methods(CONFIGS / "methods.toml")
    exported = [
        methods[name]
        for name in load_run_config(CONFIG)["methods"]
        if isinstance(methods[name], RaftOnnx)
    ]

    # A method with a `file` instead would read a path that is not there.
    assert sorted(method.release for method in exported) == sorted(RELEASED_ONNX)


def test_the_small_benchmark_runs_on_the_committed_chip_with_no_network(
    tmp_path, capsys
):
    # No network: the `no_network` fixture of conftest.py cuts it for every test.
    main(
        ["benchmark", "--config", str(CONFIG)]
        + ["--methods", "phase_correlation", "--pairs", "2", "--repeats", "1"]
        + ["--sites-config", str(CONFIGS / "sites.toml")]
        + ["--degradations-config", str(CONFIGS / "degradations.toml")]
        + ["--methods-config", str(CONFIGS / "methods.toml")]
        + ["--data-dir", str(DATA), "--out", str(tmp_path / "out")]
    )

    printed = capsys.readouterr().out
    assert "| beauce | translation | clean | phase_correlation | cpu | 2 |" in printed
    assert "| beauce | translation | hard | phase_correlation | cpu | 2 |" in printed


def test_the_build_context_lets_in_what_the_dockerfile_copies():
    let_in = {
        line.removeprefix("!").rstrip("/")
        for line in (ROOT / ".dockerignore").read_text().splitlines()
        if line.startswith("!")
    }
    copied = {source.rstrip("/") for sources in copied_sources() for source in sources}

    assert copied == let_in
    assert all((ROOT / source).exists() for source in copied)


def test_the_container_image_carries_the_licences_through_the_readme():
    # The README is wrapped for reading: compare the words, not the lines.
    readme = " ".join((ROOT / "README.md").read_text().split())

    assert any({"README.md", "LICENSE"} <= set(s) for s in copied_sources())
    assert " ".join(WEIGHTS_TERMS.split()) in readme
    assert "Contains modified Copernicus Sentinel data 2025." in readme


def test_the_container_image_is_built_with_no_token():
    # The release is public: no build secret in the Dockerfile, the Makefile or
    # the workflow, and no token reaches a layer.
    dockerfile = (ROOT / "Dockerfile").read_text()
    makefile = (ROOT / "Makefile").read_text()
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text()

    assert "--mount=type=secret" not in dockerfile
    assert "TOKEN" not in dockerfile
    assert "--secret" not in makefile
    assert "GITHUB_TOKEN" not in workflow


def test_the_docs_name_the_container_image_of_the_package_version():
    # CI pushes the version of pyproject.toml, on the tag of that version: every
    # command a reader copies must name it, with no other tag and no digest.
    # docs/decisions.md is a log, and is left as it was written.
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    name = re.escape(f"ghcr.io/{REPOSITORY}")
    docs = [ROOT / "README.md"] + [
        path
        for path in sorted((ROOT / "docs").glob("*"))
        if path.suffix in (".md", ".html") and path.name != "decisions.md"
    ]

    references = {
        doc.name: re.findall(name + r"([:@][\w.-]*)?", doc.read_text()) for doc in docs
    }

    assert references["README.md"]
    assert references["running.md"]
    assert {ref for refs in references.values() for ref in refs} == {f":{version}"}


def test_onnx_runtime_telemetry_is_turned_off_in_the_container_image():
    dockerfile = (ROOT / "Dockerfile").read_text()
    # One line per instruction, as above.
    instructions = dockerfile.replace("\\\n", " ").splitlines()

    assert any(
        "ORT_DISABLE_TELEMETRY=1" in line.split()
        for line in instructions
        if line.startswith("ENV")
    )

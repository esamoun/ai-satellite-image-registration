import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pytest
from test_raft import needs_raft

from satreg import curve, onnxexport, weights
from satreg.cli import EXPORT_METHODS, _checkpoints, main
from satreg.compute import MEMORY_READINGS, ONNXRUNTIME, file_sha256
from satreg.methods import cost_meter, deep, load_methods, missing_dependencies
from satreg.methods import raft_onnx as raft_onnx_method
from satreg.methods.raft import Raft
from satreg.methods.raft_onnx import RaftOnnx
from satreg.onnxexport import PARITY_TOLERANCE_PX, Exported, ParityError
from satreg.simulate import simulate_translation
from satreg.texture import fractal_texture
from satreg.weights import (
    RELEASED,
    RELEASED_ONNX,
    ReleasedOnnx,
    ReleasedWeights,
    WeightsRefused,
    WeightsUnavailable,
)

REPO = Path(__file__).parents[1]
CONFIGS = REPO / "configs"
METHODS_CONFIG = CONFIGS / "methods.toml"

needs_onnx = pytest.mark.skipif(
    bool(onnxexport.missing_modules()),
    reason="needs the dl and onnx extras: make install-dl install-onnx",
)
needs_onnxruntime = pytest.mark.skipif(
    bool(raft_onnx_method.missing_modules()),
    reason="needs the onnx extra: make install-onnx",
)

# The export the tests run: the small model, two refinements, half a second.
SMALL = Raft(model="small")
COUNT = 2


@pytest.fixture(scope="module")
def exported(tmp_path_factory):
    """RAFT small exported once with two refinements."""
    out = tmp_path_factory.mktemp("onnx")
    return out, onnxexport.export_checked(SMALL, "raft_small", COUNT, out)


def pair(rows, cols):
    source = fractal_texture(max(rows, cols) + 64, seed=3)
    simulated = simulate_translation(source, dx=0.4, dy=-0.3)
    return simulated.reference[:rows, :cols], simulated.moving[:rows, :cols]


# Square, then not: sides the graph was not traced on, one of them padded.
@needs_raft
@needs_onnx
@pytest.mark.parametrize("shape", [(160, 160), (130, 250)])
def test_an_exported_file_gives_the_flow_of_pytorch_at_any_size(exported, shape):
    out, _ = exported
    reference, moving = pair(*shape)

    found = RaftOnnx(file=str(out / "raft_small_r2.onnx"))(reference, moving)
    expected = Raft(model="small", iterations=COUNT)(reference, moving)

    assert found.values.shape == (2, *shape)
    assert np.abs(found.values - expected.values).max() <= PARITY_TOLERANCE_PX
    # Another count is another flow: the file holds its own.
    other = Raft(model="small", iterations=COUNT + 1)(reference, moving)
    assert np.abs(found.values - other.values).max() > PARITY_TOLERANCE_PX


@needs_raft
@needs_onnx
def test_an_export_is_named_checked_and_says_what_it_holds(exported):
    out, written = exported
    path = out / "raft_small_r2.onnx"
    cached = deep.weights_file(SMALL.weights())

    assert written == Exported(
        name="raft_small_r2",
        model="small",
        weights=cached.name,
        refinements=COUNT,
        megabytes=path.stat().st_size / 1e6,
        sha256=file_sha256(path),
        parity_px=written.parity_px,
    )
    assert 0 <= written.parity_px <= PARITY_TOLERANCE_PX
    assert RaftOnnx(file=str(path)).described() == {
        "model": "small",
        "iterations": "2",
        "fine_tuned": "false",
        "weights": cached.name,
        "weights_sha256": file_sha256(cached),
    }
    # What a run records of the method: the file by hash, and what it holds.
    assert _checkpoints({"toy": RaftOnnx(file=str(path))}) == {
        "toy": {
            "path": str(path),
            "sha256": written.sha256,
            "holds": onnxexport.described(SMALL, COUNT),
        }
    }


def test_an_export_too_far_from_pytorch_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(onnxexport, "export", lambda method, count, path: None)
    monkeypatch.setattr(onnxexport, "parity", lambda method, count, path: 0.5)

    with pytest.raises(ParityError, match="raft_small_r4.onnx is 5.00e-01 px from"):
        onnxexport.export_checked(SMALL, "raft_small", 4, tmp_path)

    # No figure at all is not a pass.
    monkeypatch.setattr(onnxexport, "parity", lambda method, count, path: math.nan)
    with pytest.raises(ParityError, match="over the 0.001 px accepted"):
        onnxexport.export_checked(SMALL, "raft_small", 4, tmp_path)


@pytest.mark.parametrize(
    ("method", "name", "stem"),
    [
        (Raft(), "raft", "raft_large"),
        (Raft(model="small", iterations=4), "raft_small_r4", "raft_small"),
        (Raft(release="raft_large_ft"), "raft_ft", "raft_large_ft"),
        (Raft(checkpoint="outputs/x.pt"), "raft_ft_local", "raft_ft_local"),
    ],
)
def test_an_export_is_named_after_its_weights(method, name, stem):
    assert onnxexport.weights_name(method, name) == stem


def test_a_fine_tuned_export_names_the_released_weights_it_holds():
    large = RELEASED["raft_large_ft"]

    assert onnxexport.described(Raft(release="raft_large_ft"), 8) == {
        "model": "large",
        "iterations": "8",
        "fine_tuned": "true",
        "weights": large.asset,
        "weights_sha256": large.sha256,
    }


@needs_onnx
def test_an_export_needs_at_least_one_refinement(tmp_path):
    with pytest.raises(ValueError, match="refinements must be positive, got 0"):
        onnxexport.export(SMALL, 0, tmp_path / "none.onnx")

    assert not (tmp_path / "none.onnx").exists()


def test_an_onnx_method_takes_one_file_from_a_path_or_from_a_release():
    for given in ({}, {"file": "a.onnx", "release": "raft_large_ft_r12"}):
        with pytest.raises(ValueError, match="from a path or from a release, one"):
            RaftOnnx(**given)
    with pytest.raises(ValueError, match="no released ONNX file named 'raft_large_ft'"):
        RaftOnnx(release="raft_large_ft")
    with pytest.raises(ValueError, match="threads must not be negative, got -1"):
        RaftOnnx(file="a.onnx", threads=-1)


@needs_onnxruntime
def test_an_onnx_method_without_its_file_says_how_to_write_it(tmp_path):
    method = RaftOnnx(file=str(tmp_path / "none.onnx"))
    reference, moving = pair(128, 128)

    with pytest.raises(FileNotFoundError, match="write it with satreg export"):
        method(reference, moving)


def test_an_onnx_method_is_timed_and_its_memory_is_not_read_call_by_call():
    method = RaftOnnx(file="a.onnx")
    calls = []

    assert cost_meter(method) is ONNXRUNTIME
    assert math.isnan(ONNXRUNTIME.peak_mib(lambda: calls.append(1)))
    # The memory call is not made: it would only be time spent.
    assert calls == []
    assert "satreg footprint" in MEMORY_READINGS[ONNXRUNTIME.name]


def test_an_onnx_method_needs_onnx_runtime_and_not_pytorch(monkeypatch):
    monkeypatch.setattr(
        raft_onnx_method.importlib.util,
        "find_spec",
        lambda name: None if name == "onnxruntime" else object(),
    )

    assert missing_dependencies(RaftOnnx(file="a.onnx")) == ["onnxruntime"]
    assert RaftOnnx.runtime == ("onnxruntime",)


def test_each_point_of_the_curve_is_a_pytorch_method_and_its_onnx_twin():
    methods = load_methods(METHODS_CONFIG)

    curve.check_methods(curve.POINTS, methods)
    for point in curve.POINTS:
        twin, torch = methods[point.onnx], methods[point.torch]
        stem = weights.onnx_name(onnxexport.weights_name(torch, point.torch), 0)[:-1]
        assert isinstance(twin, RaftOnnx)
        assert twin.threads == 4
        if point.fine_tuned:
            # The published export of the weights the PyTorch method runs.
            assert twin.release == f"{stem}{point.refinements}"
            assert RELEASED_ONNX[twin.release].weights == torch.release
            assert RELEASED_ONNX[twin.release].refinements == point.refinements
        else:
            # Where satreg export writes the pretrained model.
            assert twin.file == f"outputs/onnx/{stem}{point.refinements}.onnx"
    onnx = {name for name, m in methods.items() if isinstance(m, RaftOnnx)}
    assert onnx == {point.onnx for point in curve.POINTS}
    # satreg export writes the four models of the curve by default.
    assert {methods[name] for name in EXPORT_METHODS} == {
        methods[point.torch]
        for point in curve.POINTS
        if point.refinements == curve.TRAINED_REFINEMENTS
    }
    assert onnxexport.REFINEMENTS == curve.REFINEMENTS


def test_every_released_weights_is_published_with_each_refinement_count():
    assert set(RELEASED_ONNX) == {
        f"{name}_r{count}" for name in RELEASED for count in curve.REFINEMENTS
    }
    for name, exported in RELEASED_ONNX.items():
        assert exported.name == name
        assert exported.asset == f"{name}-{exported.sha256[:8]}.onnx"
        assert exported.tag == RELEASED[exported.weights].tag
        assert len(exported.sha256) == 64
        assert weights.lookup(name) is exported
    assert weights.lookup("raft_small_ft") is RELEASED["raft_small_ft"]
    with pytest.raises(ValueError, match="no released file named 'nothing'"):
        weights.lookup("nothing")


@pytest.mark.parametrize("name", RELEASED_ONNX)
def test_the_pinned_hash_is_the_one_of_the_published_export(name):
    table = (REPO / "docs" / "results" / "n3" / "onnx.md").read_text()

    assert f"| `{name}.onnx` |" in table
    assert f"`{RELEASED_ONNX[name].sha256}`" in table


@pytest.mark.parametrize("name", RELEASED_ONNX)
def test_the_pinned_hash_is_the_one_of_the_export_on_this_machine(name):
    written = REPO / "outputs" / "onnx" / f"{name}.onnx"
    if not written.is_file():
        pytest.skip(f"needs the export at {written}: satreg export")

    assert file_sha256(written) == RELEASED_ONNX[name].sha256


def test_the_cache_is_found_without_importing_pytorch(tmp_path, monkeypatch):
    monkeypatch.delitem(weights.sys.modules, "torch", raising=False)
    monkeypatch.setenv("TORCH_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))

    assert weights.cache_directory() == tmp_path / "home" / "hub" / "checkpoints"
    monkeypatch.delenv("TORCH_HOME")
    assert weights.cache_directory() == (
        tmp_path / "cache" / "torch" / "hub" / "checkpoints"
    )
    monkeypatch.delenv("XDG_CACHE_HOME")
    assert weights.cache_directory() == (
        Path.home() / ".cache" / "torch" / "hub" / "checkpoints"
    )
    assert "torch" not in weights.sys.modules


@pytest.mark.skipif(bool(deep.missing_modules()), reason="needs the dl extra")
def test_the_cache_is_where_pytorch_says_once_it_is_loaded(monkeypatch):
    import torch

    monkeypatch.delenv("TORCH_HOME", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    found = weights.cache_directory()
    monkeypatch.delitem(weights.sys.modules, "torch")

    assert found == Path(torch.hub.get_dir()) / "checkpoints"
    assert weights.cache_directory() == found


CONTENT = b"an export of the toy weights"


def publish(monkeypatch, content=CONTENT):
    """Declare toy weights and one export of them whose file is ``content``."""
    toy = ReleasedWeights("toy", "small", "toy-run", "toy-tag", "0" * 64)
    exported = ReleasedOnnx("toy", 4, "toy-tag", hashlib.sha256(content).hexdigest())
    monkeypatch.setattr(weights, "RELEASED", {"toy": toy})
    monkeypatch.setattr(weights, "RELEASED_ONNX", {"toy_r4": exported})
    return toy, exported


def test_a_published_export_is_the_file_satreg_export_wrote_unchanged(
    tmp_path, monkeypatch
):
    toy, exported = publish(monkeypatch)
    exports, out = tmp_path / "onnx", tmp_path / "release"
    exports.mkdir()

    with pytest.raises(FileNotFoundError, match="write it with satreg export"):
        weights.export_onnx("toy_r4", exports, out)
    (exports / "toy_r4.onnx").write_bytes(b"another export")
    with pytest.raises(WeightsRefused, match="toy_r4.onnx is not the published toy_r4"):
        weights.export_onnx("toy_r4", exports, out)
    assert not out.exists()

    (exports / "toy_r4.onnx").write_bytes(CONTENT)
    card = weights.export_onnx("toy_r4", exports, out)

    assert (out / exported.asset).read_bytes() == CONTENT
    assert card == {
        "asset": exported.asset,
        "sha256": exported.sha256,
        "bytes": len(CONTENT),
        "weights": toy.asset,
        "refinements": 4,
        "release": "toy-tag",
        "repository": weights.REPOSITORY,
    }
    # The release's notes list it under the weights it was exported from.
    notes = weights.notes([], [card])
    assert (
        f"| `{exported.asset}` | `{toy.asset}` | 4 | 0.0 | `{exported.sha256}` |"
        in notes
    )
    assert ".onnx" not in weights.notes([])


def test_a_published_export_is_fetched_and_checked_like_the_weights(
    tmp_path, monkeypatch
):
    _, exported = publish(monkeypatch)
    source, cache = tmp_path / "release", tmp_path / "cache"
    source.mkdir()

    with pytest.raises(WeightsUnavailable, match=f"no {exported.asset} in"):
        weights.fetch("toy_r4", source=source, directory=cache)
    (source / exported.asset).write_bytes(b"another file")
    with pytest.raises(WeightsRefused, match="is not the published toy_r4"):
        weights.fetch("toy_r4", source=source, directory=cache)
    assert not list(cache.iterdir())

    (source / exported.asset).write_bytes(CONTENT)
    assert weights.fetch("toy_r4", source=source, directory=cache) == (
        cache / exported.asset
    )


def test_fetch_weights_fetches_the_exports_too(tmp_path, monkeypatch, capsys):
    _, exported = publish(monkeypatch)
    monkeypatch.setattr(weights, "cache_directory", lambda: tmp_path / "cache")
    monkeypatch.setattr(weights, "RELEASED", {})
    (tmp_path / exported.asset).write_bytes(CONTENT)

    # Without a name, every published file; PyTorch is not needed for these.
    main(["fetch-weights", "--from", str(tmp_path)])

    assert capsys.readouterr().out == f"{tmp_path / 'cache' / exported.asset}\n"


def export_args(tmp_path, *options):
    return [
        "export",
        "--methods-config",
        str(METHODS_CONFIG),
        "--out",
        str(tmp_path / "onnx"),
        *options,
    ]


@needs_onnx
def test_export_refuses_what_it_cannot_write(tmp_path):
    with pytest.raises(SystemExit, match="need --refinements of at least 1, got 0"):
        main(export_args(tmp_path, "--refinements", "4", "0"))
    with pytest.raises(SystemExit, match="RAFT methods under PyTorch, not sift_ransac"):
        main(export_args(tmp_path, "--methods", "raft_small", "sift_ransac"))
    with pytest.raises(SystemExit, match="satreg: unknown method 'nothing'"):
        main(export_args(tmp_path, "--methods", "nothing"))

    assert not (tmp_path / "onnx").exists()


def test_export_says_which_extras_it_lacks(tmp_path, monkeypatch):
    monkeypatch.setattr(onnxexport, "missing_modules", lambda: ["onnx"])

    with pytest.raises(SystemExit, match="satreg: export needs .*onnx, not installed"):
        main(export_args(tmp_path))


@needs_raft
@needs_onnx
def test_export_writes_the_files_their_table_and_the_context(tmp_path, capsys):
    out = tmp_path / "onnx"

    main(export_args(tmp_path, "--methods", "raft_small", "--refinements", "2", "2"))

    assert {p.name for p in out.iterdir()} == {
        "raft_small_r2.onnx",
        "exports.csv",
        "summary.md",
        "context.json",
    }
    printed = capsys.readouterr().out
    assert printed == (out / "summary.md").read_text()
    assert f"`{file_sha256(out / 'raft_small_r2.onnx')}`" in printed
    context = json.loads((out / "context.json").read_text())
    assert context["export"] == {
        "opset": 17,
        "trace_side": 128,
        "parity_tolerance_px": 0.001,
        "parity_side": 256,
    }
    assert context["run"]["refinements"] == [2, 2]
    assert context["libraries"]["onnxruntime"]


def test_a_run_of_an_onnx_method_without_its_file_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr("satreg.cli.missing_dependencies", lambda method: [])
    monkeypatch.chdir(tmp_path)
    args = ["benchmark", "--pairs", "1", "--methods", "raft_onnx", "--out", "out"]
    for option, name in (("--methods", "methods"), ("--degradations", "degradations")):
        args += [f"{option}-config", str(CONFIGS / f"{name}.toml")]

    file = "outputs/onnx/raft_large_r12.onnx"
    with pytest.raises(SystemExit, match=f"raft_onnx needs its ONNX file at {file}"):
        main(args)

    assert not (tmp_path / "out").exists()

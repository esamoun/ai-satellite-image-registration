import json
import math
import shutil
import tomllib
from pathlib import Path

import numpy as np
import pytest
from test_onnx import COUNT, SMALL, needs_onnx
from test_raft import needs_raft
from test_validation import cached, scenes  # noqa: F401

from satreg import onnxexport, quantize
from satreg.benchmark import BenchmarkConfig, simulated_pairs
from satreg.cli import load_run_config, main, parse_args
from satreg.compute import file_sha256
from satreg.degrade import load_presets
from satreg.displacement import Translation
from satreg.methods import load_methods
from satreg.methods.raft_onnx import RaftOnnx
from satreg.quantize import DYNAMIC, FLOAT, STATIC, PairRow, Quantized
from satreg.texture import fractal_texture
from satreg.weights import RELEASED_ONNX

REPO = Path(__file__).parents[1]
CONFIGS = REPO / "configs"

needs_quantization = pytest.mark.skipif(
    bool(quantize.missing_modules()),
    reason="needs the onnx extra: make install-onnx",
)

# A toy validation set: two chips, two scenarios, two presets, eight cells.
CHIPS = {name: fractal_texture(256, seed=i) for i, name in enumerate(("town", "shore"))}
PRESETS = {
    name: preset
    for name, preset in load_presets(CONFIGS / "degradations.toml").items()
    if name in ("clean", "hard")
}
CONFIG = BenchmarkConfig(
    n_pairs=2, size=128, seed=0, scenarios=("translation", "dense"), warmup=1, repeats=1
)
CELLS = len(CHIPS) * len(CONFIG.scenarios) * len(PRESETS)
# The calibration pair of the toy set: the first one past its two scored pairs.
INDEX = CONFIG.n_pairs
FLOAT_NAME = f"raft_small_r{COUNT}"


@pytest.fixture(scope="module")
def floats(tmp_path_factory):
    """RAFT small exported once with two refinements."""
    out = tmp_path_factory.mktemp("float")
    onnxexport.export_checked(SMALL, "raft_small", COUNT, out)
    return out / f"{FLOAT_NAME}.onnx"


@pytest.fixture(scope="module")
def copies(floats):
    """Its static copy, calibrated on the toy set, and its dynamic copy."""
    pairs = quantize.calibration_pairs(CHIPS, CONFIG, PRESETS, INDEX)
    return {
        STATIC: quantize.quantize(floats, STATIC, floats.parent, pairs, INDEX),
        DYNAMIC: quantize.quantize(floats, DYNAMIC, floats.parent),
    }


def test_a_name_says_how_a_file_is_quantized_and_from_which():
    assert quantize.kind_of("raft_large_ft_r12") == FLOAT
    assert quantize.kind_of("raft_large_ft_r12_int8") == STATIC
    assert quantize.kind_of("raft_large_ft_r12_int8_dynamic") == DYNAMIC
    assert quantize.float_twin("raft_ft_onnx_int8") == "raft_ft_onnx"
    assert quantize.float_twin("raft_ft_onnx_int8_dynamic") == "raft_ft_onnx"
    with pytest.raises(ValueError, match="raft_ft_onnx is not an int8 name"):
        quantize.float_twin("raft_ft_onnx")


def test_calibration_takes_one_pair_of_every_cell_and_none_that_is_scored():
    pairs = quantize.calibration_pairs(CHIPS, CONFIG, PRESETS, INDEX)

    longer = BenchmarkConfig(
        n_pairs=INDEX + 1, size=128, seed=0, scenarios=CONFIG.scenarios
    )
    drawn = list(simulated_pairs(CHIPS, longer, PRESETS))
    expected = [pair for labels, pair in drawn if labels["pair"] == INDEX]
    assert len(pairs) == CELLS
    for found, pair in zip(pairs, expected, strict=True):
        np.testing.assert_array_equal(found.reference, pair.reference)
        np.testing.assert_array_equal(found.moving, pair.moving)
    # The scored pairs are the ones before it: none is a calibration pair.
    for _, scored in simulated_pairs(CHIPS, CONFIG, PRESETS):
        assert not any(np.array_equal(scored.moving, pair.moving) for pair in pairs)
    with pytest.raises(ValueError, match="non-negative index, got -1"):
        quantize.calibration_pairs(CHIPS, CONFIG, PRESETS, -1)


def test_the_calibration_chunk_never_divides_the_pair_count():
    for pairs in range(1, 80):
        chunk = quantize._chunk(pairs)

        assert chunk >= quantize.CALIBRATION_CHUNK
        assert pairs % chunk


@needs_raft
@needs_onnx
def test_a_static_copy_computes_on_integers_all_but_the_flow_and_the_lookup(
    floats, copies
):
    import onnx

    graph = onnx.load(str(floats))
    convolutions = [node.name for node in graph.graph.node if node.op_type == "Conv"]
    kept = quantize.quantized_convolutions(graph)
    lookups = sum(node.op_type == "GridSample" for node in graph.graph.node)
    path = floats.parent / f"{FLOAT_NAME}_int8.onnx"

    assert copies[STATIC] == Quantized(
        name=f"{FLOAT_NAME}_int8",
        source=FLOAT_NAME,
        kind=STATIC,
        megabytes=path.stat().st_size / 1e6,
        source_megabytes=floats.stat().st_size / 1e6,
        convolutions=len(convolutions),
        int8_convolutions=len(kept),
        float_lookups=lookups,
        calibration_pairs=CELLS,
        sha256=file_sha256(path),
        source_sha256=file_sha256(floats),
    )
    # At each refinement, the convolution that reads the flow and the one that
    # writes its update stay in float; the small model has no upsampling mask.
    left = set(convolutions) - set(kept)
    assert len(left) == 2 * COUNT
    assert all(any(edge in name for edge in quantize.FLOW_EDGES) for name in left)
    assert lookups == 4 * COUNT
    assert path.stat().st_size < floats.stat().st_size


@needs_raft
@needs_onnx
def test_a_dynamic_copy_stores_every_convolution_as_integers(floats, copies):
    path = floats.parent / f"{FLOAT_NAME}_int8_dynamic.onnx"
    static, dynamic = copies[STATIC], copies[DYNAMIC]

    assert dynamic.name == path.stem
    assert (dynamic.kind, dynamic.calibration_pairs) == (DYNAMIC, 0)
    assert dynamic.int8_convolutions == dynamic.convolutions == static.convolutions
    assert dynamic.float_lookups == static.float_lookups
    assert dynamic.sha256 == file_sha256(path)
    assert path.stat().st_size < floats.stat().st_size


@needs_raft
@needs_onnx
def test_a_copy_says_what_its_float_file_says_and_how_it_was_quantized(floats, copies):
    said = RaftOnnx(file=str(floats)).described()
    origin = {"quantized_from_sha256": file_sha256(floats)}

    assert said["iterations"] == str(COUNT)
    static = RaftOnnx(file=str(floats.parent / f"{copies[STATIC].name}.onnx"))
    assert static.described() == said | origin | {
        "quantization": "static",
        "calibration_method": "minmax",
        "calibration_pairs": str(CELLS),
        "calibration_pair_index": str(INDEX),
    }
    dynamic = RaftOnnx(file=str(floats.parent / f"{copies[DYNAMIC].name}.onnx"))
    assert dynamic.described() == said | origin | {"quantization": "dynamic"}


@needs_raft
@needs_onnx
def test_a_copy_is_read_next_to_its_float_file_on_the_same_pairs(floats, copies):
    methods = {
        name: RaftOnnx(file=str(floats.parent / f"{name}.onnx"), threads=1)
        for name in (FLOAT_NAME, copies[STATIC].name, copies[DYNAMIC].name)
    }

    rows = quantize.read_pairs(methods, simulated_pairs(CHIPS, CONFIG, PRESETS), CONFIG)

    assert [row.method for row in rows] == list(methods) * CELLS * CONFIG.n_pairs
    for row in rows:
        assert row.time_ms > 0
        if row.method == FLOAT_NAME:
            assert math.isnan(row.moved_px)
        else:
            # Another flow than the float file's. How near is read on the
            # fine-tuned models, not on this one at 2 refinements.
            assert row.moved_px > 0
    readings = quantize.summarize(rows, dict.fromkeys(methods, 1.0))
    assert [reading.kind for reading in readings] == [FLOAT, STATIC, DYNAMIC]
    assert all(reading.pairs == CELLS * CONFIG.n_pairs for reading in readings)


@needs_raft
@needs_onnx
def test_quantizing_again_writes_the_same_file_and_nothing_else(
    tmp_path, monkeypatch, floats, copies
):
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)
    shutil.copy(floats, tmp_path / floats.name)
    pairs = quantize.calibration_pairs(CHIPS, CONFIG, PRESETS, INDEX)

    again = quantize.quantize(tmp_path / floats.name, STATIC, tmp_path, pairs, INDEX)

    assert again == copies[STATIC]
    assert {path.name for path in tmp_path.iterdir()} == {
        "work",
        floats.name,
        f"{FLOAT_NAME}_int8.onnx",
    }
    # The quantizer's shape inference leaves its files where it runs.
    assert not list(work.iterdir())


@needs_quantization
def test_a_file_is_not_quantized_from_nothing(tmp_path):
    missing = tmp_path / "nothing.onnx"

    with pytest.raises(ValueError, match="quantized static or dynamic, not 'half'"):
        quantize.quantize(missing, "half", tmp_path)
    with pytest.raises(ValueError, match="a static copy needs calibration pairs"):
        quantize.quantize(missing, STATIC, tmp_path)
    with pytest.raises(FileNotFoundError, match="write it with satreg export"):
        quantize.quantize(missing, DYNAMIC, tmp_path)

    assert not list(tmp_path.iterdir())


def toy(dx):
    def method(reference, moving):
        method.calls += 1
        return Translation(dx=dx, dy=0.0)

    method.calls = 0
    return method


def test_every_method_runs_on_a_pair_before_any_runs_on_the_next():
    methods = {"toy": toy(1.0), "toy_int8": toy(1.25), "toy_int8_dynamic": toy(0.5)}
    config = BenchmarkConfig(
        n_pairs=3, size=64, seed=0, scenarios=("translation",), warmup=2, repeats=3
    )
    pairs = list(simulated_pairs(CHIPS, config, {"clean": PRESETS["clean"]}))

    rows = quantize.read_pairs(methods, pairs, config)

    assert [(row.site, row.pair, row.method) for row in rows] == [
        (site, pair, name) for site in CHIPS for pair in range(3) for name in methods
    ]
    assert {(row.scenario, row.degradation) for row in rows} == {
        ("translation", "clean")
    }
    # The distance to the float twin's flow, whatever the truth is.
    moved = {row.method: row.moved_px for row in rows[:3]}
    assert math.isnan(moved["toy"])
    assert moved["toy_int8"] == pytest.approx(0.25)
    assert moved["toy_int8_dynamic"] == pytest.approx(0.5)
    # Warmed up on the first pair only; on each, timed three times and called
    # once more for its memory.
    assert {method.calls for method in methods.values()} == {2 + 4 * len(pairs)}


def test_a_copy_is_not_read_without_its_float_twin_before_it():
    config = BenchmarkConfig(n_pairs=1, size=64, scenarios=("translation",))
    pairs = list(simulated_pairs(CHIPS, config, {"clean": PRESETS["clean"]}))
    message = "toy_int8 needs its float twin, toy, read before it"

    with pytest.raises(ValueError, match=message):
        quantize.read_pairs({"toy_int8": toy(1.0)}, pairs, config)
    with pytest.raises(ValueError, match=message):
        quantize.read_pairs({"toy_int8": toy(1.0), "toy": toy(1.0)}, pairs, config)


def row(method, pair, epe, time_ms, moved=math.nan, degradation="clean", failed=False):
    return PairRow(
        "town", "dense", degradation, pair, method, epe, failed, time_ms, moved
    )


ROWS = [
    row("toy", 0, 0.10, 100.0),
    row("toy_int8", 0, 0.12, 50.0, moved=0.02),
    row("toy", 1, 0.20, 300.0),
    row("toy_int8", 1, 0.26, 180.0, moved=0.06),
    row("toy", 0, 0.30, 200.0, degradation="hard"),
    row("toy_int8", 0, 3.0, 120.0, moved=2.5, degradation="hard", failed=True),
]


def test_a_reading_is_one_line_per_method_with_its_share_of_the_float_time():
    floating, copy = quantize.summarize(
        ROWS, {"toy": 20.0, "toy_int8": 7.0}, {"toy_int8": 40.0}
    )

    assert (floating.method, floating.kind, floating.megabytes) == ("toy", FLOAT, 20.0)
    assert (floating.pairs, floating.failure_rate) == (3, 0.0)
    assert floating.mean_epe == pytest.approx(0.2)
    assert floating.time_ms == 200.0
    for name in ("time_share", "moved_px", "moved_worst_px", "memory_mib"):
        assert math.isnan(getattr(floating, name))
    assert (copy.method, copy.kind, copy.megabytes) == ("toy_int8", STATIC, 7.0)
    assert copy.failure_rate == pytest.approx(1 / 3)
    # The error of the pairs it did not fail; the flow moved on every pair.
    assert copy.mean_epe == pytest.approx(0.19)
    assert (copy.time_ms, copy.time_share) == (120.0, pytest.approx(0.6))
    assert copy.moved_px == pytest.approx(0.86)
    assert copy.moved_worst_px == 2.5
    assert copy.memory_mib == 40.0


def test_the_table_of_a_reading_puts_each_float_file_above_its_copies():
    megabytes = {"toy": 20.0, "toy_int8": 7.0, "other": 4.0, "other_int8_dynamic": 2.0}
    rows = [
        row("toy", 0, 0.1, 100.0),
        row("other", 0, 0.2, 40.0),
        row("other_int8_dynamic", 0, 0.25, 30.0, moved=0.1),
        row("toy_int8", 0, 0.12, 50.0, moved=0.02),
    ]

    table = quantize.to_markdown(quantize.summarize(rows, megabytes))

    assert table.splitlines()[2:] == [
        "| toy | float | 20.0 | 0.0 % | 0.1000 | 100.0 |  |  |  |  |",
        "| toy_int8 | static | 7.0 | 0.0 % | 0.1200 | 50.0 | 0.50 | 0.0200 | 0.0200 "
        "|  |",
        "| other | float | 4.0 | 0.0 % | 0.2000 | 40.0 |  |  |  |  |",
        "| other_int8_dynamic | dynamic | 2.0 | 0.0 % | 0.2500 | 30.0 | 0.75 | 0.1000 "
        "| 0.1000 |  |",
    ]


def test_the_error_of_a_reading_is_also_given_preset_by_preset():
    assert quantize.by_degradation(ROWS).splitlines() == [
        "| method | clean: EPE (px), failed | hard: EPE (px), failed |",
        "|---|---:|---:|",
        "| toy | 0.1500, 0 of 2 | 0.3000, 0 of 1 |",
        "| toy_int8 | 0.1900, 0 of 2 | , 1 of 1 |",
    ]


def options(cached, *names):  # noqa: F811
    """The options of ``names`` among those of the ``cached`` fixture."""
    given = dict(zip(cached[::2], cached[1::2], strict=True))
    return [word for name in names for word in (name, given[name])]


DRAWING = ["--size", "128", "--scenarios", "translation", "--degradations"]
DRAWING += [
    "clean",
    "hard",
    "--degradations-config",
    str(CONFIGS / "degradations.toml"),
]
CHIP_OPTIONS = ("--sites-config", "--train-config", "--series-config", "--data-dir")


def quantize_args(tmp_path, cached, *more):  # noqa: F811
    return [
        "quantize",
        "--onnx",
        str(tmp_path / "onnx"),
        "--out",
        str(tmp_path / "files"),
        *DRAWING,
        *options(cached, *CHIP_OPTIONS),
        *more,
    ]


def test_quantize_refuses_what_it_cannot_write(tmp_path, monkeypatch, cached):  # noqa: F811
    # What is refused below is refused before onnx is imported: the same with
    # and without the onnx extra.
    monkeypatch.setattr(quantize, "missing_modules", lambda: [])
    with pytest.raises(SystemExit, match="quantize needs --static or --dynamic files"):
        main(quantize_args(tmp_path, cached))
    missing = tmp_path / "onnx" / "nothing.onnx"
    with pytest.raises(SystemExit, match=f"no export at {missing}: write it with"):
        main(quantize_args(tmp_path, cached, "--dynamic", "nothing"))
    with pytest.raises(SystemExit, match="need a --calibration-pair of at least 0"):
        main(
            quantize_args(tmp_path, cached, "--static", "a", "--calibration-pair", "-1")
        )
    monkeypatch.setattr(quantize, "missing_modules", lambda: ["onnx"])
    with pytest.raises(SystemExit, match="quantize needs onnx, not installed"):
        main(quantize_args(tmp_path, cached, "--dynamic", "nothing"))

    assert not (tmp_path / "files").exists()


def methods_config(tmp_path):
    """Declare the toy float file and its two copies as methods."""
    path = tmp_path / "methods.toml"
    path.write_text(
        "".join(
            f'[methods.toy{suffix}]\nmethod = "raft_onnx"\nthreads = 1\n'
            f'file = "{tmp_path / "onnx" / f"{FLOAT_NAME}{suffix}.onnx"}"\n'
            for suffix in ("", "_int8", "_int8_dynamic")
        )
        + '[methods.plain]\nmethod = "sift_ransac"\n'
        + '[methods.plain_int8]\nmethod = "sift_ransac"\n'
    )
    return path


def int8_args(tmp_path, cached, *more):  # noqa: F811
    return [
        "int8",
        "--methods-config",
        str(methods_config(tmp_path)),
        "--out",
        str(tmp_path / "reading"),
        *DRAWING,
        *options(cached, *CHIP_OPTIONS),
        *more,
    ]


@needs_raft
@needs_onnx
def test_quantize_then_int8_write_the_copies_and_read_them(
    tmp_path,
    capsys,
    floats,
    cached,  # noqa: F811
):
    (tmp_path / "onnx").mkdir()
    shutil.copy(floats, tmp_path / "onnx" / floats.name)
    both = ["--static", FLOAT_NAME, "--dynamic", FLOAT_NAME]

    main(quantize_args(tmp_path, cached, *both, "--calibration-pair", "2"))

    printed = capsys.readouterr().out
    files = tmp_path / "files"
    assert printed == (files / "summary.md").read_text()
    assert "minmax on 2 pairs, pair 2 of every chip, scenario and preset" in printed
    static = tmp_path / "onnx" / f"{FLOAT_NAME}_int8.onnx"
    dynamic = tmp_path / "onnx" / f"{FLOAT_NAME}_int8_dynamic.onnx"
    for path, kind in ((static, "static"), (dynamic, "dynamic")):
        assert f"| `{path.name}` | `{floats.name}` | {kind} |" in printed
        assert f"`{file_sha256(path)}`" in printed
    assert len((files / "files.csv").read_text().splitlines()) == 1 + 2
    context = json.loads((files / "context.json").read_text())
    assert context["calibration"] == {
        "method": "minmax",
        "pairs": 2,
        "pair_index": 2,
        "chips": context["calibration"]["chips"],
        "float_convolutions": list(quantize.FLOW_EDGES),
    }
    assert list(context["calibration"]["chips"]) == ["town"]

    reading = ["--methods", "toy_int8_dynamic", "toy_int8", "--pairs", "2"]
    main(int8_args(tmp_path, cached, *reading))

    printed = capsys.readouterr().out
    out = tmp_path / "reading"
    assert printed == (out / "summary.md").read_text()
    assert "the first 2 pairs of every chip, scenario and preset" in printed
    assert "validation set (town), seed 0: 4 pairs." in printed
    lines = [line for line in printed.splitlines() if line.startswith("| toy")]
    # The float twin first, then its copies in the order they were asked for.
    assert [line.split(" | ")[:2] for line in lines[:3]] == [
        ["| toy", "float"],
        ["| toy_int8_dynamic", "dynamic"],
        ["| toy_int8", "static"],
    ]
    assert len((out / "pairs.csv").read_text().splitlines()) == 1 + 4 * 3
    assert len((out / "summary.csv").read_text().splitlines()) == 1 + 3
    context = json.loads((out / "context.json").read_text())
    assert list(context["validation"]["chips"]) == ["town"]
    assert context["validation"]["pairs_per_cell"] == 2
    assert context["footprints"] is None
    megabytes = {"toy": floats, "toy_int8_dynamic": dynamic, "toy_int8": static}
    assert context["megabytes"] == {
        name: path.stat().st_size / 1e6 for name, path in megabytes.items()
    }

    # Pair 2 is the one the static copy was calibrated on.
    with pytest.raises(SystemExit, match="toy_int8 was calibrated on pair 2 of every"):
        main(int8_args(tmp_path, cached, "--methods", "toy_int8", "--pairs", "3"))
    with pytest.raises(SystemExit, match="satreg: no footprints at nothing.csv"):
        main(int8_args(tmp_path, cached, *reading, "--footprints", "nothing.csv"))


def test_int8_reads_int8_onnx_methods_only(tmp_path, cached):  # noqa: F811
    with pytest.raises(SystemExit, match="named after their float twin .*: not toy"):
        main(int8_args(tmp_path, cached, "--methods", "toy_int8", "toy"))
    with pytest.raises(SystemExit, match="int8 reads ONNX methods, not plain, plain_"):
        main(int8_args(tmp_path, cached, "--methods", "plain_int8"))
    with pytest.raises(SystemExit, match="satreg: unknown method 'nothing'"):
        main(int8_args(tmp_path, cached, "--methods", "nothing_int8"))

    assert not (tmp_path / "reading").exists()


def test_the_repository_copies_are_calibrated_and_read_on_the_validation_set():
    validation = load_run_config(CONFIGS / "validation.toml", "validate")
    making = load_run_config(CONFIGS / "quantization.toml", "quantize")
    reading = load_run_config(CONFIGS / "quantization.toml", "int8")

    # The pairs of the validation set: its chips, cells, ranges and seed.
    drawn = ["chips", "scenarios", "degradations", "size", "seed"]
    drawn += [key for key in validation if key.startswith(("max_", "local_"))]
    drawn += ["train_config", "series_config", "sites_config", "degradations_config"]
    for table in (making, reading):
        assert {key: table[key] for key in drawn} == {
            key: validation[key] for key in drawn
        }
    # Read on the light set, calibrated on the first pair past it.
    assert reading["pairs"] == validation["light_pairs"]
    assert making["calibration_pair"] == reading["pairs"] < validation["pairs"]
    assert making["calibration_pair"] == quantize.CALIBRATION_PAIR
    assert reading["failure_threshold"] == validation["failure_threshold"]


def test_each_repository_copy_is_a_method_named_after_its_float_twin():
    methods = load_methods(CONFIGS / "methods.toml")
    making = load_run_config(CONFIGS / "quantization.toml", "quantize")
    reading = load_run_config(CONFIGS / "quantization.toml", "int8")

    def stem(name):
        method = methods[name]
        return method.release or Path(method.file).stem

    written = {
        f"{name}{quantize.SUFFIXES[kind]}"
        for kind in (STATIC, DYNAMIC)
        for name in making[kind]
    }
    # Every file quantize writes is read, as a method on as many threads as
    # the float one it is named after, which runs the file it was made from.
    assert {stem(name) for name in reading["methods"]} == written
    for name in reading["methods"]:
        twin = quantize.float_twin(name)
        assert isinstance(methods[name], RaftOnnx)
        assert methods[name].threads == methods[twin].threads == 4
        assert quantize.float_twin(stem(name)) == stem(twin)
        if methods[name].file:
            assert Path(methods[name].file).parent == Path(making["onnx"])
    int8 = {name for name in methods if quantize.kind_of(name) != FLOAT}
    assert int8 == set(reading["methods"])
    # A published copy is the copy of a published float file.
    for name, published in RELEASED_ONNX.items():
        assert published.int8 == (quantize.kind_of(name) == STATIC)
        if published.int8:
            twin = RELEASED_ONNX[quantize.float_twin(name)]
            assert (twin.weights, twin.refinements, twin.tag) == (
                published.weights,
                published.refinements,
                published.tag,
            )


def test_quantize_and_int8_read_their_own_table():
    making = parse_args(["quantize", "--config", str(CONFIGS / "quantization.toml")])
    reading = parse_args(["int8", "--config", str(CONFIGS / "quantization.toml")])
    tables = tomllib.loads((CONFIGS / "quantization.toml").read_text())

    assert making.static == tables["quantize"]["static"]
    assert making.dynamic == tables["quantize"]["dynamic"]
    assert (making.onnx, making.out) == (
        Path("outputs/onnx"),
        Path("outputs/quantization/files"),
    )
    assert reading.methods == tables["int8"]["methods"]
    assert (reading.pairs, reading.warmup, reading.repeats) == (10, 1, 1)
    assert reading.out == Path("outputs/quantization")


def test_make_int8_reads_the_memory_of_the_copies_and_of_their_float_twins():
    recipe = (REPO / "Makefile").read_text()
    reading = load_run_config(CONFIGS / "quantization.toml", "int8")
    twins = dict.fromkeys(quantize.float_twin(name) for name in reading["methods"])

    assert f"\nINT8 = {' '.join(reading['methods'])}\n" in recipe
    assert f"\nINT8_FLOAT = {' '.join(twins)}\n" in recipe
    assert (
        "satreg footprint --methods $(INT8_FLOAT) $(INT8) "
        "--out $(QUANTIZATION)/footprint\n"
    ) in recipe

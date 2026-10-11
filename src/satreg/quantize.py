"""Quantize exported RAFT files to 8-bit integers, and read what it costs.

An exported file computes in 32-bit floats. Its int8 copy stores weights, and
for a static copy the values between layers too, as 8-bit integers with a scale:
a smaller file and cheaper convolutions, and a flow that moves a little. A
static copy needs example pairs to set its scales on, the calibration; a dynamic
copy needs none and works its scales out at each call.

The static setting quantizes the convolutions only, each with one scale per
output channel, and leaves in float the few that read the flow or write its
update: quantizing everything breaks the flow. ONNX Runtime has no int8
``GridSample``, RAFT's correlation lookup, which stays in float either way.
See docs/decisions.md. Needs the ``onnx`` extra.
"""

import contextlib
import dataclasses
import importlib.util
import itertools
import logging
import math
import tempfile
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .benchmark import BenchmarkConfig, simulated_pairs
from .compute import file_sha256, measure
from .degrade import Degradation
from .methods import Method, cost_meter
from .methods.raft import network_input
from .methods.raft_onnx import INPUTS
from .metrics import is_failure, score
from .simulate import SimulatedPair
from .weights import INT8_SUFFIX

# Modules a quantization needs: one reads and writes the graphs, the other
# quantizes them.
REQUIRED_MODULES = ("onnx", "onnxruntime")

# The two ways a file is quantized, and what each adds to the name of the float
# file, and to the name of its method in configs/methods.toml.
STATIC = "static"
DYNAMIC = "dynamic"
SUFFIXES = {STATIC: INT8_SUFFIX, DYNAMIC: f"{INT8_SUFFIX}_dynamic"}

# What the reading calls a file that is not quantized.
FLOAT = "float"

# Convolutions a static copy leaves in float, by a part of their name: the one
# that reads the flow, at each refinement, the one that writes its update, and
# the one that writes the weights the flow is upsampled with. A flow is a few
# pixels read to a hundredth, which 256 levels do not hold.
FLOW_EDGES = ("/motion_encoder/convflow1/", "/flow_head/conv2", "/mask_predictor/conv/")

# How the scales of a static copy are set: on the smallest and the largest
# value each tensor took over the calibration pairs.
CALIBRATION_METHOD = "minmax"

# Index of the calibration pair in each cell of the validation set: the first
# one past the light set, whose pairs 0 to 9 the copies are then scored on.
CALIBRATION_PAIR = 10

# Calibration pairs whose values ONNX Runtime holds at once, at least. It keeps
# every tensor of every pair until told to fold them into ranges.
CALIBRATION_CHUNK = 8


@dataclass(frozen=True)
class Quantized:
    """One int8 file and where it comes from.

    Attributes:
        name: The file's name without its suffix.
        source: The float file's, without its suffix.
        kind: ``"static"`` or ``"dynamic"``.
        megabytes: Size of the file, in MB.
        source_megabytes: Size of the float file, in MB.
        convolutions: Convolutions of the graph.
        int8_convolutions: Those computed on 8-bit integers.
        float_lookups: ``GridSample`` nodes, all left in float.
        calibration_pairs: Pairs the scales were set on, 0 for a dynamic file.
        sha256: SHA-256 of the file.
        source_sha256: SHA-256 of the float file.
    """

    name: str
    source: str
    kind: str
    megabytes: float
    source_megabytes: float
    convolutions: int
    int8_convolutions: int
    float_lookups: int
    calibration_pairs: int
    sha256: str
    source_sha256: str


def missing_modules() -> list[str]:
    """Name the modules a quantization needs that are not installed."""
    return [name for name in REQUIRED_MODULES if importlib.util.find_spec(name) is None]


def kind_of(name: str) -> str:
    """Tell how a file or a method is quantized, from its name.

    Returns:
        ``"static"``, ``"dynamic"`` or ``"float"``.
    """
    # The dynamic suffix ends a name the static one is part of.
    for kind in (DYNAMIC, STATIC):
        if name.endswith(SUFFIXES[kind]):
            return kind
    return FLOAT


def float_twin(name: str) -> str:
    """Name the float file, or method, an int8 one was made from.

    Raises:
        ValueError: If ``name`` is not the name of an int8 file or method.
    """
    kind = kind_of(name)
    if kind == FLOAT:
        raise ValueError(
            f"{name} is not an int8 name: one ends in {' or '.join(SUFFIXES.values())}"
        )
    return name.removesuffix(SUFFIXES[kind])


def calibration_pairs(
    chips: Mapping[str, np.ndarray],
    config: BenchmarkConfig,
    degradations: Mapping[str, Degradation],
    index: int = CALIBRATION_PAIR,
) -> list[SimulatedPair]:
    """Draw the calibration pairs: one per chip, scenario and preset.

    Every preset is there: scales set on clean pairs alone are too narrow for
    the degraded ones, whose flow then fails.

    Args:
        chips: Chip name to image. Validation chips: a benchmark chip or a
            held-out site here would leak into the files.
        config: How the validation pairs are drawn; its pair count is not read.
        degradations: Preset name to preset.
        index: Index of the pair kept in each cell.

    Returns:
        The pairs, in the order the validation set scores its cells.

    Raises:
        ValueError: If ``index`` is negative.
    """
    if index < 0:
        raise ValueError(f"the calibration pair has a non-negative index, got {index}")
    drawn = simulated_pairs(
        chips, dataclasses.replace(config, n_pairs=index + 1), degradations
    )
    return [pair for labels, pair in drawn if labels["pair"] == index]


def feed(pair: SimulatedPair) -> dict[str, np.ndarray]:
    """The inputs of an exported file for a pair, as the method prepares them."""
    images = (pair.reference, pair.moving)
    return {
        name: network_input(image)[np.newaxis]
        for name, image in zip(INPUTS, images, strict=True)
    }


def quantized_convolutions(graph: Any) -> list[str]:
    """Name the convolutions a static copy computes on integers.

    Args:
        graph: A float file, loaded by ``onnx``.

    Returns:
        Every convolution but the ones of ``FLOW_EDGES``.
    """
    return [
        node.name
        for node in graph.graph.node
        if node.op_type == "Conv" and not any(edge in node.name for edge in FLOW_EDGES)
    ]


def _counts(graph: Any) -> dict[str, int]:
    """Count the convolutions of a graph, the int8 ones, and its lookups."""
    nodes = graph.graph.node
    # A static copy keeps its convolutions, between nodes that turn integers
    # to floats and back: the runtime merges the three into one integer
    # convolution. One whose weights are stored as integers is such a one.
    stored = {
        output
        for node in nodes
        if node.op_type == "DequantizeLinear"
        for output in node.output
    }
    integer = sum(
        node.op_type == "ConvInteger"
        or (node.op_type == "Conv" and node.input[1] in stored)
        for node in nodes
    )
    return {
        "convolutions": sum(node.op_type in ("Conv", "ConvInteger") for node in nodes),
        "int8_convolutions": integer,
        "float_lookups": sum(node.op_type == "GridSample" for node in nodes),
    }


def _chunk(pairs: int) -> int:
    """How many calibration pairs ONNX Runtime folds into ranges at a time.

    Never a divisor of the pair count: ONNX Runtime then ends on an empty
    chunk and raises "No data is collected".
    """
    return next(size for size in itertools.count(CALIBRATION_CHUNK) if pairs % size)


def _reader(feeds: Iterable[dict[str, np.ndarray]]) -> Any:
    """Hand calibration inputs to ONNX Runtime, one pair at a time."""
    from onnxruntime.quantization import CalibrationDataReader

    class Reader(CalibrationDataReader):
        """The pairs, until there is none left."""

        def __init__(self) -> None:
            self._feeds = iter(feeds)

        def get_next(self) -> dict[str, np.ndarray] | None:
            return next(self._feeds, None)

    return Reader()


@contextlib.contextmanager
def _quiet() -> Iterator[None]:
    """Keep the quantizer's notes out of the log: it writes one line per tensor
    it leaves in float to the root logger."""
    root = logging.getLogger()
    level = root.level
    root.setLevel(max(level, logging.ERROR))
    try:
        yield
    finally:
        root.setLevel(level)


def _quantize_static(source: Path, path: Path, pairs: Sequence[SimulatedPair]) -> None:
    """Write the static int8 copy of a float file."""
    import onnx
    from onnxruntime import quantization

    with tempfile.TemporaryDirectory() as scratch, _quiet():
        # Constants folded and shapes inferred, as the quantizer asks. Not its
        # symbolic shape inference, which fails on RAFT's graph and leaves
        # files in the working directory.
        prepared = Path(scratch) / "prepared.onnx"
        quantization.quant_pre_process(
            str(source), str(prepared), skip_symbolic_shape=True
        )
        quantization.quantize_static(
            str(prepared),
            str(path),
            _reader(feed(pair) for pair in pairs),
            quant_format=quantization.QuantFormat.QDQ,
            nodes_to_quantize=quantized_convolutions(onnx.load(str(prepared))),
            per_channel=True,
            activation_type=quantization.QuantType.QInt8,
            weight_type=quantization.QuantType.QInt8,
            calibrate_method=quantization.CalibrationMethod.MinMax,
            extra_options={"CalibMaxIntermediateOutputs": _chunk(len(pairs))},
        )


def _quantize_dynamic(source: Path, path: Path) -> None:
    """Write the dynamic int8 copy of a float file."""
    from onnxruntime import quantization

    with _quiet():
        quantization.quantize_dynamic(
            str(source), str(path), weight_type=quantization.QuantType.QInt8
        )


def quantize(
    source: Path,
    kind: str,
    out: Path,
    pairs: Sequence[SimulatedPair] = (),
    pair_index: int = CALIBRATION_PAIR,
) -> Quantized:
    """Write the int8 copy of a float file, and say what it is in its metadata.

    The copy keeps what the float file says of itself and adds how it was
    quantized, from which file, and for a static copy on how many pairs.

    Args:
        source: The float file, as ``satreg export`` wrote it.
        kind: ``"static"`` or ``"dynamic"``.
        out: Directory the copy is written to, named after the float file and
            its kind.
        pairs: Calibration pairs of a static copy.
        pair_index: Their index in each cell of the validation set, written to
            the file so that it is not scored on them.

    Returns:
        The copy and its float file.

    Raises:
        ValueError: If ``kind`` is neither, or a static copy has no pair.
        FileNotFoundError: If the float file is not there.
    """
    import onnx

    if kind not in SUFFIXES:
        raise ValueError(f"a file is quantized {STATIC} or {DYNAMIC}, not {kind!r}")
    if kind == STATIC and not pairs:
        raise ValueError("a static copy needs calibration pairs")
    if not source.is_file():
        raise FileNotFoundError(
            f"no float file at {source}: write it with satreg export"
        )
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{source.stem}{SUFFIXES[kind]}.onnx"
    said = {"quantization": kind, "quantized_from_sha256": file_sha256(source)}
    if kind == STATIC:
        _quantize_static(source, path, pairs)
        said |= {
            "calibration_method": CALIBRATION_METHOD,
            "calibration_pairs": str(len(pairs)),
            "calibration_pair_index": str(pair_index),
        }
    else:
        _quantize_dynamic(source, path)
    float_graph = onnx.load(str(source))
    graph = onnx.load(str(path))
    described = {entry.key: entry.value for entry in float_graph.metadata_props}
    onnx.helper.set_model_props(graph, described | said)
    onnx.save(graph, str(path))
    return Quantized(
        name=path.stem,
        source=source.stem,
        kind=kind,
        megabytes=path.stat().st_size / 1e6,
        source_megabytes=source.stat().st_size / 1e6,
        **_counts(graph),
        calibration_pairs=len(pairs) if kind == STATIC else 0,
        sha256=file_sha256(path),
        source_sha256=said["quantized_from_sha256"],
    )


def files_markdown(rows: Sequence[Quantized]) -> str:
    """Render the int8 files as a table.

    Args:
        rows: The files.

    Returns:
        Markdown: one line per file, with its size, what of it is int8 and
        its hash.
    """
    lines = [
        "| file | from | kind | MB | float MB | int8 convolutions "
        "| float lookups | calibration pairs | SHA-256 |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    lines += [
        f"| `{row.name}.onnx` | `{row.source}.onnx` | {row.kind} | "
        f"{row.megabytes:.1f} | {row.source_megabytes:.1f} | "
        f"{row.int8_convolutions} of {row.convolutions} | {row.float_lookups} | "
        f"{row.calibration_pairs or ''} | `{row.sha256}` |"
        for row in rows
    ]
    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class PairRow:
    """One method on one pair of the reading.

    Attributes:
        site: Chip the pair is cut from.
        scenario: Geometric model of the pair.
        degradation: Its preset.
        pair: Its index in the cell.
        method: The method.
        mean_epe: Mean end-point error of its flow, in px.
        failed: Whether the pair counts as a failure.
        time_ms: Time of the call, in ms: the median of the timed ones.
        moved_px: For an int8 method, mean distance between its flow and its
            float twin's over the valid pixels, in px; NaN for a float method.
    """

    site: str
    scenario: str
    degradation: str
    pair: int
    method: str
    mean_epe: float
    failed: bool
    time_ms: float
    moved_px: float


def read_pairs(
    methods: Mapping[str, Method],
    pairs: Iterable[tuple[Mapping[str, str | int], SimulatedPair]],
    config: BenchmarkConfig,
) -> list[PairRow]:
    """Run int8 methods and their float twins on the same pairs, in turn.

    Every method runs on a pair before any runs on the next, as in the
    benchmark: a machine that warms up during the reading slows them all
    alike, and the times compare.

    Args:
        methods: Method name to method: int8 ones, named after their float
            twin (``float_twin``), and those twins, each before its copies.
        pairs: Labels and pair, as ``simulated_pairs`` draws them.
        config: Failure threshold, warm-up and repeat count.

    Returns:
        One row per pair and method.

    Raises:
        ValueError: If an int8 method comes without its twin, or before it.
    """
    twins = {name: float_twin(name) for name in methods if kind_of(name) != FLOAT}
    order = list(methods)
    for name, twin in twins.items():
        if twin not in methods or order.index(twin) > order.index(name):
            raise ValueError(f"{name} needs its float twin, {twin}, read before it")
    rows = []
    warmup = config.warmup
    for labels, pair in pairs:
        shape = pair.reference.shape
        estimates: dict[str, Any] = {}
        for name, method in methods.items():

            def call(method: Method = method, pair: SimulatedPair = pair) -> object:
                return method(pair.reference, pair.moving)

            measured = measure(call, config.repeats, warmup, cost_meter(method))
            estimates[name] = measured.result()
            scored = score(pair.truth, estimates[name], shape, pair.valid)
            moved = math.nan
            if name in twins:
                twin = estimates[twins[name]]
                moved = score(twin, estimates[name], shape, pair.valid).mean_epe
            rows.append(
                PairRow(
                    site=str(labels["site"]),
                    scenario=str(labels["scenario"]),
                    degradation=str(labels["degradation"]),
                    pair=int(labels["pair"]),
                    method=name,
                    mean_epe=scored.mean_epe,
                    failed=is_failure(scored, config.failure_threshold),
                    time_ms=1000 * measured.seconds,
                    moved_px=moved,
                )
            )
        warmup = 0
    return rows


@dataclass(frozen=True)
class Reading:
    """One method over the pairs of the reading.

    Attributes:
        method: The method.
        kind: ``"float"``, ``"static"`` or ``"dynamic"``.
        megabytes: Size of its file, in MB.
        pairs: Pairs it ran on.
        failure_rate: Share of them it failed.
        mean_epe: Its mean end-point error over the others, in px.
        time_ms: Median time of a call, in ms.
        time_share: That time over its float twin's in the same reading; NaN
            for a float method.
        moved_px: Mean over the pairs of the distance between its flow and its
            float twin's, in px; NaN for a float method.
        moved_worst_px: That distance on the pair where it is largest.
        memory_mib: What the method adds to a process of its own, in MiB; NaN
            if it was not read.
    """

    method: str
    kind: str
    megabytes: float
    pairs: int
    failure_rate: float
    mean_epe: float
    time_ms: float
    time_share: float
    moved_px: float
    moved_worst_px: float
    memory_mib: float


def _mean_epe(rows: Sequence[PairRow]) -> float:
    """Mean error over the pairs that did not fail; NaN if all did."""
    kept = [row.mean_epe for row in rows if not row.failed]
    return float(np.mean(kept)) if kept else math.nan


def summarize(
    rows: Sequence[PairRow],
    megabytes: Mapping[str, float],
    memory: Mapping[str, float] | None = None,
) -> list[Reading]:
    """Reduce the pairs of a reading to one line per method.

    Args:
        rows: The pairs, as ``read_pairs`` returns them.
        megabytes: Method name to the size of its file, in MB.
        memory: Method name to what it adds to a process of its own, in MiB,
            for the methods it was read for.

    Returns:
        One line per method, in the order they ran.
    """
    by_method: dict[str, list[PairRow]] = {}
    for row in rows:
        by_method.setdefault(row.method, []).append(row)
    times = {
        name: float(np.median([row.time_ms for row in own]))
        for name, own in by_method.items()
    }
    readings = []
    for name, own in by_method.items():
        kind = kind_of(name)
        moved = [row.moved_px for row in own]
        readings.append(
            Reading(
                method=name,
                kind=kind,
                megabytes=megabytes[name],
                pairs=len(own),
                failure_rate=sum(row.failed for row in own) / len(own),
                mean_epe=_mean_epe(own),
                time_ms=times[name],
                time_share=math.nan
                if kind == FLOAT
                else times[name] / times[float_twin(name)],
                moved_px=math.nan if kind == FLOAT else float(np.mean(moved)),
                moved_worst_px=math.nan if kind == FLOAT else float(np.max(moved)),
                memory_mib=(memory or {}).get(name, math.nan),
            )
        )
    return readings


def _cell(value: float, digits: int) -> str:
    """A figure of a table, empty where there is none."""
    return "" if math.isnan(value) else f"{value:.{digits}f}"


def to_markdown(readings: Sequence[Reading]) -> str:
    """Render a reading as a table, each float file above its int8 copies.

    Args:
        readings: One line per method.

    Returns:
        Markdown.
    """
    lines = [
        "| method | file | MB | failed | EPE (px) | time (ms) | time, share of "
        "float | flow moved (px) | on the worst pair (px) | memory (MiB) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    floats = [row for row in readings if row.kind == FLOAT]
    for twin in floats:
        copies = [
            row
            for row in readings
            if row.kind != FLOAT and float_twin(row.method) == twin.method
        ]
        lines += [
            f"| {row.method} | {row.kind} | {row.megabytes:.1f} | "
            f"{100 * row.failure_rate:.1f} % | {_cell(row.mean_epe, 4)} | "
            f"{row.time_ms:.1f} | {_cell(row.time_share, 2)} | "
            f"{_cell(row.moved_px, 4)} | {_cell(row.moved_worst_px, 4)} | "
            f"{_cell(row.memory_mib, 1)} |"
            for row in (twin, *copies)
        ]
    return "\n".join(lines) + "\n"


def by_degradation(rows: Sequence[PairRow]) -> str:
    """Render the error of each method under each preset.

    Args:
        rows: The pairs of a reading.

    Returns:
        Markdown: one line per method, and per preset its mean end-point error
        over the pairs it did not fail, with the count of those it failed.
    """
    presets = list(dict.fromkeys(row.degradation for row in rows))
    lines = [
        "| method | "
        + " | ".join(f"{preset}: EPE (px), failed" for preset in presets)
        + " |",
        "|---|" + "---:|" * len(presets),
    ]
    for method in dict.fromkeys(row.method for row in rows):
        cells = []
        for preset in presets:
            own = [
                row
                for row in rows
                if row.method == method and row.degradation == preset
            ]
            failed = sum(row.failed for row in own)
            cells.append(f"{_cell(_mean_epe(own), 4)}, {failed} of {len(own)}")
        lines.append(f"| {method} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"

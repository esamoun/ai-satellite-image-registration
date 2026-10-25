"""The cost curve of N3: what a RAFT model costs against how well it registers.

A point of the curve is a model (large or small), its weights (pretrained or
fine-tuned) and a number of refinements. Each point is two methods of
``configs/methods.toml``, the same model under PyTorch and under ONNX Runtime,
and is read from four places:

- the cost run, the ONNX Runtime methods on the light validation set, on the
  CPU: the curve's error, failure rate and time all come from this one run;
- the PyTorch run, the PyTorch methods on the same pairs and the same CPU: the
  table beside the curve, and the check that both runtimes run one model;
- the full run, the PyTorch methods on the full validation set, on any device:
  what fewer refinements do to a model trained with twelve;
- the footprints, what each method adds to the memory of a process of its own
  (``satreg.footprint``).

Nothing is run here. See docs/decisions.md.
"""

import csv
import json
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import ablation
from .ablation import PAIR_KEY, Key
from .footprint import Footprint
from .trainval import ALL_PRESETS

MODELS = ("large", "small")

# Refinements of the flow a point is run with. The last is the count RAFT is
# trained with, here as at torchvision: the methods named without a count.
REFINEMENTS = (4, 8, 12)
TRAINED_REFINEMENTS = 12

# What the name of a method run by ONNX Runtime ends with.
ONNX_SUFFIX = "_onnx"

# The device the curve's cost is read on.
COST_DEVICE = "cpu"

# Options of `satreg validate` that say which pairs a run scored: two runs
# with the same values scored the same pairs.
PAIRS_OPTIONS = (
    "chips",
    "scenarios",
    "degradations",
    "pairs",
    "light",
    "light_pairs",
    "size",
    "seed",
    "max_shift",
    "max_rotation",
    "max_scale_change",
    "max_shear",
    "max_local_shift",
    "local_length",
    "failure_threshold",
)
# What says it for a run of `satreg benchmark`, in place of the chips: the
# sites the pairs are cut from, and the bands of an inter-band run.
BENCHMARK_OPTIONS = ("sites", "band_pairs")


@dataclass(frozen=True)
class Point:
    """One point of the curve.

    Attributes:
        model: ``"large"`` or ``"small"``.
        fine_tuned: Whether the weights are the fine-tuned ones.
        refinements: Refinements of the flow.
    """

    model: str
    fine_tuned: bool
    refinements: int

    @property
    def torch(self) -> str:
        """The point's method under PyTorch, in ``configs/methods.toml``."""
        name = "raft" if self.model == "large" else f"raft_{self.model}"
        if self.fine_tuned:
            name += "_ft"
        if self.refinements != TRAINED_REFINEMENTS:
            name += f"_r{self.refinements}"
        return name

    @property
    def onnx(self) -> str:
        """The point's method under ONNX Runtime."""
        return self.torch + ONNX_SUFFIX

    @property
    def weights(self) -> str:
        """``"fine-tuned"`` or ``"pretrained"``."""
        return "fine-tuned" if self.fine_tuned else "pretrained"

    @property
    def series(self) -> str:
        """The line of the figure the point is on: its model and weights."""
        return f"RAFT {self.model}, {self.weights}"


# The curve decided on 2026-10-01: both models, pretrained and fine-tuned, with
# each refinement count.
POINTS = tuple(
    Point(model, fine_tuned, refinements)
    for model in MODELS
    for fine_tuned in (False, True)
    for refinements in REFINEMENTS
)


@dataclass(frozen=True)
class Pair:
    """One method on one pair, as a run's ``pairs.csv`` has it.

    Attributes:
        failed: Whether the pair counts as a failure.
        mean_epe: Mean end-point error, in px; NaN if the method raised.
        time_ms: Median time of the method's calls on the pair, in ms.
        peak_mib: Peak memory of a call as the method's meter reads it, in MiB;
            NaN if it has no figure.
    """

    failed: bool
    mean_epe: float
    time_ms: float
    peak_mib: float


Pairs = Mapping[Key, Pair]


@dataclass(frozen=True)
class Run:
    """A run of ``satreg validate``.

    Attributes:
        name: What the run is called in a message, its directory.
        pairs: Method name to its row on each pair.
        context: The run's ``context.json``.
    """

    name: str
    pairs: Mapping[str, Pairs]
    context: Mapping[str, object]


def read_run(path: Path) -> Run:
    """Read the pairs and the context of a run of ``satreg validate``.

    Args:
        path: Directory of the run.

    Returns:
        The run.

    Raises:
        FileNotFoundError: If the directory has no ``pairs.csv`` or no
            ``context.json``.
        ValueError: If a method has two rows for one pair.
    """
    pairs: dict[str, dict[Key, Pair]] = {}
    with (path / "pairs.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            key = tuple(row[column] for column in PAIR_KEY)
            of_method = pairs.setdefault(row["method"], {})
            if key in of_method:
                raise ValueError(
                    f"{path}: two rows for {row['method']} on {', '.join(key)}"
                )
            of_method[key] = Pair(
                failed=row["failed"] == "True",
                mean_epe=float(row["mean_epe"]),
                time_ms=float(row["time_ms"]),
                peak_mib=float(row["peak_mib"]),
            )
    context = json.loads((path / "context.json").read_text())
    return Run(str(path), pairs, context)


@dataclass(frozen=True)
class Scored:
    """A method over the pairs of a run, as the results tables read them.

    Attributes:
        pairs: Pairs attempted.
        failures: Pairs that failed.
        mean_epe: Mean end-point error over non-failed pairs, in px.
        time_ms: Median over every pair of its call time, in ms.
        peak_mib: Median over every pair of its call's peak memory, in MiB.
    """

    pairs: int
    failures: int
    mean_epe: float
    time_ms: float
    peak_mib: float

    @property
    def failure_rate(self) -> float:
        """Share of the pairs that failed."""
        return self.failures / self.pairs


def score(pairs: Pairs, keep: Callable[[Key], bool] | None = None) -> Scored:
    """Summarize a method over pairs, as ``report.summarize`` does a cell.

    Args:
        pairs: The method's row on each pair.
        keep: Which pairs to read, by key; all of them if ``None``.

    Returns:
        The summary.

    Raises:
        ValueError: If no pair is kept.
    """
    kept = [pair for key, pair in pairs.items() if keep is None or keep(key)]
    if not kept:
        raise ValueError("no pair to read")
    errors = [pair.mean_epe for pair in kept if not pair.failed]
    return Scored(
        pairs=len(kept),
        failures=len(kept) - len(errors),
        mean_epe=float(np.mean(errors)) if errors else math.nan,
        time_ms=float(np.median([pair.time_ms for pair in kept])),
        peak_mib=float(np.median([pair.peak_mib for pair in kept])),
    )


def largest_gap(pairs: Pairs, other: Pairs) -> float:
    """How far two methods are from each other on the pair they differ most on.

    Args:
        pairs: A method's row on each pair.
        other: Another method's, on the same pairs.

    Returns:
        Largest difference of mean end-point error between the two on a pair
        both returned an estimate for, in px; NaN if there is none.

    Raises:
        ValueError: If the two did not run on the same pairs.
    """
    if pairs.keys() != other.keys():
        raise ValueError("the two methods did not run on the same pairs")
    gaps = [abs(pairs[key].mean_epe - other[key].mean_epe) for key in pairs]
    finite = [gap for gap in gaps if not math.isnan(gap)]
    return max(finite) if finite else math.nan


@dataclass(frozen=True)
class CurveRow:
    """One point of the curve, and the same model under PyTorch beside it.

    Attributes:
        model: ``"large"`` or ``"small"``.
        weights: ``"fine-tuned"`` or ``"pretrained"``.
        refinements: Refinements of the flow.
        method: The point's method under ONNX Runtime.
        pairs: Pairs of the cost run.
        failure_rate: Share of them the method failed.
        mean_epe: Its mean end-point error over the others, in px.
        time_ms: Median time of a call under ONNX Runtime on the CPU, in ms.
        memory_mib: What the method added to a process of its own, in MiB.
        process_mib: That whole process at its highest, in MiB.
        torch_method: The point's method under PyTorch.
        torch_failure_rate: Share of the same pairs it failed, on the CPU.
        torch_mean_epe: Its mean end-point error over the others, in px.
        torch_time_ms: Median time of a call under PyTorch on the CPU, in ms.
        torch_memory_mib: What it added to a process of its own, in MiB.
        torch_process_mib: That whole process at its highest, in MiB.
        torch_call_mib: Peak memory of a call as PyTorch's profiler reads it on
            the CPU, in MiB: the figure of the N2 tables.
        largest_gap: Largest difference of mean error between the two runtimes
            on one pair, in px.
        gpu_time_ms: Median time of a call under PyTorch on a GPU, in ms; NaN
            if no such run was read.
    """

    model: str
    weights: str
    refinements: int
    method: str
    pairs: int
    failure_rate: float
    mean_epe: float
    time_ms: float
    memory_mib: float
    process_mib: float
    torch_method: str
    torch_failure_rate: float
    torch_mean_epe: float
    torch_time_ms: float
    torch_memory_mib: float
    torch_process_mib: float
    torch_call_mib: float
    largest_gap: float
    gpu_time_ms: float


@dataclass(frozen=True)
class ReferenceRow:
    """A method that is not a point, scored in the cost run beside the curve.

    Attributes:
        method: Method name.
        pairs: Pairs of the cost run.
        failure_rate: Share of them the method failed.
        mean_epe: Its mean end-point error over the others, in px.
        time_ms: Median time of a call on the CPU, in ms.
        memory_mib: What the method added to a process of its own, in MiB; NaN
            if its footprint was not read.
        process_mib: That whole process at its highest, in MiB.
    """

    method: str
    pairs: int
    failure_rate: float
    mean_epe: float
    time_ms: float
    memory_mib: float
    process_mib: float


@dataclass(frozen=True)
class RefinementRow:
    """A model with one refinement count on the full validation set.

    Attributes:
        model: ``"large"`` or ``"small"``.
        weights: ``"fine-tuned"`` or ``"pretrained"``.
        refinements: Refinements of the flow.
        degradation: Degradation preset, or ``ALL_PRESETS``.
        pairs: Pairs attempted.
        failure_rate: Share of them the model failed.
        mean_epe: Its mean end-point error over the others, in px.
        common: Pairs neither it nor the same model with
            ``TRAINED_REFINEMENTS`` refinements failed.
        gap: Its mean error minus that model's over those pairs, in px; NaN for
            ``TRAINED_REFINEMENTS`` itself.
    """

    model: str
    weights: str
    refinements: int
    degradation: str
    pairs: int
    failure_rate: float
    mean_epe: float
    common: int
    gap: float


@dataclass(frozen=True)
class Curve:
    """The curve as read.

    Attributes:
        rows: One row per point.
        references: The other methods of the cost run.
        refinements: Each point on the full validation set, over every preset
            then by preset.
        footprints: The footprint of every method in ``rows`` and
            ``references`` that has one, by method name.
        gpu: Device of the GPU run read, empty if none was.
    """

    rows: tuple[CurveRow, ...]
    references: tuple[ReferenceRow, ...]
    refinements: tuple[RefinementRow, ...]
    footprints: Mapping[str, Footprint]
    gpu: str


def check_methods(points: Sequence[Point], methods: Mapping[str, object]) -> None:
    """Check that the methods a curve reads are the models their names say.

    Args:
        points: The points.
        methods: The methods of ``configs/methods.toml``, by name.

    Raises:
        ValueError: If a point's PyTorch method is missing, or is another
            model, other weights or another refinement count.
    """
    for point in points:
        if (method := methods.get(point.torch)) is None:
            raise ValueError(f"no method {point.torch} in the methods' configuration")
        found = (
            getattr(method, "model", None),
            bool(getattr(method, "release", "") or getattr(method, "checkpoint", "")),
            getattr(method, "iterations", None),
        )
        if found != (point.model, point.fine_tuned, point.refinements):
            raise ValueError(
                f"method {point.torch} is not RAFT {point.model}, {point.weights}, "
                f"with {point.refinements} refinements"
            )


def _missing(run: Run, names: Sequence[str]) -> None:
    """Refuse a run that lacks a method the curve reads from it."""
    if missing := [name for name in names if name not in run.pairs]:
        raise ValueError(f"{run.name} has no rows for {', '.join(missing)}")


def _on_cost_device(run: Run, names: Sequence[str]) -> None:
    """Refuse a cost run that did not run on the CPU."""
    devices = run.context.get("devices", {})
    if elsewhere := [name for name in names if devices.get(name) != COST_DEVICE]:
        raise ValueError(
            f"{run.name} did not run {', '.join(elsewhere)} on the {COST_DEVICE}"
        )


def _on_a_gpu(run: Run, names: Sequence[str]) -> None:
    """Refuse a GPU run that ran a method on the CPU, or does not say where."""
    devices = run.context.get("devices", {})
    if elsewhere := [
        name for name in names if devices.get(name) in (None, COST_DEVICE)
    ]:
        raise ValueError(f"{run.name} did not run {', '.join(elsewhere)} on a GPU")


def _read_alike(footprints: Mapping[str, Footprint]) -> None:
    """Refuse footprints that were not read doing the same work."""
    if raised := [name for name, read in footprints.items() if read.error]:
        raise ValueError(
            f"a call raised while the footprint was read for {', '.join(raised)}"
        )
    if len({(read.size, read.calls) for read in footprints.values()}) > 1:
        raise ValueError(
            "the footprints were not all read on one pair size with one number of calls"
        )


def _same_pairs(run: Run, other: Run) -> None:
    """Refuse two runs whose options did not draw the same pairs."""
    scored, beside = (r.context.get("run", {}) for r in (run, other))
    options = (*PAIRS_OPTIONS, *BENCHMARK_OPTIONS)
    if unlike := [o for o in options if scored.get(o) != beside.get(o)]:
        raise ValueError(
            f"{run.name} and {other.name} did not score the same pairs: "
            f"{', '.join(unlike)} differ"
        )


def _weights_hash(run: Run, name: str) -> str | None:
    """The hash a run recorded for a method's weights, if it has one."""
    return run.context.get("checkpoints", {}).get(name, {}).get("sha256")


def check(points: Sequence[Point], cost: Run, torch: Run, full: Run) -> None:
    """Check that the three runs of a curve can be read together.

    Args:
        points: The points.
        cost: The cost run.
        torch: The PyTorch run.
        full: The full run.

    Raises:
        ValueError: If a run lacks a method, a cost run did not run on the
            CPU, the cost run and the PyTorch run did not score the same
            pairs, the full run is a light set, an ONNX file is not the model
            its method is named after, or a fine-tuned model does not have the
            same weights everywhere.
    """
    _missing(cost, [point.onnx for point in points])
    for run in (torch, full):
        _missing(run, [point.torch for point in points])
    _on_cost_device(cost, [point.onnx for point in points])
    _on_cost_device(torch, [point.torch for point in points])
    _same_pairs(cost, torch)
    if full.context.get("run", {}).get("light"):
        raise ValueError(f"{full.name} is a light set, not the full validation set")
    for point in points:
        held = cost.context.get("checkpoints", {}).get(point.onnx, {}).get("holds", {})
        said = {
            "model": point.model,
            "iterations": str(point.refinements),
            "fine_tuned": str(point.fine_tuned).lower(),
        }
        if {key: held.get(key) for key in said} != said:
            raise ValueError(
                f"{cost.name}: the file of {point.onnx} is not RAFT {point.model}, "
                f"{point.weights}, with {point.refinements} refinements"
            )
        if not point.fine_tuned:
            continue
        hashes = {
            held.get("weights_sha256"),
            _weights_hash(torch, point.torch),
            _weights_hash(full, point.torch),
        }
        if len(hashes) != 1 or None in hashes:
            raise ValueError(
                f"{point.onnx} and {point.torch} did not run the same weights in "
                f"{cost.name}, {torch.name} and {full.name}"
            )


def _memory(footprints: Mapping[str, Footprint], name: str) -> tuple[float, float]:
    """A method's footprint: its rise and its whole process, NaN without one."""
    if (found := footprints.get(name)) is None:
        return math.nan, math.nan
    return found.rise_mib, found.process_mib


def _refinements(points: Sequence[Point], full: Run) -> list[RefinementRow]:
    """Read each point on the full run, next to its model at the trained count."""
    preset = PAIR_KEY.index("degradation")
    presets = list(dict.fromkeys(key[preset] for key in full.pairs[points[0].torch]))
    scopes: list[tuple[str, Callable[[Key], bool] | None]] = [(ALL_PRESETS, None)]
    scopes += [(name, lambda key, name=name: key[preset] == name) for name in presets]

    def scores(point: Point) -> ablation.Scores:
        """The point's pairs on the full run, as the ablation compares them."""
        return {
            key: ablation.Score(pair.failed, pair.mean_epe)
            for key, pair in full.pairs[point.torch].items()
        }

    rows = []
    for degradation, keep in scopes:
        for point in points:
            trained = Point(point.model, point.fine_tuned, TRAINED_REFINEMENTS)
            scored = score(full.pairs[point.torch], keep)
            common, gap = scored.pairs - scored.failures, math.nan
            if point != trained and trained.torch in full.pairs:
                paired = ablation.compare(scores(point), scores(trained), keep)
                common, gap = paired.common, paired.difference
            rows.append(
                RefinementRow(
                    model=point.model,
                    weights=point.weights,
                    refinements=point.refinements,
                    degradation=degradation,
                    pairs=scored.pairs,
                    failure_rate=scored.failure_rate,
                    mean_epe=scored.mean_epe,
                    common=common,
                    gap=gap,
                )
            )
    return rows


def read(
    points: Sequence[Point],
    cost: Run,
    torch: Run,
    full: Run,
    footprints: Mapping[str, Footprint],
    gpu: Run | None = None,
) -> Curve:
    """Read the curve from its runs.

    Args:
        points: The points.
        cost: The cost run: the ONNX Runtime methods on the light validation
            set, on the CPU, with any other method to show beside the curve.
        torch: The PyTorch run: the PyTorch methods on the same pairs and CPU.
        full: The full run: the PyTorch methods on the full validation set.
        footprints: The footprint of each method, by method name.
        gpu: The PyTorch methods on the same pairs on a GPU, if they were run.

    Returns:
        The curve.

    Raises:
        ValueError: If the runs cannot be read together (see ``check``), a
            point has no footprint under one of its runtimes, a method the
            curve shows raised while its footprint was read, the footprints
            were not read alike, or the GPU run did not run on a GPU.
    """
    check(points, cost, torch, full)
    names = [name for point in points for name in (point.onnx, point.torch)]
    if missing := [name for name in names if name not in footprints]:
        raise ValueError(f"no footprint for {', '.join(missing)}")
    shown = dict.fromkeys([*names, *cost.pairs])
    _read_alike({name: footprints[name] for name in shown if name in footprints})
    if gpu is not None:
        _missing(gpu, [point.torch for point in points])
        _on_a_gpu(gpu, [point.torch for point in points])
        _same_pairs(cost, gpu)

    rows = []
    for point in points:
        scored, beside = score(cost.pairs[point.onnx]), score(torch.pairs[point.torch])
        memory, process = _memory(footprints, point.onnx)
        torch_memory, torch_process = _memory(footprints, point.torch)
        rows.append(
            CurveRow(
                model=point.model,
                weights=point.weights,
                refinements=point.refinements,
                method=point.onnx,
                pairs=scored.pairs,
                failure_rate=scored.failure_rate,
                mean_epe=scored.mean_epe,
                time_ms=scored.time_ms,
                memory_mib=memory,
                process_mib=process,
                torch_method=point.torch,
                torch_failure_rate=beside.failure_rate,
                torch_mean_epe=beside.mean_epe,
                torch_time_ms=beside.time_ms,
                torch_memory_mib=torch_memory,
                torch_process_mib=torch_process,
                torch_call_mib=beside.peak_mib,
                largest_gap=largest_gap(
                    cost.pairs[point.onnx], torch.pairs[point.torch]
                ),
                gpu_time_ms=math.nan
                if gpu is None
                else score(gpu.pairs[point.torch]).time_ms,
            )
        )

    on_curve = {point.onnx for point in points}
    references = []
    for name, pairs in cost.pairs.items():
        if name in on_curve:
            continue
        scored = score(pairs)
        memory, process = _memory(footprints, name)
        references.append(
            ReferenceRow(
                method=name,
                pairs=scored.pairs,
                failure_rate=scored.failure_rate,
                mean_epe=scored.mean_epe,
                time_ms=scored.time_ms,
                memory_mib=memory,
                process_mib=process,
            )
        )

    devices = () if gpu is None else gpu.context.get("devices", {}).values()
    shown = [row.method for row in rows] + [row.torch_method for row in rows]
    shown += [row.method for row in references]
    return Curve(
        rows=tuple(rows),
        references=tuple(references),
        refinements=tuple(_refinements(points, full)),
        footprints={name: footprints[name] for name in shown if name in footprints},
        gpu=", ".join(dict.fromkeys(devices)),
    )


def _px(value: float) -> str:
    """An error in px, to four decimals; ``n/a`` for a NaN."""
    return "n/a" if math.isnan(value) else f"{value:.4f}"


def _signed(value: float) -> str:
    """A difference of error in px, with its sign; ``n/a`` for a NaN."""
    return "n/a" if math.isnan(value) else f"{value:+.4f}"


def _share(value: float) -> str:
    """A rate as a percentage, to one decimal; ``n/a`` for a NaN."""
    return "n/a" if math.isnan(value) else f"{100 * value:.1f} %"


def _one(value: float) -> str:
    """A time in ms or a memory in MiB, to one decimal; ``n/a`` for a NaN."""
    return "n/a" if math.isnan(value) else f"{value:.1f}"


def _gap(value: float) -> str:
    """A difference between the two runtimes in px; ``n/a`` for a NaN."""
    return "n/a" if math.isnan(value) else f"{value:.1e}"


def _unsettled(footprints: Mapping[str, Footprint]) -> list[str]:
    """Methods whose footprint the last call still raised."""
    return [name for name, read in footprints.items() if read.settled == read.calls]


def _spread(footprints: Mapping[str, Footprint]) -> str:
    """Say how far a method's footprint moves from one process to another."""
    spreads = {
        name: read.highest_mib - read.lowest_mib
        for name, read in footprints.items()
        if read.processes > 1
    }
    if not spreads:
        return ""
    widest = max(spreads, key=lambda name: spreads[name])
    counts = sorted({footprints[name].processes for name in spreads})
    return (
        f" Each method was read in {' or '.join(map(str, counts))} processes "
        "and the median reading is given; from one process to another the "
        f"memory added moves by up to {spreads[widest]:.1f} MiB ({widest})."
    )


def to_markdown(curve: Curve, full: str = "the full validation set") -> str:
    """Render the curve as tables.

    Args:
        curve: The curve.
        full: What the pairs of the full run are, in the heading of its table.

    Returns:
        Markdown: the curve under ONNX Runtime, the same models under PyTorch
        beside it, the other methods of the cost run, and the refinement counts
        on the full run.
    """
    pairs = curve.rows[0].pairs
    lines = [
        f"ONNX Runtime on the CPU, {pairs} pairs:",
        "",
        "| model | weights | refinements | method | EPE (px) | failures | time (ms) "
        "| memory added (MiB) | whole process (MiB) |",
        "|---|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    lines += [
        f"| RAFT {row.model} | {row.weights} | {row.refinements} | {row.method} | "
        f"{_px(row.mean_epe)} | {_share(row.failure_rate)} | {_one(row.time_ms)} | "
        f"{_one(row.memory_mib)} | {_one(row.process_mib)} |"
        for row in curve.rows
    ]
    gpu = f" | time on {curve.gpu} (ms)" if curve.gpu else ""
    lines += [
        "",
        "The same models under PyTorch on the same CPU and pairs:",
        "",
        "| model | weights | refinements | method | EPE (px) | failures | time (ms) "
        "| memory added (MiB) | whole process (MiB) | memory of a call (MiB) "
        f"| largest gap with ONNX Runtime (px){gpu} |",
        "|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|"
        + ("---:|" if curve.gpu else ""),
    ]
    lines += [
        f"| RAFT {row.model} | {row.weights} | {row.refinements} | "
        f"{row.torch_method} | {_px(row.torch_mean_epe)} | "
        f"{_share(row.torch_failure_rate)} | {_one(row.torch_time_ms)} | "
        f"{_one(row.torch_memory_mib)} | {_one(row.torch_process_mib)} | "
        f"{_one(row.torch_call_mib)} | {_gap(row.largest_gap)}"
        + (f" | {_one(row.gpu_time_ms)}" if curve.gpu else "")
        + " |"
        for row in curve.rows
    ]
    if curve.references:
        lines += [
            "",
            "The other methods, on the same CPU and pairs:",
            "",
            "| method | EPE (px) | failures | time (ms) | memory added (MiB) "
            "| whole process (MiB) |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        lines += [
            f"| {row.method} | {_px(row.mean_epe)} | {_share(row.failure_rate)} | "
            f"{_one(row.time_ms)} | {_one(row.memory_mib)} | "
            f"{_one(row.process_mib)} |"
            for row in curve.references
        ]
    lines += [
        "",
        "EPE is the mean error over non-failed pairs; time is the median over "
        "pairs of a call's time. Memory added is the rise of the resident "
        "high-water mark of a process that does nothing but call the method, "
        "above its mark with the method's runtime imported: the weights, what "
        "the runtime keeps and the working memory of a call, on one pair. The "
        "whole process is the mark itself. Both are lower bounds, and neither "
        "is the memory of a call that PyTorch's profiler reads."
        + _spread(curve.footprints),
    ]
    if unsettled := _unsettled(curve.footprints):
        lines += [
            "",
            f"Memory had not settled for {', '.join(unsettled)}: the last call "
            "still raised the mark.",
        ]

    presets = list(dict.fromkeys(row.degradation for row in curve.refinements))
    by_point: dict[tuple[str, str, int], dict[str, RefinementRow]] = {}
    for row in curve.refinements:
        point = (row.model, row.weights, row.refinements)
        by_point.setdefault(point, {})[row.degradation] = row
    full_pairs = curve.refinements[0].pairs
    lines += [
        "",
        f"Fewer refinements, under PyTorch on {full}, {full_pairs} pairs:",
        "",
        "| model | weights | refinements | "
        + " | ".join(
            f"{preset}: EPE (px) | failures | against {TRAINED_REFINEMENTS} (px)"
            for preset in presets
        )
        + " |",
        "|---|---|---:|" + "---:|---:|---:|" * len(presets),
    ]
    for (model, weights, refinements), cells in by_point.items():
        lines.append(
            f"| RAFT {model} | {weights} | {refinements} | "
            + " | ".join(
                f"{_px(cells[preset].mean_epe)} | "
                f"{_share(cells[preset].failure_rate)} | "
                f"{_signed(cells[preset].gap)}"
                for preset in presets
            )
            + " |"
        )
    lines += [
        "",
        f"Against {TRAINED_REFINEMENTS} is the mean error minus that of the same "
        f"model with {TRAINED_REFINEMENTS} refinements, the count it was trained "
        "with, over the pairs neither fails: positive is worse. No model was "
        "trained again.",
    ]
    return "\n".join(lines) + "\n"


def figure(curve: Curve, path: Path, kind: str = "validation pairs") -> None:
    """Save the curve: error and failures against time, error against memory.

    Each line is a model with its weights, from the fewest refinements to the
    most, the count written at each point. The other methods of the cost run
    are single marks.

    Args:
        curve: The curve.
        path: Output PNG; parent directories are created.
        kind: What the pairs of the cost run are, in the figure's title.
    """
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    fig, (error, failures, memory) = plt.subplots(1, 3, figsize=(16.0, 4.6))
    panels = (
        (error, "time_ms", "mean_epe", 1.0),
        (failures, "time_ms", "failure_rate", 100.0),
        (memory, "memory_mib", "mean_epe", 1.0),
    )
    series: dict[tuple[str, str], list[CurveRow]] = {}
    for row in curve.rows:
        series.setdefault((row.model, row.weights), []).append(row)
    colours = {model: f"C{i}" for i, model in enumerate(MODELS)}
    for (model, weights), rows in series.items():
        rows = sorted(rows, key=lambda row: row.refinements)
        fine_tuned = weights == "fine-tuned"
        for ax, cost, accuracy, scale in panels:
            ax.plot(
                [getattr(row, cost) for row in rows],
                [scale * getattr(row, accuracy) for row in rows],
                color=colours[model],
                linestyle="-" if fine_tuned else "--",
                marker="o",
                fillstyle="full" if fine_tuned else "none",
                label=f"RAFT {model}, {weights}",
            )
            for row in rows:
                ax.annotate(
                    str(row.refinements),
                    (getattr(row, cost), scale * getattr(row, accuracy)),
                    textcoords="offset points",
                    xytext=(5, 5),
                    fontsize=8,
                )
    for row in curve.references:
        for ax, cost, accuracy, scale in panels:
            x, y = getattr(row, cost), scale * getattr(row, accuracy)
            if math.isnan(x) or math.isnan(y):
                continue
            ax.plot(x, y, color="0.35", marker="x", linestyle="none")
            ax.annotate(
                row.method,
                (x, y),
                textcoords="offset points",
                xytext=(5, 5),
                fontsize=8,
                color="0.35",
            )
    pairs = curve.rows[0].pairs
    error.set(
        xlabel="time of a call (ms)",
        ylabel="mean EPE over non-failed pairs (px)",
        title="Error against time",
        xscale="log",
    )
    failures.set(
        xlabel="time of a call (ms)",
        ylabel="failed pairs (%)",
        title="Failures against time",
        xscale="log",
    )
    memory.set(
        xlabel="memory added to a process (MiB)",
        ylabel="mean EPE over non-failed pairs (px)",
        title="Error against memory",
    )
    for ax, *_ in panels:
        ax.grid(alpha=0.3, which="both")
    error.legend(fontsize=8)
    fig.suptitle(
        f"ONNX Runtime on the CPU, {pairs} {kind}: the number at a "
        "point is its refinements",
        fontsize=10,
    )
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=110)
    plt.close(fig)

"""What running a method adds to a process's memory, read in a new process.

No counter follows ONNX Runtime's memory call by call: it allocates in native
code, outside Python's allocators and outside PyTorch. What the system does
keep is each process's resident high-water mark. Read in a process that does
nothing else, before and after the method's calls, its rise is what the method
added to the process: its weights, what its runtime keeps, and its working
memory. PyTorch methods are read the same way, so that the two runtimes are
measured with one ruler. The rise is not the same from one process to the
next, so each method is read in several and the median reading is kept. The
figure and its limits are in docs/decisions.md.
"""

import csv
import dataclasses
import gc
import importlib
import multiprocessing
import statistics
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import numpy as np

from .compute import process_peak_rss_mib
from .georef import NOMINAL
from .methods import load_methods
from .methods.base import GeoreferencedMethod
from .simulate import margin_for, simulate_translation
from .texture import fractal_texture

# Calls made on the pair. Most of the rise comes with the first, which loads
# the model, and the next few, over which the runtime's arena grows; the mark
# then creeps up by a few MiB over tens of calls (docs/decisions.md).
CALLS = 10

# New processes each method is read in. The reading kept is the one whose rise
# is the median, with the lowest and the highest rise beside it.
PROCESSES = 3

# The pair the method is called on: a synthetic texture shifted by a fraction
# of a pixel. Memory depends on its size and not on what it shows.
SHIFT = (1.37, -2.61)
SEED = 0


@dataclass(frozen=True)
class Footprint:
    """The memory one method added to a process of its own.

    Attributes:
        method: The method's name.
        size: Side of the pair it was called on, in px.
        calls: Calls made.
        baseline_mib: The process's resident high-water mark before the first
            call, with the method's runtime imported and the pair built, in MiB.
        first_mib: Rise of the mark after the first call, which loads the
            model, in MiB.
        rise_mib: Rise of the mark after the last call, in MiB.
        process_mib: The mark itself after the last call, in MiB: the whole
            process, Python and its libraries included.
        settled: Last call that raised the mark, 0 if none did. A figure that
            the last call still raised has not settled.
        time_ms: Median time of the calls after the first, in ms; NaN with a
            single call.
        processes: Processes the method was read in, each a new one. The
            figures above are those of the one whose rise is the median.
        lowest_mib: Lowest rise among those processes, in MiB.
        highest_mib: Highest rise among them, in MiB.
        error: The first call that raised and what it raised, empty if
            every call returned.
    """

    method: str
    size: int
    calls: int
    baseline_mib: float
    first_mib: float
    rise_mib: float
    process_mib: float
    settled: int
    time_ms: float
    processes: int
    lowest_mib: float
    highest_mib: float
    error: str


def pair(size: int) -> tuple[np.ndarray, np.ndarray]:
    """The pair a footprint is read on: reference and moving, ``size`` px a side."""
    margin = margin_for(max(map(abs, SHIFT)))
    source = fractal_texture(size + 2 * margin, seed=SEED)
    dx, dy = SHIFT
    simulated = simulate_translation(source, dx=dx, dy=dy, margin=margin)
    return simulated.reference, simulated.moving


def measure(name: str, methods_config: Path, size: int, calls: int) -> Footprint:
    """Call a method in this process and read what it added to its memory.

    Meant to be the only thing its process does: the mark never goes down, so
    whatever ran before hides what is smaller than it.

    Args:
        name: Name of the method in ``methods_config``.
        methods_config: The methods' configuration file.
        size: Side of the pair, in px.
        calls: Calls to make, at least one.

    Returns:
        The footprint, read in this one process.

    Raises:
        ValueError: If ``calls`` is below one, or the platform has no resident
            high-water mark to read.
    """
    if calls < 1:
        raise ValueError(f"calls must be at least 1, got {calls}")
    method = load_methods(methods_config)[name]
    # What importing the runtime costs is the process's, not the method's: it
    # is in the baseline, and in the mark of the whole process.
    for module in getattr(method, "runtime", ()):
        importlib.import_module(module)
    # A method that needs the pair's map grid is given a nominal one.
    images = pair(size)
    if isinstance(method, GeoreferencedMethod):
        images = (*images, NOMINAL)
    gc.collect()
    baseline = process_peak_rss_mib()
    if baseline is None:
        raise ValueError("this platform has no resident high-water mark to read")
    marks, seconds, error = [], [], ""
    for call in range(calls):
        started = perf_counter()
        try:
            method(*images)
        # A call that raises has still cost its memory and is read like the
        # others, whatever it raised: the first one to do so is named.
        except Exception as exc:
            if not error:
                error = f"call {call + 1}: {type(exc).__name__}: {exc}"
        seconds.append(perf_counter() - started)
        marks.append(process_peak_rss_mib())
    raised = [i + 1 for i, mark in enumerate(marks) if mark > ([baseline] + marks)[i]]
    rise = marks[-1] - baseline
    return Footprint(
        method=name,
        size=size,
        calls=calls,
        baseline_mib=baseline,
        first_mib=marks[0] - baseline,
        rise_mib=rise,
        process_mib=marks[-1],
        settled=raised[-1] if raised else 0,
        time_ms=1000 * statistics.median(seconds[1:]) if calls > 1 else float("nan"),
        processes=1,
        lowest_mib=rise,
        highest_mib=rise,
        error=error,
    )


def kept(readings: Sequence[Footprint]) -> Footprint:
    """Keep one reading of a method out of those of several processes.

    Args:
        readings: The footprints of one method, one per process.

    Returns:
        The reading whose rise is the median, the lower of the two middle ones
        for an even number, with the lowest and the highest rise beside it.
    """
    ranked = sorted(readings, key=lambda read: read.rise_mib)
    return dataclasses.replace(
        ranked[(len(ranked) - 1) // 2],
        processes=len(ranked),
        lowest_mib=ranked[0].rise_mib,
        highest_mib=ranked[-1].rise_mib,
    )


def footprints(
    names: Sequence[str],
    methods_config: Path,
    size: int,
    calls: int = CALLS,
    processes: int = PROCESSES,
) -> list[Footprint]:
    """Read the footprint of each method, in new processes of its own.

    The processes are started one after the other, never forked: a forked
    process would start with what this one has loaded. Every method is read
    once before any is read again, so that a machine that drifts during the
    readings does not favour one of them.

    Args:
        names: Names of the methods in ``methods_config``.
        methods_config: The methods' configuration file.
        size: Side of the pair, in px.
        calls: Calls each method makes in a process.
        processes: Processes each method is read in.

    Returns:
        One footprint per method, in the order given: its median reading.

    Raises:
        ValueError: If ``calls`` or ``processes`` is below one.
    """
    if calls < 1:
        raise ValueError(f"calls must be at least 1, got {calls}")
    if processes < 1:
        raise ValueError(f"processes must be at least 1, got {processes}")
    spawn = multiprocessing.get_context("spawn")
    readings: dict[str, list[Footprint]] = {name: [] for name in names}
    for _ in range(processes):
        for name in readings:
            with ProcessPoolExecutor(max_workers=1, mp_context=spawn) as fresh:
                read = fresh.submit(measure, name, methods_config, size, calls)
            readings[name].append(read.result())
    return [kept(readings[name]) for name in names]


def to_markdown(rows: Sequence[Footprint]) -> str:
    """Render footprints as a table.

    Args:
        rows: The footprints.

    Returns:
        Markdown: one line per method.
    """
    lines = [
        "| method | rise (MiB) | lowest to highest (MiB) | after the first call (MiB) "
        "| whole process (MiB) | baseline (MiB) | last call that raised it "
        "| time (ms) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    lines += [
        f"| {row.method} | {row.rise_mib:.1f} | "
        f"{row.lowest_mib:.1f} to {row.highest_mib:.1f} | {row.first_mib:.1f} | "
        f"{row.process_mib:.1f} | {row.baseline_mib:.1f} | "
        f"{row.settled} of {row.calls} | {row.time_ms:.0f} |"
        for row in rows
    ]
    table = "\n".join(lines) + "\n"
    # A method that raised was not measured doing its work.
    for row in rows:
        if row.error:
            table += f"\n{row.method} raised on {row.error}\n"
    return table


def read(path: Path) -> dict[str, Footprint]:
    """Read the footprints ``satreg footprint`` wrote.

    Args:
        path: Its ``footprints.csv``.

    Returns:
        Method name to footprint, in the file's order.
    """
    kinds = {field.name: field.type for field in dataclasses.fields(Footprint)}
    with path.open(newline="") as f:
        rows = [
            Footprint(**{name: kinds[name](value) for name, value in row.items()})
            for row in csv.DictReader(f)
        ]
    return {row.method: row for row in rows}

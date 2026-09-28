"""Merge the tables of runs made on different machines into one, by device.

A run on the M1 and a run on a Kaggle GPU each write their own directory:
``pairs.csv``, ``summary.csv`` and ``context.json``. Merging reads them back,
without running anything, and writes one table whose ``device`` column says where
each row was measured. Each device comes from a single run, so the footnote can
name the machine behind every row, and the runs must share the options that make
their pairs and their scores, so their rows are comparable.
"""

import csv
import json
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, fields
from pathlib import Path

from .compute import describe
from .report import SummaryRow, held_out_note, memory_note, to_markdown, write_csv

# Run options that decide which pairs are drawn, how they are scored and how their
# cost is read. Runs that differ on one of them are not merged.
SHARED_OPTIONS = (
    "sites",
    "pairs",
    "size",
    "scenarios",
    "degradations",
    "seed",
    "max_shift",
    "max_rotation",
    "max_scale_change",
    "max_shear",
    "max_local_shift",
    "local_length",
    "failure_threshold",
    "warmup",
    "repeats",
)

# Device of a row written before rows had one: only the methods that name a
# device, in the run's context, ran anywhere but on the CPU.
DEFAULT_DEVICE = "cpu"


class MergeError(ValueError):
    """Runs that cannot be merged into one table."""


@dataclass(frozen=True)
class Run:
    """The tables and context a benchmark run wrote to its directory.

    Attributes:
        path: The run's directory.
        summary: Its summary rows.
        pairs: Its per-pair rows, as read from the CSV, with a ``device`` column.
        context: Its ``context.json``.
    """

    path: Path
    summary: list[SummaryRow]
    pairs: list[dict[str, str]]
    context: dict[str, object]

    @property
    def devices(self) -> list[str]:
        """Devices the run's rows were measured on, in order of appearance."""
        return list(dict.fromkeys(row.device for row in self.summary))


def _device_of(row: dict[str, str], context: dict[str, object]) -> str:
    if row.get("device"):
        return row["device"]
    return context.get("devices", {}).get(row["method"], DEFAULT_DEVICE)


def _summary_row(row: dict[str, str]) -> SummaryRow:
    """Turn a line of ``summary.csv`` back into a row, typed as the dataclass."""
    return SummaryRow(**{f.name: f.type(row[f.name]) for f in fields(SummaryRow)})


def read_run(path: Path) -> Run:
    """Read the tables and context a benchmark run wrote.

    Args:
        path: Directory the run wrote, its ``--out``.

    Returns:
        The run. Rows written before rows had a device get the device the
        run's context gives their method, the CPU if it gives none.

    Raises:
        MergeError: If a file of the run is missing.
    """
    try:
        context = json.loads((path / "context.json").read_text())
        with (path / "summary.csv").open(newline="") as f:
            summary = list(csv.DictReader(f))
        with (path / "pairs.csv").open(newline="") as f:
            pairs = list(csv.DictReader(f))
    except FileNotFoundError as exc:
        raise MergeError(f"{path} is not a benchmark run: no {exc.filename}") from None
    for row in summary + pairs:
        row["device"] = _device_of(row, context)
    return Run(
        path=path,
        summary=[_summary_row(row) for row in summary],
        pairs=pairs,
        context=context,
    )


def _same(a: object, b: object) -> bool:
    # NaN never equals itself.
    if isinstance(a, float) and isinstance(b, float):
        return a == b or (math.isnan(a) and math.isnan(b))
    return a == b


def check_mergeable(runs: Sequence[Run]) -> None:
    """Refuse runs whose rows cannot share a table.

    Raises:
        MergeError: If fewer than two runs are given, two runs measured the
            same device, or two runs differ on one of ``SHARED_OPTIONS``.
    """
    if len(runs) < 2:
        raise MergeError("merging needs at least two runs")
    measured_by: dict[str, Path] = {}
    for run in runs:
        for device in run.devices:
            if device in measured_by:
                raise MergeError(
                    f"{measured_by[device]} and {run.path} both measured {device}: "
                    "a merged table takes each device from one run, run a method "
                    "on the other machine only"
                )
            measured_by[device] = run.path
    first = runs[0]
    for run in runs[1:]:
        for option in SHARED_OPTIONS:
            ours = first.context.get("run", {}).get(option)
            theirs = run.context.get("run", {}).get(option)
            if not _same(ours, theirs):
                raise MergeError(
                    f"{first.path} and {run.path} differ on {option}: "
                    f"{ours!r} against {theirs!r}"
                )


def _in_table_order(rows: list, key: Callable[[object], tuple]) -> list:
    """Put the rows of one method on several devices next to each other."""
    first_seen: dict[tuple, int] = {}
    for row in rows:
        first_seen.setdefault(key(row), len(first_seen))
    return sorted(rows, key=lambda row: first_seen[key(row)])


def _commit(context: dict[str, object]) -> str:
    code = context.get("code")
    if not code:
        return "an unrecorded commit"
    return f"commit {code['commit'][:7]}" + (" (modified)" if code["dirty"] else "")


def footnote(runs: Sequence[Run]) -> str:
    """Say where each device's rows were measured, and how.

    Args:
        runs: Mergeable runs, as checked by ``check_mergeable``.

    Returns:
        The paragraph that follows the merged table.
    """
    machines = "; ".join(
        f"{', '.join(run.devices)} rows on {describe(run.context)}, at "
        f"{_commit(run.context)}"
        for run in runs
    )
    meters = {
        f"{row.method} on {row.device}": run.context.get("cost", {})
        .get("memory", {})
        .get(row.method, "tracemalloc")
        for run in runs
        for row in run.summary
    }
    options = runs[0].context.get("run", {})
    return (
        f"\nMeasured by device: {machines}. Time is the median of "
        f"{options['repeats']} calls per pair, after {options['warmup']} warm-up "
        f"call(s) per method; {memory_note(meters)}. Details in `context.json`.\n"
    ) + held_out_note(runs[0].context.get("held_out_sites", []))


def merge(paths: Sequence[Path], out: Path) -> str:
    """Merge benchmark runs into one table with a ``device`` column.

    Args:
        paths: Directories of the runs, in the order their devices are listed.
        out: Directory to write the merged ``summary.md``, ``summary.csv``,
            ``pairs.csv`` and ``context.json`` to, which lists each run's path
            and context.

    Returns:
        The merged table as markdown, with its footnote.

    Raises:
        MergeError: If the runs cannot be merged, see ``check_mergeable``.
    """
    runs = [read_run(path) for path in paths]
    check_mergeable(runs)

    summary = _in_table_order(
        [row for run in runs for row in run.summary],
        lambda r: (r.site, r.scenario, r.degradation, r.method),
    )
    pairs = [row for run in runs for row in run.pairs]
    table = to_markdown(summary) + footnote(runs)

    write_csv(summary, out / "summary.csv")
    # Rows written before rows had a device got it last: every column, in the
    # order the first run wrote them.
    columns = list(dict.fromkeys(name for row in pairs for name in row))
    with (out / "pairs.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, restval="")
        writer.writeheader()
        writer.writerows(pairs)
    (out / "summary.md").write_text(table)
    context = {
        "merged": [
            {"path": str(run.path), "devices": run.devices, "context": run.context}
            for run in runs
        ]
    }
    (out / "context.json").write_text(json.dumps(context, indent=2) + "\n")
    return table

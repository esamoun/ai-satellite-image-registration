"""Aggregate per-pair results into the results table, and write it out."""

import csv
import math
from collections.abc import Sequence
from dataclasses import asdict, dataclass, fields
from pathlib import Path

import numpy as np

from .benchmark import PairResult
from .compute import MEMORY_READINGS


@dataclass(frozen=True)
class SummaryRow:
    """One row of the results table: a method on a device, on a site, scenario and
    degradation.

    Accuracy columns average the pairs that did not fail; failures are reported
    by ``failure_rate`` alone, so one wild estimate cannot swamp the mean. Cost
    columns take the median over every pair, failed ones included, since
    declining a pair costs time too.

    Attributes:
        site: Site name.
        scenario: Geometric model of the pairs.
        degradation: Degradation name.
        method: Method name.
        device: Device the method ran on, ``"cpu"``, ``"mps"`` or ``"cuda"``.
        n_pairs: Pairs attempted.
        cloud_fraction: Mean share of the moving image under cloud, over all pairs.
        failure_rate: Share of pairs that failed.
        mean_epe: Mean end-point error over non-failed pairs, in pixels.
        share_below_0_1: Share of pixels under 0.1 px, over non-failed pairs.
        share_below_0_5: Share of pixels under 0.5 px, over non-failed pairs.
        time_ms: Median over pairs of each pair's median call time, in ms.
        peak_mib: Median over pairs of each call's peak memory, in MiB.
    """

    site: str
    scenario: str
    degradation: str
    method: str
    device: str
    n_pairs: int
    cloud_fraction: float
    failure_rate: float
    mean_epe: float
    share_below_0_1: float
    share_below_0_5: float
    time_ms: float
    peak_mib: float


def summarize(results: Sequence[PairResult]) -> list[SummaryRow]:
    """Group per-pair results by site, scenario, degradation, method and device.

    Args:
        results: Per-pair results, in any order.

    Returns:
        One row per group, in order of first appearance.
    """
    groups: dict[tuple[str, str, str, str, str], list[PairResult]] = {}
    for r in results:
        key = (r.site, r.scenario, r.degradation, r.method, r.device)
        groups.setdefault(key, []).append(r)

    rows = []
    for (site, scenario, degradation, method, device), group in groups.items():
        kept = [r for r in group if not r.failed]

        def mean(values: list[float]) -> float:
            return float(np.mean(values)) if values else math.nan

        def median(values: list[float]) -> float:
            return float(np.median(values)) if values else math.nan

        rows.append(
            SummaryRow(
                site=site,
                scenario=scenario,
                degradation=degradation,
                method=method,
                device=device,
                n_pairs=len(group),
                cloud_fraction=mean([r.cloud_fraction for r in group]),
                failure_rate=(len(group) - len(kept)) / len(group),
                mean_epe=mean([r.mean_epe for r in kept]),
                share_below_0_1=mean([r.share_below_0_1 for r in kept]),
                share_below_0_5=mean([r.share_below_0_5 for r in kept]),
                time_ms=median([r.time_ms for r in group]),
                peak_mib=median([r.peak_mib for r in group]),
            )
        )
    return rows


def write_csv(rows: Sequence[PairResult] | Sequence[SummaryRow], path: Path) -> None:
    """Write dataclass rows to a CSV file with a header.

    Args:
        rows: Non-empty sequence of rows of a single dataclass type.
        path: Output file; parent directories are created.

    Raises:
        ValueError: If ``rows`` is empty.
    """
    if not rows:
        raise ValueError("no rows to write")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[x.name for x in fields(rows[0])])
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)


def to_markdown(rows: Sequence[SummaryRow]) -> str:
    """Render the results table as GitHub-flavoured markdown.

    Args:
        rows: Summary rows.

    Returns:
        The table, ending with a newline.
    """

    def percent(x: float) -> str:
        return "n/a" if math.isnan(x) else f"{100 * x:.1f} %"

    def pixels(x: float) -> str:
        return "n/a" if math.isnan(x) else f"{x:.4f}"

    def cost(x: float) -> str:
        return "n/a" if math.isnan(x) else f"{x:.1f}"

    header = (
        "| site | scenario | degradation | method | device | pairs | clouds "
        "| EPE (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |\n"
        "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|\n"
    )
    body = "".join(
        f"| {r.site} | {r.scenario} | {r.degradation} | {r.method} | {r.device} "
        f"| {r.n_pairs} "
        f"| {percent(r.cloud_fraction)} | {pixels(r.mean_epe)} "
        f"| {percent(r.share_below_0_1)} | {percent(r.share_below_0_5)} "
        f"| {percent(r.failure_rate)} | {cost(r.time_ms)} | {cost(r.peak_mib)} |\n"
        for r in rows
    )
    return header + body


def memory_note(meters: dict[str, str]) -> str:
    """Say how the memory column was read, naming methods read another way.

    Args:
        meters: Meter name of each method, in table order.

    Returns:
        A clause for the table's footnote, e.g. ``"memory is the peak traced by
        tracemalloc, which misses native allocations"``.
    """
    by_meter: dict[str, list[str]] = {}
    for method, meter in meters.items():
        by_meter.setdefault(meter, []).append(method)
    if len(by_meter) == 1:
        return f"memory is {MEMORY_READINGS[next(iter(by_meter))]}"
    return "memory is " + "; ".join(
        f"{MEMORY_READINGS[meter]} for {', '.join(methods)}"
        for meter, methods in by_meter.items()
    )


def held_out_note(sites: Sequence[str]) -> str:
    """Warn, under a table, that it has rows of held-out sites.

    Args:
        sites: Held-out sites the table has rows of.

    Returns:
        A paragraph to append to the table, empty if ``sites`` is.
    """
    if not sites:
        return ""
    return (
        f"\nHeld-out sites in this table: {', '.join(sites)}. They are kept for "
        "the final evaluation: no threshold, preset or variant may be chosen on "
        "their rows.\n"
    )

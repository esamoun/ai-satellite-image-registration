"""The validation set (N3): the pairs and the triplets N3's choices are made on.

The validation set is cut from the validation chips of the training chips
configuration and from nothing else: fixed, seeded pairs under the benchmark's
presets, drawn and scored by the benchmark's own code, so a validation row
reads like a row of the final table. Real-triplet closure is the second thing
choices are made on; it runs on the date series of the training and validation
chips with the cycle-consistency code. Neither reads a benchmark chip or a
held-out site: chips are asked for by role. See docs/decisions.md.

A light validation set, for use during a training, is the first pairs of every
cell of the full one: pair geometry depends only on the seed, the chip and the
pair index, so a run with fewer pairs is a prefix of a run with more.
"""

import dataclasses
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .benchmark import PairResult
from .cycle import CycleSummaryRow, TripletRow
from .cycle import summarize as cycle_summarize
from .ingest import stac_scenes
from .real import ANCHOR, Acquisition, Candidates, SeriesConfig, load_series
from .report import SummaryRow, summarize
from .trainchips import ROLES, VALIDATION, TrainingConfig

# Label of the rows that pool every chip, in place of a chip's name.
POOLED = "all chips"

# Label of the rows that pool every degradation preset.
ALL_PRESETS = "all"

# Label of the closure rows that pool every triplet of dates.
ALL_TRIPLETS = "all"

# Random subsets drawn to say how far a light set of a given size strays from
# the full one, and their seed.
SUBSET_DRAWS = 1000
SUBSET_SEED = 0


def load_validation_chips(
    training: TrainingConfig,
    series: SeriesConfig,
    data_dir: Path,
    names: Sequence[str] | None = None,
    candidates: Candidates = stac_scenes,
) -> dict[str, Acquisition]:
    """Load the image validation pairs are cut from, for each validation chip.

    It is the chip's own scene, the anchor of its series, as the benchmark cuts
    its pairs from each site's chip. The chips are asked for by role, so a
    training chip, a benchmark chip or a held-out site raises instead.

    Args:
        training: The training chips configuration.
        series: Series configuration, which says where a chip's dates are
            cached.
        data_dir: Root of downloaded data.
        names: Validation chips to load, all of them if ``None``.
        candidates: Scene search, replaced by a fake in tests.

    Returns:
        Chip name to its anchor date.

    Raises:
        ValueError: If a name is not a validation chip.
    """
    catalogue = training.benchmark.catalogue
    anchors = {}
    for chip in training.select(VALIDATION, names):
        dates = load_series(chip.site, catalogue, series, data_dir, candidates)
        anchors[chip.name] = next(a for a in dates if a.role == ANCHOR)
    return anchors


def load_closure_series(
    training: TrainingConfig,
    series: SeriesConfig,
    data_dir: Path,
    names: Sequence[str] | None = None,
    candidates: Candidates = stac_scenes,
) -> dict[str, tuple[str, list[Acquisition]]]:
    """Load the date series whose real triplets N3 reads closure on.

    These are the series of the training and validation chips. No benchmark
    chip and no held-out site is among them: only declared chips are loaded.

    Args:
        training: The training chips configuration.
        series: Series configuration, which says which dates a chip has.
        data_dir: Root of downloaded data.
        names: Chips to load, every declared chip if ``None``.
        candidates: Scene search, replaced by a fake in tests.

    Returns:
        Chip name to its role and its acquisitions, earliest first; validation
        chips first, then training chips, each in file order.

    Raises:
        ValueError: If a name is not a declared chip.
    """
    for name in names or []:
        if name in training.benchmark.sites:
            kind = "held-out site" if training.benchmark.sites[name].held_out else None
            raise ValueError(
                f"{name} is a {kind or 'benchmark chip'}: closure is read here on "
                "training and validation chips only"
            )
        if name not in training.chips:
            known = ", ".join(training.chips)
            raise ValueError(f"unknown chip {name!r} (declared: {known})")
    catalogue = training.benchmark.catalogue
    loaded = {}
    for role in sorted(ROLES, key=lambda r: r != VALIDATION):
        for chip in training.select(role):
            if names is None or chip.name in names:
                dates = load_series(chip.site, catalogue, series, data_dir, candidates)
                loaded[chip.name] = (role, dates)
    return loaded


def pooled(results: Sequence[PairResult]) -> list[SummaryRow]:
    """Summarize results over every chip at once, by scenario and preset.

    Args:
        results: Per-pair results of a validation run.

    Returns:
        The benchmark's summary rows, with ``POOLED`` in place of the site: one
        per scenario, degradation, method and device.
    """
    return summarize([dataclasses.replace(r, site=POOLED) for r in results])


@dataclass(frozen=True)
class SubsetRow:
    """How the first pairs of every cell stand for the full validation set.

    Mean errors are over non-failed pairs, pooled over chips and scenarios. The
    gap is the mean difference of error with the first method of the run, over
    the pairs neither fails. A spread is the standard deviation of the same
    figure over ``SUBSET_DRAWS`` random subsets of as many pair indices: how
    far a light set of that size strays from the full one, whichever pairs it
    holds.

    Attributes:
        pairs: Pairs per cell of the light set, its first ones.
        degradation: Degradation preset, or ``ALL_PRESETS``.
        method: Method name.
        failure_rate: Share of the light set's pairs that failed.
        full_failure_rate: The same over the full set.
        mean_epe: Mean end-point error over the light set, in px.
        full_mean_epe: The same over the full set.
        epe_spread: Spread of the mean error at this size, in px.
        gap: Mean error minus the first method's over the light set, in px; NaN
            for the first method.
        full_gap: The same over the full set.
        gap_spread: Spread of the gap at this size, in px.
    """

    pairs: int
    degradation: str
    method: str
    failure_rate: float
    full_failure_rate: float
    mean_epe: float
    full_mean_epe: float
    epe_spread: float
    gap: float
    full_gap: float
    gap_spread: float


def _ratio(sums: np.ndarray, counts: np.ndarray) -> np.ndarray:
    """Divide sums by counts, NaN where nothing was counted."""
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(counts > 0, sums / counts, math.nan)


def subset_tracking(
    results: Sequence[PairResult], sizes: Sequence[int]
) -> list[SubsetRow]:
    """Compare light sets, the first pairs of every cell, with the full set.

    A pair index is one window and one displacement, shared by every chip's
    cells, so a light set is a set of pair indices.

    Args:
        results: Per-pair results of the full validation run.
        sizes: Pairs per cell of the light sets to compare; sizes that are not
            smaller than the full set are left out.

    Returns:
        One row per size, degradation (then all of them pooled) and method.
    """
    n_pairs = max(r.pair for r in results) + 1
    methods = list(dict.fromkeys(r.method for r in results))
    degradations = list(dict.fromkeys(r.degradation for r in results))
    cells = {(r.site, r.scenario, r.degradation, r.method, r.pair): r for r in results}
    keys = list(dict.fromkeys((r.site, r.scenario, r.degradation) for r in results))
    rng = np.random.default_rng(SUBSET_SEED)

    rows = []
    for size in sorted({s for s in sizes if 0 < s < n_pairs}):
        # The light set, the full set, then random sets of the light set's size.
        draws = rng.random((SUBSET_DRAWS, n_pairs)).argsort(axis=1)[:, :size]
        for degradation in [*degradations, ALL_PRESETS]:
            kept = [k for k in keys if degradation in (k[2], ALL_PRESETS)]
            for method in methods:
                # Per pair index, over the cells: error summed over non-failed
                # pairs and their count, and the same for the difference with
                # the first method over pairs neither fails.
                error, ok, gap, both = np.zeros((4, n_pairs))
                for site, scenario, preset in kept:
                    for pair in range(n_pairs):
                        r = cells[site, scenario, preset, method, pair]
                        base = cells[site, scenario, preset, methods[0], pair]
                        if not r.failed:
                            error[pair] += r.mean_epe
                            ok[pair] += 1
                        if not r.failed and not base.failed:
                            gap[pair] += r.mean_epe - base.mean_epe
                            both[pair] += 1

                def over(index: np.ndarray, sums: np.ndarray, counts: np.ndarray):
                    return _ratio(sums[index].sum(axis=-1), counts[index].sum(axis=-1))

                first, full = np.arange(size), np.arange(n_pairs)
                is_base = method == methods[0]
                rows.append(
                    SubsetRow(
                        pairs=size,
                        degradation=degradation,
                        method=method,
                        failure_rate=1 - ok[first].sum() / (size * len(kept)),
                        full_failure_rate=1 - ok.sum() / (n_pairs * len(kept)),
                        mean_epe=float(over(first, error, ok)),
                        full_mean_epe=float(over(full, error, ok)),
                        epe_spread=float(np.nanstd(over(draws, error, ok))),
                        gap=math.nan if is_base else float(over(first, gap, both)),
                        full_gap=math.nan if is_base else float(over(full, gap, both)),
                        gap_spread=math.nan
                        if is_base
                        else float(np.nanstd(over(draws, gap, both))),
                    )
                )
    return rows


def subsets_markdown(rows: Sequence[SubsetRow]) -> str:
    """Render the light sets against the full set as markdown.

    Args:
        rows: Subset rows.

    Returns:
        The table, ending with a newline.
    """

    def percent(x: float) -> str:
        return f"{100 * x:.1f} %"

    def pixels(x: float, signed: bool = False) -> str:
        return "n/a" if math.isnan(x) else f"{x:+.4f}" if signed else f"{x:.4f}"

    header = (
        "| pairs per cell | degradation | method | failures | full | EPE (px) "
        "| full | spread | gap (px) | full | spread |\n"
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|\n"
    )
    return header + "".join(
        f"| {r.pairs} | {r.degradation} | {r.method} | {percent(r.failure_rate)} "
        f"| {percent(r.full_failure_rate)} | {pixels(r.mean_epe)} "
        f"| {pixels(r.full_mean_epe)} | {pixels(r.epe_spread)} "
        f"| {pixels(r.gap, True)} | {pixels(r.full_gap, True)} "
        f"| {pixels(r.gap_spread)} |\n"
        for r in rows
    )


def closure_by_role(
    rows: Sequence[TripletRow], roles: Mapping[str, str]
) -> list[CycleSummaryRow]:
    """Summarize real-triplet closure over the chips of each role.

    Args:
        rows: Triplet rows of a closure run on training and validation chips.
        roles: Chip name to its role.

    Returns:
        The closure summary rows, with ``"<role> chips"`` in place of the site
        and ``ALL_TRIPLETS`` in place of the triplet: one per role, method and
        device.
    """
    return cycle_summarize(
        [
            dataclasses.replace(r, site=f"{roles[r.site]} chips", triplet=ALL_TRIPLETS)
            for r in rows
        ]
    )

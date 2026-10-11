"""The final evaluation of N3, read: the criterion, then closure.

docs/decisions.md fixed on 2026-10-02, before any training code, what N3 must
show: on the simulated pairs of the two held-out sites, the fine-tuned RAFT
large fails at most as many pairs as the pretrained one, and its mean end-point
error over the pairs neither fails is lower. This module reads that from the
``pairs.csv`` of the final table, with a 95 % interval of the difference, for
the pooled pairs, per site and per cell, and the same for RAFT small, which is
reported and is not the criterion. It reads the closure of the real triplets
next to it, as better, equal or worse, and writes the paragraph that gives the
answer.

The interval is a percentile bootstrap, seeded, read two ways. Resampling the
pairs is what the criterion registered. The pairs of a site are not independent
draws, though: pair number i of a site is one window and one motion, seen under
every scenario and preset, so the second interval resamples those draws with
all their pairs, and is the wider of the two when the pairs of a draw err
alike. Both cover the draw of the pairs, not the seed of the training.

Nothing here runs a model, and nothing chooses: the rule is the one of
``satreg.ablation.beats``.
"""

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from .ablation import (
    ALL,
    BETTER,
    EQUAL,
    PAIR_KEY,
    TRIPLET_KEY,
    WORSE,
    Key,
    Paired,
    Scores,
    beats,
    closure_reading,
    compare,
)
from .cycle import REAL

# The fine-tuned model and the pretrained one it is read next to: RAFT large,
# which the criterion is on, then RAFT small.
LARGE = ("raft_ft", "raft")
SMALL = ("raft_small_ft", "raft_small")
MODELS = (LARGE, SMALL)

# What the sites the criterion is read on are called, and the others: the
# held-out sites and the seen ones, or in a rehearsal the seen sites that stand
# in for the first.
HELD_OUT, SEEN = "held-out sites", "seen sites"
STAND_IN, OTHER = "stand-in sites", "other sites"
EVERY_SITE = "every site"

# The bootstrap: resamples, the level of the interval in %, and the seed.
RESAMPLES = 10_000
LEVEL = 95.0
SEED = 0
# Draws of one batch of resamples, which bounds the memory of the bootstrap.
BATCH = 2_000_000

# A yes by less than this, in px, is written as a weak yes, and so is a yes
# whose interval reaches zero (docs/decisions.md, the limits of the criterion).
WEAK_PX = 0.005


def _px(x: float, signed: bool = False) -> str:
    """Write pixels to four decimals; a difference keeps its sign.

    A difference too small for four decimals is written in scientific
    notation, and not as a zero that would hide the sign the criterion reads.
    """
    if math.isnan(x):
        return "n/a"
    if not signed:
        return f"{x:.4f}"
    if x == 0:
        return "0.0000"
    return f"{x:+.4f}" if abs(x) >= 5e-5 else f"{x:+.0e}"


def draw_of(key: Key) -> Key:
    """The draw a pair comes from: its site and its number."""
    return key[PAIR_KEY.index("site")], key[PAIR_KEY.index("pair")]


def resampled(
    scores: Scores,
    reference: Scores,
    keys: Sequence[Key],
    group: Callable[[Key], object] | None = None,
    resamples: int = RESAMPLES,
    seed: int = SEED,
) -> np.ndarray:
    """Resample the difference of mean error between a method and a reference.

    A resample draws as many units as there are, with replacement, and reads
    the difference as the criterion does: the method's mean minus the
    reference's over the pairs neither fails, among those drawn.

    Args:
        scores: The method's score on each pair.
        reference: The reference's score on each pair.
        keys: The pairs to resample.
        group: The unit a pair belongs to, drawn with all its pairs; each pair
            is its own unit if ``None``.
        resamples: Number of resamples.
        seed: Seed of the draws.

    Returns:
        The difference in each resample, in px; NaN where a resample has no
        pair neither fails.
    """
    units: dict[object, int] = {}
    sums: list[float] = []
    counts: list[int] = []
    for key in keys:
        unit = units.setdefault(key if group is None else group(key), len(units))
        if unit == len(sums):
            sums.append(0.0)
            counts.append(0)
        if not scores[key].failed and not reference[key].failed:
            sums[unit] += scores[key].value - reference[key].value
            counts[unit] += 1
    total, count = np.array(sums), np.array(counts)
    rng = np.random.default_rng(seed)
    differences = np.empty(resamples)
    step = max(1, BATCH // len(units))
    for start in range(0, resamples, step):
        drawn = rng.integers(
            len(units), size=(min(step, resamples - start), len(units))
        )
        with np.errstate(invalid="ignore", divide="ignore"):
            differences[start : start + len(drawn)] = total[drawn].sum(axis=1) / count[
                drawn
            ].sum(axis=1)
    return differences


def interval(differences: np.ndarray, level: float = LEVEL) -> tuple[float, float]:
    """The percentile interval of resampled differences.

    Args:
        differences: The difference in each resample; NaNs are left out.
        level: Level of the interval, in %.

    Returns:
        Its two ends, in px; NaN if no resample has a difference.
    """
    kept = differences[~np.isnan(differences)]
    if not kept.size:
        return float("nan"), float("nan")
    tail = (100.0 - level) / 2
    low, high = np.percentile(kept, [tail, 100.0 - tail])
    return float(low), float(high)


@dataclass(frozen=True)
class CriterionRow:
    """A fine-tuned model next to the pretrained one, on simulated pairs.

    Attributes:
        method: The fine-tuned method.
        reference: The pretrained method.
        sites: The sites the pairs are of: a name of ``Final.scopes``.
        scenario: Scenario of the pairs, or ``ALL``.
        degradation: Degradation preset of the pairs, or ``ALL``.
        pairs: Pairs both ran on.
        failures: Those the fine-tuned method failed.
        reference_failures: Those the pretrained one failed.
        common: Those neither failed.
        mean: Mean error of the fine-tuned method over those, in px.
        reference_mean: The same for the pretrained one.
        difference: The first minus the second, in px: negative is better.
        low: Lower end of the 95 % interval of the difference by resampling
            the pairs, in px.
        high: Its upper end.
        draws: Draws of a window and a motion the pairs come from.
        draws_low: Lower end of the interval by resampling those draws, in px.
        draws_high: Its upper end.
        beats: Whether the fine-tuned method beats the pretrained one here, in
            the sense of the criterion.
    """

    method: str
    reference: str
    sites: str
    scenario: str
    degradation: str
    pairs: int
    failures: int
    reference_failures: int
    common: int
    mean: float
    reference_mean: float
    difference: float
    low: float
    high: float
    draws: int
    draws_low: float
    draws_high: float
    beats: bool


@dataclass(frozen=True)
class ClosureRow:
    """A fine-tuned model next to the pretrained one, on real triplets.

    Attributes:
        method: The fine-tuned method.
        reference: The pretrained method.
        sites: The sites the triplets are of: a name of ``Final.scopes``, or
            ``EVERY_SITE``.
        triplets: Triplets both ran on.
        failures: Those the fine-tuned method failed.
        reference_failures: Those the pretrained one failed.
        common: Those neither failed.
        mean: Mean closure of the fine-tuned method over those, in px.
        reference_mean: The same for the pretrained one.
        difference: The first minus the second, in px.
        reading: ``BETTER``, ``EQUAL`` or ``WORSE``.
    """

    method: str
    reference: str
    sites: str
    triplets: int
    failures: int
    reference_failures: int
    common: int
    mean: float
    reference_mean: float
    difference: float
    reading: str


def criterion_rows(
    pairs: Mapping[str, Scores],
    method: str,
    reference: str,
    scopes: Mapping[str, Sequence[str]],
    resamples: int = RESAMPLES,
    seed: int = SEED,
) -> list[CriterionRow]:
    """Read a fine-tuned method next to the pretrained one, scope by scope.

    Args:
        pairs: The table's pairs, by method.
        method: The fine-tuned method.
        reference: The pretrained method.
        scopes: Name of a group of sites to its sites.
        resamples: Resamples of each interval.
        seed: Seed of each interval.

    Returns:
        For each scope, one row over every pair, then one per scenario and
        preset, in the table's order.

    Raises:
        ValueError: If the two methods did not run on the same pairs, or a
            scope has no pair.
    """
    site, scenario, preset = (
        PAIR_KEY.index(c) for c in ("site", "scenario", "degradation")
    )
    scores, beside = pairs[method], pairs[reference]
    rows = []
    for name, sites in scopes.items():
        of_scope = [key for key in scores if key[site] in sites]
        cells = list(dict.fromkeys((key[scenario], key[preset]) for key in of_scope))
        for cell in [(ALL, ALL), *cells]:
            kept = {
                k for k in of_scope if cell in ((ALL, ALL), (k[scenario], k[preset]))
            }
            paired = compare(scores, beside, kept.__contains__)
            keys = [key for key in of_scope if key in kept]
            low, high = interval(resampled(scores, beside, keys, None, resamples, seed))
            draws_low, draws_high = interval(
                resampled(scores, beside, keys, draw_of, resamples, seed)
            )
            rows.append(
                CriterionRow(
                    method=method,
                    reference=reference,
                    sites=name,
                    scenario=cell[0],
                    degradation=cell[1],
                    pairs=paired.items,
                    failures=paired.failures,
                    reference_failures=paired.reference_failures,
                    common=paired.common,
                    mean=paired.mean,
                    reference_mean=paired.reference_mean,
                    difference=paired.difference,
                    low=low,
                    high=high,
                    draws=len({draw_of(key) for key in keys}),
                    draws_low=draws_low,
                    draws_high=draws_high,
                    beats=beats(paired),
                )
            )
    return rows


def closure_rows(
    triplets: Mapping[str, Scores],
    method: str,
    reference: str,
    scopes: Mapping[str, Sequence[str]],
) -> list[ClosureRow]:
    """Read a fine-tuned method next to the pretrained one on real triplets.

    Args:
        triplets: The closure run's triplets, by method; the simulated ones
            are not read.
        method: The fine-tuned method.
        reference: The pretrained method.
        scopes: Name of a group of sites to its sites.

    Returns:
        One row per scope.

    Raises:
        ValueError: If the two methods did not run on the same triplets, or a
            scope has no real triplet.
    """
    site, scenario = TRIPLET_KEY.index("site"), TRIPLET_KEY.index("scenario")
    rows = []
    for name, sites in scopes.items():
        paired = compare(
            triplets[method],
            triplets[reference],
            lambda key, sites=sites: key[scenario] == REAL and key[site] in sites,
        )
        rows.append(
            ClosureRow(
                method=method,
                reference=reference,
                sites=name,
                triplets=paired.items,
                failures=paired.failures,
                reference_failures=paired.reference_failures,
                common=paired.common,
                mean=paired.mean,
                reference_mean=paired.reference_mean,
                difference=paired.difference,
                reading=closure_reading(paired),
            )
        )
    return rows


def _paired(row: CriterionRow | ClosureRow) -> Paired:
    """The paired reading a row holds."""
    return Paired(
        items=row.pairs if isinstance(row, CriterionRow) else row.triplets,
        failures=row.failures,
        reference_failures=row.reference_failures,
        common=row.common,
        mean=row.mean,
        reference_mean=row.reference_mean,
    )


@dataclass(frozen=True)
class Final:
    """The final evaluation, read.

    Attributes:
        scopes: Name of a group of sites to its sites: the sites the criterion
            is read on, each of them, the other sites, each of them.
        rehearsal: Whether seen sites stand in for the held-out ones: the
            reading is then a test of this code and answers nothing.
        criterion: The rows of ``criterion_rows`` for each of ``MODELS``.
        closure: The rows of ``closure_rows`` for each of ``MODELS``.
        resamples: Resamples of each interval.
        seed: Seed of each interval.
    """

    scopes: Mapping[str, tuple[str, ...]]
    rehearsal: bool
    criterion: tuple[CriterionRow, ...]
    closure: tuple[ClosureRow, ...]
    resamples: int
    seed: int

    @property
    def target(self) -> str:
        """Name of the sites the criterion is read on."""
        return STAND_IN if self.rehearsal else HELD_OUT

    def pairs_of(
        self, model: tuple[str, str], sites: str, cells: bool = False
    ) -> list[CriterionRow]:
        """The criterion rows of a model on a scope: the whole, or its cells."""
        return [
            row
            for row in self.criterion
            if (row.method, row.reference, row.sites) == (*model, sites)
            and (row.scenario != ALL) == cells
        ]

    def triplets_of(self, model: tuple[str, str], sites: str) -> ClosureRow:
        """The closure row of a model on a scope."""
        return next(
            row
            for row in self.closure
            if (row.method, row.reference, row.sites) == (*model, sites)
        )

    @property
    def answer(self) -> bool:
        """Whether the fine-tuned RAFT large beats the pretrained one."""
        return self.pairs_of(LARGE, self.target)[0].beats


def read(
    pairs: Mapping[str, Scores],
    triplets: Mapping[str, Scores],
    target: Sequence[str],
    rehearsal: bool = False,
    resamples: int = RESAMPLES,
    seed: int = SEED,
) -> Final:
    """Read the criterion and the closure of the final evaluation.

    Args:
        pairs: The pairs of the final table, by method.
        triplets: The triplets of the closure run, by method.
        target: The sites the criterion is read on: the held-out sites, or in
            a rehearsal the seen sites that stand in for them.
        rehearsal: Whether this is a rehearsal.
        resamples: Resamples of each interval.
        seed: Seed of each interval.

    Returns:
        The reading.

    Raises:
        ValueError: If a method of ``MODELS`` is missing from a run, a model
            and its reference did not run on the same items, a target site has
            no pair, or the two runs are not of the same sites.
    """
    for name, run in (("the table", pairs), ("the closure run", triplets)):
        if missing := [m for model in MODELS for m in model if m not in run]:
            raise ValueError(f"{name} has no rows for {', '.join(missing)}")
    if not target:
        raise ValueError("no site to read the criterion on")
    site = PAIR_KEY.index("site")
    sites = tuple(dict.fromkeys(key[site] for key in pairs[LARGE[0]]))
    if absent := [name for name in target if name not in sites]:
        raise ValueError(f"the table has no pairs of {', '.join(absent)}")
    closed = {
        key[TRIPLET_KEY.index("site")]
        for key in triplets[LARGE[0]]
        if key[TRIPLET_KEY.index("scenario")] == REAL
    }
    if closed != set(sites):
        raise ValueError(
            "the table and the closure run are not of the same sites: "
            f"{', '.join(sites)} and {', '.join(sorted(closed))}"
        )
    others = tuple(name for name in sites if name not in target)
    first, second = (STAND_IN, OTHER) if rehearsal else (HELD_OUT, SEEN)
    scopes = {first: tuple(target), **{name: (name,) for name in target}}
    if others:
        scopes |= {second: others, **{name: (name,) for name in others}}
    criterion, closure = [], []
    for method, reference in MODELS:
        criterion += criterion_rows(pairs, method, reference, scopes, resamples, seed)
        closure += closure_rows(
            triplets, method, reference, {EVERY_SITE: sites, **scopes}
        )
    return Final(scopes, rehearsal, tuple(criterion), tuple(closure), resamples, seed)


def _between(low: float, high: float) -> str:
    """The two ends of an interval, in px, each with its sign."""
    return f"{_px(low, True)} to {_px(high, True)}"


def is_weak(row: CriterionRow) -> bool:
    """Whether a yes read on a row is a weak one.

    Returns:
        ``True`` if the difference is under ``WEAK_PX`` in absolute value, or
        one of its two intervals reaches zero.
    """
    return abs(row.difference) < WEAK_PX or not row.high < 0 or not row.draws_high < 0


def verdict(final: Final) -> str:
    """Write the answer to the criterion, and the closure reading with it.

    Args:
        final: The final evaluation, read.

    Returns:
        One paragraph: the answer in its first sentence, then how the closure
        of the real triplets reads, then what the two say together.
    """
    method, reference = LARGE
    row = final.pairs_of(LARGE, final.target)[0]
    closure = final.triplets_of(LARGE, EVERY_SITE)
    sites = ", ".join(final.scopes[final.target])
    text = (
        f"**{'Yes' if row.beats else 'No'}**: on the {row.pairs:,} simulated pairs "
        f"of the {final.target} ({sites}), {method} "
        f"{'beats' if row.beats else 'does not beat'} {reference}. It fails "
        f"{row.failures:,} pairs where {reference} fails "
        f"{row.reference_failures:,}, and over the {row.common:,} pairs neither "
        f"fails its mean EPE is {_px(row.mean)} px where {reference}'s is "
        f"{_px(row.reference_mean)} px, a difference of "
        f"{_px(row.difference, True)} px (95 % interval {_between(row.low, row.high)} "
        f"px by resampling the pairs, {_between(row.draws_low, row.draws_high)} px "
        f"by resampling the {row.draws:,} draws they come from)."
    )
    if not row.beats:
        missed = []
        if row.failures > row.reference_failures:
            missed.append("it fails more pairs")
        if not row.mean < row.reference_mean:
            missed.append("its mean EPE is not lower")
        text += f" The criterion asks for both, and {' and '.join(missed)}."
    elif is_weak(row):
        text += (
            f" It is a weak yes: the difference is under {WEAK_PX} px or one of "
            "its intervals reaches zero."
        )
    words = {BETTER: "better than", EQUAL: "equal to", WORSE: "worse than"}
    text += (
        f" On the real triplets of {EVERY_SITE}, the closure of {method} is "
        f"{words[closure.reading]} {reference}'s: it fails {closure.failures:,} of "
        f"{closure.triplets:,} triplets where {reference} fails "
        f"{closure.reference_failures:,}, and over the {closure.common:,} neither "
        f"fails its mean closure is {_px(closure.mean)} px where {reference}'s is "
        f"{_px(closure.reference_mean)} px."
    )
    if row.beats and closure.reading == WORSE:
        text += " The gain on simulated pairs did not carry to real ones."
    return text + "\n"


def _criterion_table(rows: Sequence[CriterionRow], cells: bool) -> str:
    """Render criterion rows of one model: by sites, or the cells of a scope."""
    method, reference = rows[0].method, rows[0].reference
    lead = "| scenario | degradation |" if cells else "| sites |"
    header = (
        f"{lead} pairs | {reference}: failed | {method}: failed | neither fails "
        f"| {reference}: EPE (px) | {method}: EPE (px) | difference (px) "
        "| 95 % interval, pairs (px) | 95 % interval, draws (px) | beats |\n"
        f"{'|---|---|' if cells else '|---|'}---:|---:|---:|---:|---:|---:|---:"
        "|---:|---:|---|\n"
    )
    return header + "".join(
        (f"| {r.scenario} | {r.degradation} " if cells else f"| {r.sites} ")
        + f"| {r.pairs} | {r.reference_failures} | {r.failures} | {r.common} "
        f"| {_px(r.reference_mean)} | {_px(r.mean)} | {_px(r.difference, True)} "
        f"| {_between(r.low, r.high)} | {_between(r.draws_low, r.draws_high)} "
        f"| {'yes' if r.beats else 'no'} |\n"
        for r in rows
    )


def _closure_table(rows: Sequence[ClosureRow]) -> str:
    """Render the closure rows of one model."""
    method, reference = rows[0].method, rows[0].reference
    header = (
        f"| sites | triplets | {reference}: failed | {method}: failed "
        f"| neither fails | {reference}: closure (px) | {method}: closure (px) "
        f"| difference (px) | {method} is |\n"
        "|---|---:|---:|---:|---:|---:|---:|---:|---|\n"
    )
    return header + "".join(
        f"| {r.sites} | {r.triplets} | {r.reference_failures} | {r.failures} "
        f"| {r.common} | {_px(r.reference_mean)} | {_px(r.mean)} "
        f"| {_px(r.difference, True)} | {r.reading} |\n"
        for r in rows
    )


def _lost(final: Final, model: tuple[str, str]) -> str:
    """Name the cells of the target sites where a fine-tuned model loses."""
    method, reference = model
    lost = [
        f"{row.scenario}, {row.degradation} on {row.sites} "
        f"({row.failures} failed pairs where {reference} fails "
        f"{row.reference_failures}, {_px(row.difference, True)} px)"
        for sites in final.scopes
        if sites == final.target or sites in final.scopes[final.target]
        for row in final.pairs_of(model, sites, cells=True)
        if not row.beats
    ]
    if not lost:
        return f"{method} beats {reference} in every cell of the {final.target}.\n"
    return (
        f"Cells of the {final.target} where {method} does not beat {reference}: "
        + "; ".join(lost)
        + ".\n"
    )


def to_markdown(final: Final) -> str:
    """Render the final evaluation as markdown.

    Args:
        final: The final evaluation, read.

    Returns:
        The report, ending with a newline: the answer first, then for each
        model the criterion by sites and by cell, then closure.
    """
    text = ""
    if final.rehearsal:
        text += (
            "**Rehearsal.** Seen sites stand in for the held-out ones, to test "
            "the code that reads the final evaluation. Nothing below is a "
            "result, and no choice is made on it.\n\n"
        )
    text += verdict(final)
    leads = {
        LARGE: "The criterion: {0} next to {1}, RAFT large.",
        SMALL: "RAFT small, {0} next to {1}: read the same way and reported, "
        "not the criterion.",
    }
    for model in MODELS:
        whole = [row for sites in final.scopes for row in final.pairs_of(model, sites)]
        text += f"\n**{leads[model].format(*model)}**\n\n"
        text += _criterion_table(whole, cells=False)
        for sites in (final.target, *final.scopes[final.target]):
            text += (
                f"\nBy cell, on {'the ' if sites == final.target else ''}{sites}:\n\n"
            )
            text += _criterion_table(
                final.pairs_of(model, sites, cells=True), cells=True
            )
        text += "\n" + _lost(final, model)
    for model in MODELS:
        rows = [r for r in final.closure if (r.method, r.reference) == model]
        text += (
            f"\n**Closure of the real triplets, {model[0]} next to {model[1]}.**\n\n"
            + _closure_table(rows)
        )
    text += (
        "\nAn EPE or a closure is a mean over the pairs or triplets neither of "
        "the two models fails. A difference is the fine-tuned model minus the "
        "pretrained one: negative is better. A model beats the other if it "
        "fails at most as many pairs and its mean EPE is lower, with no margin. "
        "A closure is worse with more failed triplets, or with as many and a "
        "higher mean.\n"
        f"\nThe intervals are percentile bootstraps of the difference, "
        f"{final.resamples:,} resamples with seed {final.seed}, the pairs "
        "neither model fails found again in each resample. The first resamples "
        "the pairs, as the criterion registered. The second resamples the "
        "draws: pair number i of a site is one window and one draw of its "
        "motion, seen under every scenario and preset, and is drawn with all "
        "its pairs. In "
        "a cell a draw has one pair, and the two are the same. Both cover the "
        "draw of the pairs, not the seed of the training: each model was "
        "trained once.\n"
    )
    return text

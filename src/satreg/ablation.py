"""The ablation (N3): two fine-tuned variants read against the pretrained model.

RAFT large is fine-tuned twice, on same-date pairs only and on same-date and
cross-date pairs, and one of the two is retained. This module reads what
``satreg validate`` and ``satreg validate-cycle`` wrote for the pretrained model
and the two variants, and applies the rule of docs/decisions.md, written before
either training ran. The rule is applied to the two trainings of the ablation
and to nothing else: runs that differ by more than the share of cross-date
pairs, or that stopped short of their step budget, are reported and choose
nothing.

Every reading is paired: two methods are compared on the same pairs, or the
same triplets. A mean error is taken over the items neither method fails, as
the criterion of N3 does, since a method that fails more drops its worst items
and its own mean improves. The failure counts say what that leaves out.

Nothing here runs a model, and nothing reads a benchmark chip or a held-out
site: the tables it reads are those of the validation chips and of the real
triplets of the training and validation chips.
"""

import csv
import json
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import trainval
from .compute import file_sha256
from .train import BEST, LOG, SESSION_KEYS, VALIDATIONS, LogRow, read_log
from .trainchips import TRAIN, VALIDATION
from .trainval import ValidationRow
from .validation import ROLE_LABELS

# Columns that name a pair of ``pairs.csv`` and a triplet of ``triplets.csv``,
# whatever the method: two methods of a run are compared on equal keys.
PAIR_KEY = ("site", "bands", "scenario", "degradation", "pair")
TRIPLET_KEY = ("site", "scenario", "triplet", "window")

# How a closure reads next to another, in the words of docs/decisions.md.
BETTER = "better"
EQUAL = "equal"
WORSE = "worse"

# What a paired reading is of: simulated pairs of the validation set, real
# triplets by role of the chips, real triplets of each validation chip.
VALIDATION_SET = "validation"
CLOSURE = "closure"
CLOSURE_BY_CHIP = "closure by chip"

# Label of a row that pools every scenario or every preset.
ALL = "all"

# The one setting the two trainings of the ablation are not given alike.
CROSS_DATE = "pairs.cross_date"

# Settings of a run that do not say two trainings differ: those a session may
# change on resuming, and the validation a run kept, which it found.
NOT_GIVEN = {"train": SESSION_KEYS, "validation": ("kept",)}

# Stretches a training loss is averaged over in the figure.
CURVE_STRETCHES = 50

Key = tuple[str, ...]


@dataclass(frozen=True)
class Score:
    """One method on one pair or one triplet.

    Attributes:
        failed: Whether the method failed it.
        value: Mean end-point error of the pair, or mean closure of the
            triplet, in px; NaN where the method gave nothing.
    """

    failed: bool
    value: float


Scores = dict[Key, Score]


def read_scores(path: Path, key: Sequence[str], value: str) -> dict[str, Scores]:
    """Read the per-item rows of a run, by method.

    Args:
        path: ``pairs.csv`` or ``triplets.csv`` of a run.
        key: Columns that name an item, whatever the method.
        value: Column of the item's score.

    Returns:
        Method name to its score on each item, in the file's order.

    Raises:
        ValueError: If a method has two rows for one item, as a run on two
            devices would give.
    """
    scores: dict[str, Scores] = {}
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            item = tuple(row[column] for column in key)
            of_method = scores.setdefault(row["method"], {})
            if item in of_method:
                raise ValueError(
                    f"{path}: two rows for {row['method']} on {', '.join(item)}"
                )
            of_method[item] = Score(row["failed"] == "True", float(row[value]))
    return scores


def read_pairs(path: Path) -> dict[str, Scores]:
    """Read the ``pairs.csv`` of a validation run: mean end-point error."""
    return read_scores(path, PAIR_KEY, "mean_epe")


def read_triplets(path: Path) -> dict[str, Scores]:
    """Read the ``triplets.csv`` of a closure run: mean closure."""
    return read_scores(path, TRIPLET_KEY, "mean_closure")


@dataclass(frozen=True)
class Paired:
    """A method next to a reference method, on the same items.

    Attributes:
        items: Pairs or triplets both ran on.
        failures: Items the method failed.
        reference_failures: Items the reference failed.
        common: Items neither failed, which the means are over.
        mean: Mean score of the method over those, in px; NaN if there is none.
        reference_mean: The same for the reference.
    """

    items: int
    failures: int
    reference_failures: int
    common: int
    mean: float
    reference_mean: float

    @property
    def difference(self) -> float:
        """The method's mean minus the reference's, in px: negative is better."""
        return self.mean - self.reference_mean


def compare(
    scores: Scores, reference: Scores, keep: Callable[[Key], bool] | None = None
) -> Paired:
    """Read a method next to a reference on the items both ran on.

    Args:
        scores: The method's score on each item.
        reference: The reference's score on each item.
        keep: Which items to read, by key; all of them if ``None``.

    Returns:
        The paired reading.

    Raises:
        ValueError: If the two did not run on the same items, or none is kept.
    """
    if scores.keys() != reference.keys():
        raise ValueError("the two methods did not run on the same items")
    kept = [k for k in scores if keep is None or keep(k)]
    if not kept:
        raise ValueError("no item to compare on")
    common = [k for k in kept if not scores[k].failed and not reference[k].failed]

    def mean(of: Scores) -> float:
        return float(np.mean([of[k].value for k in common])) if common else math.nan

    return Paired(
        items=len(kept),
        failures=sum(scores[k].failed for k in kept),
        reference_failures=sum(reference[k].failed for k in kept),
        common=len(common),
        mean=mean(scores),
        reference_mean=mean(reference),
    )


def beats(paired: Paired) -> bool:
    """Whether a method beats its reference, in the sense of N3's criterion.

    It fails at most as many pairs, and its mean error over the pairs neither
    fails is lower. There is no margin.
    """
    return (
        paired.failures <= paired.reference_failures
        and paired.mean < paired.reference_mean
    )


def closure_reading(paired: Paired) -> str:
    """Say how a method's closure reads next to its reference's.

    Returns:
        ``WORSE`` for more failed triplets, or as many and a higher mean
        closure over the triplets neither fails; ``BETTER`` the other way
        round; ``EQUAL`` when neither separates them.
    """
    if paired.failures != paired.reference_failures:
        return BETTER if paired.failures < paired.reference_failures else WORSE
    if paired.mean < paired.reference_mean:
        return BETTER
    if paired.mean > paired.reference_mean:
        return WORSE
    return EQUAL


@dataclass(frozen=True)
class Choice:
    """What the rule gives.

    Attributes:
        retained: The variant retained, ``None`` if neither is.
        eligible: The variants that beat the pretrained model on the validation
            set, in the order they were given.
        reason: The step of the rule that decided, as a sentence.
    """

    retained: str | None
    eligible: tuple[str, ...]
    reason: str


def choose(
    variants: tuple[str, str],
    validation: Mapping[str, Paired],
    closure: Paired,
    accuracy: Paired,
) -> Choice:
    """Apply the rule that chooses between the two variants.

    A variant is eligible if it beats the pretrained model on the validation
    set. With none eligible nothing is retained, with one it is retained. Two
    eligible variants are compared on the closure of the real triplets of the
    validation chips, then, if that does not separate them, on their mean error
    on the validation set; the first variant is kept if nothing does.

    Args:
        variants: The two variants; the first is the simpler recipe.
        validation: Each variant next to the pretrained model on the whole
            validation set.
        closure: The second variant next to the first on the real triplets of
            the validation chips.
        accuracy: The second variant next to the first on the whole validation
            set.

    Returns:
        The choice, and why.
    """
    first, second = variants
    eligible = tuple(v for v in variants if beats(validation[v]))
    if not eligible:
        return Choice(
            None,
            eligible,
            "Neither variant beats the pretrained model on the validation set: "
            "nothing is retained.",
        )
    if len(eligible) == 1:
        return Choice(
            eligible[0],
            eligible,
            f"Only {eligible[0]} beats the pretrained model on the validation "
            "set: it is retained.",
        )
    reading = closure_reading(closure)
    if reading != EQUAL:
        retained, other = (second, first) if reading == BETTER else (first, second)
        return Choice(
            retained,
            eligible,
            "Both variants beat the pretrained model on the validation set. On "
            f"the real triplets of the validation chips, {retained} closes better "
            f"than {other}: it is retained.",
        )
    lower, higher = (
        accuracy.mean < accuracy.reference_mean,
        accuracy.mean > accuracy.reference_mean,
    )
    # Neither holds for two equal means, nor with no pair to take a mean over.
    if lower or higher:
        retained, other = (second, first) if lower else (first, second)
        return Choice(
            retained,
            eligible,
            "Both variants beat the pretrained model on the validation set and "
            "their closure on the validation chips is equal. On the validation "
            f"set, {retained} has a lower mean error than {other}: it is retained.",
        )
    return Choice(
        first,
        eligible,
        "Both variants beat the pretrained model on the validation set, and "
        f"neither closure nor mean error separates them: {first}, the simpler "
        "recipe, is retained.",
    )


@dataclass(frozen=True)
class ComparisonRow:
    """One paired reading, as a row of ``comparisons.csv``.

    Attributes:
        measure: ``VALIDATION_SET`` for simulated pairs, ``CLOSURE`` for real
            triplets by role of the chips, ``CLOSURE_BY_CHIP`` for those of
            each validation chip.
        method: The method read.
        reference: The method it is read next to.
        scope: Scenario of the pairs or ``ALL``; role of the chips, or the
            chip, for closure.
        degradation: Degradation preset of the pairs or ``ALL``; empty for
            closure.
        items: Pairs or triplets both methods ran on.
        failures: Those the method failed.
        reference_failures: Those the reference failed.
        common: Those neither failed.
        mean: Mean error or closure of the method over those, in px.
        reference_mean: The same for the reference.
        difference: The method's mean minus the reference's, in px.
    """

    measure: str
    method: str
    reference: str
    scope: str
    degradation: str
    items: int
    failures: int
    reference_failures: int
    common: int
    mean: float
    reference_mean: float
    difference: float


def _row(
    measure: str, method: str, reference: str, scope: str, preset: str, paired: Paired
) -> ComparisonRow:
    return ComparisonRow(
        measure=measure,
        method=method,
        reference=reference,
        scope=scope,
        degradation=preset,
        items=paired.items,
        failures=paired.failures,
        reference_failures=paired.reference_failures,
        common=paired.common,
        mean=paired.mean,
        reference_mean=paired.reference_mean,
        difference=paired.difference,
    )


def validation_rows(
    pairs: Mapping[str, Scores], method: str, reference: str
) -> list[ComparisonRow]:
    """Read a method next to a reference on the validation set, cell by cell.

    Args:
        pairs: The validation run's pairs, by method.
        method: The method read.
        reference: The method it is read next to.

    Returns:
        One row per scenario and preset, in the run's order, then one over
        every pair.
    """
    scenario, preset = PAIR_KEY.index("scenario"), PAIR_KEY.index("degradation")
    cells = list(dict.fromkeys((k[scenario], k[preset]) for k in pairs[method]))
    rows = [
        _row(
            VALIDATION_SET,
            method,
            reference,
            *cell,
            compare(
                pairs[method],
                pairs[reference],
                lambda k, cell=cell: (k[scenario], k[preset]) == cell,
            ),
        )
        for cell in cells
    ]
    whole = compare(pairs[method], pairs[reference])
    return [*rows, _row(VALIDATION_SET, method, reference, ALL, ALL, whole)]


def closure_rows(
    triplets: Mapping[str, Scores],
    roles: Mapping[str, str],
    method: str,
    reference: str,
) -> list[ComparisonRow]:
    """Read a method next to a reference on real triplets, by role of the chips.

    Args:
        triplets: The closure run's triplets, by method.
        roles: Chip name to its role.
        method: The method read.
        reference: The method it is read next to.

    Returns:
        One row for the validation chips, then one for the training chips,
        then one for each validation chip, in the order of ``roles``.

    Raises:
        ValueError: If a role or a validation chip has no triplet.
    """
    site = TRIPLET_KEY.index("site")

    def row(measure: str, scope: str, keep: Callable[[Key], bool]) -> ComparisonRow:
        paired = compare(triplets[method], triplets[reference], keep)
        return _row(measure, method, reference, scope, "", paired)

    by_role = [
        row(CLOSURE, ROLE_LABELS[role], lambda k, role=role: roles[k[site]] == role)
        for role in (VALIDATION, TRAIN)
    ]
    by_chip = [
        row(CLOSURE_BY_CHIP, chip, lambda k, chip=chip: k[site] == chip)
        for chip, role in roles.items()
        if role == VALIDATION
    ]
    return by_role + by_chip


def paired_of(row: ComparisonRow) -> Paired:
    """The paired reading a row holds."""
    return Paired(
        items=row.items,
        failures=row.failures,
        reference_failures=row.reference_failures,
        common=row.common,
        mean=row.mean,
        reference_mean=row.reference_mean,
    )


@dataclass(frozen=True)
class TrainingRun:
    """What a training left in its directory, read back.

    Attributes:
        method: Name of the method that runs its kept weights.
        path: The run's directory.
        sha256: SHA-256 of the kept weights the tables were scored with.
        context: Its ``context.json``.
        log: Its steps, every session included.
        validations: Its validations on the light validation set.
    """

    method: str
    path: Path
    sha256: str
    context: dict[str, object]
    log: list[LogRow]
    validations: list[ValidationRow]

    @property
    def kept(self) -> ValidationRow | None:
        """The validation whose weights the run kept."""
        return trainval.best(self.validations)

    @property
    def budget(self) -> int:
        """Steps the run was given."""
        return int(self.context["train"]["steps"])

    @property
    def steps(self) -> int:
        """Steps the run did."""
        return self.log[-1].step if self.log else 0


def read_training(method: str, checkpoint: Path, sha256: str) -> TrainingRun:
    """Read the run a method's kept weights come from.

    Args:
        method: Name of the method.
        checkpoint: The weights the method runs: the ``BEST`` of a run.
        sha256: Their SHA-256, as the validation run recorded it.

    Returns:
        The run.

    Raises:
        ValueError: If the weights are not a run's kept ones, the run's files
            are not next to them, or the file is no longer the one the
            validation run scored.
    """
    if checkpoint.name != BEST:
        raise ValueError(
            f"{method} runs {checkpoint}: the ablation reads a run's kept "
            f"weights, {BEST}"
        )
    path = checkpoint.parent
    try:
        context = json.loads((path / "context.json").read_text())
    except FileNotFoundError:
        raise ValueError(f"{path} is not a training run: no context.json") from None
    log = read_log(path / LOG)
    validations = trainval.read_validations(path / VALIDATIONS)
    if not log or not validations:
        raise ValueError(f"{path} is not a training run: no {LOG} or {VALIDATIONS}")
    if "steps" not in context.get("train", {}) or "cross_date" not in context.get(
        "pairs", {}
    ):
        raise ValueError(
            f"{path} is not a training run: its context.json gives no step "
            "budget or no cross-date share"
        )
    # A run that goes on rewrites its kept weights under the same name.
    try:
        on_disk = file_sha256(checkpoint)
    except FileNotFoundError:
        raise ValueError(f"no weights at {checkpoint}") from None
    if on_disk != sha256:
        raise ValueError(
            f"{checkpoint} is not the file {method} was scored with: its SHA-256 "
            f"starts with {on_disk[:16]}, the validation run recorded "
            f"{sha256[:16]}. Score the three methods again (make ablation)"
        )
    return TrainingRun(method, path, sha256, context, log, validations)


def differences(first: TrainingRun, second: TrainingRun) -> list[str]:
    """Name the settings two runs were not given alike.

    Args:
        first: A run.
        second: Another.

    Returns:
        The settings of the training, the pairs, the degradation ranges, the
        chips and the light validation set that differ, as ``table.key``;
        ``CROSS_DATE`` alone for the two runs of the ablation. The settings of
        ``NOT_GIVEN`` are left out.
    """

    def given(run: TrainingRun, table: str) -> dict[str, object]:
        settings = run.context.get(table, {})
        return {k: v for k, v in settings.items() if k not in NOT_GIVEN.get(table, ())}

    def differing(table: str) -> list[str]:
        a, b = given(first, table), given(second, table)
        return [
            f"{table}.{k}" for k in sorted(a.keys() | b.keys()) if a.get(k) != b.get(k)
        ]

    names = [
        name for table in ("train", "pairs", "ranges") for name in differing(table)
    ]
    if first.context.get("chips") != second.context.get("chips"):
        names.append("chips")
    return names + differing("validation")


def departures(first: TrainingRun, second: TrainingRun) -> list[str]:
    """Say what keeps two runs from being the two trainings of the ablation.

    The ablation is two runs given alike but for the share of cross-date pairs,
    none for the first, and both run to their step budget. The rule was written
    for those and is applied to nothing else.

    Args:
        first: The run of the same-date variant.
        second: The run of the cross-date variant.

    Returns:
        One phrase per departure; empty for the two trainings of the ablation.
    """

    def share(run: TrainingRun) -> float:
        return float(run.context["pairs"]["cross_date"])

    found = []
    if other := [n for n in differences(first, second) if n != CROSS_DATE]:
        found.append(
            "the two runs differ by more than the share of cross-date pairs "
            f"({', '.join(other)})"
        )
    if share(first) != 0:
        found.append(
            f"{first.method} was trained with a cross-date share of "
            f"{share(first):g}, not on same-date pairs only"
        )
    if share(second) <= 0:
        found.append(f"{second.method} was trained with no cross-date pair")
    found += [
        f"{run.method} stopped at step {run.steps} of {run.budget}"
        for run in (first, second)
        if run.steps < run.budget
    ]
    return found


def check_scored(
    validation: Mapping[str, object],
    closure: Mapping[str, object],
    runs: Sequence[TrainingRun],
) -> dict[str, str]:
    """Check the two scored runs are the ones the rule reads.

    The rule reads the full validation set and the closure of every chip the
    trainings used. What those chips are is taken from the trainings: the
    validation chips, and their scenes, are those of the light validation set
    each one validated on.

    Args:
        validation: The ``context.json`` of the validation run.
        closure: The ``context.json`` of the closure run.
        runs: The trainings.

    Returns:
        Chip name to its role, for the chips of the closure run.

    Raises:
        ValueError: If a run is not one of ``satreg validate`` or ``satreg
            validate-cycle``, the validation run is the light set or is not on
            the validation chips of the trainings, or the closure run misses a
            chip or has one more.
    """
    scored = validation.get("validation")
    if not isinstance(scored, dict) or "light" not in scored:
        raise ValueError("the validation run is not one of satreg validate")
    if scored["light"]:
        raise ValueError(
            "the validation run is the light validation set: the rule reads the "
            "full one"
        )
    roles = (closure.get("validation") or {}).get("chips")
    if not isinstance(roles, dict) or not set(roles.values()) <= {VALIDATION, TRAIN}:
        raise ValueError("the closure run is not one of satreg validate-cycle")
    for run in runs:
        chips = run.context.get("validation", {}).get("chips", {})
        if scored.get("chips") != chips:
            raise ValueError(
                f"the validation run is not on the chips {run.method} validated "
                f"on during its training, scene for scene: it is on "
                f"{', '.join(scored.get('chips') or {}) or 'none'}, the "
                f"training on {', '.join(chips) or 'none'}"
            )
        expected = {
            **dict.fromkeys(chips, VALIDATION),
            **dict.fromkeys(run.context.get("chips", []), TRAIN),
        }
        if roles != expected:
            unlike = sorted(
                chip
                for chip in roles.keys() | expected.keys()
                if roles.get(chip) != expected.get(chip)
            )
            raise ValueError(
                f"the closure run is not on the chips of {run.method}'s training: "
                f"{', '.join(unlike)} missing, added or under another role"
            )
    return roles


def _px(x: float, signed: bool = False) -> str:
    """Write pixels to four decimals; a difference keeps its sign.

    The rule reads the exact difference, so one too small for four decimals is
    written in scientific notation and not as a zero that would hide its sign.
    """
    if math.isnan(x):
        return "n/a"
    if not signed:
        return f"{x:.4f}"
    if x == 0:
        return "0.0000"
    return f"{x:+.4f}" if abs(x) >= 5e-5 else f"{x:+.0e}"


def _reads(row: ComparisonRow) -> str:
    """Say how a closure row reads, as the words that go before the reference."""
    return {BETTER: "better than", EQUAL: "equal to", WORSE: "worse than"}[
        closure_reading(paired_of(row))
    ]


def comparison_markdown(rows: Sequence[ComparisonRow]) -> str:
    """Render paired readings of one method next to one reference as markdown.

    Args:
        rows: Rows of one measure, one method and one reference, non-empty.

    Returns:
        The table, ending with a newline.
    """
    method, reference = rows[0].method, rows[0].reference
    pairs = rows[0].measure == VALIDATION_SET
    what = "EPE" if pairs else "closure"
    lead = {
        VALIDATION_SET: "| scenario | degradation |",
        CLOSURE: "| chips |",
        CLOSURE_BY_CHIP: "| validation chip |",
    }[rows[0].measure]
    header = (
        f"{lead} {'pairs' if pairs else 'triplets'} | {reference}: failed "
        f"| {method}: failed | neither fails | {reference}: {what} (px) "
        f"| {method}: {what} (px) | difference (px) |\n"
        f"{'|---|---|' if pairs else '|---|'}---:|---:|---:|---:|---:|---:|---:|\n"
    )
    return header + "".join(
        (f"| {r.scope} | {r.degradation} " if pairs else f"| {r.scope} ")
        + f"| {r.items} | {r.reference_failures} | {r.failures} | {r.common} "
        f"| {_px(r.reference_mean)} | {_px(r.mean)} | {_px(r.difference, True)} |\n"
        for r in rows
    )


def runs_markdown(runs: Sequence[TrainingRun]) -> str:
    """Render what the trainings were and what they kept, one column per run.

    Args:
        runs: The runs, non-empty.

    Returns:
        The table, ending with a newline.
    """

    def commits(run: TrainingRun) -> str:
        sessions = run.context.get("sessions", [])
        seen = dict.fromkeys(str(s["code"]["commit"])[:7] for s in sessions)
        return ", ".join(seen) or str(run.context.get("commit"))[:7]

    def pretrained(run: TrainingRun) -> str:
        scores = [
            r.score
            for r in run.validations
            if r.step == 0 and r.degradation == trainval.ALL_PRESETS
        ]
        return _px(scores[0]) if scores else "n/a"

    def speed(run: TrainingRun) -> str:
        return f"{np.median([r.seconds for r in run.log]):.2f}"

    def last_loss(run: TrainingRun) -> str:
        tenth = run.log[-max(1, len(run.log) // 10) :]
        return f"{np.mean([r.loss for r in tenth]):.4f}"

    lines = {
        "run directory": lambda r: f"`{r.path}`",
        "cross-date share": lambda r: f"{r.context['pairs']['cross_date']:g}",
        "seed": lambda r: str(r.context["pairs"]["seed"]),
        "steps done / budget": lambda r: f"{r.steps} / {r.budget}",
        "sessions": lambda r: str(len(r.context.get("sessions", []))),
        "commit": commits,
        "median s/step": speed,
        "training loss, last tenth of the steps": last_loss,
        "validations": lambda r: str(
            sum(v.degradation == trainval.ALL_PRESETS for v in r.validations)
        ),
        "selection score, pretrained (px)": pretrained,
        "selection score, kept (px)": lambda r: _px(r.kept.score) if r.kept else "n/a",
        "kept step": lambda r: str(r.kept.step) if r.kept else "none",
        f"SHA-256 of `{BEST}`": lambda r: f"`{r.sha256[:16]}`",
    }
    header = "| | " + " | ".join(r.method for r in runs) + " |\n"
    header += "|---|" + "---:|" * len(runs) + "\n"
    return header + "".join(
        f"| {label} | " + " | ".join(cell(r) for r in runs) + " |\n"
        for label, cell in lines.items()
    )


def curves(runs: Sequence[TrainingRun], path: Path) -> None:
    """Save the loss and validation curves of the trainings, side by side.

    The left panel is the training loss, averaged over consecutive stretches.
    The right panel is the selection score on the light validation set, with
    each run's kept step circled and the pretrained weights at step 0.

    Args:
        runs: The runs, non-empty.
        path: Output PNG; parent directories are created.
    """
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    fig, (loss, score) = plt.subplots(1, 2, figsize=(11.0, 4.0))
    for run in runs:
        chunks = np.array_split(
            np.arange(len(run.log)), min(CURVE_STRETCHES, len(run.log))
        )
        loss.plot(
            [run.log[c[-1]].step for c in chunks],
            [np.mean([run.log[i].loss for i in c]) for c in chunks],
            label=run.method,
        )
        rows = [r for r in run.validations if r.degradation == trainval.ALL_PRESETS]
        (line,) = score.plot(
            [r.step for r in rows],
            [r.score for r in rows],
            marker=".",
            label=run.method,
        )
        if (kept := run.kept) is not None:
            score.plot(
                kept.step,
                kept.score,
                marker="o",
                markersize=11,
                fillstyle="none",
                color=line.get_color(),
            )
    loss.set(xlabel="step", ylabel="sequence loss", title="Training loss")
    score.set(
        xlabel="step",
        ylabel="selection score (px)",
        title="Light validation set (kept step circled)",
    )
    for ax in (loss, score):
        ax.grid(alpha=0.3)
        ax.legend()
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=110)
    plt.close(fig)


@dataclass(frozen=True)
class Ablation:
    """The ablation, read.

    Attributes:
        baseline: The pretrained method.
        variants: The two fine-tuned variants; the first is the simpler recipe.
        runs: The training each variant comes from, in the same order.
        rows: Every paired reading: each variant next to the baseline, then the
            second variant next to the first, on the validation set and on
            closure.
        departures: What keeps the runs from being the two trainings of the
            ablation; empty for those.
        choice: What the rule gives; ``None`` with a departure, the rule being
            applied to the two trainings of the ablation only.
    """

    baseline: str
    variants: tuple[str, str]
    runs: tuple[TrainingRun, TrainingRun]
    rows: list[ComparisonRow]
    departures: tuple[str, ...]
    choice: Choice | None

    def of(self, measure: str, method: str, reference: str) -> list[ComparisonRow]:
        """The rows of one measure, one method and one reference."""
        return [
            r
            for r in self.rows
            if (r.measure, r.method, r.reference) == (measure, method, reference)
        ]


def read(
    pairs: Mapping[str, Scores],
    triplets: Mapping[str, Scores],
    roles: Mapping[str, str],
    baseline: str,
    runs: tuple[TrainingRun, TrainingRun],
) -> Ablation:
    """Read the two variants next to the baseline and apply the rule.

    Args:
        pairs: The validation run's pairs, by method.
        triplets: The closure run's triplets, by method.
        roles: Chip name to its role, for the chips of the closure run.
        baseline: The pretrained method.
        runs: The training of each variant; the first is the simpler recipe.

    Returns:
        The ablation.

    Raises:
        ValueError: If a method is missing from a run, the methods of a run
            did not score the same items, or a triplet is of a chip without a
            role.
    """
    first, second = variants = (runs[0].method, runs[1].method)
    for name, scores in ((VALIDATION_SET, pairs), (CLOSURE, triplets)):
        if missing := [m for m in (baseline, *variants) if m not in scores]:
            raise ValueError(f"the {name} run has no row for {', '.join(missing)}")
    site = TRIPLET_KEY.index("site")
    if unknown := sorted({k[site] for k in triplets[baseline]} - roles.keys()):
        raise ValueError(f"the closure run gives no role to {', '.join(unknown)}")
    rows = []
    for method, reference in ((first, baseline), (second, baseline), (second, first)):
        rows += validation_rows(pairs, method, reference)
        rows += closure_rows(triplets, roles, method, reference)

    def whole(measure: str, method: str, reference: str) -> Paired:
        scope = ALL if measure == VALIDATION_SET else ROLE_LABELS[VALIDATION]
        return next(
            paired_of(r)
            for r in rows
            if (r.measure, r.method, r.reference, r.scope)
            == (measure, method, reference, scope)
        )

    found = tuple(departures(*runs))
    choice = (
        None
        if found
        else choose(
            variants,
            {v: whole(VALIDATION_SET, v, baseline) for v in variants},
            whole(CLOSURE, second, first),
            whole(VALIDATION_SET, second, first),
        )
    )
    return Ablation(baseline, variants, runs, rows, found, choice)


def to_markdown(ablation: Ablation) -> str:
    """Render the ablation as markdown.

    Args:
        ablation: The ablation, read.

    Returns:
        The report, ending with a newline: the trainings, each variant next to
        the pretrained model on the validation set and on closure, the two
        variants next to each other, and what the rule gives, or why it is not
        applied.
    """
    baseline, (first, second) = ablation.baseline, ablation.variants
    differing = differences(*ablation.runs)
    text = "The two trainings:\n\n" + runs_markdown(ablation.runs)
    text += (
        "\nSettings the two runs were not given alike: "
        f"{', '.join(differing) or 'none'}. The device and the number of worker "
        "processes are not compared: a session may change them. The two "
        "training losses are not on the same pairs (a cross-date pair has a "
        "truth off by what its two dates are misregistered by), so they are not "
        "compared; the selection scores are, both being on the light validation "
        "set.\n"
    )
    for variant in (first, second):
        validation = ablation.of(VALIDATION_SET, variant, baseline)
        closure = ablation.of(CLOSURE, variant, baseline)
        whole = paired_of(validation[-1])
        text += (
            f"\n{variant} next to {baseline}, on the validation set:\n\n"
            + comparison_markdown(validation)
            + f"\n{variant} {'beats' if beats(whole) else 'does not beat'} "
            f"{baseline} on the validation set: it fails {whole.failures} pairs "
            f"where {baseline} fails {whole.reference_failures}, and over the "
            f"{whole.common} pairs neither fails its mean error is "
            f"{_px(whole.mean)} px where {baseline}'s is "
            f"{_px(whole.reference_mean)} px.\n"
            "\nOn the real triplets:\n\n"
            + comparison_markdown(closure)
            + f"\nIts closure is {_reads(closure[0])} {baseline} on the "
            f"validation chips and {_reads(closure[1])} it on the training "
            "chips.\n"
        )
    closure = ablation.of(CLOSURE, second, first)
    text += (
        f"\n{second} next to {first}, on the validation set:\n\n"
        + comparison_markdown(ablation.of(VALIDATION_SET, second, first))
        + "\nOn the real triplets:\n\n"
        + comparison_markdown(closure)
        + f"\nThe closure of {second} is {_reads(closure[0])} {first} on the "
        f"validation chips and {_reads(closure[1])} it on the training chips. "
        "The validation chips decide. A model trained on cross-date pairs has "
        "seen the dates of the training chips, so its closure there is a "
        "training score: it is reported and decides nothing.\n"
        "\nThe same closure, one validation chip at a time:\n\n"
        + comparison_markdown(ablation.of(CLOSURE_BY_CHIP, second, first))
        + "\nAn EPE or a closure is a mean over the pairs or triplets neither of "
        "the two methods of a table fails, so a method's figure changes with "
        "the method it is read next to. A difference is the method read minus "
        "the one it is read next to: negative is better. A closure is worse "
        "with more failed triplets, or with as many and a higher mean.\n"
    )
    if ablation.choice is None:
        return text + (
            "\n**The rule is not applied.** It was written for the two trainings "
            "of the ablation, given alike but for the share of cross-date pairs "
            "and run to their step budget, and these are not: "
            f"{'; '.join(ablation.departures)}. The tables above choose nothing.\n"
        )
    return text + f"\n**What the rule gives.** {ablation.choice.reason}\n"

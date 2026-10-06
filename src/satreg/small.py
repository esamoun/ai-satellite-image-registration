"""RAFT small fine-tuned (N3), read next to the pretrained one and to RAFT large.

RAFT small is trained once, with the pairs the ablation retained and the recipe
RAFT large was trained with. This module reads what ``satreg validate`` and
``satreg validate-cycle`` wrote for four methods, the fine-tuned and the
pretrained RAFT small, the fine-tuned and the pretrained RAFT large, and says
which of three words the training gets, as docs/decisions.md defined them
before it ran: a gain, no gain, or worse.

The verdict is given to that training and to no other: a run that was not given
what RAFT large was but for the model, or that stopped short of its step
budget, is reported and gets none.

The readings are the paired ones of the ablation (``satreg.ablation``): two
methods on the same pairs or the same triplets, a mean over the items neither
fails. Nothing here runs a model, and nothing reads a benchmark chip or a
held-out site.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from .ablation import (
    ALL,
    CLOSURE,
    READING_NOTE,
    VALIDATION_SET,
    ComparisonRow,
    Paired,
    Scores,
    TrainingRun,
    against_markdown,
    beats,
    check_methods,
    closure_rows,
    differences,
    paired_of,
    runs_markdown,
    validation_rows,
)

# What the training gets, in the words of the ticket.
GAIN = "gain"
NO_GAIN = "no gain"
WORSE = "worse"

# The one setting the training is not given like RAFT large's, and its values.
MODEL = "train.model"
SMALL, LARGE = "small", "large"


@dataclass(frozen=True)
class Verdict:
    """What the training of RAFT small gets.

    Attributes:
        word: ``GAIN``, ``NO_GAIN`` or ``WORSE``.
        reason: Why, as a sentence.
    """

    word: str
    reason: str


def judge(trained: str, pretrained: str, paired: Paired) -> Verdict:
    """Say whether fine-tuning was a gain, in the sense of N3's criterion.

    A gain if the fine-tuned model beats the pretrained one on the validation
    set: it fails at most as many pairs and its mean error over the pairs
    neither fails is lower. Worse if the pretrained one beats the fine-tuned
    one, the same criterion the other way round. No gain otherwise: fewer
    failures bought with a higher mean error, a lower mean error bought with
    more failures, or nothing that separates the two.

    Args:
        trained: The fine-tuned method.
        pretrained: The pretrained method.
        paired: The first next to the second on the whole validation set.

    Returns:
        The verdict.
    """
    counts = (
        f"{trained} fails {paired.failures} pairs where {pretrained} fails "
        f"{paired.reference_failures}, and over the {paired.common} pairs neither "
        f"fails its mean error is {paired.mean:.4f} px where {pretrained}'s is "
        f"{paired.reference_mean:.4f} px"
    )
    if beats(paired):
        return Verdict(GAIN, f"{counts}: it beats {pretrained}.")
    swapped = Paired(
        items=paired.items,
        failures=paired.reference_failures,
        reference_failures=paired.failures,
        common=paired.common,
        mean=paired.reference_mean,
        reference_mean=paired.mean,
    )
    if beats(swapped):
        return Verdict(WORSE, f"{counts}: {pretrained} beats it.")
    return Verdict(NO_GAIN, f"{counts}: neither beats the other.")


def departures(small: TrainingRun, large: TrainingRun) -> list[str]:
    """Say what keeps a run from being the training of RAFT small.

    That training is given what the retained training of RAFT large was, but
    for the model, and is run to its step budget.

    Args:
        small: The run of RAFT small.
        large: The run of RAFT large it is read next to.

    Returns:
        One phrase per departure; empty for the training of RAFT small.
    """
    found = []
    if other := [n for n in differences(small, large) if n != MODEL]:
        found.append(f"the two runs differ by more than the model ({', '.join(other)})")
    for run, model in ((small, SMALL), (large, LARGE)):
        if (trained := run.context["train"].get("model")) != model:
            found.append(f"{run.method} was trained as RAFT {trained}, not {model}")
    found += [
        f"{run.method} stopped at step {run.steps} of {run.budget}"
        for run in (small, large)
        if run.steps < run.budget
    ]
    return found


@dataclass(frozen=True)
class Reading:
    """The training of RAFT small, read.

    Attributes:
        pretrained: The pretrained RAFT small.
        large_pretrained: The pretrained RAFT large.
        runs: The training of RAFT small, then the one of RAFT large.
        comparisons: The method read and its reference, for each paired
            reading: the fine-tuned small next to the pretrained small, to the
            fine-tuned large and to the pretrained large, then the pretrained
            small next to the pretrained large.
        rows: Those readings, on the validation set and on closure.
        departures: What keeps the run from being the training of RAFT small;
            empty for it.
        verdict: What the training gets; ``None`` with a departure.
    """

    pretrained: str
    large_pretrained: str
    runs: tuple[TrainingRun, TrainingRun]
    comparisons: tuple[tuple[str, str], ...]
    rows: list[ComparisonRow]
    departures: tuple[str, ...]
    verdict: Verdict | None

    @property
    def method(self) -> str:
        """The fine-tuned RAFT small."""
        return self.runs[0].method

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
    pretrained: str,
    large_pretrained: str,
    runs: tuple[TrainingRun, TrainingRun],
) -> Reading:
    """Read the fine-tuned RAFT small next to the three other methods.

    Args:
        pairs: The validation run's pairs, by method.
        triplets: The closure run's triplets, by method.
        roles: Chip name to its role, for the chips of the closure run.
        pretrained: The pretrained RAFT small.
        large_pretrained: The pretrained RAFT large.
        runs: The training of RAFT small, then the one of RAFT large.

    Returns:
        The reading.

    Raises:
        ValueError: If a method is missing from a run, the methods of a run
            did not score the same items, or a triplet is of a chip without a
            role.
    """
    trained, large = (run.method for run in runs)
    check_methods(
        pairs, triplets, roles, (trained, pretrained, large, large_pretrained)
    )
    comparisons = (
        (trained, pretrained),
        (trained, large),
        (trained, large_pretrained),
        (pretrained, large_pretrained),
    )
    rows = []
    for method, reference in comparisons:
        rows += validation_rows(pairs, method, reference)
        rows += closure_rows(triplets, roles, method, reference)
    found = tuple(departures(*runs))
    whole = next(
        paired_of(r)
        for r in rows
        if (r.measure, r.method, r.reference, r.scope)
        == (VALIDATION_SET, trained, pretrained, ALL)
    )
    verdict = None if found else judge(trained, pretrained, whole)
    return Reading(
        pretrained, large_pretrained, runs, comparisons, rows, found, verdict
    )


# What each paired reading says, by its place in ``Reading.comparisons``.
LEADS = (
    "What the training changed",
    "What is left to RAFT large, both fine-tuned",
    "Next to RAFT large as it was before any training",
    "The gap before any training",
)


def to_markdown(reading: Reading) -> str:
    """Render the reading as markdown.

    Args:
        reading: The training of RAFT small, read.

    Returns:
        The report, ending with a newline: the two trainings, the four paired
        readings on the validation set and on closure, and the verdict, or why
        none is given.
    """
    differing = differences(*reading.runs)
    text = "The two trainings:\n\n" + runs_markdown(reading.runs)
    text += (
        "\nSettings the two runs were not given alike: "
        f"{', '.join(differing) or 'none'}. The device and the number of worker "
        "processes are not compared: a session may change them. With the same "
        "seed and the same pairs configuration, pair number i is the same pair "
        "in both runs.\n"
    )
    for lead, (method, reference) in zip(LEADS, reading.comparisons, strict=True):
        text += f"\n**{lead}.**\n" + against_markdown(
            reading.of(VALIDATION_SET, method, reference),
            reading.of(CLOSURE, method, reference),
        )
    text += (
        "\nA model trained on cross-date pairs has seen the dates of the "
        "training chips, so its closure there is a training score: it is "
        "reported, and the verdict is read on the validation set.\n" + READING_NOTE
    )
    if reading.verdict is None:
        return text + (
            "\n**No verdict.** The three words were defined for the training of "
            "RAFT small, given what the retained training of RAFT large was but "
            "for the model and run to its step budget, and this is not it: "
            f"{'; '.join(reading.departures)}. The tables above give none.\n"
        )
    return text + (
        f"\n**Verdict: {reading.verdict.word}.** On the validation set, "
        f"{reading.verdict.reason}\n"
    )

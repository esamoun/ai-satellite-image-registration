"""Validation during a training (N3): the light validation set, and which
checkpoint a run keeps.

Every few steps, a training scores its network on the light validation set:
the pairs ``satreg validate --light`` scores, drawn by the benchmark's own code
and scored by its own metric. The run keeps the weights of the validation with
the lowest selection score. That score is written here, before the first real
run, so that no run can choose it afterwards. See docs/decisions.md.
"""

import csv
import dataclasses
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from .benchmark import BenchmarkConfig, simulated_pairs
from .degrade import Degradation
from .methods import raft
from .metrics import score
from .simulate import SimulatedPair

# Label of the row that pools every degradation preset: the one whose score
# chooses the checkpoint.
ALL_PRESETS = "all"


def selection_score(epes: Sequence[float], threshold: float) -> float:
    """The figure a run's checkpoints are compared on, lower being better.

    It is the mean end-point error over every pair, a pair above the failure
    threshold counting for the threshold. The table's mean error leaves failed
    pairs out, so a network that fails more pairs can show a lower one; here a
    failure costs, and costs the same whether the pair is 2 px or 30 px off, so
    one cloud-covered pair does not decide among checkpoints.

    Args:
        epes: Mean end-point error of each pair, in px; NaN for a pair the
            network gave no finite flow on.
        threshold: Mean end-point error above which a pair failed, in px.

    Returns:
        The score, in px, between 0 and ``threshold``.

    Raises:
        ValueError: If there is no pair.
    """
    if not len(epes):
        raise ValueError("no pair to score")
    capped = [threshold if not e <= threshold else e for e in epes]
    return float(np.mean(capped))


@dataclass(frozen=True)
class ValidationRow:
    """A network on the light validation set, for one preset or all of them.

    Attributes:
        step: Training steps done when it was scored, 0 for the pretrained
            weights.
        degradation: Degradation preset, or ``ALL_PRESETS``.
        pairs: Pairs scored.
        score: Selection score over those pairs, in px.
        mean_epe: Mean end-point error over the non-failed pairs, in px, as in
            the validation tables; NaN if every pair failed.
        failure_rate: Share of the pairs that failed.
        seconds: Time the whole validation took, every preset included.
    """

    step: int
    degradation: str
    pairs: int
    score: float
    mean_epe: float
    failure_rate: float
    seconds: float


def _row(
    step: int, degradation: str, epes: Sequence[float], threshold: float, seconds: float
) -> ValidationRow:
    passed = [e for e in epes if e <= threshold]
    return ValidationRow(
        step=step,
        degradation=degradation,
        pairs=len(epes),
        score=selection_score(epes, threshold),
        mean_epe=float(np.mean(passed)) if passed else math.nan,
        failure_rate=1 - len(passed) / len(epes),
        seconds=seconds,
    )


class LightValidation:
    """The light validation set, drawn once and scored at each validation.

    The pairs are those of ``run_benchmark`` on the same images and
    configuration, so a network scored here and the method that loads its
    checkpoint, scored by ``satreg validate --light``, get the same errors.
    """

    def __init__(
        self,
        images: Mapping[str, np.ndarray],
        config: BenchmarkConfig,
        degradations: Mapping[str, Degradation],
        iterations: int,
        device: str,
    ) -> None:
        """Draw the pairs.

        Args:
            images: Validation chip name to the image its pairs are cut from.
            config: The validation run's parameters, ``n_pairs`` being the
                light set's pairs per chip, scenario and preset.
            degradations: Preset name to preset.
            iterations: Recurrent refinements of the flow.
            device: Device the network is on.
        """
        self.config = config
        self.iterations = iterations
        self.device = device
        self.pairs: list[tuple[str, SimulatedPair]] = [
            (str(labels["degradation"]), pair)
            for labels, pair in simulated_pairs(images, config, degradations)
        ]

    def errors(self, network: Any) -> list[tuple[str, float]]:
        """Score a network on every pair.

        Args:
            network: A RAFT network in evaluation mode, on the set's device.

        Returns:
            The preset and the mean end-point error of each pair, in px, over
            the pair's valid pixels.
        """
        errors = []
        for degradation, pair in self.pairs:
            flow = raft.estimate(
                network, pair.reference, pair.moving, self.iterations, self.device
            )
            scored = score(pair.truth, flow, pair.reference.shape, pair.valid)
            errors.append((degradation, scored.mean_epe))
        return errors

    def __call__(self, network: Any, step: int) -> list[ValidationRow]:
        """Score a network and sum it up by preset.

        Args:
            network: A RAFT network in evaluation mode, on the set's device.
            step: Training steps done.

        Returns:
            One row per preset, then the row over all of them.
        """
        started = perf_counter()
        errors = self.errors(network)
        seconds = perf_counter() - started
        threshold = self.config.failure_threshold
        presets = list(dict.fromkeys(degradation for degradation, _ in errors))
        rows = [
            _row(step, p, [e for d, e in errors if d == p], threshold, seconds)
            for p in presets
        ]
        everything = [e for _, e in errors]
        return [*rows, _row(step, ALL_PRESETS, everything, threshold, seconds)]


def best(rows: Sequence[ValidationRow]) -> ValidationRow | None:
    """The validation whose weights a run keeps.

    Args:
        rows: Every validation of the run so far.

    Returns:
        The row over all presets with the lowest selection score among the
        trained steps, the earliest of equal ones; ``None`` before the first.
        Step 0, the pretrained weights, is a reference and is never kept.
    """
    trained = [r for r in rows if r.degradation == ALL_PRESETS and r.step > 0]
    return min(trained, key=lambda r: (r.score, r.step), default=None)


def read_validations(path: Path) -> list[ValidationRow]:
    """Read a run's validations, empty if there is none."""
    if not path.exists():
        return []
    kinds = {f.name: f.type for f in dataclasses.fields(ValidationRow)}
    with path.open(newline="") as f:
        return [
            ValidationRow(**{name: kinds[name](value) for name, value in r.items()})
            for r in csv.DictReader(f)
        ]


def write_validations(rows: Sequence[ValidationRow], path: Path) -> None:
    """Write a run's validations, one row per step and preset."""
    with path.open("w", newline="") as f:
        names = [x.name for x in dataclasses.fields(ValidationRow)]
        writer = csv.DictWriter(f, fieldnames=names)
        writer.writeheader()
        writer.writerows(dataclasses.asdict(row) for row in rows)


def to_markdown(rows: Sequence[ValidationRow]) -> str:
    """Render a run's validations as markdown, one line per step.

    Args:
        rows: The run's validations.

    Returns:
        The table, ending with a newline: per step, the selection score, then
        the mean error and the failure rate of each preset. The kept step is
        marked.
    """
    presets = list(
        dict.fromkeys(r.degradation for r in rows if r.degradation != ALL_PRESETS)
    )
    cells = {(r.step, r.degradation): r for r in rows}
    kept = best(rows)
    header = "| step | score (px) |" + "".join(
        f" {p}: EPE (px) | failures |" for p in presets
    )
    lines = [header, "|---:|---:|" + "---:|---:|" * len(presets)]
    for step in dict.fromkeys(r.step for r in rows):
        mark = " (kept)" if kept is not None and step == kept.step else ""
        line = f"| {step}{mark} | {cells[step, ALL_PRESETS].score:.4f} |"
        for p in presets:
            r = cells[step, p]
            line += f" {r.mean_epe:.3f} | {100 * r.failure_rate:.1f} % |"
        lines.append(line)
    return "\n".join(lines) + "\n"

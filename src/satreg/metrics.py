"""Accuracy of an estimated displacement against the ground truth."""

from dataclasses import dataclass

import numpy as np

from .displacement import Displacement

# A pair whose mean end-point error exceeds this counts as a failure rather than
# as an inaccurate result. At one pixel the method has lost the sub-pixel regime
# the benchmark is about. See docs/decisions.md.
FAILURE_EPE_PX = 1.0


@dataclass(frozen=True)
class PairScore:
    """Accuracy of one estimate on one pair.

    Attributes:
        mean_epe: Mean end-point error over valid pixels, in pixels.
        share_below_0_1: Share of valid pixels with an error under 0.1 px.
        share_below_0_5: Share of valid pixels with an error under 0.5 px.
    """

    mean_epe: float
    share_below_0_1: float
    share_below_0_5: float


def endpoint_error(
    truth: Displacement,
    estimate: Displacement,
    shape: tuple[int, int],
    mask: np.ndarray | None = None,
) -> np.ndarray:
    """Per-pixel Euclidean distance between two displacements.

    Args:
        truth: Ground-truth displacement.
        estimate: Estimated displacement.
        shape: ``(rows, cols)`` of the reference grid.
        mask: Optional boolean array of ``shape``; only ``True`` pixels are kept.

    Returns:
        1-D array of end-point errors in pixels, one per valid pixel.

    Raises:
        ValueError: If ``mask`` does not match ``shape`` or keeps no pixel.
    """
    diff = estimate.field(shape) - truth.field(shape)
    epe = np.hypot(diff[0], diff[1])
    if mask is None:
        return epe.ravel()
    if mask.shape != tuple(shape):
        raise ValueError(f"mask shape {mask.shape} does not match {shape}")
    if not mask.any():
        raise ValueError("mask keeps no pixel")
    return epe[mask]


def score(
    truth: Displacement,
    estimate: Displacement,
    shape: tuple[int, int],
    mask: np.ndarray | None = None,
) -> PairScore:
    """Summarise the end-point error of one estimate.

    Args:
        truth: Ground-truth displacement.
        estimate: Estimated displacement.
        shape: ``(rows, cols)`` of the reference grid.
        mask: Optional boolean array of valid pixels.

    Returns:
        The pair's score. Non-finite estimates give a NaN mean error and zero
        shares, which ``is_failure`` treats as a failure.
    """
    epe = endpoint_error(truth, estimate, shape, mask)
    return PairScore(
        mean_epe=float(epe.mean()),
        share_below_0_1=float(np.mean(epe < 0.1)),
        share_below_0_5=float(np.mean(epe < 0.5)),
    )


def is_failure(pair_score: PairScore, threshold: float = FAILURE_EPE_PX) -> bool:
    """Tell whether a scored estimate counts as a failure.

    Args:
        pair_score: Score of the estimate.
        threshold: Mean end-point error above which the estimate failed, in px.

    Returns:
        ``True`` if the mean error is not finite or exceeds ``threshold``.
    """
    return not np.isfinite(pair_score.mean_epe) or pair_score.mean_epe > threshold

"""An affine transform fitted by RANSAC to matched points, shared by the sparse
matchers so that they differ only in how they find their matches."""

from collections.abc import Mapping

import cv2
import numpy as np

from ..displacement import Affine
from .base import Estimate, RegistrationFailure

# RANSAC iterations and confidence, OpenCV's defaults for estimateAffine2D.
RANSAC_MAX_ITERS = 2000
RANSAC_CONFIDENCE = 0.99

# Levenberg-Marquardt iterations that refine the RANSAC model on its inliers.
REFINE_ITERS = 10

# An affine transform has six unknowns, fixed by three point matches.
MIN_POINTS_FOR_AFFINE = 3


def check_parameters(ransac_threshold: float, min_inliers: int) -> None:
    """Refuse RANSAC parameters that cannot give a trusted fit.

    Raises:
        ValueError: If ``ransac_threshold`` is not positive or ``min_inliers`` is
            below ``MIN_POINTS_FOR_AFFINE``.
    """
    if ransac_threshold <= 0:
        raise ValueError(f"ransac_threshold must be positive, got {ransac_threshold}")
    if min_inliers < MIN_POINTS_FOR_AFFINE:
        raise ValueError(
            f"min_inliers must be at least {MIN_POINTS_FOR_AFFINE}, got {min_inliers}"
        )


def fit_affine(
    ref_points: np.ndarray,
    mov_points: np.ndarray,
    ransac_threshold: float,
    min_inliers: int,
    diagnostics: Mapping[str, float] | None = None,
) -> Estimate:
    """Fit the affine displacement that maps matched reference points to moving ones.

    Args:
        ref_points: ``(n, 2)`` points of the reference image, in OpenCV's
            ``(x, y) = (col, row)`` order, pixel centres on integers as in the
            displacement convention.
        mov_points: ``(n, 2)`` matching points of the moving image, same order.
        ransac_threshold: Largest reprojection error of an inlier, in pixels.
        min_inliers: Fewest matches, then inliers, for the fit to be trusted.
        diagnostics: What the method counted before matching, e.g. keypoints.

    Returns:
        The affine estimate, with ``diagnostics`` plus the match and inlier
        counts.

    Raises:
        RegistrationFailure: If there are fewer than ``min_inliers`` matches or
            inliers, or RANSAC finds no model.
    """
    diagnostics = {**(diagnostics or {}), "matches": len(ref_points)}
    if len(ref_points) < min_inliers:
        raise RegistrationFailure(
            f"{len(ref_points)} matches, need {min_inliers}", diagnostics
        )

    model, inliers = cv2.estimateAffine2D(
        np.asarray(ref_points, dtype=np.float32),
        np.asarray(mov_points, dtype=np.float32),
        method=cv2.RANSAC,
        ransacReprojThreshold=ransac_threshold,
        maxIters=RANSAC_MAX_ITERS,
        confidence=RANSAC_CONFIDENCE,
        refineIters=REFINE_ITERS,
    )
    diagnostics["inliers"] = 0 if inliers is None else int(inliers.sum())
    if model is None or diagnostics["inliers"] < min_inliers:
        raise RegistrationFailure(
            f"{diagnostics['inliers']} inliers, need {min_inliers}", diagnostics
        )

    # The model maps reference (x, y) to moving (x, y): swap to (row, col).
    matrix = model[:, :2][::-1, ::-1]
    affine = Affine(
        matrix=(
            (float(matrix[0, 0]), float(matrix[0, 1])),
            (float(matrix[1, 0]), float(matrix[1, 1])),
        ),
        offset=(float(model[1, 2]), float(model[0, 2])),
    )
    return Estimate(affine, diagnostics)

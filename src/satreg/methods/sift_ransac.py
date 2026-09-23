"""SIFT keypoints matched by ratio test, an affine transform fitted by RANSAC."""

from dataclasses import dataclass

import cv2
import numpy as np

from ..displacement import Affine
from .base import Estimate, RegistrationFailure

# Each image is stretched to 8 bits between these percentiles of its own values.
# Stretching on the image's own statistics makes the conversion blind to a gain
# or offset between the two images, and the 1 % tails keep a few saturated or
# dark pixels from compressing the rest of the range. See docs/decisions.md.
STRETCH_PERCENTILES = (1.0, 99.0)

# RANSAC iterations and confidence, OpenCV's defaults for estimateAffine2D.
RANSAC_MAX_ITERS = 2000
RANSAC_CONFIDENCE = 0.99

# Levenberg-Marquardt iterations that refine the RANSAC model on its inliers.
REFINE_ITERS = 10

# An affine transform has six unknowns, fixed by three point matches.
MIN_POINTS_FOR_AFFINE = 3


def to_uint8(image: np.ndarray) -> np.ndarray:
    """Convert an image to the 8 bits OpenCV's SIFT reads.

    Values are stretched linearly so that the ``STRETCH_PERCENTILES`` of the
    image map to 0 and 255, then clipped and rounded. The mapping depends on the
    image alone, so a gain or offset applied to it leaves the result unchanged,
    whatever degradation the pair went through.

    Args:
        image: 2-D image, any real dtype.

    Returns:
        The 8-bit image. A flat image maps to zeros.
    """
    lo, hi = np.percentile(image, STRETCH_PERCENTILES)
    if hi <= lo:
        return np.zeros(image.shape, dtype=np.uint8)
    scaled = (image.astype(float) - lo) * (255 / (hi - lo))
    return np.clip(np.round(scaled), 0, 255).astype(np.uint8)


@dataclass(frozen=True)
class SiftRansac:
    """Feature-based registration: SIFT, Lowe's ratio test, RANSAC affine fit.

    Attributes:
        ratio: A match is kept if its descriptor distance is below ``ratio``
            times that of the second-best candidate, in (0, 1].
        ransac_threshold: Largest reprojection error of an inlier, in pixels.
        min_inliers: Fewest inliers for the fit to be trusted, at least 3.
            Below it the method reports a failure rather than a guess.
    """

    ratio: float = 0.75
    ransac_threshold: float = 1.0
    min_inliers: int = 10

    def __post_init__(self) -> None:
        if not 0 < self.ratio <= 1:
            raise ValueError(f"ratio must be in (0, 1], got {self.ratio}")
        if self.ransac_threshold <= 0:
            raise ValueError(
                f"ransac_threshold must be positive, got {self.ransac_threshold}"
            )
        if self.min_inliers < MIN_POINTS_FOR_AFFINE:
            raise ValueError(
                f"min_inliers must be at least {MIN_POINTS_FOR_AFFINE}, "
                f"got {self.min_inliers}"
            )

    def __call__(self, reference: np.ndarray, moving: np.ndarray) -> Estimate:
        """Estimate an affine displacement from matched keypoints.

        Args:
            reference: Reference image.
            moving: Moving image, same shape as ``reference``.

        Returns:
            The affine estimate, with the keypoint, match and inlier counts as
            diagnostics.

        Raises:
            RegistrationFailure: If there are fewer than ``min_inliers`` matches
                or inliers, or RANSAC finds no model.
        """
        sift = cv2.SIFT_create()
        ref_keys, ref_desc = sift.detectAndCompute(to_uint8(reference), None)
        mov_keys, mov_desc = sift.detectAndCompute(to_uint8(moving), None)
        diagnostics = {"keypoints": min(len(ref_keys), len(mov_keys))}

        matches = []
        if ref_desc is not None and mov_desc is not None and len(mov_keys) >= 2:
            candidates = cv2.BFMatcher(cv2.NORM_L2).knnMatch(ref_desc, mov_desc, k=2)
            matches = [
                best
                for best, second in candidates
                if best.distance < self.ratio * second.distance
            ]
        diagnostics["matches"] = len(matches)
        if len(matches) < self.min_inliers:
            raise RegistrationFailure(
                f"{len(matches)} matches, need {self.min_inliers}", diagnostics
            )

        # OpenCV points are (x, y) = (col, row), with pixel centres on integers
        # as in the displacement convention.
        ref_points = np.float32([ref_keys[m.queryIdx].pt for m in matches])
        mov_points = np.float32([mov_keys[m.trainIdx].pt for m in matches])
        model, inliers = cv2.estimateAffine2D(
            ref_points,
            mov_points,
            method=cv2.RANSAC,
            ransacReprojThreshold=self.ransac_threshold,
            maxIters=RANSAC_MAX_ITERS,
            confidence=RANSAC_CONFIDENCE,
            refineIters=REFINE_ITERS,
        )
        diagnostics["inliers"] = 0 if inliers is None else int(inliers.sum())
        if model is None or diagnostics["inliers"] < self.min_inliers:
            raise RegistrationFailure(
                f"{diagnostics['inliers']} inliers, need {self.min_inliers}",
                diagnostics,
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

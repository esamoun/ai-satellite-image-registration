"""SIFT keypoints matched by ratio test, an affine transform fitted by RANSAC."""

from dataclasses import dataclass

import cv2
import numpy as np

from . import ransac
from .base import Estimate

# Each image is stretched to 8 bits between these percentiles of its own values.
# Stretching on the image's own statistics makes the conversion blind to a gain
# or offset between the two images, and the 1 % tails keep a few saturated or
# dark pixels from compressing the rest of the range. See docs/decisions.md.
STRETCH_PERCENTILES = (1.0, 99.0)


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
        ransac.check_parameters(self.ransac_threshold, self.min_inliers)

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
        # OpenCV points are (x, y) = (col, row), with pixel centres on integers
        # as in the displacement convention.
        ref_points = np.float32([ref_keys[m.queryIdx].pt for m in matches])
        mov_points = np.float32([mov_keys[m.trainIdx].pt for m in matches])
        return ransac.fit_affine(
            ref_points.reshape(-1, 2),
            mov_points.reshape(-1, 2),
            self.ransac_threshold,
            self.min_inliers,
            diagnostics,
        )

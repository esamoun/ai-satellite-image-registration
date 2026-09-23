"""Sub-pixel phase correlation, from scikit-image."""

import numpy as np
from skimage.registration import phase_cross_correlation

from ..displacement import Translation

# Refines the correlation peak on a grid of 1/100 px. Coarser factors cap the
# resolution above the 0.1 px target the benchmark is about.
UPSAMPLE_FACTOR = 100


def phase_correlation(reference: np.ndarray, moving: np.ndarray) -> Translation:
    """Estimate a global translation by phase correlation.

    Args:
        reference: Reference image.
        moving: Moving image, same shape as ``reference``.

    Returns:
        The estimated translation.
    """
    shift, _, _ = phase_cross_correlation(
        reference, moving, upsample_factor=UPSAMPLE_FACTOR
    )
    # scikit-image returns the shift that brings the moving image back onto the
    # reference: the opposite of the displacement convention used here.
    dy, dx = -shift
    return Translation(dx=float(dx), dy=float(dy))

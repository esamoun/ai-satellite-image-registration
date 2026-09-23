"""Sub-pixel phase correlation, from scikit-image."""

from dataclasses import dataclass

import numpy as np
from skimage.filters import window as apodisation_window
from skimage.registration import phase_cross_correlation

from ..displacement import Translation

# Refines the correlation peak on a grid of 1/100 px. Coarser factors cap the
# resolution above the 0.1 px target the benchmark is about.
UPSAMPLE_FACTOR = 100

# Apodisation windows a variant can use, by the name scikit-image gives them.
WINDOWS = ("hann",)


def phase_correlation(
    reference: np.ndarray, moving: np.ndarray, window: str | None = None
) -> Translation:
    """Estimate a global translation by phase correlation.

    Args:
        reference: Reference image.
        moving: Moving image, same shape as ``reference``.
        window: Apodisation window, one of ``WINDOWS``, or ``None`` for none.
            Each image is centred on its own mean before it is windowed, so the
            window does not add the same bump to both images.

    Returns:
        The estimated translation.
    """
    if window is not None:
        taper = apodisation_window(window, reference.shape)
        reference = (reference - reference.mean()) * taper
        moving = (moving - moving.mean()) * taper
    shift, _, _ = phase_cross_correlation(
        reference, moving, upsample_factor=UPSAMPLE_FACTOR
    )
    # scikit-image returns the shift that brings the moving image back onto the
    # reference: the opposite of the displacement convention used here.
    dy, dx = -shift
    return Translation(dx=float(dx), dy=float(dy))


@dataclass(frozen=True)
class PhaseCorrelation:
    """Phase correlation with configurable parameters, for method variants.

    Attributes:
        window: Apodisation window, one of ``WINDOWS``, or ``None`` for none.
    """

    window: str | None = None

    def __post_init__(self) -> None:
        if self.window is not None and self.window not in WINDOWS:
            raise ValueError(
                f"window must be one of {', '.join(WINDOWS)}, got {self.window!r}"
            )

    def __call__(self, reference: np.ndarray, moving: np.ndarray) -> Translation:
        """Estimate a global translation, see ``phase_correlation``."""
        return phase_correlation(reference, moving, self.window)

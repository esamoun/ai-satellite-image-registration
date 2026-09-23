"""Simulated image pairs with an exactly known displacement."""

import math
from dataclasses import dataclass

import numpy as np
from scipy import ndimage

from .displacement import Displacement, Translation

# Border discarded after a Fourier shift. The shift treats the window as periodic,
# which rings at its edges; the ringing decays inwards and is negligible past this.
RINGING_BORDER_PX = 16


@dataclass(frozen=True)
class SimulatedPair:
    """A reference image, a moving image and the displacement between them.

    Attributes:
        reference: Reference image.
        moving: Moving image, same shape as ``reference``.
        truth: Ground-truth displacement, in the convention of ``displacement``.
    """

    reference: np.ndarray
    moving: np.ndarray
    truth: Displacement


def margin_for(max_shift: float) -> int:
    """Pixels to keep around a window so a shift up to ``max_shift`` is clean.

    Args:
        max_shift: Largest absolute shift component that will be applied, in px.

    Returns:
        Margin in pixels, on each side of the window.
    """
    return math.ceil(abs(max_shift)) + RINGING_BORDER_PX


def fourier_shift(image: np.ndarray, dy: float, dx: float) -> np.ndarray:
    """Shift an image by a sub-pixel amount with band-limited interpolation.

    Content at ``p`` in ``image`` ends up at ``p + (dy, dx)`` in the output. Unlike
    spline interpolation, this does not low-pass the shifted image, which would
    otherwise make the moving image blurrier than the reference and bias every
    method. The image is mirrored before the FFT so the wrap-around is continuous.

    Args:
        image: 2-D image.
        dy: Shift along rows, in pixels.
        dx: Shift along columns, in pixels.

    Returns:
        Shifted image, same shape and float dtype.
    """
    pad = margin_for(max(abs(dy), abs(dx)))
    padded = np.pad(image, pad, mode="symmetric")
    spectrum = ndimage.fourier_shift(np.fft.fft2(padded), (dy, dx))
    return np.fft.ifft2(spectrum).real[pad:-pad, pad:-pad]


def simulate_translation(
    source: np.ndarray, dx: float, dy: float, margin: int | None = None
) -> SimulatedPair:
    """Build a pair whose moving image is the reference shifted by ``(dx, dy)``.

    The whole ``source`` window is shifted, then both images are cropped to its
    centre, leaving out ``margin`` px on each side. The moving image therefore
    shows real content coming in at its edges, instead of wrapped-around or
    padded pixels.

    Args:
        source: 2-D window larger than the wanted pair by the margin on each side.
        dx: Shift along columns, in pixels.
        dy: Shift along rows, in pixels.
        margin: Pixels cropped on each side. Defaults to, and may not be less
            than, ``margin_for(max(|dx|, |dy|))``.

    Returns:
        The simulated pair with a ``Translation`` ground truth.

    Raises:
        ValueError: If ``source`` is not 2-D, the margin too small for the
            shift, or ``source`` too small for the margin.
    """
    if source.ndim != 2:
        raise ValueError(f"source must be 2-D, got shape {source.shape}")
    needed = margin_for(max(abs(dx), abs(dy)))
    if margin is None:
        margin = needed
    if margin < needed:
        raise ValueError(f"margin {margin} px is below the {needed} px needed")
    if min(source.shape) <= 2 * margin:
        raise ValueError(
            f"source {source.shape} is too small for a {margin} px margin per side"
        )

    source = source.astype(float)
    crop = (slice(margin, -margin), slice(margin, -margin))
    return SimulatedPair(
        reference=source[crop],
        moving=fourier_shift(source, dy, dx)[crop],
        truth=Translation(dx=dx, dy=dy),
    )

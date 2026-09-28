"""How two images of the same ground differ in appearance, measured without
registering them.

The degradation presets claim what a good and a poor pair look like: noise, a
sharpness difference, a contrast and tone change, clouds. These estimators put
numbers on the same quantities for any pair, real or simulated, so presets can be
set next to real pairs. All but the correlation read each image's statistics or
power spectrum, which a shift does not change, so they do not depend on how well
the pair is registered, which is what the methods being compared estimate. See
docs/decisions.md.
"""

import math
from dataclasses import dataclass

import numpy as np
from scipy import signal

# Immerkær's operator: the difference of two Laplacians, which cancels smooth
# image structure and keeps white noise.
IMMERKAER_KERNEL = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], dtype=float)

# Spatial frequencies, in cycles per pixel, over which a sharpness difference is
# fitted. Below, the Hann window's own lobe dominates the spectrum; above,
# independent noise flattens the ratio of the two spectra towards one.
BLUR_BAND = (0.05, 0.25)
BLUR_BINS = 20

# Quantiles of the two histograms a tone curve is read from. Their ends are left
# out, so a few saturated or dark pixels do not bend it.
TONE_QUANTILES = np.linspace(0.05, 0.95, 19)


def noise_sigma(image: np.ndarray) -> float:
    """Standard deviation of the white noise in an image, by Immerkær's method.

    Immerkær, "Fast noise variance estimation", CVIU 64(2), 1996. Texture that
    the operator does not cancel (sharp edges, fine periodic patterns) reads as
    noise, so the estimate is an upper bound on a textured image.

    Args:
        image: 2-D image, at least 3 x 3.

    Returns:
        The noise standard deviation, in the image's units.
    """
    rows, cols = image.shape
    response = signal.convolve2d(image.astype(float), IMMERKAER_KERNEL, mode="valid")
    return (
        math.sqrt(math.pi / 2)
        * float(np.abs(response).sum())
        / (6 * (rows - 2) * (cols - 2))
    )


def snr_db(image: np.ndarray) -> float:
    """Scene contrast over noise, as the ``noise`` degradation defines it.

    Args:
        image: 2-D image.

    Returns:
        ``20 * log10(std(image) / noise_sigma(image))``, in decibels.
    """
    return 20 * math.log10(float(image.std()) / noise_sigma(image))


def _radial_power(image: np.ndarray, edges: np.ndarray) -> np.ndarray:
    """Mean power of a Hann-windowed image in rings of spatial frequency."""
    rows, cols = image.shape
    window = np.outer(np.hanning(rows), np.hanning(cols))
    power = np.abs(np.fft.fft2((image - image.mean()) * window)) ** 2
    freq = np.hypot(np.fft.fftfreq(rows)[:, None], np.fft.fftfreq(cols)[None, :])
    ring = np.digitize(freq, edges)
    return np.array([power[ring == i].mean() for i in range(1, len(edges))])


def blur_difference(reference: np.ndarray, moving: np.ndarray) -> float:
    """The Gaussian blur that makes the sharper image as soft as the other.

    A Gaussian of standard deviation ``s`` multiplies the power spectrum by
    ``exp(-4 pi^2 s^2 f^2)``, so the log ratio of the two images' radial power
    spectra is a line in ``f^2`` of slope ``-4 pi^2 (s_moving^2 - s_reference^2)``.
    A contrast change only moves its intercept. The slope is fitted over
    ``BLUR_BAND``. Ground that changed between two dates also changes the
    spectrum, so on real pairs this is an apparent sharpness difference.

    Args:
        reference: 2-D image.
        moving: 2-D image, same shape.

    Returns:
        ``sign(d) * sqrt(|d|)`` with ``d = s_moving^2 - s_reference^2``, in
        pixels: positive when the moving image is the blurrier one.
    """
    edges = np.linspace(*BLUR_BAND, BLUR_BINS + 1)
    centres = (edges[:-1] + edges[1:]) / 2
    ratio = np.log(_radial_power(moving, edges) / _radial_power(reference, edges))
    slope = np.polyfit(centres**2, ratio, 1)[0]
    d = -slope / (4 * math.pi**2)
    return math.copysign(math.sqrt(abs(d)), d)


def tone_bend(reference: np.ndarray, moving: np.ndarray) -> float:
    """How far the tone curve between two images is from a straight line.

    The moving image's quantiles are fitted by an affine function of the
    reference's, which a gain and an offset leave exact. What the line misses is
    a bend of the tone curve, such as a gamma. No curve shape is assumed: a
    fitted gamma is not identifiable when a few bright pixels stretch an image's
    range and the rest of its histogram sits in a small part of it, which is
    common at 10 m (roofs, bare soil, water glint). Only the histograms are
    compared, so the result does not depend on registration; ground that changed
    between two dates also bends the curve, so on real pairs this is an apparent
    tone change.

    Args:
        reference: Pixels of the reference image, any shape.
        moving: Pixels of the moving image, any shape.

    Returns:
        Root mean square residual of the affine fit, over the spread between the
        moving image's first and last fitted quantiles. 0 for a straight line.
    """
    u = np.quantile(reference, TONE_QUANTILES)
    v = np.quantile(moving, TONE_QUANTILES)
    design = np.stack([np.ones_like(u), u], axis=1)
    residual = v - design @ np.linalg.lstsq(design, v, rcond=None)[0]
    return float(np.sqrt(np.mean(residual**2)) / (v[-1] - v[0]))


@dataclass(frozen=True)
class Appearance:
    """How the moving image of a pair differs from its reference.

    Attributes:
        snr_reference_db: SNR of the reference, by ``snr_db``.
        snr_moving_db: SNR of the moving image.
        blur_px: Signed sharpness difference, by ``blur_difference``.
        gain: Standard deviation of the moving image over the reference's.
        offset: Mean of the moving image minus the reference's, in reference
            standard deviations.
        tone_bend: Bend of the tone curve, by ``tone_bend``.
        correlation: Pearson correlation of the two images, pixel by pixel. It
            falls with every difference above, with ground change, and with
            misregistration.
    """

    snr_reference_db: float
    snr_moving_db: float
    blur_px: float
    gain: float
    offset: float
    tone_bend: float
    correlation: float


def appearance(reference: np.ndarray, moving: np.ndarray) -> Appearance:
    """Measure how a moving image differs from its reference.

    Args:
        reference: 2-D image.
        moving: 2-D image of the same ground, same shape.

    Returns:
        The measurements.
    """
    reference = reference.astype(float)
    moving = moving.astype(float)
    return Appearance(
        snr_reference_db=snr_db(reference),
        snr_moving_db=snr_db(moving),
        blur_px=blur_difference(reference, moving),
        gain=float(moving.std() / reference.std()),
        offset=float((moving.mean() - reference.mean()) / reference.std()),
        tone_bend=tone_bend(reference, moving),
        correlation=float(np.corrcoef(reference.ravel(), moving.ravel())[0, 1]),
    )


def windows(size: int, shape: tuple[int, int]) -> list[tuple[slice, slice]]:
    """Tile an image into square windows, dropping the incomplete ones.

    Args:
        size: Side of a window, in pixels.
        shape: ``(rows, cols)`` of the image.

    Returns:
        ``(rows, cols)`` slices of each window, row by row.
    """
    return [
        (slice(top, top + size), slice(left, left + size))
        for top in range(0, shape[0] - size + 1, size)
        for left in range(0, shape[1] - size + 1, size)
    ]

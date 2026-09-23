"""Simulated image pairs with an exactly known displacement.

Every warp is band-limited interpolation: a Fourier phase ramp for a translation,
and the same interpolation applied in two one-dimensional passes for an affine
transform. See docs/decisions.md.
"""

import math
from dataclasses import dataclass

import numpy as np
from scipy import ndimage

from .displacement import Affine, Displacement, Translation

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
        cloud: Opacity of the clouds laid over the moving image, in [0, 1], same
            shape as ``moving``. ``None`` if the pair has no clouds.
    """

    reference: np.ndarray
    moving: np.ndarray
    truth: Displacement
    cloud: np.ndarray | None = None

    @property
    def cloud_fraction(self) -> float:
        """Share of moving-image pixels at least half covered by cloud."""
        if self.cloud is None:
            return 0.0
        return float(np.mean(self.cloud >= 0.5))

    @property
    def valid(self) -> np.ndarray:
        """Reference pixels whose content is still inside the moving image.

        A reference pixel is valid if its displaced position lies within the
        pixel centres of the moving image. Near the borders, content leaves the
        moving image, and the displacement there cannot be observed.
        """
        shape = self.reference.shape
        target = np.indices(shape, dtype=float) + self.truth.field(shape)
        rows, cols = shape
        return (
            (target[0] >= 0)
            & (target[0] <= rows - 1)
            & (target[1] >= 0)
            & (target[1] <= cols - 1)
        )


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


def _resample_lines(lines: np.ndarray, slope: float, offsets: np.ndarray) -> np.ndarray:
    """Resample each line of an array at evenly spaced positions, band-limited.

    Line ``l`` is sampled at ``slope * j + offsets[l]`` for ``j`` in
    ``0 .. n - 1``, by evaluating the Fourier series of the mirrored line there:
    the one-dimensional version of ``fourier_shift``, which it reduces to when
    ``slope`` is 1.

    Args:
        lines: ``(n_lines, n)`` array.
        slope: Spacing of the sample positions, in input pixels.
        offsets: Position of the first sample of each line, ``(n_lines,)``.

    Returns:
        Resampled lines, same shape as ``lines``.
    """
    n = lines.shape[1]
    j = np.arange(n)
    positions = slope * j[None, :] + offsets[:, None]
    pad = margin_for(float(np.abs(positions - j).max()))
    padded = np.pad(lines, ((0, 0), (pad, pad)), mode="symmetric")
    n_padded = padded.shape[1]
    k = np.fft.fftfreq(n_padded, d=1 / n_padded)
    # The positions of every line share their spacing, so the Fourier basis is
    # one matrix, and each line only adds its own phase ramp.
    basis = np.exp(2j * np.pi * np.outer(k, slope * j + pad) / n_padded)
    ramps = np.exp(2j * np.pi * np.outer(offsets, k) / n_padded)
    spectrum = np.fft.fft(padded, axis=1)
    # Taking the real part splits the Nyquist term evenly between +/- n/2.
    return ((spectrum * ramps) @ basis).real / n_padded


def fourier_affine(image: np.ndarray, transform: Affine) -> np.ndarray:
    """Warp an image by an affine transform with band-limited interpolation.

    Content at ``p`` in ``image`` ends up at ``transform.apply(p)`` in the output.
    The inverse map is split into a pass along rows, then a pass along columns
    (Catmull and Smith's two-pass decomposition), each a resampling at evenly
    spaced positions done by ``_resample_lines``. With an identity matrix it
    matches ``fourier_shift``.

    Args:
        image: 2-D image.
        transform: Affine transform in the image's pixel coordinates.

    Returns:
        Warped image, same shape and float dtype.

    Raises:
        ValueError: If the transform is too far from the identity for a two-pass
            decomposition (a turn of 45 degrees or more, or a mirror image).
    """
    inverse = np.linalg.inv(np.asarray(transform.matrix))
    start = -inverse @ transform.offset
    # Output pixel (y, x) samples the image at inverse @ (y, x) + start.
    (a, b), (c, d) = inverse
    if a <= abs(b) or np.linalg.det(inverse) <= 0:
        raise ValueError(f"cannot warp by {transform} in two passes")
    rows, cols = image.shape

    # Pass 1, along each image row v: output column x reads row v at a column
    # that is linear in x, with the same slope on every row.
    v = np.arange(rows)
    along_rows = _resample_lines(
        image,
        slope=(a * d - b * c) / a,
        offsets=(c / a) * v + start[1] - c * start[0] / a,
    )
    # Pass 2, along each output column x: output row y reads row a * y + b * x +
    # start[0] of the first pass.
    x = np.arange(cols)
    return _resample_lines(along_rows.T, slope=a, offsets=b * x + start[0]).T


def affine_reach(transform: Affine, shape: tuple[int, int]) -> float:
    """Largest row or column distance between an output pixel and its source.

    Args:
        transform: Affine transform in the pixel coordinates of the grid.
        shape: ``(rows, cols)`` of the grid.

    Returns:
        The largest absolute row or column offset, in pixels. The map is affine,
        so it is reached at a corner of the grid.
    """
    inverse = np.linalg.inv(np.asarray(transform.matrix))
    rows, cols = shape
    corners = np.array([[0, 0, rows - 1, rows - 1], [0, cols - 1, 0, cols - 1]])
    sources = inverse @ (corners - np.reshape(transform.offset, (2, 1)))
    return float(np.abs(sources - corners).max())


def simulate_affine(
    source: np.ndarray, transform: Affine, margin: int
) -> SimulatedPair:
    """Build a pair whose moving image is the reference warped by ``transform``.

    As in ``simulate_translation``, the whole ``source`` window is warped, then
    both images are cropped to its centre, so the moving image shows real
    content at its edges.

    Args:
        source: 2-D window larger than the wanted pair by the margin on each side.
        transform: Ground truth, in the pixel coordinates of the cropped pair.
        margin: Pixels cropped on each side, at least ``margin_for`` the
            transform's reach over the pair.

    Returns:
        The simulated pair with ``transform`` as its ground truth.

    Raises:
        ValueError: If ``source`` is not 2-D or too small for the margin, or the
            margin is too small for the transform.
    """
    if source.ndim != 2:
        raise ValueError(f"source must be 2-D, got shape {source.shape}")
    if min(source.shape) <= 2 * margin:
        raise ValueError(
            f"source {source.shape} is too small for a {margin} px margin per side"
        )
    rows, cols = source.shape
    needed = margin_for(affine_reach(transform, (rows - 2 * margin, cols - 2 * margin)))
    if margin < needed:
        raise ValueError(f"margin {margin} px is below the {needed} px needed")

    # The same transform, in the pixel coordinates of the uncropped window.
    m = np.full(2, float(margin))
    offset = np.asarray(transform.offset) + m - np.asarray(transform.matrix) @ m
    in_source = Affine(transform.matrix, (float(offset[0]), float(offset[1])))

    source = source.astype(float)
    crop = (slice(margin, -margin), slice(margin, -margin))
    return SimulatedPair(
        reference=source[crop],
        moving=fourier_affine(source, in_source)[crop],
        truth=transform,
    )

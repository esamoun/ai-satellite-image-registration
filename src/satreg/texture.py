"""Synthetic stand-in for a satellite chip, so the pipeline runs with no network."""

import numpy as np

# Sentinel-2 10 m bands have an MTF of roughly 0.2-0.3 at Nyquist. Without it, the
# texture carries energy at Nyquist that no sub-pixel shift can represent cleanly,
# and the simulated pairs themselves become the main error source.
MTF_AT_NYQUIST = 0.3


def power_law_field(
    shape: tuple[int, int],
    exponent: float,
    rng: np.random.Generator,
    mtf_at_nyquist: float = 1.0,
) -> np.ndarray:
    """Generate a random field whose amplitude spectrum falls as ``1 / f**exponent``.

    Args:
        shape: ``(rows, cols)`` of the field.
        exponent: Spectral slope. 1 gives the texture of natural scenes; larger
            values give smoother fields dominated by large structures.
        rng: Generator for the random phases and amplitudes.
        mtf_at_nyquist: Value at Nyquist of a Gaussian MTF applied to the
            spectrum, in (0, 1]. 1 applies none.

    Returns:
        Float array of ``shape`` with zero mean and unit standard deviation.

    Raises:
        ValueError: If ``mtf_at_nyquist`` is out of range.
    """
    if not 0 < mtf_at_nyquist <= 1:
        raise ValueError(f"mtf_at_nyquist must be in (0, 1], got {mtf_at_nyquist}")

    fy = np.fft.fftfreq(shape[0])[:, None]
    fx = np.fft.fftfreq(shape[1])[None, :]
    freq = np.hypot(fy, fx)
    amplitude = np.zeros_like(freq)
    np.power(freq, -exponent, out=amplitude, where=freq > 0)
    amplitude *= mtf_at_nyquist ** ((freq / 0.5) ** 2)

    noise = rng.normal(size=shape) + 1j * rng.normal(size=shape)
    field = np.fft.ifft2(noise * amplitude).real
    return (field - field.mean()) / field.std()


def fractal_texture(
    size: int, seed: int, mtf_at_nyquist: float = MTF_AT_NYQUIST
) -> np.ndarray:
    """Generate a square 1/f texture seen through a Gaussian sensor MTF.

    Natural and remote-sensing scenes have roughly 1/f amplitude spectra, so this
    gives phase correlation and feature matchers structure at every scale.

    Args:
        size: Side length in pixels.
        seed: Seed for the random phases and amplitudes.
        mtf_at_nyquist: MTF value at the Nyquist frequency, in (0, 1].

    Returns:
        ``(size, size)`` float array with zero mean and unit standard deviation.

    Raises:
        ValueError: If ``size`` is too small or ``mtf_at_nyquist`` out of range.
    """
    if size < 8:
        raise ValueError(f"size must be at least 8 px, got {size}")
    return power_law_field(
        (size, size), 1.0, np.random.default_rng(seed), mtf_at_nyquist
    )

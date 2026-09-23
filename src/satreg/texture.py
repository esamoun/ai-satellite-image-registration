"""Synthetic stand-in for a satellite chip, so the pipeline runs with no network."""

import numpy as np

# Sentinel-2 10 m bands have an MTF of roughly 0.2-0.3 at Nyquist. Without it, the
# texture carries energy at Nyquist that no sub-pixel shift can represent cleanly,
# and the simulated pairs themselves become the main error source.
MTF_AT_NYQUIST = 0.3


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
    if not 0 < mtf_at_nyquist <= 1:
        raise ValueError(f"mtf_at_nyquist must be in (0, 1], got {mtf_at_nyquist}")

    rng = np.random.default_rng(seed)
    fy = np.fft.fftfreq(size)[:, None]
    fx = np.fft.fftfreq(size)[None, :]
    freq = np.hypot(fy, fx)
    amplitude = np.divide(1.0, freq, out=np.zeros_like(freq), where=freq > 0)
    amplitude *= mtf_at_nyquist ** ((freq / 0.5) ** 2)

    noise = rng.normal(size=(size, size)) + 1j * rng.normal(size=(size, size))
    image = np.fft.ifft2(noise * amplitude).real
    return (image - image.mean()) / image.std()

import numpy as np
import pytest
from scipy import ndimage

from satreg.appearance import (
    appearance,
    blur_difference,
    noise_sigma,
    snr_db,
    tone_bend,
    windows,
)
from satreg.texture import fractal_texture


@pytest.fixture
def texture():
    """A 256 px 1/f texture, scaled like Sentinel-2 digital numbers."""
    return 1000 + 300 * fractal_texture(256, seed=3)


def test_noise_on_a_smooth_image_is_measured_at_its_level():
    rows, cols = np.mgrid[:256, :256]
    smooth = 1000 + 2 * rows + 3 * cols  # a plane, which the operator cancels
    noisy = smooth + np.random.default_rng(0).normal(0, 5, smooth.shape)

    assert noise_sigma(smooth) == pytest.approx(0, abs=1e-9)
    assert noise_sigma(noisy) == pytest.approx(5, rel=0.03)
    assert snr_db(noisy) == pytest.approx(20 * np.log10(noisy.std() / 5), abs=0.3)


@pytest.mark.parametrize("sigma", [1.0, 1.5])
def test_blur_difference_recovers_the_kernel_width(texture, sigma):
    blurred = ndimage.gaussian_filter(texture, sigma, mode="reflect")

    assert blur_difference(texture, blurred) == pytest.approx(sigma, rel=0.05)


def test_a_narrow_kernel_reads_as_the_width_it_samples_to(texture):
    # A 0.4 px Gaussian sampled on the pixel grid is a 3-tap kernel whose
    # frequency response matches a Gaussian of about 0.28 px: that is what the
    # mild preset's blur does to an image.
    blurred = ndimage.gaussian_filter(texture, 0.4, mode="reflect")

    assert blur_difference(texture, blurred) == pytest.approx(0.28, abs=0.03)


def test_blur_difference_is_signed_and_ignores_contrast_and_level(texture):
    blurred = ndimage.gaussian_filter(texture, 1.0, mode="reflect")
    sharp_first = blur_difference(texture, blurred)

    assert blur_difference(blurred, texture) == pytest.approx(-sharp_first)
    assert blur_difference(texture, 0.6 * blurred + 500) == pytest.approx(sharp_first)
    assert blur_difference(texture, texture) == pytest.approx(0, abs=1e-6)


def test_tone_bend_is_zero_for_a_gain_and_offset_and_not_for_a_gamma(texture):
    u = (texture - texture.min()) / np.ptp(texture)

    assert tone_bend(u, 1.3 * u - 0.2) == pytest.approx(0, abs=1e-9)
    assert tone_bend(u, u**1.5) > 0.01
    assert tone_bend(u, u**1.5) > tone_bend(u, u**1.2)


def test_tone_bend_reads_only_the_histograms(texture):
    u = (texture - texture.min()) / np.ptp(texture)
    moving = u**1.5

    shifted = np.roll(moving, (17, -40), axis=(0, 1))

    assert tone_bend(u, shifted) == pytest.approx(tone_bend(u, moving))


def test_appearance_of_a_contrast_and_level_change(texture):
    moving = 1.5 * (texture - texture.mean()) + texture.mean() + 0.3 * texture.std()

    measured = appearance(texture, moving)

    assert measured.gain == pytest.approx(1.5)
    assert measured.offset == pytest.approx(0.3)
    assert measured.correlation == pytest.approx(1)
    assert measured.blur_px == pytest.approx(0, abs=1e-6)
    assert measured.tone_bend == pytest.approx(0, abs=1e-9)
    assert measured.snr_moving_db == pytest.approx(measured.snr_reference_db)


def test_windows_tile_the_image_and_drop_the_incomplete_ones():
    tiles = windows(256, (1024, 700))

    assert len(tiles) == 8
    assert tiles[0] == (slice(0, 256), slice(0, 256))
    assert tiles[1] == (slice(0, 256), slice(256, 512))
    assert tiles[-1] == (slice(768, 1024), slice(256, 512))
    assert windows(256, (100, 100)) == []

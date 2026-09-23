import numpy as np
import pytest
from scipy import ndimage

from satreg.displacement import Translation
from satreg.simulate import (
    RINGING_BORDER_PX,
    fourier_shift,
    margin_for,
    simulate_translation,
)
from satreg.texture import fractal_texture


def test_integer_shift_follows_the_displacement_convention():
    # moving(p + d) = reference(p): content moves by +d.
    source = fractal_texture(128, seed=0)

    pair = simulate_translation(source, dx=3, dy=-2)

    ref, mov = pair.reference, pair.moving
    np.testing.assert_allclose(mov[:-2, 3:], ref[2:, :-3], atol=1e-6)
    assert pair.truth == Translation(dx=3, dy=-2)


def test_sub_pixel_shift_matches_the_exact_band_limited_shift():
    # On a periodic image the FFT shift is exact, so a window cut from a shifted
    # periodic texture is the ground truth for the same window shifted alone.
    full = fractal_texture(512, seed=1)
    dy, dx = 0.5, -0.3
    exact = np.fft.ifft2(ndimage.fourier_shift(np.fft.fft2(full), (dy, dx))).real
    window = (slice(100, 300), slice(100, 300))

    pair = simulate_translation(full[window], dx=dx, dy=dy)

    m = margin_for(max(abs(dx), abs(dy)))
    inner = (slice(100 + m, 300 - m), slice(100 + m, 300 - m))
    error = np.abs(pair.moving - exact[inner])
    # Texture has unit standard deviation: the error is a few percent of it.
    assert error.max() < 0.1
    assert error.std() < 0.02


def test_fourier_shift_does_not_blur():
    image = fractal_texture(128, seed=2)

    there_and_back = fourier_shift(fourier_shift(image, 0.5, 0.5), -0.5, -0.5)

    b = RINGING_BORDER_PX
    assert there_and_back[b:-b, b:-b].std() == pytest.approx(
        image[b:-b, b:-b].std(), rel=0.02
    )


def test_pair_is_the_source_minus_the_margin():
    source = fractal_texture(100, seed=0)

    pair = simulate_translation(source, dx=1.2, dy=0.4)

    m = margin_for(1.2)
    assert pair.reference.shape == pair.moving.shape == (100 - 2 * m, 100 - 2 * m)
    np.testing.assert_array_equal(pair.reference, source[m:-m, m:-m])


def test_explicit_margin_is_honoured_and_checked():
    source = fractal_texture(128, seed=0)

    assert simulate_translation(source, 1.0, 1.0, margin=30).reference.shape == (
        68,
        68,
    )
    with pytest.raises(ValueError, match="margin"):
        simulate_translation(source, dx=5.0, dy=0.0, margin=margin_for(1.0))


@pytest.mark.parametrize(
    "source", [np.zeros((30, 30)), np.zeros((8, 128, 128))], ids=["small", "3-D"]
)
def test_unusable_sources_are_rejected(source):
    with pytest.raises(ValueError):
        simulate_translation(source, dx=1.0, dy=1.0)

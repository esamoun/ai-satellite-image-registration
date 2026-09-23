import numpy as np
import pytest

from satreg.texture import fractal_texture


def test_texture_is_standardised():
    image = fractal_texture(128, seed=0)

    assert image.shape == (128, 128)
    assert abs(image.mean()) < 1e-9
    assert image.std() == pytest.approx(1.0)


def test_same_seed_gives_same_texture_and_another_seed_does_not():
    a = fractal_texture(64, seed=3)

    np.testing.assert_array_equal(a, fractal_texture(64, seed=3))
    assert not np.allclose(a, fractal_texture(64, seed=4))


def test_lower_mtf_leaves_less_energy_near_nyquist():
    def nyquist_energy(image):
        spectrum = np.abs(np.fft.fft2(image)) ** 2
        f = np.hypot(*np.meshgrid(np.fft.fftfreq(128), np.fft.fftfreq(128)))
        return spectrum[f > 0.4].sum() / spectrum.sum()

    sharp = fractal_texture(128, seed=0, mtf_at_nyquist=1.0)
    blurred = fractal_texture(128, seed=0, mtf_at_nyquist=0.1)

    assert nyquist_energy(blurred) < nyquist_energy(sharp) / 10


@pytest.mark.parametrize("kwargs", [{"size": 4}, {"size": 64, "mtf_at_nyquist": 0}])
def test_invalid_parameters_are_rejected(kwargs):
    with pytest.raises(ValueError):
        fractal_texture(seed=0, **kwargs)

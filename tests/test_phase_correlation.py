import numpy as np
import pytest

from satreg.degrade import Blur
from satreg.displacement import Translation
from satreg.methods import METHODS, load_methods
from satreg.methods.phase_correlation import PhaseCorrelation, phase_correlation
from satreg.simulate import simulate_translation
from satreg.texture import fractal_texture


def test_sign_convention_on_an_integer_shift():
    # Content moved 3 px right and 2 px up must read as dx=+3, dy=-2.
    pair = simulate_translation(fractal_texture(256, seed=0), dx=3, dy=-2)

    estimate = phase_correlation(pair.reference, pair.moving)

    assert estimate.dx == pytest.approx(3, abs=0.01)
    assert estimate.dy == pytest.approx(-2, abs=0.01)


@pytest.mark.parametrize(
    ("dx", "dy"),
    [(0.0, 0.0), (0.25, -0.4), (-1.37, 2.81), (3.9, -3.95), (0.05, 0.02)],
)
def test_recovers_known_sub_pixel_shifts_on_a_clean_pair(dx, dy):
    pair = simulate_translation(fractal_texture(300, seed=7), dx=dx, dy=dy)

    estimate = phase_correlation(pair.reference, pair.moving)

    assert isinstance(estimate, Translation)
    assert estimate.dx == pytest.approx(dx, abs=0.05)
    assert estimate.dy == pytest.approx(dy, abs=0.05)


def test_is_registered_under_a_stable_name():
    assert METHODS["phase_correlation"] is phase_correlation


@pytest.mark.parametrize(("dx", "dy"), [(0.25, -0.4), (-1.37, 2.81), (3.9, -3.95)])
def test_hann_variant_recovers_known_sub_pixel_shifts(dx, dy):
    pair = simulate_translation(fractal_texture(300, seed=7), dx=dx, dy=dy)

    estimate = PhaseCorrelation(window="hann")(pair.reference, pair.moving)

    assert estimate.dx == pytest.approx(dx, abs=0.05)
    assert estimate.dy == pytest.approx(dy, abs=0.05)


def test_hann_variant_ignores_the_level_of_the_images():
    # Sentinel-2 digital numbers sit far above their spread; the window must
    # taper the content, not add the same bump to both images.
    pair = simulate_translation(fractal_texture(256, seed=3), dx=1.3, dy=-0.7)
    hann = PhaseCorrelation(window="hann")

    low = hann(pair.reference, pair.moving)
    high = hann(pair.reference + 5000, pair.moving + 5000)

    assert (high.dx, high.dy) == pytest.approx((low.dx, low.dy), abs=1e-6)


def test_hann_variant_keeps_a_blurred_pair_on_its_shift():
    pair = simulate_translation(fractal_texture(256, seed=5), dx=2.4, dy=-1.6)
    blurred = Blur(sigma=1.0)(pair, np.random.default_rng(0))

    estimate = PhaseCorrelation(window="hann")(blurred.reference, blurred.moving)

    assert estimate.dx == pytest.approx(2.4, abs=0.05)
    assert estimate.dy == pytest.approx(-1.6, abs=0.05)


def test_default_parameters_match_the_plain_function():
    pair = simulate_translation(fractal_texture(128, seed=1), dx=0.6, dy=0.2)

    assert PhaseCorrelation()(pair.reference, pair.moving) == phase_correlation(
        pair.reference, pair.moving
    )


def test_unknown_window_is_rejected(tmp_path):
    config = tmp_path / "methods.toml"
    config.write_text('[methods.phase_correlation]\nwindow = "blackman"\n')

    with pytest.raises(ValueError, match="window must be one of hann"):
        load_methods(config)

import pytest

from satreg.displacement import Translation
from satreg.methods import METHODS
from satreg.methods.phase_correlation import phase_correlation
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

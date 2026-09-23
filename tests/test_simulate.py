import math

import numpy as np
import pytest
from scipy import ndimage

from satreg.displacement import Affine, Translation
from satreg.simulate import (
    RINGING_BORDER_PX,
    affine_reach,
    fourier_affine,
    fourier_shift,
    margin_for,
    simulate_affine,
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


# Far larger than the benchmark's ranges, so that a wrong sign or order shows.
STRONG_AFFINE = {
    "rotation_deg": 2.0,
    "scale": 1.02,
    "shear": 0.01,
    "dx": 1.3,
    "dy": -0.7,
}


def blobs(shape, centres, sigma=1.5, inverse=None):
    """Gaussian spots, each seen through the linear map whose inverse is given.

    A spot of width 1.5 px is band-limited to 1e-5 at Nyquist, so band-limited
    interpolation should move it with no visible error.
    """
    inverse = np.eye(2) if inverse is None else inverse
    grid = np.indices(shape, dtype=float)
    out = np.zeros(shape)
    for centre in centres:
        local = np.tensordot(inverse, grid - np.reshape(centre, (2, 1, 1)), axes=1)
        out += np.exp(-(local**2).sum(axis=0) / (2 * sigma**2))
    return out


def test_affine_truth_matches_the_warp_on_a_point_grid():
    size, margin = 160, 30
    truth = Affine.about(((size - 1) / 2, (size - 1) / 2), **STRONG_AFFINE)
    # Points on the reference grid of the pair, drawn in the uncropped window.
    points = [
        (r, c) for r in range(15, size - 14, 26) for c in range(15, size - 14, 26)
    ]
    source = blobs((size + 2 * margin,) * 2, np.add(points, margin))

    pair = simulate_affine(source, truth, margin)

    field = truth.field(pair.reference.shape)
    for r, c in points:
        expected = np.array([r, c]) + field[:, r, c]
        top, left = np.round(expected).astype(int) - 7
        window = pair.moving[top : top + 15, left : left + 15]
        rows, cols = np.indices(window.shape)
        found = (
            np.array(
                [
                    (window * rows).sum() + top * window.sum(),
                    (window * cols).sum() + left * window.sum(),
                ]
            )
            / window.sum()
        )
        np.testing.assert_allclose(found, expected, atol=1e-3)


def test_affine_warp_matches_an_analytic_rendering():
    # Warping spots rendered at p gives spots, stretched by the linear part,
    # rendered at transform(p). The spots stay clear of the edges, where the
    # intermediate pass runs out of image; pairs crop that band away.
    shape = (120, 120)
    transform = Affine.about((60.0, 60.0), **STRONG_AFFINE)
    centres = [(r, c) for r in range(30, 91, 15) for c in range(30, 91, 15)]
    moved = [transform.apply(np.array(p, dtype=float)) for p in centres]

    warped = fourier_affine(blobs(shape, centres), transform)

    exact = blobs(shape, moved, inverse=np.linalg.inv(transform.matrix))
    b = RINGING_BORDER_PX
    np.testing.assert_allclose(warped[b:-b, b:-b], exact[b:-b, b:-b], atol=1e-3)


@pytest.mark.parametrize(("dy", "dx"), [(0.5, 0.5), (0.3, -0.7), (3.0, -2.0)])
def test_affine_warp_without_linear_part_is_the_fourier_shift(dy, dx):
    # The same interpolation for every scenario: a translation warped as an
    # affine transform gives the translation scenario's moving image.
    image = fractal_texture(160, seed=3)

    as_affine = fourier_affine(image, Affine(((1.0, 0.0), (0.0, 1.0)), (dy, dx)))

    b = RINGING_BORDER_PX
    shifted = fourier_shift(image, dy, dx)
    np.testing.assert_allclose(as_affine[b:-b, b:-b], shifted[b:-b, b:-b], atol=1e-3)


def test_affine_pair_is_cropped_like_a_translation_pair():
    source = fractal_texture(136, seed=0)
    truth = Affine.about((43.5, 43.5), **STRONG_AFFINE)

    pair = simulate_affine(source, truth, margin=24)

    assert pair.reference.shape == pair.moving.shape == (88, 88)
    np.testing.assert_array_equal(pair.reference, source[24:-24, 24:-24])
    assert pair.truth == truth


def test_affine_margin_is_checked_against_the_reach():
    source = fractal_texture(200, seed=0)
    truth = Affine.about((79.5, 79.5), rotation_deg=5.0)

    reach = affine_reach(truth, (160, 160))

    # A 5 degree turn about the centre moves each corner coordinate by
    # 79.5 (sin 5 + 1 - cos 5) px at most.
    turn = math.radians(5.0)
    assert reach == pytest.approx(79.5 * (math.sin(turn) + 1 - math.cos(turn)))
    with pytest.raises(ValueError, match="margin"):
        simulate_affine(source, truth, margin=20)


def test_affine_warp_refuses_what_two_passes_cannot_do():
    with pytest.raises(ValueError, match="two passes"):
        fourier_affine(np.zeros((32, 32)), Affine.about((16.0, 16.0), rotation_deg=60))


def test_valid_pixels_are_those_whose_content_stays_in_the_moving_image():
    pair = simulate_translation(fractal_texture(100, seed=0), dx=3.0, dy=-1.5)
    rows, cols = pair.reference.shape

    valid = pair.valid

    # Content moves 3 px right and 1.5 px up: the last 3 columns and the first
    # 2 rows leave the image.
    assert valid.shape == (rows, cols)
    assert not valid[:, -3:].any() and valid[2:, : cols - 3].all()
    assert not valid[:2].any()


def test_valid_pixels_of_a_zoom_exclude_the_border():
    size = 60
    truth = Affine.about(((size - 1) / 2,) * 2, scale=1.1)

    pair = simulate_affine(fractal_texture(size + 80, seed=0), truth, margin=40)

    # Points more than 29.5 / 1.1 = 26.8 px from the centre along an axis leave.
    valid = pair.valid
    assert valid[30, 30] and valid[30, 3] and not valid[30, 2]
    assert not valid[0, 0]

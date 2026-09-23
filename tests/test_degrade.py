from pathlib import Path

import numpy as np
import pytest
from scipy import ndimage

from satreg.degrade import Blur, Clouds, Noise, Preset, Radiometry, load_presets
from satreg.displacement import Translation
from satreg.simulate import SimulatedPair, simulate_translation
from satreg.texture import fractal_texture

REPO_PRESETS = Path(__file__).parents[1] / "configs" / "degradations.toml"

EVERY_DEGRADATION = [
    Radiometry(gain=0.7, offset=-0.5, gamma=1.5),
    Clouds(cover=0.3),
    Blur(sigma=1.0),
    Noise(snr_db=15),
    Preset(Radiometry(gamma=0.8), Clouds(cover=0.1), Blur(sigma=0.5), Noise(20)),
]


def clean_pair(seed: int = 0, size: int = 160) -> SimulatedPair:
    source = fractal_texture(size + 40, seed=seed)
    return simulate_translation(source, dx=1.3, dy=-0.7, margin=20)


def flat_pair(moving: np.ndarray) -> SimulatedPair:
    """A pair whose moving image is given, to measure a degradation in isolation."""
    reference = fractal_texture(moving.shape[0], seed=9)
    return SimulatedPair(reference, moving, Translation(0.0, 0.0))


def rng(seed: int = 0) -> np.random.Generator:
    return np.random.default_rng(seed)


@pytest.mark.parametrize("snr_db", [10.0, 20.0, 35.0])
def test_noise_reaches_the_requested_snr_on_both_images(snr_db):
    pair = clean_pair()

    noisy = Noise(snr_db)(pair, rng())

    for clean, degraded in [
        (pair.reference, noisy.reference),
        (pair.moving, noisy.moving),
    ]:
        noise = degraded - clean
        measured = 20 * np.log10(pair.reference.std() / noise.std())
        assert measured == pytest.approx(snr_db, abs=0.1)
        assert abs(noise.mean()) < 0.05 * noise.std()


def test_noise_is_drawn_independently_for_each_image():
    pair = clean_pair()

    noisy = Noise(10.0)(pair, rng())

    a = (noisy.reference - pair.reference).ravel()
    b = (noisy.moving - pair.moving).ravel()
    assert abs(np.corrcoef(a, b)[0, 1]) < 0.03


@pytest.mark.parametrize("sigma", [1.5, 3.0])
def test_blur_attenuates_white_noise_as_a_gaussian_of_that_sigma(sigma):
    # A normalised 2-D Gaussian of sigma s keeps 1 / (4 pi s^2) of the variance
    # of white noise.
    white = rng(1).normal(size=(512, 512))

    blurred = Blur(sigma)(flat_pair(white), rng()).moving

    assert blurred.var() == pytest.approx(1 / (4 * np.pi * sigma**2), rel=0.05)


def test_blur_leaves_the_reference_alone_and_zero_sigma_changes_nothing():
    pair = clean_pair()

    blurred = Blur(1.0)(pair, rng())

    assert blurred.reference is pair.reference
    assert Blur(0.0)(pair, rng()) is pair


def test_linear_radiometry_scales_contrast_and_shifts_level():
    pair = clean_pair()

    changed = Radiometry(gain=0.6, offset=0.4)(pair, rng()).moving

    assert changed.std() == pytest.approx(0.6 * pair.moving.std())
    shift = changed.mean() - pair.moving.mean()
    assert shift == pytest.approx(0.4 * pair.reference.std())


def test_radiometry_is_relative_to_the_image_level():
    # Sentinel-2 digital numbers sit around a mean far above their spread; a
    # contrast gain must not turn into a huge level shift there.
    pair = clean_pair()
    bright = SimulatedPair(
        1500 + 300 * pair.reference, 1500 + 300 * pair.moving, pair.truth
    )

    changed = Radiometry(gain=0.7, gamma=1.5)(bright, rng()).moving
    reference = Radiometry(gain=0.7, gamma=1.5)(pair, rng()).moving

    np.testing.assert_allclose(changed, 1500 + 300 * reference)


@pytest.mark.parametrize("gamma", [0.6, 1.5])
def test_gamma_bends_values_but_keeps_their_order_and_range(gamma):
    pair = clean_pair()

    changed = Radiometry(gamma=gamma)(pair, rng()).moving

    assert changed.min() == pytest.approx(pair.moving.min())
    assert changed.max() == pytest.approx(pair.moving.max())
    np.testing.assert_array_equal(
        np.argsort(changed, axis=None), np.argsort(pair.moving, axis=None)
    )
    assert not np.allclose(changed, pair.moving)


@pytest.mark.parametrize("cover", [0.05, 0.3, 0.7])
def test_clouds_cover_the_requested_share_with_soft_edges(cover):
    pair = clean_pair()

    cloudy = Clouds(cover)(pair, rng())

    assert cloudy.cloud_fraction == pytest.approx(cover, abs=1 / cloudy.cloud.size)
    assert cloudy.cloud.min() >= 0 and cloudy.cloud.max() <= 1
    edges = np.mean((cloudy.cloud > 0) & (cloudy.cloud < 1))
    assert 0.01 < edges < 0.5
    assert np.mean(cloudy.cloud == 1) > 0


def test_clouds_are_bright_and_leave_clear_pixels_untouched():
    pair = clean_pair()
    clouds = Clouds(0.3, brightness=4.0)

    cloudy = clouds(pair, rng())

    clear = cloudy.cloud == 0
    np.testing.assert_array_equal(cloudy.moving[clear], pair.moving[clear])
    level = pair.reference.mean() + 4.0 * pair.reference.std()
    np.testing.assert_allclose(cloudy.moving[cloudy.cloud == 1], level)
    assert cloudy.reference is pair.reference


def test_clouds_form_a_few_large_banks_not_speckle():
    cloudy = Clouds(0.3)(clean_pair(size=256), rng())

    _, banks = ndimage.label(cloudy.cloud >= 0.5)
    assert banks < 30


def test_no_cloud_cover_leaves_the_pair_unchanged():
    pair = clean_pair()

    assert Clouds(0.0)(pair, rng()) is pair
    assert pair.cloud_fraction == 0.0


def test_stacked_clouds_combine_their_opacity():
    pair = clean_pair()

    once = Clouds(0.2)(pair, rng(1))
    twice = Clouds(0.2)(once, rng(2))

    assert np.all(twice.cloud >= once.cloud)
    assert twice.cloud_fraction > once.cloud_fraction


@pytest.mark.parametrize("degrade", EVERY_DEGRADATION, ids=lambda d: type(d).__name__)
def test_degradations_never_change_the_geometry(degrade):
    pair = clean_pair()
    before = (pair.reference.copy(), pair.moving.copy())

    degraded = degrade(pair, rng())

    assert degraded.truth == pair.truth == Translation(dx=1.3, dy=-0.7)
    assert degraded.reference.shape == degraded.moving.shape == pair.moving.shape
    # The clean pair is left as it was, so every preset starts from the same one.
    np.testing.assert_array_equal(pair.reference, before[0])
    np.testing.assert_array_equal(pair.moving, before[1])


def test_blur_moves_no_content():
    # Blurring the moving image must give the same image as shifting a blurred
    # scene: blur and shift commute when the blur has no geometry of its own.
    # Checked on the pixels themselves, not through a registration method, which
    # has biases of its own (see docs/failures.md).
    source = fractal_texture(200, seed=0)
    pair = simulate_translation(source, dx=1.3, dy=-0.7, margin=20)

    blurred = Blur(1.0)(pair, rng()).moving

    expected = simulate_translation(
        ndimage.gaussian_filter(source, 1.0), dx=1.3, dy=-0.7, margin=20
    ).moving
    # Past 4 sigma from the border, where the blur of the cropped pair and of the
    # full scene see the same pixels. The texture has unit standard deviation.
    inner = (slice(4, -4), slice(4, -4))
    assert np.abs(blurred - expected)[inner].max() < 0.03


@pytest.mark.parametrize("degrade", EVERY_DEGRADATION, ids=lambda d: type(d).__name__)
def test_same_seed_gives_the_same_pair_bit_for_bit(degrade):
    pair = clean_pair()

    first, second = degrade(pair, rng(7)), degrade(pair, rng(7))

    np.testing.assert_array_equal(first.reference, second.reference)
    np.testing.assert_array_equal(first.moving, second.moving)


def test_another_seed_gives_other_noise_and_clouds():
    pair = clean_pair()
    degrade = Preset(clouds=Clouds(0.3), noise=Noise(20))

    first, second = degrade(pair, rng(7)), degrade(pair, rng(8))

    assert not np.array_equal(first.moving, second.moving)
    assert not np.array_equal(first.cloud, second.cloud)


def test_preset_applies_its_steps_in_physical_order():
    pair = clean_pair()
    steps = [Radiometry(gamma=1.4), Clouds(0.2), Blur(0.8), Noise(25)]

    by_hand = pair
    generator = rng(3)
    for step in steps:
        by_hand = step(by_hand, generator)
    preset = Preset(noise=steps[3], blur=steps[2], clouds=steps[1], radiometry=steps[0])

    np.testing.assert_array_equal(preset(pair, rng(3)).moving, by_hand.moving)


def test_repository_presets_load_in_file_order_and_clean_is_the_identity():
    presets = load_presets(REPO_PRESETS)
    pair = clean_pair()

    assert list(presets) == ["clean", "mild", "hard"]
    assert presets["clean"](pair, rng()) is pair
    assert presets["hard"].clouds.cover > presets["mild"].clouds.cover
    assert presets["hard"].noise.snr_db < presets["mild"].noise.snr_db


def test_presets_parse_parameters_and_ignore_key_order(tmp_path):
    path = tmp_path / "presets.toml"
    path.write_text(
        "[presets.a]\nnoise = { snr_db = 20 }\nblur = { sigma = 0.5 }\n"
        "[presets.b]\nblur = { sigma = 0.5 }\nnoise = { snr_db = 20 }\n"
    )

    presets = load_presets(path)

    assert presets["a"] == presets["b"] == Preset(blur=Blur(0.5), noise=Noise(20))


@pytest.mark.parametrize(
    "body, message",
    [
        ("[other]\n", "presets"),
        ("[presets.a]\nhaze = { depth = 1 }\n", "preset a: unknown degradation haze"),
        ("[presets.a]\nblur = { radius = 1 }\n", "preset a:.*radius"),
        ("[presets.a]\nblur = { sigma = -1 }\n", "preset a:.*sigma"),
        ("[presets.a]\nclouds = { cover = 1.5 }\n", "preset a:.*cover"),
    ],
)
def test_invalid_presets_are_rejected_with_the_preset_named(tmp_path, body, message):
    path = tmp_path / "presets.toml"
    path.write_text(body)

    with pytest.raises(ValueError, match=message):
        load_presets(path)


@pytest.mark.parametrize(
    "build",
    [
        lambda: Radiometry(gain=0),
        lambda: Radiometry(gamma=-1),
        lambda: Clouds(cover=-0.1),
        lambda: Clouds(cover=0.2, softness=0),
        lambda: Blur(sigma=-0.5),
    ],
)
def test_invalid_parameters_are_rejected(build):
    with pytest.raises(ValueError):
        build()

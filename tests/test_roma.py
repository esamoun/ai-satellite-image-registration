from pathlib import Path

import numpy as np
import pytest

from satreg.displacement import Affine, Dense
from satreg.methods import (
    METHODS,
    Estimate,
    RegistrationFailure,
    cost_meter,
    deep,
    load_methods,
    missing_dependencies,
)
from satreg.methods.lightglue import network_input
from satreg.methods.roma import (
    IMAGENET_MEAN,
    IMAGENET_STD,
    Roma,
    lattice,
    to_pair_grid,
    to_pixels,
    weights_files,
    working_input,
)
from satreg.metrics import score
from satreg.simulate import (
    affine_reach,
    margin_for,
    simulate_affine,
    simulate_translation,
)
from satreg.texture import fractal_texture

REPO_CONFIG = Path(__file__).parents[1] / "configs" / "methods.toml"

# The network tests run RoMa on a 224 px working grid, the smallest that still
# covers a 160 px pair with finer cells, so that each call takes about 2 s on the
# M1's CPU (2.9 s at the configured 280).
TEST_RESOLUTION = 224


def _skip_reason() -> str | None:
    if missing := missing_dependencies(METHODS["roma"]):
        return f"needs romatch ({', '.join(missing)} missing): make install-roma"
    for weights in weights_files():
        if not Path(weights).exists():
            return f"needs RoMa's weights at {weights}: make install-roma"
    return None


# The tests that run the network. The conftest refuses network access, so the
# weights must already be in PyTorch's cache.
needs_roma = pytest.mark.skipif(_skip_reason() is not None, reason=_skip_reason() or "")
needs_torch = pytest.mark.skipif(
    bool(deep.missing_modules()), reason="needs the dl extra: make install-dl"
)


def _normalised_centres(n: int) -> np.ndarray:
    """Where RoMa puts the centres of ``n`` pixels: -1 and 1 are the outer edges."""
    return (2 * np.arange(n) + 1) / n - 1


def _warp_of(transform: Affine, working: int, shape: tuple[int, int]) -> np.ndarray:
    """The normalised (x, y) warp RoMa would return on a ``working`` px grid for
    a pair of ``shape`` moved by ``transform``, in the pair's pixels."""
    rows, cols = shape
    y, x = np.meshgrid(
        _normalised_centres(working), _normalised_centres(working), indexing="ij"
    )
    # Working-grid centres in the pair's pixels, mapped, then normalised back.
    pixels = np.stack([(y + 1) * rows / 2 - 0.5, (x + 1) * cols / 2 - 0.5])
    moved = transform.apply(pixels)
    return np.stack([(2 * moved[1] + 1) / cols - 1, (2 * moved[0] + 1) / rows - 1])


def test_pixel_centres_map_to_integers():
    rows, cols = 5, 8
    y, x = np.meshgrid(
        _normalised_centres(rows), _normalised_centres(cols), indexing="ij"
    )

    pixels = to_pixels(np.stack([x, y]), (rows, cols))

    np.testing.assert_allclose(pixels, np.indices((rows, cols)), atol=1e-12)


def test_the_outer_edges_are_half_a_pixel_beyond_the_outer_centres():
    np.testing.assert_allclose(
        to_pixels(np.array([[-1.0, 1.0], [-1.0, 1.0]]), (4, 10)),
        [[-0.5, 3.5], [-0.5, 9.5]],
    )


@pytest.mark.parametrize("working", [560, 224, 280])
def test_a_linear_map_on_the_working_grid_resamples_exactly(working):
    # The working grid's centres, written in the pair's pixels: a linear map
    # that must read back as the pair's own indices.
    size = 256
    centres = (np.arange(working) + 0.5) * size / working - 0.5
    maps = np.stack(np.meshgrid(centres, centres, indexing="ij"))

    resampled = to_pair_grid(maps, (size, size))

    # Between the outermost working centres the interpolation is exact. On a
    # coarser working grid, the pair's outer centres lie beyond them and take
    # the nearest one.
    inner = slice(2, -2)
    np.testing.assert_allclose(
        resampled[:, inner, inner], np.indices((size, size))[:, inner, inner]
    )


@pytest.mark.parametrize("working", [560, 224])
@pytest.mark.parametrize(
    "transform",
    [
        Affine(matrix=((1.0, 0.0), (0.0, 1.0)), offset=(-0.4, 0.25)),
        Affine.about((127.5, 127.5), rotation_deg=1.0, scale=1.01, dx=1.3, dy=-0.7),
    ],
    ids=["shift", "affine"],
)
def test_a_known_warp_reads_as_its_displacement(working, transform):
    shape = (256, 256)
    warp = _warp_of(transform, working, shape)

    positions = to_pixels(to_pair_grid(warp, shape), shape)

    inner = (slice(None), slice(2, -2), slice(2, -2))
    field = positions - np.indices(shape)
    np.testing.assert_allclose(field[inner], transform.field(shape)[inner], atol=1e-9)


def test_leaving_out_the_half_pixel_would_shift_the_field():
    # romatch's to_pixel_coordinates puts pixel centres on half-integers: read
    # against integer indices, a zero shift would come out as half a pixel.
    shape = (64, 64)
    warp = _warp_of(Affine(((1.0, 0.0), (0.0, 1.0)), (0.0, 0.0)), 224, shape)
    x, y = to_pair_grid(warp, shape)

    naive = np.stack([(y + 1) * shape[0] / 2, (x + 1) * shape[1] / 2])

    np.testing.assert_allclose((naive - np.indices(shape))[:, 2:-2, 2:-2], 0.5)


@pytest.mark.parametrize(("shape", "most"), [((256, 256), 5000), ((130, 250), 900)])
def test_the_lattice_is_regular_centred_and_within_budget(shape, most):
    rows, cols = lattice(shape, most)

    assert rows.size <= most
    steps = np.unique(np.diff(rows[:, 0])), np.unique(np.diff(cols[0]))
    assert len(steps[0]) == 1 and steps[0] == steps[1]
    assert abs(rows.min() - (shape[0] - 1 - rows.max())) <= 1
    assert abs(cols.min() - (shape[1] - 1 - cols.max())) <= 1


@needs_torch
def test_working_input_is_resized_and_normalised_like_a_photograph():
    image = np.random.default_rng(0).integers(1000, 3000, (100, 130)).astype(float)

    channels = working_input(image, 224)

    assert channels.shape == (3, 224, 224)
    assert channels.dtype == np.float32


@needs_torch
def test_working_input_at_the_image_size_is_lightglues_input_normalised():
    # Resizing to the image's own size samples the source centres exactly, so
    # only ImageNet's normalisation is left.
    image = np.random.default_rng(0).integers(1000, 3000, (56, 56)).astype(float)

    channels = working_input(image, 56)

    unnormalised = channels * IMAGENET_STD[:, None, None] + IMAGENET_MEAN[:, None, None]
    np.testing.assert_allclose(unnormalised, network_input(image), atol=1e-6)


@needs_torch
def test_working_input_ignores_the_gain_and_offset_of_an_image():
    image = np.random.default_rng(0).integers(1000, 3000, (32, 32)).astype(float)

    np.testing.assert_allclose(
        working_input(3.0 * image + 500.0, 56), working_input(image, 56), atol=1e-5
    )


@pytest.mark.parametrize(
    ("parameters", "message"),
    [
        ({"output": "flow"}, "output must be one of dense, affine"),
        ({"resolution": 500}, "resolution must be a positive multiple of 14"),
        ({"upsample_resolution": 280}, "upsample_resolution must be 0 or above"),
        ({"certainty_threshold": 1.0}, "certainty_threshold must be in"),
        ({"min_certain_fraction": 1.5}, "min_certain_fraction must be in"),
        ({"max_matches": 5}, "max_matches must be at least min_inliers"),
        ({"ransac_threshold": 0.0}, "ransac_threshold must be positive"),
        ({"min_inliers": 2}, "min_inliers must be at least 3"),
        ({"device": "tpu"}, "device must be one of cpu, mps, cuda"),
    ],
)
def test_bad_parameters_are_rejected(parameters, message):
    with pytest.raises(ValueError, match=message):
        Roma(**parameters)


def test_roma_is_registered_with_its_dense_variant():
    methods = load_methods(REPO_CONFIG)

    assert METHODS["roma"] == Roma()
    assert methods["roma"] == Roma(
        output="affine",
        resolution=280,
        upsample_resolution=0,
        certainty_threshold=0.5,
        min_certain_fraction=0.005,
        max_matches=5000,
        ransac_threshold=1.0,
        min_inliers=10,
        device="cpu",
    )
    assert methods["roma_dense"] == Roma(output="dense")


def test_roma_needs_the_dl_extra_and_romatch(monkeypatch):
    monkeypatch.setattr(deep.importlib.util, "find_spec", lambda name: None)

    assert missing_dependencies(Roma()) == [
        "torch",
        "torchvision",
        "romatch",
        "einops",
        "loguru",
    ]


def test_roma_is_measured_on_its_device():
    assert cost_meter(Roma()).name == "torch-cpu"
    assert cost_meter(Roma(device="mps")).name == "none"


def _small(**parameters) -> Roma:
    return Roma(resolution=TEST_RESOLUTION, **parameters)


@needs_roma
@pytest.mark.parametrize("output", ["dense", "affine"])
def test_sign_convention_on_an_integer_shift(output):
    # Content moved 3 px right and 2 px up must read as dx=+3, dy=-2.
    pair = simulate_translation(fractal_texture(192, seed=0), dx=3, dy=-2)

    estimate = _small(output=output)(pair.reference, pair.moving)

    field = estimate.displacement.field(pair.reference.shape)
    np.testing.assert_allclose(np.median(field, axis=(1, 2)), [-2.0, 3.0], atol=0.1)


@needs_roma
@pytest.mark.parametrize("output", ["dense", "affine"])
def test_recovers_a_sub_pixel_translation(output):
    pair = simulate_translation(fractal_texture(192, seed=7), dx=0.25, dy=-0.4)

    estimate = _small(output=output)(pair.reference, pair.moving)

    assert isinstance(estimate.displacement, Dense if output == "dense" else Affine)
    pair_score = score(pair.truth, estimate.displacement, pair.reference.shape)
    # Measured 0.038 px (dense) and 0.032 px (affine) on a 160 px pair when this
    # test was written.
    assert pair_score.mean_epe < 0.08


@needs_roma
def test_the_affine_fit_recovers_a_known_affine():
    size, centre = 160, 79.5
    truth = Affine.about(
        (centre, centre), rotation_deg=1.5, scale=1.01, shear=0.005, dx=1.3, dy=-0.7
    )
    margin = margin_for(affine_reach(truth, (size, size)))
    pair = simulate_affine(fractal_texture(size + 2 * margin, seed=3), truth, margin)

    estimate = _small()(pair.reference, pair.moving)

    pair_score = score(truth, estimate.displacement, pair.reference.shape, pair.valid)
    assert pair_score.mean_epe < 0.1


@needs_roma
def test_reports_its_certainty_and_the_fit_its_counts():
    pair = simulate_translation(fractal_texture(160, seed=0), dx=0.5, dy=0.5)

    dense = _small(output="dense")(pair.reference, pair.moving)
    affine = _small()(pair.reference, pair.moving)

    assert isinstance(dense, Estimate)
    assert set(dense.diagnostics) == {"mean_certainty", "certain_fraction"}
    assert 0.5 < dense.diagnostics["mean_certainty"] <= 1
    assert dense.diagnostics["certain_fraction"] > 0.9
    assert 10 <= affine.diagnostics["inliers"] <= affine.diagnostics["matches"]


@needs_roma
def test_the_field_is_on_the_grid_of_a_pair_that_is_not_square():
    pair = simulate_translation(fractal_texture(220, seed=4), dx=0.3, dy=0.6)
    reference, moving = pair.reference[:130, :180], pair.moving[:130, :180]

    estimate = _small(output="dense")(reference, moving)

    assert estimate.displacement.shape == (130, 180)
    shift = np.median(estimate.displacement.field((130, 180)), axis=(1, 2))
    np.testing.assert_allclose(shift, [0.6, 0.3], atol=0.1)


@needs_roma
@pytest.mark.parametrize(
    ("reference", "moving"),
    [
        (np.full((128, 128), 1200.0), np.full((128, 128), 1200.0)),
        (np.add.outer(np.arange(128.0), np.arange(128.0)),) * 2,
        (fractal_texture(128, seed=1), fractal_texture(128, seed=2)),
    ],
    ids=["flat", "ramp", "unrelated"],
)
def test_too_little_certain_area_is_a_failure_not_a_guess(reference, moving):
    with pytest.raises(
        RegistrationFailure, match="of the pixels are certain"
    ) as failure:
        _small()(reference, moving)

    assert failure.value.diagnostics["certain_fraction"] < 0.005

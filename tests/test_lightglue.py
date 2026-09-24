from pathlib import Path

import numpy as np
import pytest

from satreg.displacement import Affine
from satreg.methods import (
    METHODS,
    Estimate,
    RegistrationFailure,
    cost_meter,
    deep,
    load_methods,
    missing_dependencies,
)
from satreg.methods.lightglue import FEATURES, LightGlue, network_input
from satreg.metrics import score
from satreg.simulate import (
    affine_reach,
    margin_for,
    simulate_affine,
    simulate_translation,
)
from satreg.texture import fractal_texture

REPO_CONFIG = Path(__file__).parents[1] / "configs" / "methods.toml"

# Mean EPE bounds on clean synthetic pairs, per extractor. ALIKED refines its
# keypoints below the pixel: measured 0.015 to 0.023 px on translations and
# 0.041 px on the affine pair. DISK keeps them on whole pixels, and only the
# averaging over many inliers brings it under a pixel: 0.11 to 0.14 px, and
# 0.078 px on the affine pair.
TRANSLATION_TOLERANCE_PX = {"aliked": 0.04, "disk": 0.2}
AFFINE_TOLERANCE_PX = {"aliked": 0.06, "disk": 0.15}


def _skip_reason() -> str | None:
    if missing := missing_dependencies(METHODS["lightglue"]):
        return f"needs the dl extra ({', '.join(missing)} missing): make install-dl"
    for features in FEATURES:
        for weights in LightGlue(features=features).weights_files():
            if not Path(weights).exists():
                return f"needs the {features} weights at {weights}: make install-dl"
    return None


# The tests that run the networks. The conftest refuses network access, so the
# weights must already be in PyTorch's cache.
needs_lightglue = pytest.mark.skipif(
    _skip_reason() is not None, reason=_skip_reason() or ""
)


def test_network_input_is_three_equal_channels_in_the_unit_range():
    image = np.arange(10_000, dtype=np.uint16).reshape(100, 100)

    channels = network_input(image)

    assert channels.shape == (3, 100, 100)
    assert channels.dtype == np.float32
    assert channels.min() == 0.0 and channels.max() == 1.0
    np.testing.assert_array_equal(channels[0], channels[2])


def test_network_input_ignores_the_gain_and_offset_of_an_image():
    image = np.random.default_rng(0).integers(1000, 3000, (32, 32)).astype(float)

    np.testing.assert_allclose(
        network_input(3.0 * image + 500.0), network_input(image), atol=1e-6
    )


@pytest.mark.parametrize(
    ("parameters", "message"),
    [
        ({"features": "superpoint"}, "features must be one of aliked, disk"),
        ({"max_keypoints": 0}, "max_keypoints must be positive"),
        ({"match_threshold": 1.0}, "match_threshold must be in"),
        ({"ransac_threshold": 0.0}, "ransac_threshold must be positive"),
        ({"min_inliers": 2}, "min_inliers must be at least 3"),
        ({"device": "tpu"}, "device must be one of cpu, mps, cuda"),
    ],
)
def test_bad_parameters_are_rejected(parameters, message):
    with pytest.raises(ValueError, match=message):
        LightGlue(**parameters)


def test_lightglue_is_registered_with_its_disk_variant():
    methods = load_methods(REPO_CONFIG)

    assert METHODS["lightglue"] == LightGlue()
    assert methods["lightglue"] == LightGlue(
        features="aliked",
        max_keypoints=2048,
        match_threshold=0.1,
        ransac_threshold=1.0,
        min_inliers=10,
        device="cpu",
    )
    assert methods["lightglue_disk"] == LightGlue(features="disk")


def test_lightglue_needs_the_dl_extra_and_kornia(monkeypatch):
    monkeypatch.setattr(deep.importlib.util, "find_spec", lambda name: None)

    assert missing_dependencies(LightGlue(features="disk")) == [
        "torch",
        "torchvision",
        "kornia",
    ]


def test_lightglue_is_measured_on_its_device():
    assert cost_meter(LightGlue()).name == "torch-cpu"
    assert cost_meter(LightGlue(device="mps")).name == "none"


@needs_lightglue
@pytest.mark.parametrize("features", FEATURES)
def test_sign_convention_on_an_integer_shift(features):
    # Content moved 3 px right and 2 px up must read as dx=+3, dy=-2.
    pair = simulate_translation(fractal_texture(256, seed=0), dx=3, dy=-2)

    estimate = LightGlue(features=features)(pair.reference, pair.moving)

    field = estimate.displacement.field(pair.reference.shape)
    np.testing.assert_allclose(np.mean(field, axis=(1, 2)), [-2.0, 3.0], atol=0.05)


@needs_lightglue
@pytest.mark.parametrize("features", FEATURES)
@pytest.mark.parametrize(("dx", "dy"), [(0.0, 0.0), (0.25, -0.4), (-1.37, 2.81)])
def test_recovers_a_known_translation(features, dx, dy):
    pair = simulate_translation(fractal_texture(300, seed=7), dx=dx, dy=dy)

    estimate = LightGlue(features=features)(pair.reference, pair.moving)

    assert isinstance(estimate.displacement, Affine)
    pair_score = score(pair.truth, estimate.displacement, pair.reference.shape)
    assert pair_score.mean_epe < TRANSLATION_TOLERANCE_PX[features]


@needs_lightglue
@pytest.mark.parametrize("features", FEATURES)
def test_recovers_a_known_affine(features):
    size, centre = 256, 127.5
    truth = Affine.about(
        (centre, centre), rotation_deg=1.5, scale=1.01, shear=0.005, dx=1.3, dy=-0.7
    )
    margin = margin_for(affine_reach(truth, (size, size)))
    source = fractal_texture(size + 2 * margin, seed=3)
    pair = simulate_affine(source, truth, margin)

    estimate = LightGlue(features=features)(pair.reference, pair.moving)

    pair_score = score(truth, estimate.displacement, pair.reference.shape, pair.valid)
    assert pair_score.mean_epe < AFFINE_TOLERANCE_PX[features]


@needs_lightglue
def test_reports_keypoints_matches_and_inliers():
    pair = simulate_translation(fractal_texture(256, seed=0), dx=0.5, dy=0.5)

    estimate = LightGlue()(pair.reference, pair.moving)

    assert isinstance(estimate, Estimate)
    diagnostics = estimate.diagnostics
    assert 10 <= diagnostics["inliers"] <= diagnostics["matches"]
    assert diagnostics["matches"] <= diagnostics["keypoints"]


@needs_lightglue
@pytest.mark.parametrize("features", FEATURES)
@pytest.mark.parametrize(
    "image",
    [np.full((128, 128), 1200.0), np.add.outer(np.arange(128.0), np.arange(128.0))],
    ids=["flat", "ramp"],
)
def test_textureless_image_fails_cleanly(features, image):
    with pytest.raises(RegistrationFailure, match="matches, need 10") as failure:
        LightGlue(features=features)(image, image)

    assert failure.value.diagnostics["matches"] < 10


@needs_lightglue
@pytest.mark.parametrize("features", FEATURES)
def test_unrelated_images_are_a_failure_not_a_guess(features):
    reference = fractal_texture(128, seed=1)
    unrelated = fractal_texture(128, seed=2)

    with pytest.raises(RegistrationFailure, match="need 10"):
        LightGlue(features=features)(reference, unrelated)


@needs_lightglue
def test_disk_keypoints_stay_on_an_image_it_must_pad():
    # 130 x 150 px, which DISK's U-Net only takes padded to 144 x 160.
    pair = simulate_translation(fractal_texture(200, seed=4), dx=0.3, dy=0.6)
    reference, moving = pair.reference[:130, :150], pair.moving[:130, :150]
    method = LightGlue(features="disk")

    keypoints, _ = method.keypoints(reference)
    estimate = method(reference, moving)

    assert keypoints[:, 0].max() < 150 and keypoints[:, 1].max() < 130
    shift = estimate.displacement.field(reference.shape)[:, 65, 75]
    np.testing.assert_allclose(shift, [0.6, 0.3], atol=0.2)

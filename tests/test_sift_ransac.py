import json
from pathlib import Path

import numpy as np
import pytest

from satreg.benchmark import BenchmarkConfig, run_benchmark
from satreg.displacement import Affine
from satreg.methods import METHODS, Estimate, RegistrationFailure, load_methods
from satreg.methods.sift_ransac import SiftRansac, to_uint8
from satreg.metrics import score
from satreg.simulate import (
    affine_reach,
    margin_for,
    simulate_affine,
    simulate_translation,
)
from satreg.texture import fractal_texture

REPO_CONFIG = Path(__file__).parents[1] / "configs" / "methods.toml"

# Clean pairs of 256 px on the synthetic texture. SIFT keypoints land to a few
# thousandths of a pixel there, and a thousand inliers average them further.
TOLERANCE_PX = 0.02


def test_sign_convention_on_an_integer_shift():
    # Content moved 3 px right and 2 px up must read as dx=+3, dy=-2.
    pair = simulate_translation(fractal_texture(256, seed=0), dx=3, dy=-2)

    estimate = SiftRansac()(pair.reference, pair.moving)

    field = estimate.displacement.field(pair.reference.shape)
    assert np.allclose(field[0], -2, atol=TOLERANCE_PX)
    assert np.allclose(field[1], 3, atol=TOLERANCE_PX)


@pytest.mark.parametrize(("dx", "dy"), [(0.0, 0.0), (0.25, -0.4), (-1.37, 2.81)])
def test_recovers_a_known_translation(dx, dy):
    pair = simulate_translation(fractal_texture(300, seed=7), dx=dx, dy=dy)

    estimate = SiftRansac()(pair.reference, pair.moving)

    assert isinstance(estimate.displacement, Affine)
    pair_score = score(pair.truth, estimate.displacement, pair.reference.shape)
    assert pair_score.mean_epe < TOLERANCE_PX


def test_recovers_a_known_affine():
    size, centre = 256, 127.5
    truth = Affine.about(
        (centre, centre), rotation_deg=1.5, scale=1.01, shear=0.005, dx=1.3, dy=-0.7
    )
    margin = margin_for(affine_reach(truth, (size, size)))
    source = fractal_texture(size + 2 * margin, seed=3)
    pair = simulate_affine(source, truth, margin)

    estimate = SiftRansac()(pair.reference, pair.moving)

    found = estimate.displacement
    assert np.allclose(found.matrix, truth.matrix, atol=1e-4)
    pair_score = score(truth, found, pair.reference.shape, pair.valid)
    assert pair_score.mean_epe < TOLERANCE_PX


def test_reports_inliers_as_a_diagnostic():
    pair = simulate_translation(fractal_texture(256, seed=0), dx=0.5, dy=0.5)

    estimate = SiftRansac(min_inliers=10)(pair.reference, pair.moving)

    assert isinstance(estimate, Estimate)
    diagnostics = estimate.diagnostics
    assert 10 <= diagnostics["inliers"] <= diagnostics["matches"]
    assert diagnostics["matches"] <= diagnostics["keypoints"]


@pytest.mark.parametrize(
    "image",
    [np.full((128, 128), 1200.0), np.add.outer(np.arange(128.0), np.arange(128.0))],
    ids=["flat", "ramp"],
)
def test_textureless_image_fails_cleanly(image):
    with pytest.raises(RegistrationFailure, match="0 matches, need 10") as failure:
        SiftRansac()(image, image)

    assert failure.value.diagnostics == {"keypoints": 0, "matches": 0}


def test_too_few_inliers_is_a_failure_not_a_guess():
    pair = simulate_translation(fractal_texture(128, seed=1), dx=1.0, dy=0.0)
    unrelated = fractal_texture(128, seed=2)

    with pytest.raises(RegistrationFailure, match="need 10"):
        SiftRansac()(pair.reference, unrelated)


def test_benchmark_counts_the_failure_and_keeps_running():
    sites = {"flat": np.full((256, 256), 1200.0), "textured": fractal_texture(256, 0)}
    config = BenchmarkConfig(n_pairs=2, size=64, max_shift=2.0)

    results = run_benchmark(sites, {"sift_ransac": SiftRansac(min_inliers=5)}, config)

    flat = [r for r in results if r.site == "flat"]
    textured = [r for r in results if r.site == "textured"]
    assert all(r.failed for r in flat)
    assert all(r.error.startswith("RegistrationFailure: 0 matches") for r in flat)
    assert all(json.loads(r.diagnostics)["matches"] == 0 for r in flat)
    assert not any(r.failed for r in textured)
    assert all(json.loads(r.diagnostics)["inliers"] >= 5 for r in textured)


def test_conversion_to_8_bits_ignores_gain_and_offset():
    image = fractal_texture(128, seed=0) * 680 + 2300

    converted = to_uint8(image)

    assert converted.dtype == np.uint8
    assert converted.min() == 0 and converted.max() == 255
    assert np.array_equal(to_uint8(0.7 * image - 500), converted)


def test_parameters_come_from_the_configuration(tmp_path):
    config = tmp_path / "methods.toml"
    config.write_text(
        "[methods.sift_ransac]\nratio = 0.6\nransac_threshold = 2.0\nmin_inliers = 20\n"
    )

    methods = load_methods(config)

    assert methods["sift_ransac"] == SiftRansac(
        ratio=0.6, ransac_threshold=2.0, min_inliers=20
    )
    assert methods["phase_correlation"] is METHODS["phase_correlation"]


def test_repository_configuration_loads():
    assert isinstance(load_methods(REPO_CONFIG)["sift_ransac"], SiftRansac)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("[methods.orb]\n", "no configurable method orb"),
        ("[methods.sift_ransac]\nratio = 1.5\n", "ratio must be in"),
        ("[methods.sift_ransac]\nmin_inliers = 2\n", "min_inliers must be at least"),
        ("[methods.sift_ransac]\nsigma = 1.6\n", "unexpected keyword"),
    ],
)
def test_bad_configuration_is_rejected(tmp_path, text, message):
    config = tmp_path / "methods.toml"
    config.write_text(text)

    with pytest.raises(ValueError, match=message):
        load_methods(config)


def test_is_registered_under_a_stable_name():
    assert isinstance(METHODS["sift_ransac"], SiftRansac)

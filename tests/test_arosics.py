import json
from pathlib import Path

import numpy as np
import pytest
from rasterio import Affine
from rasterio.crs import CRS

from satreg.benchmark import BenchmarkConfig, run_benchmark
from satreg.displacement import Translation
from satreg.georef import NOMINAL, Georef
from satreg.ingest import read_chip, read_georef
from satreg.methods import METHODS, RegistrationFailure, load_methods
from satreg.methods.arosics import Arosics, missing_modules, to_displacement
from satreg.metrics import score
from satreg.simulate import simulate_translation
from satreg.texture import fractal_texture

# 320 px of the Beauce chip (Sentinel-2 L2A B04, 2025-07-01), on its own UTM grid.
# Contains modified Copernicus Sentinel data 2025.
CHIP = Path(__file__).parent / "data" / "beauce_b04_320.tif"
MARGIN = 32

# The project's target. AROSICS' sub-pixel step, a ratio of the correlation peak
# to its larger neighbour, lands within 0.03 to 0.1 px of fractional shifts on
# this chip, and exactly on whole ones.
TOLERANCE_PX = 0.1

needs_arosics = pytest.mark.skipif(
    bool(missing_modules()),
    reason=f"AROSICS is an optional extra, not installed: missing "
    f"{', '.join(missing_modules())} (see docs/running.md)",
)


def chip_pair(dx, dy):
    """A pair cut from the real-chip fixture, and the grid of its reference."""
    image, georef = read_chip(CHIP), read_georef(CHIP)
    pair = simulate_translation(image, dx=dx, dy=dy, margin=MARGIN)
    return pair, georef.window(MARGIN, MARGIN)


def test_map_shift_converts_on_a_north_up_grid():
    # Content 1.2 px right and 0.7 px up: AROSICS moves the moving grid's origin
    # 12 m west and 7 m south to correct it.
    found = to_displacement(-12.0, -7.0, NOMINAL)

    assert (found.dx, found.dy) == pytest.approx((1.2, -0.7))


def test_map_shift_converts_on_any_grid():
    # South-up, 20 m by 5 m pixels, slightly rotated.
    grid = Georef(CRS.from_epsg(32631), Affine(20.0, 1.0, 0.0, -0.5, 5.0, 0.0))
    d = np.array([0.3, -2.4])  # (dx, dy)
    t = grid.transform
    correction = np.array([[t.a, t.b], [t.d, t.e]]) @ -d

    found = to_displacement(*correction, grid)

    assert isinstance(found, Translation)
    assert (found.dx, found.dy) == pytest.approx((0.3, -2.4))


def test_needs_a_georeferenced_pair():
    image = fractal_texture(64, seed=0)

    with pytest.raises(ValueError, match="georeferenced"):
        Arosics()(image, image, None)


@needs_arosics
def test_sign_convention_on_an_integer_shift():
    # Content moved 3 px right and 2 px up must read as dx=+3, dy=-2.
    pair, georef = chip_pair(dx=3, dy=-2)

    found = Arosics()(pair.reference, pair.moving, georef).displacement

    assert (found.dx, found.dy) == pytest.approx((3, -2), abs=1e-6)


@needs_arosics
@pytest.mark.parametrize(("dx", "dy"), [(0.25, -0.4), (-1.37, 2.81), (0.5, 0.5)])
def test_recovers_a_known_sub_pixel_shift_on_a_real_chip(dx, dy):
    pair, georef = chip_pair(dx, dy)

    estimate = Arosics()(pair.reference, pair.moving, georef)

    pair_score = score(pair.truth, estimate.displacement, pair.reference.shape)
    assert pair_score.mean_epe < TOLERANCE_PX
    assert estimate.diagnostics["window"] == 256
    assert estimate.diagnostics["reliability"] > 90


@needs_arosics
def test_textureless_image_fails_cleanly():
    flat = np.full((256, 256), 1200.0)

    with pytest.raises(RegistrationFailure, match="window became too small"):
        Arosics()(flat, flat, NOMINAL)


@needs_arosics
def test_shift_beyond_max_shift_fails_cleanly():
    pair, georef = chip_pair(dx=4, dy=-4)

    with pytest.raises(RegistrationFailure, match="too large to be valid"):
        Arosics(max_shift=3)(pair.reference, pair.moving, georef)


@needs_arosics
def test_low_reliability_is_a_failure_not_a_guess():
    pair, georef = chip_pair(dx=0.25, dy=-0.4)

    with pytest.raises(RegistrationFailure, match="need 99.9 %") as failure:
        Arosics(min_reliability=99.9)(pair.reference, pair.moving, georef)

    assert failure.value.diagnostics["reliability"] < 99.9


@needs_arosics
def test_benchmark_runs_it_on_the_grid_of_each_pair():
    sites = {"beauce": read_chip(CHIP), "flat": np.full((320, 320), 1200.0)}
    georefs = {"beauce": read_georef(CHIP), "flat": NOMINAL}
    config = BenchmarkConfig(n_pairs=2, size=256, scenarios=("translation",))

    results = run_benchmark(sites, {"arosics": Arosics()}, config, georefs=georefs)

    beauce = [r for r in results if r.site == "beauce"]
    flat = [r for r in results if r.site == "flat"]
    assert not any(r.failed for r in beauce)
    assert all(json.loads(r.diagnostics)["window"] == 256 for r in beauce)
    assert all(r.failed and r.error.startswith("RegistrationFailure") for r in flat)


def test_parameters_come_from_the_configuration(tmp_path):
    config = tmp_path / "methods.toml"
    config.write_text(
        "[methods.arosics]\n"
        "window = 128\nmax_shift = 8.0\nmax_iter = 3\nmin_reliability = 40.0\n"
    )

    methods = load_methods(config)

    assert methods["arosics"] == Arosics(
        window=128, max_shift=8.0, max_iter=3, min_reliability=40.0
    )


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("[methods.arosics]\nwindow = 0\n", "window must be positive"),
        ("[methods.arosics]\nmin_reliability = 120\n", "min_reliability must be"),
        ("[methods.arosics]\nbinary_ws = false\n", "unexpected keyword"),
    ],
)
def test_bad_configuration_is_rejected(tmp_path, text, message):
    config = tmp_path / "methods.toml"
    config.write_text(text)

    with pytest.raises(ValueError, match=message):
        load_methods(config)


def test_is_registered_under_a_stable_name():
    assert isinstance(METHODS["arosics"], Arosics)

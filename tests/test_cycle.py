import dataclasses
import datetime as dt
import math

import numpy as np
import pytest

from satreg.benchmark import BenchmarkConfig
from satreg.cycle import (
    LEGS,
    REAL,
    Leg,
    closure_error,
    displacement_summary,
    draw_triplet,
    motion_markdown,
    motion_summary,
    run_real,
    run_simulated,
    summarize,
    to_markdown,
    triplet_row,
)
from satreg.degrade import Clouds, Preset
from satreg.displacement import Affine, Translation, compose
from satreg.georef import NOMINAL
from satreg.methods import RegistrationFailure, phase_correlation
from satreg.presetcheck import WINDOW_PX, role_order
from satreg.real import Acquisition
from satreg.simulate import fourier_shift
from satreg.texture import fractal_texture

SHAPE = (32, 32)
EVERYWHERE = np.ones(SHAPE, bool)
NOWHERE = np.zeros(SHAPE, bool)
LABELS = {
    "site": "synthetic",
    "scenario": REAL,
    "triplet": "anchor-days-season",
    "window": 0,
    "method": "fake",
    "device": "cpu",
}
CONFIG = BenchmarkConfig(
    n_pairs=2, size=64, max_shift=2.0, seed=0, scenarios=("translation",), repeats=1
)
IMAGE = fractal_texture(256, seed=0)


def far_off(reference, moving):
    return Translation(dx=50.0, dy=0.0)


def declines(reference, moving):
    raise RegistrationFailure("too few inliers")


def leg(displacement, error=""):
    return Leg(displacement, error, "", time_ms=1.0, peak_mib=2.0)


def test_exact_legs_close_to_zero():
    ab = Affine.about((15.5, 15.5), rotation_deg=0.3, dx=1.2)
    bc = Translation(dx=-0.4, dy=0.9)

    residual = closure_error(ab, bc, compose(ab, bc), SHAPE, EVERYWHERE)

    np.testing.assert_allclose(residual, 0.0, atol=1e-12)


def test_errors_that_belong_to_one_date_cancel_out_of_the_closure():
    # Each date seen offset by its own error: each leg is wrong by the difference.
    truth = {"A": np.array([0.0, 0.0]), "B": np.array([1.0, 2.0]), "C": [3.0, -1.0]}
    bias = {"A": np.array([0.3, -0.2]), "B": np.array([-0.1, 0.4]), "C": [0.2, 0.2]}

    def estimate(x, y):
        d = np.add(truth[y], bias[y]) - np.add(truth[x], bias[x])
        return Translation(dx=d[1], dy=d[0])

    residual = closure_error(
        estimate("A", "B"), estimate("B", "C"), estimate("A", "C"), SHAPE, EVERYWHERE
    )

    np.testing.assert_allclose(residual, 0.0, atol=1e-12)


def test_an_error_every_call_makes_shows_once_in_the_closure():
    bias = Translation(dx=0.3, dy=-0.4)

    residual = closure_error(bias, bias, bias, SHAPE, EVERYWHERE)

    np.testing.assert_allclose(residual, 0.5)


def test_pixels_displaced_off_the_grid_are_not_a_closure():
    ab = Translation(dx=10.0, dy=0.0)
    zero = Translation(dx=0.0, dy=0.0)

    residual = closure_error(ab, zero, ab, SHAPE, EVERYWHERE)

    assert residual.size == SHAPE[0] * (SHAPE[1] - 10)


def test_a_failed_leg_fails_the_triplet_and_says_which():
    good = leg(Translation(dx=0.0, dy=0.0))

    row = triplet_row(
        LABELS,
        [good, leg(None, "RegistrationFailure: too few"), good],
        LEGS,
        SHAPE,
        NOWHERE,
        threshold=1.0,
    )

    assert row.failed
    assert row.error == "B-C: RegistrationFailure: too few"
    assert math.isnan(row.mean_closure)
    assert (row.time_ms, row.peak_mib) == (1.0, 2.0)


def test_a_triplet_that_does_not_close_within_the_threshold_fails():
    off = leg(Translation(dx=1.5, dy=0.0))

    row = triplet_row(LABELS, [off, off, off], LEGS, SHAPE, NOWHERE, threshold=1.0)

    assert row.failed
    assert row.error == ""
    assert row.mean_closure == pytest.approx(1.5)
    assert (row.share_below_0_1, row.share_below_0_5) == (0.0, 0.0)


def test_a_triplet_with_every_pixel_hidden_fails():
    zero = leg(Translation(dx=0.0, dy=0.0))

    row = triplet_row(LABELS, [zero] * 3, LEGS, SHAPE, EVERYWHERE, threshold=1.0)

    assert row.failed
    assert row.cloud_fraction == 1.0
    assert "keeps no pixel" in row.error


def test_simulated_triplet_rows_carry_the_true_error_next_to_the_closure():
    truths = (Translation(1.0, 0.0), Translation(2.0, 0.0), Translation(3.0, 0.0))
    # Every leg 0.2 px off along rows: the closure sees it once, the EPE thrice.
    legs = [leg(Translation(dx=t.dx, dy=0.2)) for t in truths]

    row = triplet_row(LABELS, legs, LEGS, SHAPE, NOWHERE, 1.0, truths)

    assert row.mean_closure == pytest.approx(0.2)
    assert row.true_epe == pytest.approx(0.2)
    assert row.truth_closure == pytest.approx(0.0, abs=1e-12)


def test_a_translation_is_all_translation():
    assert displacement_summary(Translation(dx=3.0, dy=4.0), SHAPE) == (5.0, 0.0)


def test_an_affine_translates_by_its_centre_and_the_rest_grows_outwards():
    affine = Affine.about((15.5, 15.5), rotation_deg=1.0, dx=3.0, dy=4.0)
    grid = np.indices(SHAPE, dtype=float) - 15.5
    rest = np.hypot(*grid) * 2 * np.sin(np.radians(0.5))

    translation, non_translation = displacement_summary(affine, SHAPE)

    assert translation == pytest.approx(5.0)
    assert non_translation == pytest.approx(np.percentile(rest, 95))


@pytest.mark.parametrize("scenario", ["translation", "affine", "dense"])
def test_a_simulated_triplet_closes_on_its_truths(scenario):
    triplet = draw_triplet(IMAGE, CONFIG, np.random.default_rng(1), scenario)
    ab, bc, ac = triplet.truths
    shape = (CONFIG.size, CONFIG.size)

    residual = closure_error(ab, bc, ac, shape, np.ones(shape, bool))

    # Composing a dense field reads it between pixels, at a small cost.
    assert residual.max() < (1e-3 if scenario == "dense" else 1e-10)
    assert residual.mean() < (1e-4 if scenario == "dense" else 1e-10)


def test_every_scenario_draws_the_same_window_and_centre_shifts():
    def centre_shifts(scenario):
        triplet = draw_triplet(IMAGE, CONFIG, np.random.default_rng(2), scenario)
        c = (CONFIG.size - 1) // 2
        return triplet.images[0], [t.field((64, 64))[:, c, c] for t in triplet.truths]

    reference, translation = centre_shifts("translation")
    same_reference, affine = centre_shifts("affine")

    np.testing.assert_array_equal(reference, same_reference)
    # The centre is half a pixel from the pixel read, so rotation shows a little.
    np.testing.assert_allclose(translation, affine, atol=0.05)


def test_phase_correlation_closes_clean_translation_triplets_like_its_truth():
    legs, rows = run_simulated(
        "synthetic",
        IMAGE,
        {"phase_correlation": phase_correlation},
        CONFIG,
        {"clean": Preset()},
    )

    assert len(legs) == 3 * CONFIG.n_pairs
    assert [r.pair for r in legs[:3]] == list(LEGS)
    assert len(rows) == CONFIG.n_pairs
    for row in rows:
        assert not row.failed
        # Three legs' errors add up in the closure, and cancel in part.
        assert row.true_epe < 0.1
        assert row.mean_closure < 3 * row.true_epe
        assert row.truth_closure == pytest.approx(0.0, abs=1e-10)


def test_a_method_far_off_or_declining_fails_every_simulated_triplet():
    _, rows = run_simulated(
        "synthetic",
        IMAGE,
        {"far_off": far_off, "declines": declines},
        CONFIG,
        {"clean": Preset()},
    )

    assert all(r.failed for r in rows)
    summary = summarize(rows)
    assert [s.failure_rate for s in summary] == [1.0, 1.0]
    assert all(math.isnan(s.mean_closure) for s in summary)


def test_each_image_of_a_degraded_triplet_is_the_same_in_every_leg():
    seen = []

    def records(reference, moving):
        seen.append((reference, moving))
        return Translation(dx=0.0, dy=0.0)

    # One timed call per leg, then one for its memory.
    run_simulated(
        "synthetic",
        IMAGE,
        {"records": records},
        dataclasses.replace(CONFIG, warmup=0),
        {"cloudy": Preset(clouds=Clouds(cover=0.3))},
    )

    (a1, b1), (b2, c1), (a2, c2) = seen[:6:2]
    np.testing.assert_array_equal(a1, a2)
    np.testing.assert_array_equal(b1, b2)
    np.testing.assert_array_equal(c1, c2)


# Each date is the chip shifted by its own amount, so every pair of dates is a
# known translation, and every triplet closes exactly.
SHIFTS = {
    "anchor": (0.0, 0.0),
    "days": (0.4, -0.3),
    "season": (1.1, 0.6),
    "year": (-0.7, 1.3),
}


def series(cloudy_role=None):
    chip = 1000 + 300 * fractal_texture(2 * WINDOW_PX, seed=5)
    dates = []
    for day, (role, (dy, dx)) in enumerate(SHIFTS.items(), start=1):
        scl = np.full(chip.shape, 4, np.uint8)
        if role == cloudy_role:
            scl[:WINDOW_PX, :WINDOW_PX] = 9  # the first window
        dates.append(
            Acquisition(
                role=role,
                image=fourier_shift(chip, dy, dx),
                scl=scl,
                georef=NOMINAL,
                item_id=f"item-{day}",
                datetime=dt.datetime(2025, day, 1, 10, 56, tzinfo=dt.UTC),
                platform="sentinel-2a",
            )
        )
    return dates


def test_real_triplets_register_each_pair_once_and_close():
    legs, rows = run_real("synthetic", series(), {"pc": phase_correlation}, CONFIG)

    # Four windows, six pairs: every pair once, although triplets share them.
    assert len(legs) == len({(r.pair, r.window) for r in legs}) == 4 * 6
    assert len(rows) == 4 * 4
    assert {r.triplet for r in rows} == {
        "anchor-days-season",
        "anchor-days-year",
        "anchor-season-year",
        "days-season-year",
    }
    assert all(not r.failed and r.mean_closure < 0.1 for r in rows)
    days_season = next(r for r in legs if r.pair == "days-season")
    assert days_season.gap_days == 28
    assert days_season.translation_px == pytest.approx(math.hypot(0.7, 0.9), abs=0.05)
    assert days_season.non_translation_px == 0.0


def test_a_window_hidden_on_one_date_is_left_out_of_its_triplets():
    _, rows = run_real("synthetic", series("days"), {"pc": phase_correlation}, CONFIG)

    # "days" is in three of the four triplets; they lose one window each.
    assert len(rows) == 4 * 4 - 3
    assert {r.window for r in rows if r.triplet == "anchor-season-year"} == {0, 1, 2, 3}


def test_the_tables_show_real_and_simulated_triplets_apart():
    real_legs, real_rows = run_real(
        "synthetic", series(), {"pc": phase_correlation}, CONFIG
    )
    sim_legs, sim_rows = run_simulated(
        "synthetic", IMAGE, {"pc": phase_correlation}, CONFIG, {"clean": Preset()}
    )

    table = to_markdown(summarize(real_rows + sim_rows))
    motion = motion_markdown(
        motion_summary(real_legs + sim_legs, role_order(["days", "season", "year"]))
    )

    real, simulated = table.split("\n\n")
    assert "| synthetic | anchor-days-season | pc | cpu | 4 |" in real
    assert (
        "true EPE" in simulated
        and "| synthetic | translation | clean | pc |" in simulated
    )
    lines = motion.splitlines()
    assert lines[2].startswith("| simulated translation | truth | 4 |")
    assert lines[3].startswith("| anchor-days | pc | 4 |")
    assert lines[3].endswith("| translation only |")

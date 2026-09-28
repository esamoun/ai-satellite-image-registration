import dataclasses
import datetime as dt

import numpy as np
import pytest

from satreg.benchmark import BenchmarkConfig
from satreg.degrade import Clouds, Preset
from satreg.displacement import Affine, Dense, Translation
from satreg.falsechange import (
    NONE,
    Resampler,
    changed,
    correct,
    curve_summary,
    false_change_rate,
    match_level,
    on_curve,
    plot,
    real_summary,
    run_real,
    run_simulated,
    shifted,
    simulated_summary,
    threshold,
)
from satreg.georef import NOMINAL
from satreg.methods import phase_correlation
from satreg.presetcheck import WINDOW_PX
from satreg.real import Acquisition
from satreg.simulate import fourier_shift, oversampled_sample, simulate_translation
from satreg.texture import fractal_texture

CONFIG = BenchmarkConfig(
    n_pairs=2, size=64, max_shift=2.0, seed=0, scenarios=("translation",), repeats=1
)
IMAGE = fractal_texture(256, seed=0)


def step_edge(rows=32, cols=64, at=32):
    image = np.zeros((rows, cols))
    image[:, at:] = 1.0
    return image


def test_the_resampler_reads_as_the_simulator_does():
    image = fractal_texture(48, seed=1)
    positions = (
        np.indices(image.shape, dtype=float) + np.array([0.3, -1.7])[:, None, None]
    )

    ours = Resampler(image, reach=2.0)(positions)

    np.testing.assert_allclose(ours, oversampled_sample(image, positions), atol=1e-9)


def test_correcting_with_no_displacement_returns_the_image():
    image = fractal_texture(48, seed=2)

    np.testing.assert_allclose(correct(image, Translation(0.0, 0.0)), image, atol=1e-9)


def test_a_one_pixel_shift_flags_one_column_of_a_step_edge_and_none_once_corrected():
    reference = step_edge()
    # moving(p + d) = reference(p): the edge sits one column to the right.
    moving = step_edge(at=33)
    everywhere = np.ones(reference.shape, bool)

    uncorrected = changed(reference, correct(moving, Translation(0.0, 0.0)), 0.5)
    corrected = changed(reference, correct(moving, Translation(dx=1.0, dy=0.0)), 0.5)

    assert uncorrected.sum() == reference.shape[0]
    assert uncorrected[:, 32].all()
    assert corrected.sum() == 0
    assert false_change_rate(reference, moving, everywhere, 0.5) == pytest.approx(
        1 / 64
    )


def test_a_two_pixel_shift_flags_two_columns_of_a_step_edge():
    reference = step_edge()
    moving = step_edge(at=34)

    flagged = changed(reference, correct(moving, Translation(0.0, 0.0)), 0.5)

    assert flagged.sum() == 2 * reference.shape[0]


def test_zero_residual_on_a_noise_free_pair_leaves_no_false_change():
    source = fractal_texture(96, seed=3)
    pair = simulate_translation(source, dx=0.4, dy=-0.7)
    limit = threshold(pair.reference, pair.moving)

    corrected = correct(pair.moving, pair.truth)
    uncorrected = correct(pair.moving, Translation(0.0, 0.0))

    assert false_change_rate(pair.reference, corrected, pair.valid, limit) == 0.0
    assert false_change_rate(pair.reference, uncorrected, pair.valid, limit) > 0.0


def test_the_level_match_undoes_a_gain_and_an_offset():
    reference = fractal_texture(48, seed=4)
    everywhere = np.ones(reference.shape, bool)

    gain, offset = match_level(reference, (reference - 5) / 2, everywhere, everywhere)

    assert gain == pytest.approx(2.0)
    assert offset == pytest.approx(5.0)


def test_the_threshold_grows_with_the_noise():
    rng = np.random.default_rng(0)
    flat = np.zeros((128, 128))
    noisy = [flat + rng.normal(0, sigma, flat.shape) for sigma in (1.0, 1.0)]

    assert threshold(*noisy) == pytest.approx(3 * np.sqrt(2), rel=0.1)


@pytest.mark.parametrize(
    "displacement",
    [
        Translation(dx=0.5, dy=-1.0),
        Affine.about((10.0, 10.0), rotation_deg=2.0, dx=1.0),
        Dense(np.ones((2, 20, 20))),
    ],
)
def test_a_shift_adds_a_constant_to_any_displacement(displacement):
    shape = (20, 20)

    moved = shifted(displacement, 0.25, -0.5)

    assert type(moved) is type(displacement)
    np.testing.assert_allclose(
        moved.field(shape) - displacement.field(shape),
        np.broadcast_to(np.reshape((0.25, -0.5), (2, 1, 1)), (2, *shape)),
    )


def test_simulated_false_changes_grow_with_the_residual_and_place_each_method(
    tmp_path,
):
    curve, rows = run_simulated(
        "synthetic",
        IMAGE,
        {"pc": phase_correlation},
        CONFIG,
        {"clean": Preset()},
        residuals=(0.0, 0.5, 1.0),
    )

    assert len(curve) == 2 * 3
    assert all(r.false_change == 0.0 for r in curve if r.residual_px == 0.0)
    points = curve_summary(curve)
    by_residual = {p.residual_px: p.mean for p in points}
    assert by_residual[0.0] < by_residual[0.5] < by_residual[1.0]

    assert [r.method for r in rows] == [NONE, "pc"] * 2
    for none, pc in zip(rows[::2], rows[1::2], strict=True):
        assert none.residual_px > pc.residual_px
        assert pc.residual_px < 0.05 and not pc.failed
        assert pc.false_change <= none.false_change
    summary = simulated_summary(rows, points)
    assert [s.method for s in summary] == [NONE, "pc"]
    assert summary[1].at_zero == 0.0
    assert on_curve(points, "synthetic", "clean", 0.25) == pytest.approx(
        by_residual[0.5] / 2
    )

    plot(points, summary, tmp_path / "false_change.png")
    assert (tmp_path / "false_change.png").stat().st_size > 0


def test_simulated_pixels_under_cloud_are_left_out():
    clear_curve, _ = run_simulated(
        "synthetic", IMAGE, {}, CONFIG, {"clean": Preset()}, residuals=(0.0,)
    )
    cloudy_curve, _ = run_simulated(
        "synthetic",
        IMAGE,
        {},
        CONFIG,
        {"cloudy": Preset(clouds=Clouds(cover=0.3))},
        residuals=(0.0,),
    )

    for clear, cloudy in zip(clear_curve, cloudy_curve, strict=True):
        assert cloudy.n_pixels < clear.n_pixels
        # The clouds are not counted as changes.
        assert cloudy.false_change == 0.0


# Displacement of each date's content from the anchor's, (dy, dx) in px.
SHIFTS = {"anchor": (0.0, 0.0), "days": (0.4, -0.2), "season": (1.1, 0.7)}


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


def test_real_pairs_count_changes_on_stable_ground_for_each_method():
    shape = (2 * WINDOW_PX, 2 * WINDOW_PX)
    stable = np.zeros(shape, bool)
    stable[:, : WINDOW_PX + 64] = True

    rows = run_real("synthetic", series(), stable, {"pc": phase_correlation}, CONFIG)

    # Three pairs of dates, four windows, no correction then the method.
    assert len(rows) == 3 * 4 * 2
    assert {r.pair for r in rows} == {"anchor-days", "anchor-season", "days-season"}
    for none, pc in zip(rows[::2], rows[1::2], strict=True):
        assert (none.method, pc.method) == (NONE, "pc")
        assert not pc.failed
        assert pc.stable_px + pc.other_px <= (WINDOW_PX - 16) ** 2
        assert pc.stable_changed_px <= none.stable_changed_px
        assert pc.stable_changed_px <= 0.001 * max(pc.stable_px, 1)
    # The two right-hand windows are almost all other ground.
    assert all(r.stable_px < 64 * WINDOW_PX for r in rows if r.window % 2 == 1)
    by_site = real_summary(rows, "site")
    assert [(r.site, r.pair, r.method) for r in by_site] == [
        ("synthetic", "all", NONE),
        ("synthetic", "all", "pc"),
    ]
    assert by_site[1].stable_changed < by_site[0].stable_changed


def test_a_real_window_hidden_on_one_date_is_left_out_of_its_pairs():
    stable = np.ones((2 * WINDOW_PX, 2 * WINDOW_PX), bool)

    rows = run_real("synthetic", series("days"), stable, {}, CONFIG)

    # "days" is in two of the three pairs; they lose one window each.
    assert len(rows) == 3 * 4 - 2


def test_real_pairs_pool_by_roles_whichever_date_is_the_reference():
    stable = np.ones((2 * WINDOW_PX, 2 * WINDOW_PX), bool)
    rows = run_real("a", series(), stable, {}, CONFIG)
    # A site whose "days" date comes before its anchor.
    swapped = [
        dataclasses.replace(r, site="b", pair="days-anchor")
        for r in rows
        if r.pair == "anchor-days"
    ]

    by_pair = real_summary(rows + swapped, "pair", ["anchor", "days", "season"])

    assert [r.pair for r in by_pair] == ["anchor-days", "anchor-season", "days-season"]
    assert by_pair[0].n_windows == 2 * 4

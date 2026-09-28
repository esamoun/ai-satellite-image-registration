import dataclasses
import datetime as dt
import math

import numpy as np
import pytest

from satreg.degrade import Blur, Clouds, Noise, Preset, Radiometry
from satreg.georef import Georef
from satreg.presetcheck import (
    WINDOW_PX,
    AppearanceRow,
    measure,
    preset_row,
    real_row,
    role_order,
    summarize,
    to_markdown,
)
from satreg.real import RealPair
from satreg.texture import fractal_texture

HARD = Preset(
    radiometry=Radiometry(gain=0.7, offset=-0.5, gamma=1.5),
    clouds=Clouds(cover=0.3),
    blur=Blur(sigma=1.0),
    noise=Noise(snr_db=15),
)
ROLES = role_order(["days", "season", "year"])


@pytest.fixture
def chip():
    """A 512 px chip, four measurement windows."""
    return 1000 + 300 * fractal_texture(2 * WINDOW_PX, seed=5)


def test_windows_under_cloud_are_not_measured(chip):
    cloud = np.zeros(chip.shape, bool)
    cloud[:WINDOW_PX, :WINDOW_PX] = True  # one whole window
    cloud[WINDOW_PX, WINDOW_PX : WINDOW_PX + 100] = True  # 100 pixels of another

    medians, n = measure(chip, 2 * chip, cloud)

    assert n == 3
    assert medians["gain"] == pytest.approx(2)


def test_a_pair_with_no_clear_window_measures_nothing(chip):
    medians, n = measure(chip, chip, np.ones(chip.shape, bool))

    assert n == 0
    assert all(math.isnan(v) for v in medians.values())


def test_the_clean_preset_changes_nothing(chip):
    row = preset_row("beauce", chip, "clean", Preset())

    assert (row.source, row.pair, row.n_windows) == ("preset", "clean", 4)
    assert row.blur_px == pytest.approx(0, abs=1e-6)
    assert row.gain == pytest.approx(1)
    assert row.correlation == pytest.approx(1)
    assert row.cloud_fraction == 0


def test_a_preset_is_measured_without_its_clouds_but_reports_their_cover(chip):
    row = preset_row("beauce", chip, "hard", HARD)
    no_clouds = preset_row(
        "beauce", chip, "hard", dataclasses.replace(HARD, clouds=None)
    )

    assert row.cloud_fraction == 0.3
    assert row.gain == no_clouds.gain
    # Noise on both images flattens the moving image's spectrum at high
    # frequency, so the blur reads below its nominal 1 px.
    assert 0.3 < row.blur_px < 1.0
    assert row.snr_moving_db < 16


def test_a_preset_row_is_the_same_for_the_same_seed(chip):
    first = preset_row("beauce", chip, "hard", HARD, seed=1)

    assert preset_row("beauce", chip, "hard", HARD, seed=1) == first
    assert preset_row("beauce", chip, "hard", HARD, seed=2) != first


def test_a_real_row_names_the_pair_by_its_roles_and_leaves_out_hidden_pixels(chip):
    cloud = np.zeros(chip.shape, bool)
    cloud[:WINDOW_PX, :] = True
    pair = RealPair(
        reference=np.round(chip + 2000).astype(np.uint16),
        moving=np.round(1.2 * (chip + 2000)).astype(np.uint16),
        georef=Georef("EPSG:32631", None),
        cloud=cloud,
        roles=("days", "anchor"),
        dates=(
            dt.datetime(2025, 6, 26, 10, tzinfo=dt.UTC),
            dt.datetime(2025, 7, 1, 10, tzinfo=dt.UTC),
        ),
        scene_ids=("a", "b"),
        platforms=("sentinel-2b", "sentinel-2c"),
    )

    row = real_row("beauce", pair)

    assert row.pair == "days-anchor"
    assert (row.reference_date, row.moving_date, row.gap_days) == (
        "2025-06-26",
        "2025-07-01",
        5,
    )
    assert row.platforms == "sentinel-2b/sentinel-2c"
    assert row.cloud_fraction == 0.5
    assert row.n_windows == 2
    assert row.gain == pytest.approx(1.2, rel=1e-3)


def row(site, pair, source="real", gain=1.0, n_windows=16, gap_days=5, **values):
    fields = {
        "snr_reference_db": 20.0,
        "snr_moving_db": 20.0,
        "blur_px": 0.1,
        "offset": 0.0,
        "tone_bend": 0.01,
        "correlation": 0.9,
        **values,
    }
    return AppearanceRow(
        site=site,
        source=source,
        pair=pair,
        reference_date="",
        moving_date="",
        gap_days=gap_days,
        platforms="",
        cloud_fraction=0.0,
        n_windows=n_windows,
        gain=gain,
        **fields,
    )


def test_a_pair_and_its_reverse_are_one_kind_of_pair_across_sites():
    rows = [
        row("beauce", "anchor-days", gain=2.0, blur_px=-0.3),
        row("vosges", "days-anchor", gain=0.5, blur_px=0.1, snr_moving_db=12.0),
        row("toulouse", "anchor-days", gain=1.25, blur_px=0.2),
    ]

    (summary,) = summarize(rows, ROLES)

    assert (summary.source, summary.pair, summary.n_sites) == ("real", "anchor-days", 3)
    # A gain and its inverse are the same contrast change.
    assert summary.values["contrast"] == (2.0, 1.25, 2.0)
    assert summary.values["blur_px"] == pytest.approx((0.2, 0.1, 0.3))
    assert summary.values["snr_db"] == (20.0, 12.0, 20.0)


def test_presets_come_first_then_role_pairs_in_series_order():
    rows = [
        row("beauce", "season-year"),
        row("beauce", "anchor-season"),
        row("beauce", "hard", source="preset"),
        row("beauce", "days-anchor"),
        row("beauce", "mild", source="preset"),
    ]

    summary = summarize(rows, ROLES)

    assert [(s.source, s.pair) for s in summary] == [
        ("preset", "hard"),
        ("preset", "mild"),
        ("real", "anchor-days"),
        ("real", "anchor-season"),
        ("real", "season-year"),
    ]


def test_sites_without_a_measured_window_are_left_out_of_a_summary():
    rows = [
        row("beauce", "anchor-days", gain=2.0),
        row("vosges", "anchor-days", n_windows=0),
    ]

    (summary,) = summarize(rows, ROLES)

    assert summary.n_sites == 1
    assert summary.values["contrast"] == (2.0, 2.0, 2.0)


def test_the_table_shows_each_preset_s_nominal_values_under_its_measured_ones():
    rows = [
        row("beauce", "hard", source="preset", gain=0.5, gap_days=0),
        row("beauce", "anchor-days", n_windows=0),
    ]

    table = to_markdown(summarize(rows, ROLES), {"hard": HARD})

    lines = table.splitlines()
    assert lines[0].startswith("| pairs | sites | gap (days) | SNR (dB) |")
    assert lines[2].startswith("| preset `hard` | 1 | 0 | 20.0 [20.0, 20.0] |")
    assert lines[3] == (
        "| ↳ nominal | | | 15 (added) | 1 | 1.43 | 0.5 | gamma 1.5 |  | 30 % |"
    )
    assert lines[4].startswith("| anchor-days | 0 | 5 | n/a |")

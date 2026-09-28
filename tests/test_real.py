import dataclasses
import datetime as dt
from pathlib import Path

import numpy as np
import pytest
import rasterio
from test_ingest import (
    CENTRE,
    CLOUD,
    SHADOW,
    SHAPE,
    SNOW,
    TRANSFORM,
    site_at,
    write_cog,
    write_scl,
)

from satreg.georef import Georef
from satreg.ingest import Scene, cache_path
from satreg.real import (
    ANCHOR,
    SCL_NO_DATA,
    Acquisition,
    DateRule,
    SeriesConfig,
    fetch_series,
    load_series,
    load_series_config,
    make_pair,
    pairs,
    read_acquisition,
    series_path,
    triplets,
)
from satreg.sites import Catalogue, load_sites

CATALOGUE = Catalogue(url="https://stac.example", collection="sentinel-2-c1-l2a")
TILE, ORBIT = "MGRS-31UCP", 94
CONFIG = SeriesConfig(
    sites=("beauce",),
    max_scene_cloud=50.0,
    dates={
        "days": DateRule(offset_days=0, within_days=15),
        "season": DateRule(offset_days=91, within_days=30),
    },
)
# The fixture chip covers 20 m pixels (59, 84) to (91, 116).
CHIP_CLOUD = {CLOUD: (slice(60, 80), slice(90, 110))}


def acquisition_scene(
    tmp_path, day, *, cloud_cover=1.0, tile=TILE, orbit=ORBIT, scl=None, suffix=""
):
    """A scene of the fixture tile on ``day``, with its own band and SCL files.

    Args:
        tmp_path: Where to write its files.
        day: Acquisition date.
        cloud_cover: Scene cloud cover, in percent.
        tile: MGRS tile.
        orbit: Relative orbit.
        scl: Classification fill, as ``write_scl`` takes it; clear if ``None``.
        suffix: Distinguishes two items of the same day.
    """
    item_id = f"S2B_T31UCP_{day:%Y%m%d}{suffix}"
    seed = day.toordinal() + len(suffix)
    data = np.random.default_rng(seed).integers(1, 10_000, SHAPE, dtype=np.uint16)
    href = write_cog(tmp_path / f"{item_id}_B04.tif", data)
    scl_href = write_scl(tmp_path / f"{item_id}_SCL.tif", scl)
    return Scene(
        item_id=item_id,
        href=href,
        cloud_cover=cloud_cover,
        datetime=f"{day.isoformat()}T10:56:29+00:00",
        scl_href=scl_href,
        platform="sentinel-2b",
        tile=tile,
        relative_orbit=orbit,
    )


def catalogue_of(*scenes):
    """A fake scene search over ``scenes`` that records its calls."""

    def candidates(site, catalogue, start, end, max_cloud, tile):
        candidates.calls.append((start, end, max_cloud, tile))
        found = [
            s
            for s in scenes
            if start <= s.date <= end
            and s.cloud_cover <= max_cloud
            and (tile is None or s.tile == tile)
        ]
        return sorted(found, key=lambda s: (s.cloud_cover, s.item_id))

    candidates.calls = []
    return candidates


@pytest.fixture
def series(tmp_path):
    """A site, its scenes, and a search over them.

    The anchor is the clearest scene of the site's date range, 2025-07-01. Near
    it: a second item of the anchor's day, a date on another orbit, one on
    another tile and one cloudy over the chip, all closer than the clear date
    the ``days`` role must take, 2025-06-26. The ``season`` role targets
    2025-09-30 and takes 2025-09-28.
    """
    d = dt.date
    scenes = {
        "anchor": acquisition_scene(tmp_path, d(2025, 7, 1), cloud_cover=0.1),
        "twin": acquisition_scene(tmp_path, d(2025, 7, 1), suffix="_1"),
        "orbit": acquisition_scene(tmp_path, d(2025, 7, 2), orbit=51),
        "tile": acquisition_scene(tmp_path, d(2025, 7, 3), tile="MGRS-31UDP"),
        "cloudy": acquisition_scene(tmp_path, d(2025, 6, 29), scl=CHIP_CLOUD),
        "days": acquisition_scene(tmp_path, d(2025, 6, 26)),
        "far": acquisition_scene(tmp_path, d(2025, 7, 20)),
        "season": acquisition_scene(tmp_path, d(2025, 9, 28), cloud_cover=30.0),
    }
    return site_at(*CENTRE), scenes, catalogue_of(*scenes.values())


def test_every_date_of_a_series_is_on_the_anchor_s_grid(series, tmp_path):
    site, _, candidates = series

    paths = fetch_series(site, CATALOGUE, CONFIG, tmp_path / "data", candidates)
    acquisitions = [read_acquisition(path) for path in paths.values()]

    assert list(paths) == [ANCHOR, "days", "season"]
    anchor = acquisitions[0]
    for a in acquisitions:
        assert a.image.shape == a.scl.shape == (64, 64)
        assert a.georef == anchor.georef
    # The anchor is the benchmark chip itself.
    with rasterio.open(cache_path(site, CATALOGUE, tmp_path / "data")) as src:
        np.testing.assert_array_equal(anchor.image, src.read(1))


def test_each_role_takes_the_nearest_clear_date_on_the_anchor_s_tile_and_orbit(
    series, tmp_path
):
    site, scenes, candidates = series

    paths = fetch_series(site, CATALOGUE, CONFIG, tmp_path / "data", candidates)

    ids = {role: read_acquisition(p).item_id for role, p in paths.items()}
    assert ids == {
        ANCHOR: scenes["anchor"].item_id,
        "days": scenes["days"].item_id,
        "season": scenes["season"].item_id,
    }
    # Each role searched the anchor's tile, around its target, under the
    # series' scene cloud limit.
    days, season = candidates.calls[-2:]
    assert days == (dt.date(2025, 6, 16), dt.date(2025, 7, 16), 50.0, TILE)
    assert season == (dt.date(2025, 8, 31), dt.date(2025, 10, 30), 50.0, TILE)


def test_a_series_in_the_cache_is_loaded_without_any_search(series, tmp_path):
    site, _, candidates = series
    first = fetch_series(site, CATALOGUE, CONFIG, tmp_path / "data", candidates)
    calls = len(candidates.calls)

    again = fetch_series(site, CATALOGUE, CONFIG, tmp_path / "data", candidates)

    assert again == first
    assert len(candidates.calls) == calls


def test_a_date_records_its_scene_satellite_and_target(series, tmp_path):
    site, scenes, candidates = series

    paths = fetch_series(site, CATALOGUE, CONFIG, tmp_path / "data", candidates)

    with rasterio.open(paths["season"]) as src:
        tags = src.tags()
        assert src.descriptions == ("B04", "SCL")
    assert tags["item_id"] == scenes["season"].item_id
    assert tags["platform"] == "sentinel-2b"
    assert tags["tile"] == TILE
    assert tags["relative_orbit"] == "94"
    assert tags["target"] == "2025-09-30"


def test_no_clear_date_within_a_role_s_window_is_an_error(tmp_path):
    anchor = acquisition_scene(tmp_path, dt.date(2025, 7, 1), cloud_cover=0.1)
    cloudy = acquisition_scene(tmp_path, dt.date(2025, 7, 5), scl=CHIP_CLOUD)
    candidates = catalogue_of(anchor, cloudy)

    with pytest.raises(LookupError, match="days of 2025-07-01.*1 tried"):
        fetch_series(site_at(*CENTRE), CATALOGUE, CONFIG, tmp_path, candidates)
    assert not series_path(
        site_at(*CENTRE), CATALOGUE, CONFIG, "days", tmp_path
    ).exists()


def test_a_few_no_data_pixels_are_hidden_not_disqualifying(tmp_path):
    anchor = acquisition_scene(tmp_path, dt.date(2025, 7, 1), cloud_cover=0.1)
    gappy = acquisition_scene(tmp_path, dt.date(2025, 7, 11))
    with rasterio.open(gappy.href, "r+") as dst:
        data = dst.read(1)
        data[150, 200:205] = 0  # 5 pixels of the chip, under its 1 % limit
        dst.write(data, 1)
    season = acquisition_scene(tmp_path, dt.date(2025, 9, 30))
    candidates = catalogue_of(anchor, gappy, season)

    paths = fetch_series(site_at(*CENTRE), CATALOGUE, CONFIG, tmp_path, candidates)

    days = read_acquisition(paths["days"])
    assert days.item_id == gappy.item_id
    # Chip pixel (32, 32) is source pixel (150, 200).
    assert (days.scl[32, 32:37] == SCL_NO_DATA).all()
    assert days.hidden.sum() == 5


def test_the_cache_key_follows_the_date_rules_but_not_holding_out(tmp_path):
    site = site_at(*CENTRE)
    path = series_path(site, CATALOGUE, CONFIG, "days", tmp_path)

    held_out = dataclasses.replace(site, held_out=True)
    wider = dataclasses.replace(
        CONFIG, dates={**CONFIG.dates, "season": DateRule(91, 45)}
    )
    assert series_path(held_out, CATALOGUE, CONFIG, "days", tmp_path) == path
    assert series_path(site, CATALOGUE, wider, "days", tmp_path) != path
    assert path.parent == tmp_path / "real" / "beauce"


def acquisition(role, day, scl=None, georef=None):
    image = np.random.default_rng(day).integers(1, 10_000, (8, 8), np.uint16)
    return Acquisition(
        role=role,
        image=image,
        scl=np.full((8, 8), 4, np.uint8) if scl is None else scl,
        georef=georef or Georef("EPSG:32631", TRANSFORM),
        item_id=f"item-{day}",
        datetime=dt.datetime(2025, 7, day, 10, 56, tzinfo=dt.UTC),
        platform="sentinel-2a" if day % 2 else "sentinel-2b",
    )


def test_a_pair_hides_what_either_date_hides(tmp_path):
    first = np.full((8, 8), 4, np.uint8)
    first[0, :3] = CLOUD
    first[1, 0] = SNOW  # snow is ground, not hidden
    second = np.full((8, 8), 4, np.uint8)
    second[0, 2:5] = SHADOW
    second[7, 7] = SCL_NO_DATA

    pair = make_pair(acquisition("anchor", 1, first), acquisition("days", 3, second))

    expected = np.zeros((8, 8), bool)
    expected[0, :5] = True
    expected[7, 7] = True
    np.testing.assert_array_equal(pair.cloud, expected)
    np.testing.assert_array_equal(pair.valid, ~expected)
    assert pair.cloud_fraction == 6 / 64


def test_a_pair_carries_both_dates_and_no_truth():
    pair = make_pair(acquisition("anchor", 1), acquisition("days", 11))

    assert pair.roles == ("anchor", "days")
    assert pair.scene_ids == ("item-1", "item-11")
    assert pair.platforms == ("sentinel-2a", "sentinel-2a")
    assert pair.gap_days == 10
    assert not hasattr(pair, "truth")


def test_dates_on_different_grids_do_not_pair():
    moved = Georef("EPSG:32631", TRANSFORM @ TRANSFORM.translation(1, 0))

    with pytest.raises(ValueError, match="same grid"):
        make_pair(acquisition("anchor", 1), acquisition("days", 3, georef=moved))


def test_four_dates_give_six_pairs_and_four_triplets_in_date_order():
    series = [
        acquisition("year", 30),
        acquisition("anchor", 10),
        acquisition("days", 4),
        acquisition("season", 20),
    ]

    found = pairs(series)

    assert len(found) == 6
    assert all(p.dates[0] < p.dates[1] for p in found)
    assert found[0].roles == ("days", "anchor")
    assert [tuple(a.role for a in t) for t in triplets(series)] == [
        ("days", "anchor", "season"),
        ("days", "anchor", "year"),
        ("days", "season", "year"),
        ("anchor", "season", "year"),
    ]


def test_load_series_returns_the_dates_in_order(series, tmp_path):
    site, scenes, candidates = series

    loaded = load_series(site, CATALOGUE, CONFIG, tmp_path / "data", candidates)

    assert [a.role for a in loaded] == ["days", ANCHOR, "season"]


def write_config(tmp_path, text):
    path = tmp_path / "real.toml"
    path.write_text(text)
    return path


def test_series_config_is_read_in_file_order(tmp_path):
    path = write_config(
        tmp_path,
        '[series]\nsites = ["beauce"]\nmax_scene_cloud = 40\n'
        "[series.dates]\nyear = { offset_days = 365, within_days = 30 }\n"
        "days = { offset_days = 0, within_days = 15 }\n",
    )

    config = load_series_config(path)

    assert config.sites == ("beauce",)
    assert config.max_scene_cloud == 40.0
    assert list(config.dates) == ["year", "days"]
    assert config.dates["year"] == DateRule(365, 30)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ('[series]\nsites = ["beauce"]\n', "sites and dates"),
        (
            '[series]\nsites = ["beauce"]\nwhen = 1\n'
            "[series.dates]\ndays = { offset_days = 0, within_days = 15 }\n",
            "unknown \\[series\\] key 'when'",
        ),
        (
            '[series]\nsites = ["beauce"]\n'
            "[series.dates]\nanchor = { offset_days = 0, within_days = 15 }\n",
            "'anchor' is the chip's own date",
        ),
        (
            '[series]\nsites = ["beauce"]\n'
            "[series.dates]\ndays = { offset_days = 0, within_days = -1 }\n",
            "date days: within_days must be >= 0",
        ),
        (
            '[series]\nsites = ["beauce"]\n'
            "[series.dates]\ndays = { offset_days = 0 }\n",
            "date days",
        ),
    ],
)
def test_bad_series_config_is_rejected(tmp_path, text, message):
    with pytest.raises(ValueError, match=message):
        load_series_config(write_config(tmp_path, text))


def test_repository_series_config_is_valid():
    configs = Path(__file__).parents[1] / "configs"

    config = load_series_config(configs / "real.toml")

    assert list(config.dates) == ["days", "season", "year"]
    assert set(config.sites) == set(load_sites(configs / "sites.toml").sites)

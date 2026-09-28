import datetime as dt
from pathlib import Path

import numpy as np
import pystac
import pytest
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import transform as transform_coords

from satreg import ingest
from satreg.ingest import (
    ChipUnavailable,
    Scene,
    band_href,
    cache_path,
    chip_cover,
    fetch_chip,
    read_chip,
    read_georef,
    read_scl,
    read_window,
    relative_orbit,
    scl_href,
    stac_scenes,
    stac_search,
)
from satreg.sites import Catalogue, Site

CATALOGUE = Catalogue(url="https://stac.example", collection="sentinel-2-c1-l2a")
CRS = "EPSG:32631"
# A 10 m grid in UTM 31N, over the Beauce, like a Sentinel-2 tile.
TRANSFORM = from_origin(390_000, 5_345_000, 10, 10)
SHAPE = (300, 400)
CENTRE = (150, 200)  # (row, col) of the pixel the test site is centred on
# The 64 px chip of the test site starts at 10 m pixel (118, 168), which is
# 20 m pixel (59, 84), and covers 32 x 32 pixels of the 20 m grid.
SCL_CHIP = (slice(59, 91), slice(84, 116))

# SCL classes: vegetation, cloud shadow, cloud (high probability), snow, water.
VEGETATION, SHADOW, CLOUD, SNOW, WATER = 4, 3, 9, 11, 6


def write_cog(path, data, nodata=0, transform=TRANSFORM):
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=data.shape[1],
        height=data.shape[0],
        count=1,
        dtype=data.dtype,
        crs=CRS,
        transform=transform,
        nodata=nodata,
    ) as dst:
        dst.write(data, 1)
    return str(path)


@pytest.fixture
def source(tmp_path):
    """A tiny single-band GeoTIFF standing in for a Sentinel-2 COG."""
    data = np.random.default_rng(0).integers(1, 10_000, SHAPE, dtype=np.uint16)
    return write_cog(tmp_path / "B04.tif", data), data


def write_scl(path, fill=None):
    """A scene classification on the 20 m grid of the fixture tile.

    Args:
        path: Where to write it.
        fill: ``{class: (rows, cols)}`` slices of the 20 m grid to set to that
            class; the rest is vegetation.
    """
    scl = np.full((SHAPE[0] // 2, SHAPE[1] // 2), VEGETATION, np.uint8)
    for value, where in (fill or {}).items():
        scl[where] = value
    transform = TRANSFORM @ TRANSFORM.scale(2)
    return write_cog(path, scl, transform=transform)


def site_at(row, col, chip_px=64, **overrides):
    """A site centred on the middle of pixel ``(row, col)`` of the fixture grid."""
    x, y = TRANSFORM @ (col + 0.5, row + 0.5)
    lons, lats = transform_coords(CRS, "EPSG:4326", [x], [y])
    fields = {
        "name": "beauce",
        "lon": lons[0],
        "lat": lats[0],
        "chip_px": chip_px,
        "start": dt.date(2025, 4, 1),
        "end": dt.date(2025, 9, 30),
        "max_cloud": 5.0,
        **overrides,
    }
    return Site(**fields)


def searching(*scenes):
    """A fake scene search that records its calls."""

    def search(site, catalogue):
        search.calls += 1
        return list(scenes)

    search.calls = 0
    return search


def scene(href, item_id="S2B_T31UCP_20250701", cloud_cover=0.1, scl=None):
    """A candidate scene; its classification is clear unless ``scl`` is given."""
    if scl is None:
        scl = write_scl(Path(href).with_name(f"{item_id}_SCL.tif"))
    return Scene(item_id, href, cloud_cover, "2025-07-01T10:56:29Z", scl)


def test_chip_is_a_window_of_the_source_grid_without_resampling(source):
    href, data = source
    row, col = CENTRE

    chip, profile = read_window(href, site_at(row, col))

    top, left = row - 32, col - 32
    np.testing.assert_array_equal(chip, data[top : top + 64, left : left + 64])
    assert chip.dtype == np.uint16
    assert profile["crs"] == CRS
    # Same pixel size, origin moved by whole pixels: the chip is on the source grid.
    assert profile["transform"] == TRANSFORM @ TRANSFORM.translation(left, top)
    assert profile["nodata"] == 0


def test_chip_grid_is_read_back_from_the_file(tmp_path):
    chip = tmp_path / "chip.tif"
    write_cog(chip, np.ones((8, 8), np.uint16))

    georef = read_georef(chip)

    assert georef.crs == CRS
    assert georef.transform == TRANSFORM
    assert georef.window(3, 5).transform @ (0, 0) == TRANSFORM @ (5, 3)


def test_chip_leaving_the_raster_is_unavailable(source):
    href, _ = source

    with pytest.raises(ChipUnavailable, match="leaves the raster"):
        read_window(href, site_at(10, 200))


def test_chip_with_no_data_pixels_is_unavailable(tmp_path):
    data = np.ones(SHAPE, dtype=np.uint16)
    data[:, :190] = 0  # the edge of the swath
    href = write_cog(tmp_path / "edge.tif", data)

    with pytest.raises(ChipUnavailable, match="no-data"):
        read_window(href, site_at(*CENTRE))


def test_a_chip_with_no_data_pixels_is_read_when_the_caller_masks_them(tmp_path):
    data = np.ones(SHAPE, dtype=np.uint16)
    data[:, :190] = 0
    href = write_cog(tmp_path / "edge.tif", data)

    chip, profile = read_window(href, site_at(*CENTRE), allow_nodata=True)

    # The chip starts on column 168, so its first 22 columns have no data.
    assert (chip[:, :22] == 0).all() and (chip[:, 22:] == 1).all()
    assert profile["nodata"] == 0


def test_fetched_chip_keeps_crs_geotransform_and_its_scene(source, tmp_path):
    href, data = source
    site = site_at(*CENTRE)

    path = fetch_chip(site, CATALOGUE, tmp_path / "data", searching(scene(href)))

    assert path == cache_path(site, CATALOGUE, tmp_path / "data")
    with rasterio.open(path) as chip:
        assert chip.crs == CRS
        assert chip.transform == TRANSFORM @ TRANSFORM.translation(168, 118)
        assert chip.tags()["item_id"] == "S2B_T31UCP_20250701"
        assert chip.tags()["band"] == "B04"
    np.testing.assert_array_equal(read_chip(path), data[118:182, 168:232])


def test_second_fetch_uses_the_cache_and_makes_no_search(source, tmp_path):
    href, _ = source
    site = site_at(*CENTRE)
    search = searching(scene(href))

    first = fetch_chip(site, CATALOGUE, tmp_path, search)
    second = fetch_chip(site, CATALOGUE, tmp_path, search)

    assert first == second
    assert search.calls == 1


def test_changing_the_site_changes_the_cache_entry():
    sites = [
        site_at(*CENTRE),
        site_at(*CENTRE, chip_px=128),
        site_at(*CENTRE, max_cloud=20.0),
        site_at(*CENTRE, band="B08"),
    ]

    paths = [cache_path(site, CATALOGUE, Path("data")) for site in sites]

    assert len(set(paths)) == len(sites)
    assert paths[0].parent == Path("data/chips/beauce")
    assert paths[3].name.startswith("B08_")


def test_scenes_that_cannot_give_a_complete_chip_are_skipped(source, tmp_path):
    href, _ = source
    edge = np.zeros(SHAPE, dtype=np.uint16)
    edge_href = write_cog(tmp_path / "edge.tif", edge)
    search = searching(
        scene(edge_href, item_id="edge", cloud_cover=0.0),
        scene(href, item_id="complete", cloud_cover=1.0),
    )

    path = fetch_chip(site_at(*CENTRE), CATALOGUE, tmp_path / "data", search)

    with rasterio.open(path) as chip:
        assert chip.tags()["item_id"] == "complete"


def test_no_usable_scene_is_an_error_and_caches_nothing(tmp_path):
    site = site_at(*CENTRE)

    with pytest.raises(LookupError, match="beauce"):
        fetch_chip(site, CATALOGUE, tmp_path, searching())
    assert not cache_path(site, CATALOGUE, tmp_path).exists()


def asset(href, *bands):
    return pystac.Asset(href, extra_fields={"eo:bands": [{"name": b} for b in bands]})


def test_band_asset_is_the_single_band_one_not_the_colour_composite():
    assets = {
        "visual": asset("TCI.tif", "B04", "B03", "B02"),
        "red": asset("B04.tif", "B04"),
        "nir": asset("B08.tif", "B08"),
    }

    assert band_href(assets, "B04") == "B04.tif"
    assert band_href(assets, "B08") == "B08.tif"
    with pytest.raises(ValueError, match="B12"):
        band_href(assets, "B12")


def item(item_id, cloud_cover, **properties):
    stac_item = pystac.Item(
        id=item_id,
        geometry=None,
        bbox=None,
        datetime=dt.datetime(2025, 7, 1, tzinfo=dt.UTC),
        properties={"eo:cloud_cover": cloud_cover, **properties},
    )
    stac_item.add_asset("red", asset(f"{item_id}/B04.tif", "B04"))
    stac_item.add_asset("scl", pystac.Asset(f"{item_id}/SCL.tif"))
    return stac_item


def test_search_asks_for_the_site_and_sorts_least_cloudy_first(monkeypatch):
    requests = []

    class FakeClient:
        @staticmethod
        def open(url):
            assert url == CATALOGUE.url
            return FakeClient()

        def search(self, **params):
            requests.append(params)
            items = [item("b", 2.0), item("c", 0.5), item("a", 2.0)]
            return type("Search", (), {"items": lambda self: iter(items)})()

    monkeypatch.setattr(ingest, "Client", FakeClient)
    site = site_at(*CENTRE)

    scenes = stac_search(site, CATALOGUE)

    assert [s.item_id for s in scenes] == ["c", "a", "b"]
    assert scenes[0].href == "c/B04.tif"
    assert scenes[0].scl_href == "c/SCL.tif"
    (params,) = requests
    assert params["collections"] == ["sentinel-2-c1-l2a"]
    assert params["intersects"]["coordinates"] == [site.lon, site.lat]
    assert params["datetime"] == "2025-04-01/2025-09-30"
    assert params["query"] == {"eo:cloud_cover": {"lte": 5.0}}


def test_a_search_on_one_tile_asks_for_it_and_records_satellite_tile_and_orbit(
    monkeypatch,
):
    requests = []
    found = item(
        "a",
        1.0,
        platform="sentinel-2c",
        **{
            "grid:code": "MGRS-31UCP",
            "s2:product_uri": "S2C_MSIL2A_20250701T105041_N0511_R051_T31UCP_2025.SAFE",
        },
    )

    class FakeClient:
        @staticmethod
        def open(url):
            return FakeClient()

        def search(self, **params):
            requests.append(params)
            return type("Search", (), {"items": lambda self: iter([found])})()

    monkeypatch.setattr(ingest, "Client", FakeClient)

    (scene,) = stac_scenes(
        site_at(*CENTRE),
        CATALOGUE,
        dt.date(2025, 6, 1),
        dt.date(2025, 6, 30),
        50.0,
        tile="MGRS-31UCP",
    )

    (params,) = requests
    assert params["datetime"] == "2025-06-01/2025-06-30"
    assert params["query"] == {
        "eo:cloud_cover": {"lte": 50.0},
        "grid:code": {"eq": "MGRS-31UCP"},
    }
    assert (scene.platform, scene.tile, scene.relative_orbit) == (
        "sentinel-2c",
        "MGRS-31UCP",
        51,
    )
    assert scene.date == dt.date(2025, 7, 1)


@pytest.mark.parametrize(
    ("properties", "orbit"),
    [
        ({"s2:product_uri": "S2B_MSIL2A_20250701T105619_N0511_R094_T31UCP"}, 94),
        ({"sat:relative_orbit": 8, "s2:product_uri": "S2B_R094_T31UCP"}, 8),
        ({"s2:product_uri": "S2B_MSIL2A_20250701"}, 0),
        ({}, 0),
    ],
)
def test_relative_orbit_is_read_from_the_item_or_its_product_name(properties, orbit):
    assert relative_orbit(properties) == orbit


def test_scene_classification_asset_is_found_by_its_key():
    assets = {"red": asset("B04.tif", "B04"), "scl": pystac.Asset("SCL.tif")}

    assert scl_href(assets) == "SCL.tif"
    with pytest.raises(ValueError, match="scl"):
        scl_href({"red": asset("B04.tif", "B04")})


def test_chip_cover_counts_the_classes_over_the_chip_only(source, tmp_path):
    href, _ = source
    rows, cols = SCL_CHIP
    scl = write_scl(
        tmp_path / "SCL.tif",
        {
            # A quarter of the chip's 32 x 32 pixels, split between cloud rows...
            CLOUD: (slice(rows.start, rows.start + 4), cols),
            # ...cloud shadow rows, and a snow and a water column.
            SHADOW: (slice(rows.start + 4, rows.start + 8), cols),
            SNOW: (rows, slice(cols.start, cols.start + 2)),
            WATER: (rows, slice(cols.stop - 1, cols.stop)),
        },
    )
    # Cloud all around the chip, never on it.
    with rasterio.open(scl, "r+") as dst:
        data = dst.read(1)
        data[: rows.start, :] = CLOUD
        data[rows.stop :, :] = CLOUD
        dst.write(data, 1)
    _, profile = read_window(href, site_at(*CENTRE))

    cover = chip_cover(scl, profile)

    # Snow and water columns overwrite the cloud and shadow rows they cross.
    assert cover == pytest.approx(
        {
            "cloud": 100 * 4 * 29 / 1024,
            "shadow": 100 * 4 * 29 / 1024,
            "snow": 100 * 2 * 32 / 1024,
            "water": 100 * 1 * 32 / 1024,
        }
    )


def test_a_chip_on_an_odd_pixel_counts_every_20_m_pixel_it_touches(source, tmp_path):
    href, _ = source
    # The chip starts on 10 m pixel (119, 169), inside 20 m pixel (59, 84).
    _, profile = read_window(href, site_at(CENTRE[0] + 1, CENTRE[1] + 1))
    scl = write_scl(tmp_path / "SCL.tif", {CLOUD: (slice(59, 60), slice(None))})

    cover = chip_cover(scl, profile)

    assert cover["cloud"] == pytest.approx(100 / 33)


def test_each_chip_pixel_takes_the_class_of_the_20_m_pixel_under_its_centre(
    source, tmp_path
):
    href, _ = source
    # The chip starts on 10 m pixel (119, 169), halfway through a 20 m pixel.
    _, profile = read_window(href, site_at(CENTRE[0] + 1, CENTRE[1] + 1))
    rows, cols = SHAPE[0] // 2, SHAPE[1] // 2
    codes = ((np.arange(rows)[:, None] * 7 + np.arange(cols)[None, :]) % 251).astype(
        np.uint8
    )
    scl = write_cog(
        tmp_path / "SCL.tif", codes, transform=TRANSFORM @ TRANSFORM.scale(2)
    )

    chip_scl = read_scl(scl, profile)

    row, col = np.arange(64)[:, None] + 119, np.arange(64)[None, :] + 169
    np.testing.assert_array_equal(chip_scl, codes[row // 2, col // 2])
    assert chip_scl.dtype == np.uint8


def test_classification_not_covering_the_chip_is_unavailable(source, tmp_path):
    href, _ = source
    _, profile = read_window(href, site_at(*CENTRE))
    small = np.full((60, 90), VEGETATION, np.uint8)
    scl = write_cog(
        tmp_path / "SCL.tif", small, transform=TRANSFORM @ TRANSFORM.scale(2)
    )

    with pytest.raises(ChipUnavailable, match="does not cover"):
        read_scl(scl, profile)


def test_classification_on_another_grid_is_unavailable(source, tmp_path):
    href, _ = source
    scl = tmp_path / "SCL.tif"
    with rasterio.open(
        scl,
        "w",
        driver="GTiff",
        width=200,
        height=150,
        count=1,
        dtype="uint8",
        crs="EPSG:32632",
        transform=TRANSFORM @ TRANSFORM.scale(2),
    ) as dst:
        dst.write(np.full((150, 200), VEGETATION, np.uint8), 1)
    _, profile = read_window(href, site_at(*CENTRE))

    with pytest.raises(ChipUnavailable, match="EPSG:32632"):
        chip_cover(scl, profile)


def test_a_clear_scene_with_a_cloud_on_the_chip_is_skipped(source, tmp_path):
    href, _ = source
    # The least cloudy scene has 3 % of the chip under cloud and none elsewhere.
    rows, _ = SCL_CHIP
    cloudy = write_scl(tmp_path / "cloudy.tif", {CLOUD: (rows, slice(84, 85))})
    search = searching(
        scene(href, item_id="cloud_on_chip", cloud_cover=0.0, scl=cloudy),
        scene(href, item_id="clear_chip", cloud_cover=3.0),
    )

    path = fetch_chip(site_at(*CENTRE), CATALOGUE, tmp_path / "data", search)

    with rasterio.open(path) as chip:
        assert chip.tags()["item_id"] == "clear_chip"


def test_cloud_shadow_counts_against_the_chip_but_snow_does_not(source, tmp_path):
    href, _ = source
    rows, cols = SCL_CHIP
    shadowed = write_scl(tmp_path / "shadow.tif", {SHADOW: (rows, slice(84, 85))})
    snowy = write_scl(tmp_path / "snow.tif", {SNOW: (slice(59, 75), cols)})
    search = searching(
        scene(href, item_id="shadow", cloud_cover=0.0, scl=shadowed),
        scene(href, item_id="snow", cloud_cover=1.0, scl=snowy),
    )

    path = fetch_chip(site_at(*CENTRE), CATALOGUE, tmp_path / "data", search)

    with rasterio.open(path) as chip:
        tags = chip.tags()
    assert tags["item_id"] == "snow"
    assert tags["chip_snow_pct"] == "50.000"
    assert tags["chip_cloud_pct"] == tags["chip_shadow_pct"] == "0.000"
    assert tags["chip_water_pct"] == "0.000"


def test_the_chip_cloud_limit_is_the_site_s(source, tmp_path):
    href, _ = source
    rows, _ = SCL_CHIP
    cloudy = write_scl(tmp_path / "cloudy.tif", {CLOUD: (rows, slice(84, 85))})
    site = site_at(*CENTRE, max_chip_cloud=5.0)

    path = fetch_chip(
        site, CATALOGUE, tmp_path, searching(scene(href, cloud_cover=0.0, scl=cloudy))
    )

    with rasterio.open(path) as chip:
        assert chip.tags()["chip_cloud_pct"] == "3.125"


def test_no_scene_with_a_clear_chip_names_the_chip_limit(source, tmp_path):
    href, _ = source
    cloudy = write_scl(tmp_path / "cloudy.tif", {CLOUD: SCL_CHIP})

    with pytest.raises(LookupError, match="1.0 % cloud and cloud shadow"):
        fetch_chip(
            site_at(*CENTRE), CATALOGUE, tmp_path, searching(scene(href, scl=cloudy))
        )


def test_holding_a_site_out_keeps_its_cached_chip():
    site = site_at(*CENTRE)
    held_out = site_at(*CENTRE, held_out=True)

    assert cache_path(site, CATALOGUE, Path("data")) == cache_path(
        held_out, CATALOGUE, Path("data")
    )

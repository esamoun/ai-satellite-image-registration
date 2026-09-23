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
    fetch_chip,
    read_chip,
    read_window,
    stac_search,
)
from satreg.sites import Catalogue, Site

CATALOGUE = Catalogue(url="https://stac.example", collection="sentinel-2-c1-l2a")
CRS = "EPSG:32631"
# A 10 m grid in UTM 31N, over the Beauce, like a Sentinel-2 tile.
TRANSFORM = from_origin(390_000, 5_345_000, 10, 10)
SHAPE = (300, 400)
CENTRE = (150, 200)  # (row, col) of the pixel the test site is centred on


def write_cog(path, data, nodata=0):
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=data.shape[1],
        height=data.shape[0],
        count=1,
        dtype=data.dtype,
        crs=CRS,
        transform=TRANSFORM,
        nodata=nodata,
    ) as dst:
        dst.write(data, 1)
    return str(path)


@pytest.fixture
def source(tmp_path):
    """A tiny single-band GeoTIFF standing in for a Sentinel-2 COG."""
    data = np.random.default_rng(0).integers(1, 10_000, SHAPE, dtype=np.uint16)
    return write_cog(tmp_path / "B04.tif", data), data


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


def scene(href, item_id="S2B_T31UCP_20250701", cloud_cover=0.1):
    return Scene(item_id, href, cloud_cover, "2025-07-01T10:56:29Z")


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


def item(item_id, cloud_cover):
    stac_item = pystac.Item(
        id=item_id,
        geometry=None,
        bbox=None,
        datetime=dt.datetime(2025, 7, 1, tzinfo=dt.UTC),
        properties={"eo:cloud_cover": cloud_cover},
    )
    stac_item.add_asset("red", asset(f"{item_id}/B04.tif", "B04"))
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
    (params,) = requests
    assert params["collections"] == ["sentinel-2-c1-l2a"]
    assert params["intersects"]["coordinates"] == [site.lon, site.lat]
    assert params["datetime"] == "2025-04-01/2025-09-30"
    assert params["query"] == {"eo:cloud_cover": {"lte": 5.0}}

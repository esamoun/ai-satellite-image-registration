import numpy as np
import pytest
import rasterio
from rasterio.transform import array_bounds, from_bounds
from rasterio.warp import transform_bounds

from satreg.georef import NOMINAL
from satreg.landcover import (
    NO_DATA,
    class_shares,
    fetch_landcover,
    read_landcover,
    read_on_grid,
    stable_ground,
    tile_name,
    tiles_for,
)

SHAPE = (64, 64)


def fake_tile(path, bounds, west_class=50, east_class=40):
    """A WorldCover-like tile over ``bounds`` (degrees): one class each side."""
    west, south, east, north = bounds
    rows, cols = 200, 200
    data = np.full((rows, cols), east_class, np.uint8)
    data[:, : cols // 2] = west_class
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=rows,
        width=cols,
        count=1,
        dtype="uint8",
        crs="EPSG:4326",
        transform=from_bounds(west, south, east, north, cols, rows),
        nodata=NO_DATA,
    ) as dst:
        dst.write(data, 1)


def chip_bounds_deg(margin=0.01):
    bounds = array_bounds(*SHAPE, NOMINAL.transform)
    west, south, east, north = transform_bounds(NOMINAL.crs, "EPSG:4326", *bounds)
    return west - margin, south - margin, east + margin, north + margin


@pytest.mark.parametrize(
    ("lat", "lon", "name"),
    [(48.2, 1.5, "N48E000"), (43.6, 5.4, "N42E003"), (-0.5, -0.5, "S03W003")],
)
def test_tiles_are_named_by_their_south_west_corner(lat, lon, name):
    assert tile_name(lat, lon) == name


def test_the_nominal_chip_falls_in_one_tile():
    assert tiles_for(NOMINAL, SHAPE) == ["N48E000"]


def test_the_land_cover_is_read_on_the_chip_grid(tmp_path):
    fake_tile(tmp_path / "N48E000.tif", chip_bounds_deg())

    classes = read_on_grid(NOMINAL, SHAPE, str(tmp_path / "{tile}.tif"))

    assert classes.shape == SHAPE
    assert set(np.unique(classes)) == {40, 50}
    # West is built-up, east is cropland.
    assert classes[:, 0].tolist() == [50] * SHAPE[0]
    assert classes[:, -1].tolist() == [40] * SHAPE[0]


def test_a_chip_no_tile_covers_is_an_error(tmp_path):
    with pytest.raises(LookupError):
        read_on_grid(NOMINAL, SHAPE, str(tmp_path / "{tile}.tif"))


def test_the_land_cover_is_cached(tmp_path):
    tile = tmp_path / "N48E000.tif"
    fake_tile(tile, chip_bounds_deg())
    url = str(tmp_path / "{tile}.tif")

    path = fetch_landcover("site", NOMINAL, SHAPE, tmp_path / "data", url)
    tile.unlink()

    assert fetch_landcover("site", NOMINAL, SHAPE, tmp_path / "data", url) == path
    assert read_landcover(path).shape == SHAPE


def test_stable_ground_is_eroded_away_from_other_classes_but_not_the_border():
    classes = np.full((9, 9), 40, np.uint8)
    classes[2:7, 1:5] = 50  # built-up, surrounded by cropland
    classes[:, 7:] = 60  # bare ground along the right border

    stable = stable_ground(classes)

    assert stable[3:6, 2:4].all()
    # The bare strip loses its column beside cropland, not its pixels on the
    # image border.
    assert stable[:, 8].all() and not stable[:, 7].any()
    assert stable.sum() == 6 + 9
    assert stable_ground(classes, erosion_px=0).sum() == 20 + 18


def test_class_shares_name_the_classes_present_and_sum_to_a_hundred():
    classes = np.full((10, 10), 50, np.uint8)
    classes[:3] = 80
    classes[9, :5] = NO_DATA
    classes[9, 5:] = 7  # not a WorldCover value

    shares = class_shares(classes)

    assert shares == {
        "no data": 5.0,
        "class 7": 5.0,
        "built-up": 60.0,
        "permanent water bodies": 30.0,
    }

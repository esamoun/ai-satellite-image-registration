"""Stable ground from an external land-cover map, ESA WorldCover 2021.

A pixel of a real pair is stable ground if WorldCover classes it as built-up or
as bare or sparsely vegetated: surfaces whose reflectance does not follow the
crop calendar or the canopy. The map is external to the methods compared, so it
does not favour any of them. It is read on the chip's own grid by nearest
neighbour, then eroded by a pixel, so a pixel next to a class boundary, where
the 10 m map and the 10 m chip do not share a grid, is left out. See
docs/decisions.md.
"""

import hashlib
import json
import logging
import math
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.errors import RasterioIOError
from rasterio.transform import array_bounds
from rasterio.vrt import WarpedVRT
from rasterio.warp import transform_bounds
from scipy import ndimage

from .georef import Georef
from .ingest import GDAL_HTTP_OPTIONS

logger = logging.getLogger(__name__)

# One 3 x 3 degree COG per tile, named by its south-west corner, on ESA's public
# bucket (no account needed).
WORLDCOVER_URL = (
    "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
    "ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
)

# Side of a WorldCover tile, in degrees.
TILE_DEG = 3

# WorldCover's value where it has no data, and outside every tile.
NO_DATA = 0

# WorldCover classes, by value.
CLASSES = {
    10: "tree cover",
    20: "shrubland",
    30: "grassland",
    40: "cropland",
    50: "built-up",
    60: "bare / sparse vegetation",
    70: "snow and ice",
    80: "permanent water bodies",
    90: "herbaceous wetland",
    95: "mangroves",
    100: "moss and lichen",
}

# Classes counted as stable ground: their reflectance does not follow a season.
STABLE_CLASSES = (50, 60)

# Pixels a stable area is eroded by, so a pixel next to another class is left out.
EROSION_PX = 1


def tile_name(lat: float, lon: float) -> str:
    """Name the WorldCover tile a point falls in.

    Args:
        lat: Latitude, in degrees.
        lon: Longitude, in degrees.

    Returns:
        The tile's name, e.g. ``"N48E000"``.
    """
    south = TILE_DEG * math.floor(lat / TILE_DEG)
    west = TILE_DEG * math.floor(lon / TILE_DEG)
    return (
        f"{'N' if south >= 0 else 'S'}{abs(south):02d}"
        f"{'E' if west >= 0 else 'W'}{abs(west):03d}"
    )


def tiles_for(georef: Georef, shape: tuple[int, int]) -> list[str]:
    """Name every WorldCover tile a grid overlaps.

    Args:
        georef: Map grid of the chip.
        shape: ``(rows, cols)`` of the chip.

    Returns:
        Tile names, south-west first.
    """
    bounds = array_bounds(*shape, georef.transform)
    west, south, east, north = transform_bounds(georef.crs, "EPSG:4326", *bounds)
    lats = range(math.floor(south / TILE_DEG), math.floor(north / TILE_DEG) + 1)
    lons = range(math.floor(west / TILE_DEG), math.floor(east / TILE_DEG) + 1)
    return [tile_name(TILE_DEG * a, TILE_DEG * o) for a in lats for o in lons]


def landcover_path(
    site: str, georef: Georef, shape: tuple[int, int], url: str, data_dir: Path
) -> Path:
    """Where the land cover of a chip is cached.

    Args:
        site: Site name.
        georef: Map grid of the chip.
        shape: ``(rows, cols)`` of the chip.
        url: Tile URL template the map is read from.
        data_dir: Root of downloaded data.

    Returns:
        ``data_dir/landcover/<site>_<hash>.tif``, the hash of the grid and URL.
    """
    params = {
        "crs": georef.crs.to_wkt(),
        "transform": list(georef.transform)[:6],
        "shape": list(shape),
        "url": url,
    }
    key = hashlib.sha256(json.dumps(params).encode()).hexdigest()[:12]
    return data_dir / "landcover" / f"{site}_{key}.tif"


def read_on_grid(
    georef: Georef, shape: tuple[int, int], url: str = WORLDCOVER_URL
) -> np.ndarray:
    """Read WorldCover on a chip's grid, by nearest neighbour.

    Args:
        georef: Map grid of the chip.
        shape: ``(rows, cols)`` of the chip.
        url: Tile URL template, with a ``{tile}`` field.

    Returns:
        WorldCover class of each chip pixel, ``NO_DATA`` where no tile covers it.

    Raises:
        LookupError: If no tile covers any of the chip.
    """
    out = np.full(shape, NO_DATA, np.uint8)
    with rasterio.Env(**GDAL_HTTP_OPTIONS):
        for tile in tiles_for(georef, shape):
            href = url.format(tile=tile)
            try:
                src = rasterio.open(href)
            except RasterioIOError:
                # WorldCover has no tile over open sea.
                logger.info("no WorldCover tile at %s", href)
                continue
            with (
                src,
                WarpedVRT(
                    src,
                    crs=georef.crs,
                    transform=georef.transform,
                    width=shape[1],
                    height=shape[0],
                    resampling=Resampling.nearest,
                    src_nodata=NO_DATA,
                    nodata=NO_DATA,
                ) as vrt,
            ):
                data = vrt.read(1)
            out = np.where(out == NO_DATA, data, out)
    if (out == NO_DATA).all():
        raise LookupError(f"no WorldCover tile covers the chip ({url})")
    return out


def fetch_landcover(
    site: str,
    georef: Georef,
    shape: tuple[int, int],
    data_dir: Path,
    url: str = WORLDCOVER_URL,
) -> Path:
    """Return the cached land cover of a chip, reading it first if needed.

    Args:
        site: Site name.
        georef: Map grid of the chip.
        shape: ``(rows, cols)`` of the chip.
        data_dir: Root of downloaded data.
        url: Tile URL template, replaced by a local file in tests.

    Returns:
        Path of a single-band GeoTIFF on the chip's grid.
    """
    path = landcover_path(site, georef, shape, url, data_dir)
    if path.exists():
        return path
    classes = read_on_grid(georef, shape, url)
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(".partial")
    profile = {
        "driver": "GTiff",
        "dtype": "uint8",
        "count": 1,
        "height": shape[0],
        "width": shape[1],
        "crs": georef.crs,
        "transform": georef.transform,
        "nodata": NO_DATA,
    }
    with rasterio.open(partial, "w", **profile) as dst:
        dst.write(classes, 1)
        dst.update_tags(site=site, source=url, product="ESA WorldCover 2021 v200")
    # Renamed only once complete, so an interrupted read is not a cache hit.
    partial.replace(path)
    logger.info("%s: land cover %s", site, path)
    return path


def read_landcover(path: Path) -> np.ndarray:
    """Load a cached land cover.

    Args:
        path: GeoTIFF written by ``fetch_landcover``.

    Returns:
        WorldCover class of each chip pixel.
    """
    with rasterio.open(path) as src:
        return src.read(1)


def stable_ground(
    classes: np.ndarray,
    stable: tuple[int, ...] = STABLE_CLASSES,
    erosion_px: int = EROSION_PX,
) -> np.ndarray:
    """Pixels of stable ground, away from the edges of their class.

    Args:
        classes: WorldCover class of each pixel.
        stable: Classes counted as stable.
        erosion_px: Pixels the stable area is eroded by. The image border does
            not erode it: it is not a class boundary.

    Returns:
        Boolean array, same shape.
    """
    mask = np.isin(classes, stable)
    if erosion_px == 0:
        return mask
    return ndimage.binary_erosion(
        mask, structure=np.ones((3, 3), bool), iterations=erosion_px, border_value=1
    )

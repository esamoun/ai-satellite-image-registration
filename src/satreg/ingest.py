"""Sentinel-2 chips: found through STAC, read from the native COG, cached on disk.

A chip is a window of the source COG taken on its own pixel grid: whole pixels,
no resampling and no reprojection. It keeps the source CRS and a geotransform
that is the source one offset by a whole number of pixels, so the sub-pixel
geometry the benchmark measures is the sensor product's. See docs/decisions.md.
"""

import hashlib
import json
import logging
import math
import warnings
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pystac
import rasterio
from pystac_client import Client
from rasterio.warp import transform as transform_coords
from rasterio.windows import Window

from .sites import Catalogue, Site

logger = logging.getLogger(__name__)

# Scenes tried, least cloudy first, before giving up on a site. A scene is skipped
# when the chip falls off its tile or into its no-data area.
MAX_CANDIDATES = 10

# Upper bound on items requested from the catalogue. Half a year over one point
# is about 150 items (two relative orbits, sometimes two overlapping tiles), and
# the cloud filter keeps a fraction of them.
MAX_ITEMS = 200

# Read only the COG itself over HTTP, not a listing of its directory, and retry
# transient errors.
GDAL_HTTP_OPTIONS = {
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
    "GDAL_HTTP_MAX_RETRY": "3",
    "GDAL_HTTP_RETRY_DELAY": "1",
}


@dataclass(frozen=True)
class Scene:
    """A candidate acquisition for a site.

    Attributes:
        item_id: STAC item id.
        href: URL or path of the COG holding the site's band.
        cloud_cover: Scene cloud cover, in percent.
        datetime: Acquisition time, ISO 8601.
    """

    item_id: str
    href: str
    cloud_cover: float
    datetime: str


Search = Callable[[Site, Catalogue], list[Scene]]
"""Finds the candidate scenes of a site, least cloudy first."""


class ChipUnavailable(Exception):
    """A scene cannot provide a complete chip for a site."""


def band_href(assets: Mapping[str, pystac.Asset], band: str) -> str:
    """Find the single-band asset holding ``band``.

    Multi-band assets such as the true-colour ``visual`` image also list the band,
    but are 8-bit renderings, so they are skipped.

    Args:
        assets: Assets of a STAC item.
        band: Band name, e.g. ``B04``.

    Returns:
        The asset's href.

    Raises:
        ValueError: If no single-band asset holds ``band``.
    """
    for asset in assets.values():
        bands = asset.extra_fields.get("eo:bands") or asset.extra_fields.get("bands")
        if bands and len(bands) == 1 and bands[0].get("name") == band:
            return asset.href
    raise ValueError(f"no single-band asset for {band} among {sorted(assets)}")


def stac_search(site: Site, catalogue: Catalogue) -> list[Scene]:
    """Search the catalogue for scenes covering the site centre.

    Args:
        site: Site to search for.
        catalogue: STAC API and collection.

    Returns:
        Scenes under the site's cloud limit, least cloudy first, ties broken by
        item id so the choice does not depend on the order the API returns.
    """
    search = Client.open(catalogue.url).search(
        collections=[catalogue.collection],
        intersects={"type": "Point", "coordinates": [site.lon, site.lat]},
        datetime=f"{site.start.isoformat()}/{site.end.isoformat()}",
        query={"eo:cloud_cover": {"lte": site.max_cloud}},
        max_items=MAX_ITEMS,
    )
    with warnings.catch_warnings():
        # pystac tries to migrate the storage extension of every item and warns
        # that it cannot parse plain HTTPS hrefs. Harmless, and not ours to fix.
        warnings.filterwarnings("ignore", "Could not parse bucket", UserWarning)
        items = list(search.items())
    scenes = [
        Scene(
            item_id=item.id,
            href=band_href(item.assets, site.band),
            cloud_cover=float(item.properties["eo:cloud_cover"]),
            datetime=item.datetime.isoformat(),
        )
        for item in items
    ]
    return sorted(scenes, key=lambda s: (s.cloud_cover, s.item_id))


def read_window(href: str, site: Site) -> tuple[np.ndarray, dict]:
    """Read the chip of a site from one COG, on the COG's own pixel grid.

    The site centre is projected into the COG's CRS to find the pixel it falls
    in. That pixel ends up at ``(chip_px // 2, chip_px // 2)`` in the chip, and
    only whole source pixels are read.

    Args:
        href: URL or path of a single-band COG.
        site: Site whose chip to read.

    Returns:
        The chip, and a GeoTIFF profile carrying the source CRS, the chip's
        geotransform, dtype and no-data value.

    Raises:
        ChipUnavailable: If the chip leaves the raster or contains no-data pixels.
    """
    with rasterio.Env(**GDAL_HTTP_OPTIONS), rasterio.open(href) as src:
        xs, ys = transform_coords("EPSG:4326", src.crs, [site.lon], [site.lat])
        col, row = ~src.transform @ (xs[0], ys[0])
        half = site.chip_px // 2
        left, top = math.floor(col) - half, math.floor(row) - half
        if (
            left < 0
            or top < 0
            or left + site.chip_px > src.width
            or top + site.chip_px > src.height
        ):
            raise ChipUnavailable("the chip leaves the raster")

        window = Window(left, top, site.chip_px, site.chip_px)
        data = src.read(1, window=window)
        if src.nodata is not None and (missing := int(np.sum(data == src.nodata))):
            raise ChipUnavailable(f"the chip has {missing} no-data pixels")

        profile = {
            "driver": "GTiff",
            "width": site.chip_px,
            "height": site.chip_px,
            "count": 1,
            "dtype": data.dtype,
            "crs": src.crs,
            "transform": src.window_transform(window),
            "nodata": src.nodata,
            "compress": "deflate",
        }
    return data, profile


def cache_path(site: Site, catalogue: Catalogue, data_dir: Path) -> Path:
    """Where the chip of a site is cached.

    The file name hashes every parameter that decides which chip is read, so
    editing a site in the configuration fetches a new chip instead of silently
    reusing the old one.

    Args:
        site: Site of the chip.
        catalogue: Catalogue the chip comes from.
        data_dir: Root of downloaded data.

    Returns:
        ``data_dir/chips/<site>/<band>_<hash>.tif``.
    """
    params = {**asdict(site), **asdict(catalogue)}
    key = hashlib.sha256(json.dumps(params, default=str).encode()).hexdigest()[:12]
    return data_dir / "chips" / site.name / f"{site.band}_{key}.tif"


def fetch_chip(
    site: Site, catalogue: Catalogue, data_dir: Path, search: Search = stac_search
) -> Path:
    """Return the cached chip of a site, fetching it first if it is not cached.

    A cached chip is returned without any network call. Otherwise candidate scenes
    are tried least cloudy first, and the first complete chip is written, with
    the scene it came from recorded in the GeoTIFF tags.

    Args:
        site: Site of the chip.
        catalogue: Catalogue to search.
        data_dir: Root of downloaded data.
        search: Scene search, replaced by a fake in tests.

    Returns:
        Path of the chip GeoTIFF.

    Raises:
        LookupError: If no scene of the first ``MAX_CANDIDATES`` gives a complete
            chip.
    """
    path = cache_path(site, catalogue, data_dir)
    if path.exists():
        logger.info("%s: cached chip %s", site.name, path)
        return path

    scenes = search(site, catalogue)
    for scene in scenes[:MAX_CANDIDATES]:
        try:
            data, profile = read_window(scene.href, site)
        except ChipUnavailable as exc:
            logger.info("%s: skipping %s: %s", site.name, scene.item_id, exc)
            continue

        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_suffix(".partial")
        with rasterio.open(partial, "w", **profile) as dst:
            dst.write(data, 1)
            dst.update_tags(
                site=site.name,
                band=site.band,
                item_id=scene.item_id,
                datetime=scene.datetime,
                cloud_cover=str(scene.cloud_cover),
                source=scene.href,
            )
        # Renamed only once complete, so an interrupted download is not a cache hit.
        partial.replace(path)
        logger.info("%s: fetched %s from %s", site.name, path, scene.item_id)
        return path

    raise LookupError(
        f"{site.name}: none of {min(len(scenes), MAX_CANDIDATES)} scenes under "
        f"{site.max_cloud} % cloud between {site.start} and {site.end} gives a "
        f"complete {site.chip_px} px chip"
    )


def read_chip(path: Path) -> np.ndarray:
    """Load a cached chip as a 2-D array of its stored digital numbers.

    Args:
        path: Chip GeoTIFF written by ``fetch_chip``.

    Returns:
        The chip's single band.
    """
    with rasterio.open(path) as src:
        return src.read(1)

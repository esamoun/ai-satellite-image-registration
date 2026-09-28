"""Sentinel-2 chips: found through STAC, read from the native COG, cached on disk.

A chip is a window of the source COG taken on its own pixel grid: whole pixels,
no resampling and no reprojection. It keeps the source CRS and a geotransform
that is the source one offset by a whole number of pixels, so the sub-pixel
geometry the benchmark measures is the sensor product's. A scene is only used if
its scene classification (SCL) shows the chip window clear enough of cloud and
cloud shadow. See docs/decisions.md.
"""

import datetime as dt
import hashlib
import json
import logging
import math
import re
import warnings
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pystac
import rasterio
from pystac_client import Client
from rasterio.transform import array_bounds
from rasterio.warp import transform as transform_coords
from rasterio.windows import Window, from_bounds

from .georef import Georef
from .sites import Catalogue, Site

logger = logging.getLogger(__name__)

# Scenes tried, least cloudy first, before giving up on a site. A scene is skipped
# when the chip falls off its tile or into its no-data area.
MAX_CANDIDATES = 10

# Classes of the Sentinel-2 L2A scene classification (SCL) counted over a chip.
# Cloud is medium and high probability cloud and thin cirrus.
SCL_CLASSES = {
    "cloud": (8, 9, 10),
    "shadow": (3,),
    "snow": (11,),
    "water": (6,),
}

# Classes that disqualify a chip, by share of its pixels (Site.max_chip_cloud).
SCL_REJECTED = ("cloud", "shadow")

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
        scl_href: URL or path of the scene classification COG.
        platform: Satellite, e.g. ``sentinel-2b``; empty if the catalogue does
            not say.
        tile: MGRS tile as the catalogue's ``grid:code`` gives it, e.g.
            ``MGRS-31UCP``; empty if it does not say.
        relative_orbit: Relative orbit number, 0 if unknown.
    """

    item_id: str
    href: str
    cloud_cover: float
    datetime: str
    scl_href: str
    platform: str = ""
    tile: str = ""
    relative_orbit: int = 0

    @property
    def date(self) -> dt.date:
        """Acquisition date, in UTC."""
        return dt.date.fromisoformat(self.datetime[:10])


Search = Callable[[Site, Catalogue], list[Scene]]
"""Finds the candidate scenes of a site, least cloudy first."""

BandHrefs = Callable[[str, Catalogue, Sequence[str]], dict[str, str]]
"""Finds the single-band COG of each named band in one item, by item id."""

# Bands a multi-band chip may hold: the 10 m bands, which share the grid of the
# site's chip, so none is resampled. See docs/decisions.md.
TEN_METRE_BANDS = ("B02", "B03", "B04", "B08")


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


def scl_href(assets: Mapping[str, pystac.Asset]) -> str:
    """Find the scene classification (SCL) asset of an L2A item.

    Args:
        assets: Assets of a STAC item.

    Returns:
        The asset's href.

    Raises:
        ValueError: If the item has no ``scl`` asset.
    """
    if "scl" not in assets:
        raise ValueError(f"no scene classification (scl) among {sorted(assets)}")
    return assets["scl"].href


def relative_orbit(properties: Mapping) -> int:
    """Relative orbit of a Sentinel-2 item, 0 if its properties do not give it.

    Earth Search's Collection 1 items have no ``sat:relative_orbit``, but the
    orbit is in the product name, e.g. ``S2B_MSIL2A_..._R094_T31UCP_...``.

    Args:
        properties: Properties of a STAC item.

    Returns:
        The relative orbit number.
    """
    if "sat:relative_orbit" in properties:
        return int(properties["sat:relative_orbit"])
    found = re.search(r"_R(\d{3})_", properties.get("s2:product_uri", ""))
    return int(found.group(1)) if found else 0


def stac_scenes(
    site: Site,
    catalogue: Catalogue,
    start: dt.date,
    end: dt.date,
    max_cloud: float,
    tile: str | None = None,
) -> list[Scene]:
    """Search the catalogue for scenes covering the site centre.

    Args:
        site: Site to search for.
        catalogue: STAC API and collection.
        start: First acquisition date, inclusive.
        end: Last acquisition date, inclusive.
        max_cloud: Highest scene cloud cover, in percent.
        tile: Only scenes of this ``grid:code``, e.g. ``MGRS-31UCP``, if given.

    Returns:
        Scenes under the cloud limit, least cloudy first, ties broken by item id
        so the order does not depend on the order the API returns.
    """
    query: dict[str, dict] = {"eo:cloud_cover": {"lte": max_cloud}}
    if tile is not None:
        query["grid:code"] = {"eq": tile}
    search = Client.open(catalogue.url).search(
        collections=[catalogue.collection],
        intersects={"type": "Point", "coordinates": [site.lon, site.lat]},
        datetime=f"{start.isoformat()}/{end.isoformat()}",
        query=query,
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
            scl_href=scl_href(item.assets),
            platform=item.properties.get("platform", ""),
            tile=item.properties.get("grid:code", ""),
            relative_orbit=relative_orbit(item.properties),
        )
        for item in items
    ]
    return sorted(scenes, key=lambda s: (s.cloud_cover, s.item_id))


def stac_search(site: Site, catalogue: Catalogue) -> list[Scene]:
    """Search the catalogue for scenes covering the site centre.

    Args:
        site: Site to search for.
        catalogue: STAC API and collection.

    Returns:
        Scenes of the site's date range under its cloud limit, least cloudy
        first, ties broken by item id.
    """
    return stac_scenes(site, catalogue, site.start, site.end, site.max_cloud)


def stac_band_hrefs(
    item_id: str, catalogue: Catalogue, bands: Sequence[str]
) -> dict[str, str]:
    """Find the single-band COG of each band in one item of the catalogue.

    Args:
        item_id: STAC item id, as a chip's ``item_id`` tag records it.
        catalogue: STAC API and collection.
        bands: Band names, e.g. ``("B04", "B08")``.

    Returns:
        Band name to the href of its COG.

    Raises:
        LookupError: If the collection has no item of that id.
        ValueError: If the item has no single-band asset for a band.
    """
    search = Client.open(catalogue.url).search(
        collections=[catalogue.collection], ids=[item_id], max_items=1
    )
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", "Could not parse bucket", UserWarning)
        items = list(search.items())
    if not items:
        raise LookupError(f"no item {item_id} in {catalogue.collection}")
    return {band: band_href(items[0].assets, band) for band in bands}


def read_window(
    href: str, site: Site, allow_nodata: bool = False
) -> tuple[np.ndarray, dict]:
    """Read the chip of a site from one COG, on the COG's own pixel grid.

    The site centre is projected into the COG's CRS to find the pixel it falls
    in. That pixel ends up at ``(chip_px // 2, chip_px // 2)`` in the chip, and
    only whole source pixels are read.

    Args:
        href: URL or path of a single-band COG.
        site: Site whose chip to read.
        allow_nodata: Return a chip with no-data pixels instead of refusing it,
            for a caller that masks them.

    Returns:
        The chip, and a GeoTIFF profile carrying the source CRS, the chip's
        geotransform, dtype and no-data value.

    Raises:
        ChipUnavailable: If the chip leaves the raster, or contains no-data
            pixels and ``allow_nodata`` is false.
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
        if (
            not allow_nodata
            and src.nodata is not None
            and (missing := int(np.sum(data == src.nodata)))
        ):
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


def chip_cover(href: str, profile: Mapping) -> dict[str, float]:
    """Share of each counted SCL class over the ground a chip covers.

    The classification is on the 20 m grid of the chip's tile, whose pixels are
    whole pairs of 10 m pixels. The 20 m pixels read are every one the chip
    touches, so when the chip starts on an odd 10 m pixel a half pixel of margin
    is counted on each side.

    Args:
        href: URL or path of the scene classification COG.
        profile: GeoTIFF profile of the chip, as ``read_window`` returns it.

    Returns:
        Class name of ``SCL_CLASSES`` to its share of the pixels read, in percent.

    Raises:
        ChipUnavailable: If the classification is not on the chip's CRS or does
            not cover the chip.
    """
    bounds = array_bounds(profile["height"], profile["width"], profile["transform"])
    with rasterio.Env(**GDAL_HTTP_OPTIONS), rasterio.open(href) as src:
        if src.crs != profile["crs"]:
            raise ChipUnavailable(f"the classification is in {src.crs}")
        window = from_bounds(*bounds, transform=src.transform)
        # Rounded first so that float noise on an exact edge adds no pixel.
        left = math.floor(round(window.col_off, 6))
        top = math.floor(round(window.row_off, 6))
        right = math.ceil(round(window.col_off + window.width, 6))
        bottom = math.ceil(round(window.row_off + window.height, 6))
        if left < 0 or top < 0 or right > src.width or bottom > src.height:
            raise ChipUnavailable("the classification does not cover the chip")
        scl = src.read(1, window=Window(left, top, right - left, bottom - top))
    return {
        name: 100 * float(np.isin(scl, classes).mean())
        for name, classes in SCL_CLASSES.items()
    }


def read_scl(href: str, profile: Mapping) -> np.ndarray:
    """The scene classification on the chip's own grid.

    Each chip pixel takes the class of the classification pixel its centre falls
    in. On a Sentinel-2 tile the 20 m grid is made of whole pairs of 10 m pixels,
    so this is an exact lookup, never an interpolation between classes.

    Args:
        href: URL or path of the scene classification COG.
        profile: GeoTIFF profile of the chip, as ``read_window`` returns it.

    Returns:
        Class codes, of the chip's shape, as ``uint8``.

    Raises:
        ChipUnavailable: If the classification is not on the chip's CRS or does
            not cover the chip.
    """
    rows, cols = profile["height"], profile["width"]
    centres = profile["transform"] @ (
        np.arange(cols)[None, :] + 0.5,
        np.arange(rows)[:, None] + 0.5,
    )
    with rasterio.Env(**GDAL_HTTP_OPTIONS), rasterio.open(href) as src:
        if src.crs != profile["crs"]:
            raise ChipUnavailable(f"the classification is in {src.crs}")
        col, row = ~src.transform @ centres
        col, row = np.floor(col).astype(int), np.floor(row).astype(int)
        left, top = int(col.min()), int(row.min())
        right, bottom = int(col.max()) + 1, int(row.max()) + 1
        if left < 0 or top < 0 or right > src.width or bottom > src.height:
            raise ChipUnavailable("the classification does not cover the chip")
        scl = src.read(1, window=Window(left, top, right - left, bottom - top))
    return scl[row - top, col - left].astype(np.uint8)


def cache_path(site: Site, catalogue: Catalogue, data_dir: Path) -> Path:
    """Where the chip of a site is cached.

    The file name hashes every parameter that decides which chip is read, so
    editing a site in the configuration fetches a new chip instead of silently
    reusing the old one. Whether the site is held out does not decide it.

    Args:
        site: Site of the chip.
        catalogue: Catalogue the chip comes from.
        data_dir: Root of downloaded data.

    Returns:
        ``data_dir/chips/<site>/<band>_<hash>.tif``.
    """
    return data_dir / "chips" / site.name / f"{site.band}_{_key(site, catalogue)}.tif"


def _key(site: Site, catalogue: Catalogue, **extra: object) -> str:
    """Hash every parameter that decides which chip is read, and ``extra``."""
    params = {**asdict(site), **asdict(catalogue), **extra}
    del params["held_out"]
    return hashlib.sha256(json.dumps(params, default=str).encode()).hexdigest()[:12]


def bands_cache_path(
    site: Site, catalogue: Catalogue, data_dir: Path, bands: Sequence[str]
) -> Path:
    """Where the multi-band chip of a site is cached.

    Args:
        site: Site of the chip.
        catalogue: Catalogue the chip comes from.
        data_dir: Root of downloaded data.
        bands: Bands of the chip, in the order it stores them.

    Returns:
        ``data_dir/chips/<site>/<band>-<band>..._<hash>.tif``, the hash covering
        the band list as well as the site's own chip parameters.
    """
    key = _key(site, catalogue, bands=list(bands))
    return data_dir / "chips" / site.name / f"{'-'.join(bands)}_{key}.tif"


def fetch_chip(
    site: Site, catalogue: Catalogue, data_dir: Path, search: Search = stac_search
) -> Path:
    """Return the cached chip of a site, fetching it first if it is not cached.

    A cached chip is returned without any network call. Otherwise candidate scenes
    are tried least cloudy first, and the first chip that is complete and has at
    most ``site.max_chip_cloud`` percent of cloud and cloud shadow is written,
    with the scene it came from and the chip's share of each counted SCL class
    recorded in the GeoTIFF tags.

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
            cover = chip_cover(scene.scl_href, profile)
            if (rejected := sum(cover[name] for name in SCL_REJECTED)) > (
                site.max_chip_cloud
            ):
                raise ChipUnavailable(
                    f"{rejected:.2f} % of the chip is cloud or cloud shadow "
                    f"(limit {site.max_chip_cloud} %)"
                )
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
                **{f"chip_{name}_pct": f"{share:.3f}" for name, share in cover.items()},
            )
        # Renamed only once complete, so an interrupted download is not a cache hit.
        partial.replace(path)
        logger.info("%s: fetched %s from %s", site.name, path, scene.item_id)
        return path

    raise LookupError(
        f"{site.name}: none of {min(len(scenes), MAX_CANDIDATES)} scenes under "
        f"{site.max_cloud} % cloud between {site.start} and {site.end} gives a "
        f"complete {site.chip_px} px chip under {site.max_chip_cloud} % cloud and "
        "cloud shadow"
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


def read_georef(path: Path) -> Georef:
    """Read the map grid of a cached chip.

    Args:
        path: Chip GeoTIFF written by ``fetch_chip``.

    Returns:
        The chip's CRS and geotransform, those of its source COG offset by whole
        pixels.
    """
    with rasterio.open(path) as src:
        return Georef(src.crs, src.transform)


def check_bands(bands: Sequence[str]) -> None:
    """Refuse a band list a multi-band chip cannot hold.

    Args:
        bands: Band names.

    Raises:
        ValueError: If the list is empty, repeats a band, or names a band outside
            ``TEN_METRE_BANDS``.
    """
    if not bands:
        raise ValueError("a multi-band chip needs at least one band")
    if len(set(bands)) != len(bands):
        raise ValueError(f"bands repeat: {list(bands)}")
    if unknown := [band for band in bands if band not in TEN_METRE_BANDS]:
        raise ValueError(
            f"band {unknown[0]} is not a 10 m band ({', '.join(TEN_METRE_BANDS)}): "
            "it would need resampling onto the chip's grid"
        )


def fetch_bands(
    site: Site,
    catalogue: Catalogue,
    data_dir: Path,
    bands: Sequence[str],
    search: Search = stac_search,
    hrefs: BandHrefs = stac_band_hrefs,
) -> Path:
    """Return the cached multi-band chip of a site, fetching it first if needed.

    The bands are read from the scene of the site's own chip (``fetch_chip``,
    which chooses it by cloud), over the same window, so each band of the chip
    covers the same ground on the same grid, and the site's own band is the
    single-band chip to the digital number.

    Args:
        site: Site of the chip.
        catalogue: Catalogue to search.
        data_dir: Root of downloaded data.
        bands: Bands to hold, among ``TEN_METRE_BANDS``, in the order stored.
        search: Scene search for the site's own chip, replaced in tests.
        hrefs: Band lookup in the chosen item, replaced in tests.

    Returns:
        Path of the chip GeoTIFF, one band per name, each band described by it.

    Raises:
        ValueError: If the band list is invalid, see ``check_bands``.
        ChipUnavailable: If a band's window is not on the grid of the site's
            chip or has no-data pixels.
    """
    check_bands(bands)
    path = bands_cache_path(site, catalogue, data_dir, bands)
    if path.exists():
        logger.info("%s: cached chip %s", site.name, path)
        return path

    chip = fetch_chip(site, catalogue, data_dir, search)
    with rasterio.open(chip) as src:
        item_id = src.tags()["item_id"]
        grid = (src.crs, src.transform)
    sources = hrefs(item_id, catalogue, bands)
    layers = []
    for band in bands:
        data, band_profile = read_window(sources[band], site)
        if (band_profile["crs"], band_profile["transform"]) != grid:
            raise ChipUnavailable(
                f"{band} of {item_id} is not on the grid of the {site.band} chip"
            )
        layers.append(data)
    # The profile of a window read, as ``fetch_chip`` writes it, not the chip's
    # own, whose block layout does not apply to an untiled file.
    profile = band_profile

    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(".partial")
    profile.update(count=len(bands), dtype=layers[0].dtype, compress="deflate")
    with rasterio.open(partial, "w", **profile) as dst:
        for index, (band, data) in enumerate(zip(bands, layers, strict=True), 1):
            dst.write(data, index)
            dst.set_band_description(index, band)
        dst.update_tags(
            site=site.name,
            bands=",".join(bands),
            item_id=item_id,
            chip=chip.name,
            sources=json.dumps(sources),
        )
    partial.replace(path)
    logger.info("%s: fetched %s from %s", site.name, path, item_id)
    return path


def read_bands(path: Path) -> dict[str, np.ndarray]:
    """Load a multi-band chip as one 2-D array per band.

    Args:
        path: Chip GeoTIFF written by ``fetch_bands``.

    Returns:
        Band name to its stored digital numbers, in the order stored.
    """
    with rasterio.open(path) as src:
        return {band: src.read(index) for index, band in enumerate(src.descriptions, 1)}

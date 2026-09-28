"""Real multi-temporal pairs: Sentinel-2 acquisitions of one site, on one grid.

A site's series starts from the scene of its benchmark chip, the anchor, and adds
one date per rule of the series configuration: the clear date nearest a target
offset from the anchor, on the anchor's tile and relative orbit. Two dates then
differ by what the product leaves (residual misregistration, season, ground
change), not by viewing geometry. Every date is the same window of the tile grid
as the anchor, so the images of a pair share one geotransform and a pixel of one
is the same ground as the pixel of the other, up to what the product leaves. A
real pair has no ground truth. See docs/decisions.md.
"""

import datetime as dt
import hashlib
import itertools
import json
import logging
import tomllib
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import rasterio

from .georef import Georef
from .ingest import (
    SCL_CLASSES,
    SCL_REJECTED,
    ChipUnavailable,
    Scene,
    chip_cover,
    fetch_chip,
    read_scl,
    read_window,
    stac_scenes,
)
from .sites import Catalogue, Site

logger = logging.getLogger(__name__)

# Role of the date every series starts from: the scene of the site's chip.
ANCHOR = "anchor"

# SCL class of pixels without data. A date's no-data pixels in the band are set
# to it, whatever the classification says there.
SCL_NO_DATA = 0

# SCL classes that hide the ground of a date: cloud and cloud shadow, the classes
# that disqualify a chip, and no data. A few no-data pixels do not disqualify a
# date as they do a benchmark chip: they are hidden like cloud and count against
# the same limit.
HIDDEN = (
    *(code for name in SCL_REJECTED for code in SCL_CLASSES[name]),
    SCL_NO_DATA,
)

Candidates = Callable[
    [Site, Catalogue, dt.date, dt.date, float, str | None], list[Scene]
]
"""Finds the scenes covering a site between two dates, under a scene cloud limit,
on one tile if one is named: ``stac_scenes`` or a fake in tests."""


@dataclass(frozen=True)
class DateRule:
    """Which date of the series a role takes.

    Attributes:
        offset_days: Target date, in days after the anchor.
        within_days: Largest distance from the target accepted, in days.
    """

    offset_days: int
    within_days: int

    def __post_init__(self) -> None:
        if self.within_days < 0:
            raise ValueError(f"within_days must be >= 0, got {self.within_days}")


@dataclass(frozen=True)
class SeriesConfig:
    """Contents of the series configuration file.

    Attributes:
        sites: Sites whose series are built, by name.
        max_scene_cloud: Highest scene cloud cover of a candidate date, in
            percent. The chip's own classification decides; this only bounds how
            many scenes are looked at.
        dates: Role to the rule that picks its date, in file order. Roles are
            filled in that order, and a date taken by one role is not given to
            another.
    """

    sites: tuple[str, ...]
    max_scene_cloud: float
    dates: dict[str, DateRule]


def load_series_config(path: Path) -> SeriesConfig:
    """Read the series configuration file.

    Args:
        path: TOML file with a ``[series]`` table holding ``sites`` and
            ``max_scene_cloud``, and a ``[series.dates]`` table of
            ``role = { offset_days = ..., within_days = ... }``.

    Returns:
        The parsed configuration.

    Raises:
        ValueError: If a table or key is missing, unknown or invalid.
    """
    with path.open("rb") as f:
        raw = tomllib.load(f)
    table = raw.get("series")
    if not table or not table.get("dates") or not table.get("sites"):
        raise ValueError(f"{path} needs a [series] table with sites and dates")
    unknown = sorted(set(table) - {"sites", "max_scene_cloud", "dates"})
    if unknown:
        raise ValueError(f"{path}: unknown [series] key {unknown[0]!r}")
    if ANCHOR in table["dates"]:
        raise ValueError(f"{path}: {ANCHOR!r} is the chip's own date, not a rule")
    dates = {}
    for role, rule in table["dates"].items():
        try:
            dates[role] = DateRule(**rule)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{path}: date {role}: {exc}") from exc
    max_scene_cloud = float(table.get("max_scene_cloud", 100.0))
    if not 0 <= max_scene_cloud <= 100:
        raise ValueError(f"{path}: max_scene_cloud must be in [0, 100]")
    return SeriesConfig(tuple(table["sites"]), max_scene_cloud, dates)


@dataclass(frozen=True)
class Acquisition:
    """One date of a series.

    Attributes:
        role: ``ANCHOR`` or the role of the date rule that picked it.
        image: The chip, in the product's digital numbers.
        scl: Scene classification on the chip's grid, same shape as ``image``.
        georef: Map grid of the chip.
        item_id: STAC item id of the scene.
        datetime: Acquisition time, UTC.
        platform: Satellite, e.g. ``sentinel-2b``.
    """

    role: str
    image: np.ndarray
    scl: np.ndarray
    georef: Georef
    item_id: str
    datetime: dt.datetime
    platform: str

    @property
    def hidden(self) -> np.ndarray:
        """Pixels whose ground this date does not show: cloud or cloud shadow."""
        return np.isin(self.scl, HIDDEN)


@dataclass(frozen=True)
class RealPair:
    """Two acquisitions of the same ground on the same grid, without ground truth.

    Attributes:
        reference: Reference image, the earlier date.
        moving: Moving image, the later date, same shape as ``reference``.
        georef: Map grid of both images.
        cloud: Pixels hidden by cloud or cloud shadow on either date.
        roles: Roles of the reference and moving dates.
        dates: Acquisition times of the reference and moving dates.
        scene_ids: STAC item ids of the reference and moving scenes.
        platforms: Satellites of the reference and moving dates.
    """

    reference: np.ndarray
    moving: np.ndarray
    georef: Georef
    cloud: np.ndarray
    roles: tuple[str, str]
    dates: tuple[dt.datetime, dt.datetime]
    scene_ids: tuple[str, str]
    platforms: tuple[str, str]

    @property
    def cloud_fraction(self) -> float:
        """Share of pixels hidden on either date."""
        return float(self.cloud.mean())

    @property
    def valid(self) -> np.ndarray:
        """Pixels whose ground both dates show."""
        return ~self.cloud

    @property
    def gap_days(self) -> int:
        """Days between the two acquisitions."""
        return (self.dates[1].date() - self.dates[0].date()).days


def make_pair(reference: Acquisition, moving: Acquisition) -> RealPair:
    """Pair two acquisitions of one series.

    Args:
        reference: Acquisition registered to.
        moving: Acquisition registered.

    Returns:
        The pair, its cloud mask the union of the two dates' hidden pixels.

    Raises:
        ValueError: If the two chips are not on the same grid.
    """
    if reference.image.shape != moving.image.shape or reference.georef != (
        moving.georef
    ):
        raise ValueError(
            f"{reference.item_id} and {moving.item_id} are not on the same grid: "
            f"{reference.georef} {reference.image.shape} against {moving.georef} "
            f"{moving.image.shape}"
        )
    return RealPair(
        reference=reference.image,
        moving=moving.image,
        georef=reference.georef,
        cloud=reference.hidden | moving.hidden,
        roles=(reference.role, moving.role),
        dates=(reference.datetime, moving.datetime),
        scene_ids=(reference.item_id, moving.item_id),
        platforms=(reference.platform, moving.platform),
    )


def chronological(series: list[Acquisition]) -> list[Acquisition]:
    """The acquisitions of a series, earliest first."""
    return sorted(series, key=lambda a: a.datetime)


def pairs(series: list[Acquisition]) -> list[RealPair]:
    """Every pair of a series, the earlier date as reference.

    Args:
        series: Acquisitions of one site.

    Returns:
        One pair per two acquisitions, in chronological order of reference,
        then of moving date.
    """
    return [
        make_pair(a, b) for a, b in itertools.combinations(chronological(series), 2)
    ]


def triplets(
    series: list[Acquisition],
) -> list[tuple[Acquisition, Acquisition, Acquisition]]:
    """Every three acquisitions of a series, each triplet in chronological order.

    Args:
        series: Acquisitions of one site.

    Returns:
        The triplets, for cycle consistency.
    """
    return list(itertools.combinations(chronological(series), 3))


def series_path(
    site: Site, catalogue: Catalogue, config: SeriesConfig, role: str, data_dir: Path
) -> Path:
    """Where one date of a site's series is cached.

    The key hashes every parameter that picks the date: the site's (which pick
    the anchor), the catalogue, and the whole series configuration, since a
    date taken by one role is not given to the next. Which sites the
    configuration lists does not decide it, nor whether the site is held out.

    Args:
        site: Site of the series.
        catalogue: Catalogue the dates come from.
        config: Series configuration.
        role: ``ANCHOR`` or a role of ``config.dates``.
        data_dir: Root of downloaded data.

    Returns:
        ``data_dir/real/<site>/<band>_<role>_<hash>.tif``.
    """
    params = {**asdict(site), **asdict(catalogue)}
    del params["held_out"]
    params["max_scene_cloud"] = config.max_scene_cloud
    params["dates"] = {name: asdict(rule) for name, rule in config.dates.items()}
    key = hashlib.sha256(json.dumps(params, default=str).encode()).hexdigest()[:12]
    return data_dir / "real" / site.name / f"{site.band}_{role}_{key}.tif"


def _write_date(
    path: Path,
    site: Site,
    scene: Scene,
    role: str,
    grid: Mapping | None = None,
    target: dt.date | None = None,
) -> None:
    """Read one date of a series and cache it, band and classification.

    Args:
        path: Cache path of the date.
        site: Site of the series.
        scene: Scene to read.
        role: Role of the date.
        grid: Profile of the anchor, whose grid the date must be on; ``None``
            for the anchor itself.
        target: Date the role aimed at, recorded in the tags.

    Raises:
        ChipUnavailable: If the scene cannot give a chip on the anchor's grid
            with at most the site's chip cloud limit hidden, no data included.
    """
    if grid is not None:
        # Checked on the anchor's grid first, which reads only the 20 m
        # classification, not the band.
        cover = chip_cover(scene.scl_href, grid)
        if (rejected := sum(cover[name] for name in SCL_REJECTED)) > (
            site.max_chip_cloud
        ):
            raise ChipUnavailable(
                f"{rejected:.2f} % of the chip is cloud or cloud shadow "
                f"(limit {site.max_chip_cloud} %)"
            )
    data, profile = read_window(scene.href, site, allow_nodata=grid is not None)
    if grid is not None and (
        profile["crs"] != grid["crs"] or profile["transform"] != grid["transform"]
    ):
        raise ChipUnavailable("the chip is not on the anchor's grid")
    cover = chip_cover(scene.scl_href, profile)
    scl = read_scl(scene.scl_href, profile)
    nodata = (
        data == profile["nodata"]
        if profile["nodata"] is not None
        else np.zeros(data.shape, bool)
    )
    scl[nodata] = SCL_NO_DATA
    hidden = 100 * float(np.isin(scl, HIDDEN).mean())
    # The anchor is the benchmark chip, already accepted on its 20 m cover.
    if grid is not None and hidden > site.max_chip_cloud:
        raise ChipUnavailable(
            f"{hidden:.2f} % of the chip is cloud, cloud shadow or no data "
            f"(limit {site.max_chip_cloud} %)"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(".partial")
    with rasterio.open(partial, "w", **{**profile, "count": 2}) as dst:
        dst.write(data, 1)
        dst.write(scl.astype(data.dtype), 2)
        dst.set_band_description(1, site.band)
        dst.set_band_description(2, "SCL")
        dst.update_tags(
            site=site.name,
            band=site.band,
            role=role,
            item_id=scene.item_id,
            datetime=scene.datetime,
            platform=scene.platform,
            tile=scene.tile,
            relative_orbit=str(scene.relative_orbit),
            cloud_cover=str(scene.cloud_cover),
            source=scene.href,
            scl_source=scene.scl_href,
            target=target.isoformat() if target else "",
            chip_nodata_pct=f"{100 * float(nodata.mean()):.3f}",
            chip_hidden_pct=f"{hidden:.3f}",
            **{f"chip_{name}_pct": f"{share:.3f}" for name, share in cover.items()},
        )
    # Renamed only once complete, so an interrupted download is not a cache hit.
    partial.replace(path)
    logger.info("%s: %s date %s from %s", site.name, role, path, scene.item_id)


def _cached_date(path: Path) -> dt.date:
    with rasterio.open(path) as src:
        return dt.date.fromisoformat(src.tags()["datetime"][:10])


def fetch_series(
    site: Site,
    catalogue: Catalogue,
    config: SeriesConfig,
    data_dir: Path,
    candidates: Candidates = stac_scenes,
) -> dict[str, Path]:
    """Return the cached dates of a site's series, fetching the missing ones.

    A series whose dates are all cached is returned without any network call.
    Otherwise the anchor is the scene of the site's chip (fetched first if not
    cached), and each role takes, in configuration order, the scene nearest its
    target date that is on the anchor's tile and relative orbit, is not on a
    date already taken, and gives a complete chip under the site's chip cloud
    limit. Ties go to the earlier date, then to the item id.

    Args:
        site: Site of the series.
        catalogue: Catalogue to search.
        config: Series configuration.
        data_dir: Root of downloaded data.
        candidates: Scene search, replaced by a fake in tests.

    Returns:
        Role to the path of its cached date, the anchor first.

    Raises:
        LookupError: If the anchor scene is not found again, or no scene within
            a role's window gives a usable chip.
    """
    roles = (ANCHOR, *config.dates)
    paths = {
        role: series_path(site, catalogue, config, role, data_dir) for role in roles
    }
    if all(path.exists() for path in paths.values()):
        return paths

    chip = fetch_chip(
        site,
        catalogue,
        data_dir,
        lambda s, c: candidates(s, c, s.start, s.end, s.max_cloud, None),
    )
    with rasterio.open(chip) as src:
        anchor_id = src.tags()["item_id"]
        anchor_date = dt.date.fromisoformat(src.tags()["datetime"][:10])
        grid = src.profile
    found = [
        s
        for s in candidates(site, catalogue, anchor_date, anchor_date, 100.0, None)
        if s.item_id == anchor_id
    ]
    if not found:
        raise LookupError(f"{site.name}: the chip's scene {anchor_id} is not found")
    anchor = found[0]
    if not paths[ANCHOR].exists():
        _write_date(paths[ANCHOR], site, anchor, ANCHOR)

    taken = {anchor_date}
    for role, rule in config.dates.items():
        if paths[role].exists():
            taken.add(_cached_date(paths[role]))
            continue
        target = anchor_date + dt.timedelta(days=rule.offset_days)
        window = dt.timedelta(days=rule.within_days)
        scenes = candidates(
            site,
            catalogue,
            target - window,
            target + window,
            config.max_scene_cloud,
            anchor.tile,
        )
        scenes = sorted(
            (
                s
                for s in scenes
                if s.tile == anchor.tile
                and s.relative_orbit == anchor.relative_orbit
                and s.date not in taken
                and abs((s.date - target).days) <= rule.within_days
            ),
            key=lambda s: (abs((s.date - target).days), s.date, s.item_id),
        )
        for scene in scenes:
            try:
                _write_date(paths[role], site, scene, role, grid, target)
            except ChipUnavailable as exc:
                logger.info(
                    "%s: %s: skipping %s: %s", site.name, role, scene.item_id, exc
                )
                continue
            taken.add(scene.date)
            break
        else:
            raise LookupError(
                f"{site.name}: no scene within {rule.within_days} days of {target} "
                f"on {anchor.tile}, orbit {anchor.relative_orbit}, gives a complete "
                f"chip under {site.max_chip_cloud} % cloud and cloud shadow "
                f"({len(scenes)} tried)"
            )
    return paths


def read_acquisition(path: Path) -> Acquisition:
    """Load one cached date of a series.

    Args:
        path: GeoTIFF written by ``fetch_series``.

    Returns:
        The acquisition.
    """
    with rasterio.open(path) as src:
        tags = src.tags()
        return Acquisition(
            role=tags["role"],
            image=src.read(1),
            scl=src.read(2).astype(np.uint8),
            georef=Georef(src.crs, src.transform),
            item_id=tags["item_id"],
            datetime=dt.datetime.fromisoformat(tags["datetime"]),
            platform=tags["platform"],
        )


def load_series(
    site: Site,
    catalogue: Catalogue,
    config: SeriesConfig,
    data_dir: Path,
    candidates: Candidates = stac_scenes,
) -> list[Acquisition]:
    """Load a site's series, fetching the dates that are not cached.

    Args:
        site: Site of the series.
        catalogue: Catalogue to search.
        config: Series configuration.
        data_dir: Root of downloaded data.
        candidates: Scene search, replaced by a fake in tests.

    Returns:
        The acquisitions, earliest first.
    """
    paths = fetch_series(site, catalogue, config, data_dir, candidates)
    return chronological([read_acquisition(path) for path in paths.values()])

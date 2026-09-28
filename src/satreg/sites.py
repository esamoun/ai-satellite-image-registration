"""Sites and STAC catalogue, as declared in the sites configuration file."""

import datetime as dt
import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BAND = "B04"

# Highest share of cloud and cloud shadow accepted over the chip itself, in
# percent of its pixels, as the L2A scene classification (SCL) reads them.
DEFAULT_MAX_CHIP_CLOUD = 1.0


@dataclass(frozen=True)
class Catalogue:
    """A STAC API and the collection chips are read from.

    Attributes:
        url: Root URL of the STAC API.
        collection: Collection id, e.g. ``sentinel-2-c1-l2a``.
    """

    url: str
    collection: str


@dataclass(frozen=True)
class Site:
    """Where and when to cut a chip.

    Attributes:
        name: Site name, used in results tables and cache paths.
        lon: Longitude of the chip centre, in degrees.
        lat: Latitude of the chip centre, in degrees.
        chip_px: Side of the square chip, in pixels of the source grid.
        start: First acquisition date searched, inclusive.
        end: Last acquisition date searched, inclusive.
        max_cloud: Highest scene cloud cover accepted, in percent.
        band: Band name as the STAC ``eo:bands`` list gives it, e.g. ``B04``.
        max_chip_cloud: Highest share of cloud and cloud shadow accepted over
            the chip window, in percent, read from the scene classification.
        held_out: Whether the site is kept for the final evaluation (N3), out of
            every run that chooses a threshold, a preset or a variant.
    """

    name: str
    lon: float
    lat: float
    chip_px: int
    start: dt.date
    end: dt.date
    max_cloud: float
    band: str = DEFAULT_BAND
    max_chip_cloud: float = DEFAULT_MAX_CHIP_CLOUD
    held_out: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.start, dt.date) or not isinstance(self.end, dt.date):
            raise ValueError(f"{self.name}: start and end must be TOML dates")
        if not -180 <= self.lon <= 180 or not -90 <= self.lat <= 90:
            raise ValueError(f"{self.name}: ({self.lon}, {self.lat}) is not lon/lat")
        if self.chip_px < 1:
            raise ValueError(f"{self.name}: chip_px must be positive")
        if self.start > self.end:
            raise ValueError(f"{self.name}: start {self.start} is after end {self.end}")
        if not 0 <= self.max_cloud <= 100:
            raise ValueError(f"{self.name}: max_cloud must be in [0, 100]")
        if not 0 <= self.max_chip_cloud <= 100:
            raise ValueError(f"{self.name}: max_chip_cloud must be in [0, 100]")
        if not isinstance(self.held_out, bool):
            raise ValueError(f"{self.name}: held_out must be true or false")


@dataclass(frozen=True)
class SitesConfig:
    """Contents of the sites configuration file.

    Attributes:
        catalogue: Where scenes are searched and read.
        sites: Site name to site.
    """

    catalogue: Catalogue
    sites: dict[str, Site]


def load_sites(path: Path) -> SitesConfig:
    """Read the sites configuration file.

    Args:
        path: TOML file with a ``[stac]`` table and one ``[sites.<name>]`` table
            per site.

    Returns:
        The parsed configuration.

    Raises:
        ValueError: If a table is missing, or a site has missing, unknown or
            invalid keys.
    """
    with path.open("rb") as f:
        raw = tomllib.load(f)
    if "stac" not in raw or "sites" not in raw:
        raise ValueError(f"{path} needs a [stac] table and [sites.<name>] tables")

    try:
        catalogue = Catalogue(**raw["stac"])
    except TypeError as exc:
        raise ValueError(f"{path}: [stac]: {exc}") from exc
    sites = {}
    for name, fields in raw["sites"].items():
        try:
            sites[name] = Site(name=name, **fields)
        except TypeError as exc:
            raise ValueError(f"{path}: site {name}: {exc}") from exc
    return SitesConfig(catalogue=catalogue, sites=sites)

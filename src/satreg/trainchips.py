"""Training and validation chips (N3), declared apart from the benchmark sites.

Fine-tuning cuts its pairs from chips of their own, never from a benchmark chip.
They live in their own configuration file, which no benchmark command reads, and
come out of it as ``TrainingChip``, not as a bare ``Site``. The configuration
refuses a chip that takes the name of a benchmark site or could share a pixel
with one, held-out sites included, and ``TrainingConfig.select`` is the one way
to ask for the chips of a role.

A chip is accepted if the date series rule finds every date of its series and
its land cover, read from ESA WorldCover on the chip's grid, passes the rule of
its landscape. See docs/decisions.md.
"""

import datetime as dt
import math
import shutil
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import rasterio

from .georef import Georef
from .ingest import TEN_METRE_BANDS, stac_scenes
from .landcover import (
    CLASSES,
    WORLDCOVER_URL,
    class_shares,
    fetch_landcover,
    read_landcover,
)
from .real import ANCHOR, Candidates, SeriesConfig, fetch_series, series_path
from .sites import Site, SitesConfig

# Landscape types a network may be trained on. Mountain and desert are the
# landscapes of the held-out sites.
LANDSCAPES = ("open fields", "urban", "forest", "coast")

TRAIN, VALIDATION = "train", "validation"
ROLES = (TRAIN, VALIDATION)

# Ground size of a pixel of the 10 m bands, in metres.
PIXEL_M = 10.0

# Mean radius of the Earth, in metres, for distances between chip centres.
EARTH_RADIUS_M = 6_371_008.8

# Two chips are told apart only if their centres are further than the sum of
# their footprint radii by this factor: a sphere is within 0.5 % of the
# ellipsoid, and a UTM pixel within 0.1 % of 10 m on the ground.
OVERLAP_MARGIN = 1.01


@dataclass(frozen=True)
class TrainingChip:
    """A chip N3 trains or validates on.

    Attributes:
        site: Where and when the chip is cut, as for a benchmark chip.
        role: ``TRAIN``, or ``VALIDATION`` for a chip set aside whole from
            training.
        landscape: Landscape type, one of ``LANDSCAPES``.
    """

    site: Site
    role: str
    landscape: str

    def __post_init__(self) -> None:
        if self.role not in ROLES:
            raise ValueError(
                f"{self.name}: role must be one of {', '.join(ROLES)}, "
                f"got {self.role!r}"
            )
        if self.landscape not in LANDSCAPES:
            raise ValueError(
                f"{self.name}: landscape must be one of {', '.join(LANDSCAPES)}, "
                f"got {self.landscape!r}"
            )
        if self.site.held_out:
            raise ValueError(f"{self.name}: a held-out site is not trained on")

    @property
    def name(self) -> str:
        """Name of the chip, used in cache paths."""
        return self.site.name


@dataclass(frozen=True)
class LandcoverRule:
    """What the land cover of a chip must look like for its landscape.

    Attributes:
        minimum: WorldCover class name to the lowest share accepted, in percent
            of the chip's pixels.
        maximum: WorldCover class name to the highest share accepted.
    """

    minimum: dict[str, float] = field(default_factory=dict)
    maximum: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, share in (*self.minimum.items(), *self.maximum.items()):
            if name not in CLASSES.values():
                known = ", ".join(CLASSES.values())
                raise ValueError(f"{name!r} is not a WorldCover class ({known})")
            if not 0 <= share <= 100:
                raise ValueError(f"{name}: a share must be in [0, 100], got {share}")

    def failures(self, shares: dict[str, float], landscape: str) -> list[str]:
        """Say how a chip's land cover breaks the rule.

        Args:
            shares: Class name to its share of the chip, in percent; a class
                that is absent has none.
            landscape: Landscape the rule is for, named in the messages.

        Returns:
            One sentence per bound that is not met, none if the chip passes.
        """
        found = []
        for name, least in self.minimum.items():
            if (share := shares.get(name, 0.0)) < least:
                found.append(
                    f"{name} covers {share:.1f} % of the chip, under the "
                    f"{least:g} % required of {landscape} chips"
                )
        for name, most in self.maximum.items():
            if (share := shares.get(name, 0.0)) > most:
                found.append(
                    f"{name} covers {share:.1f} % of the chip, over the "
                    f"{most:g} % allowed for {landscape} chips"
                )
        return found


def centre_distance_m(a: Site, b: Site) -> float:
    """Great-circle distance between the centres of two sites, in metres."""
    lat_a, lat_b = math.radians(a.lat), math.radians(b.lat)
    half_lat = (lat_b - lat_a) / 2
    half_lon = math.radians(b.lon - a.lon) / 2
    h = (
        math.sin(half_lat) ** 2
        + math.cos(lat_a) * math.cos(lat_b) * math.sin(half_lon) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))


def footprint_radius_m(site: Site) -> float:
    """Radius of a circle around a site's centre that contains its chip.

    The chip is a square of ``chip_px`` pixels of 10 m around the pixel the
    centre falls in, whatever the tile grid it is cut from: half its diagonal,
    with a pixel of margin for where the centre sits in its pixel.

    Args:
        site: Site of the chip.

    Returns:
        The radius, in metres.

    Raises:
        ValueError: If the site's band is not a 10 m band.
    """
    if site.band not in TEN_METRE_BANDS:
        raise ValueError(f"{site.name}: {site.band} is not a 10 m band")
    return (site.chip_px / 2 + 1) * PIXEL_M * math.sqrt(2)


def may_overlap(a: Site, b: Site) -> bool:
    """Whether the chips of two sites could share a pixel.

    The test is on the circles around the two footprints, so it needs no fetched
    chip and errs on the side of refusing: chips it tells apart share no ground.

    Args:
        a: A site.
        b: Another site.

    Returns:
        False only if the two circles do not touch.
    """
    reach = footprint_radius_m(a) + footprint_radius_m(b)
    return centre_distance_m(a, b) <= OVERLAP_MARGIN * reach


@dataclass(frozen=True)
class TrainingConfig:
    """Contents of the training chips configuration file.

    Attributes:
        chips: Chip name to chip.
        acceptance: Landscape to the land-cover rule its chips must pass; a
            landscape without a rule has none.
        benchmark: The benchmark sites, which give the catalogue and which no
            chip may be or overlap.
    """

    chips: dict[str, TrainingChip]
    acceptance: dict[str, LandcoverRule]
    benchmark: SitesConfig

    def __post_init__(self) -> None:
        for name, chip in self.chips.items():
            if name in self.benchmark.sites:
                raise ValueError(
                    f"{name} is a benchmark site: a training chip cannot take its name"
                )
            for other in self.benchmark.sites.values():
                if may_overlap(chip.site, other):
                    kind = "held-out site" if other.held_out else "benchmark chip"
                    raise ValueError(
                        f"{name} could overlap the {kind} {other.name}: their "
                        f"centres are {centre_distance_m(chip.site, other) / 1000:.1f}"
                        " km apart"
                    )
        chips = list(self.chips.values())
        for i, chip in enumerate(chips):
            for other in chips[i + 1 :]:
                if may_overlap(chip.site, other.site):
                    raise ValueError(
                        f"{chip.name} could overlap {other.name}: their centres are "
                        f"{centre_distance_m(chip.site, other.site) / 1000:.1f} km "
                        "apart"
                    )
        for landscape in self.acceptance:
            if landscape not in LANDSCAPES:
                raise ValueError(
                    f"acceptance rule for {landscape!r}, which is not one of "
                    f"{', '.join(LANDSCAPES)}"
                )

    def select(
        self, role: str, names: Sequence[str] | None = None
    ) -> list[TrainingChip]:
        """The chips of one role: the only chips pairs of that role are cut from.

        Args:
            role: ``TRAIN`` or ``VALIDATION``.
            names: Chips asked for, all of the role if ``None``.

        Returns:
            The chips, in the order asked, or in file order.

        Raises:
            ValueError: If the role is unknown, or a name is a benchmark chip, a
                held-out site, a chip of the other role or no chip at all.
        """
        if role not in ROLES:
            raise ValueError(f"role must be one of {', '.join(ROLES)}, got {role!r}")
        if names is None:
            return [chip for chip in self.chips.values() if chip.role == role]
        for name in names:
            if name in self.benchmark.sites:
                if self.benchmark.sites[name].held_out:
                    raise ValueError(
                        f"{name} is a held-out site, kept for the final "
                        f"evaluation: no {role} pair is cut from it"
                    )
                raise ValueError(
                    f"{name} is a benchmark chip: no {role} pair is cut from it"
                )
            if name not in self.chips:
                known = ", ".join(self.chips)
                raise ValueError(f"unknown chip {name!r} (declared: {known})")
            if self.chips[name].role != role:
                raise ValueError(
                    f"{name} is a {self.chips[name].role} chip: no {role} pair "
                    "is cut from it"
                )
        return [self.chips[name] for name in names]


def load_training_chips(path: Path, benchmark: SitesConfig) -> TrainingConfig:
    """Read the training chips configuration file.

    Args:
        path: TOML file with one ``[chips.<name>]`` table per chip, holding
            ``role``, ``landscape`` and the keys of a site; a ``[defaults]``
            table of site keys every chip takes unless it sets its own; and
            ``[acceptance.<landscape>]`` tables of ``min`` and ``max`` shares by
            WorldCover class name.
        benchmark: The benchmark sites, as ``load_sites`` reads them.

    Returns:
        The parsed configuration.

    Raises:
        ValueError: If a table is missing or has unknown or invalid keys, or a
            chip is, or could overlap, a benchmark site or another chip.
    """
    with path.open("rb") as f:
        raw = tomllib.load(f)
    if not raw.get("chips"):
        raise ValueError(f"{path} needs [chips.<name>] tables")
    if unknown := sorted(set(raw) - {"chips", "defaults", "acceptance"}):
        raise ValueError(f"{path}: unknown table {unknown[0]!r}")

    defaults = raw.get("defaults", {})
    chips = {}
    for name, table in raw["chips"].items():
        fields = {**defaults, **table}
        try:
            role, landscape = fields.pop("role"), fields.pop("landscape")
        except KeyError as exc:
            raise ValueError(f"{path}: chip {name}: no {exc.args[0]}") from None
        if "held_out" in fields:
            raise ValueError(f"{path}: chip {name}: a chip is never held out")
        try:
            chips[name] = TrainingChip(Site(name=name, **fields), role, landscape)
        except TypeError as exc:
            raise ValueError(f"{path}: chip {name}: {exc}") from exc

    acceptance = {}
    for landscape, table in raw.get("acceptance", {}).items():
        if unknown := sorted(set(table) - {"min", "max"}):
            raise ValueError(
                f"{path}: acceptance of {landscape}: unknown key {unknown[0]!r}"
            )
        try:
            acceptance[landscape] = LandcoverRule(
                minimum=dict(table.get("min", {})), maximum=dict(table.get("max", {}))
            )
        except ValueError as exc:
            raise ValueError(f"{path}: acceptance of {landscape}: {exc}") from exc
    try:
        return TrainingConfig(chips, acceptance, benchmark)
    except ValueError as exc:
        raise ValueError(f"{path}: {exc}") from exc


@dataclass(frozen=True)
class DateRecord:
    """What one date of a chip's series is, as its GeoTIFF tags record it.

    Attributes:
        role: ``ANCHOR`` or the role of the date rule that picked it.
        path: Cached GeoTIFF of the date.
        item_id: STAC item id of the scene.
        datetime: Acquisition time, UTC.
        platform: Satellite, e.g. ``sentinel-2b``.
        hidden_pct: Share of the chip hidden by cloud, cloud shadow or no data.
    """

    role: str
    path: Path
    item_id: str
    datetime: dt.datetime
    platform: str
    hidden_pct: float


@dataclass(frozen=True)
class ChipCheck:
    """A chip against the acceptance rule.

    Attributes:
        chip: The chip.
        dates: The dates of its series that were found, the anchor first.
        shares: WorldCover class name to its share of the chip, in percent;
            empty if the chip has no anchor date, hence no grid.
        failures: Why the chip is refused; empty if it is accepted.
        georef: Map grid of the chip, ``None`` without an anchor date.
    """

    chip: TrainingChip
    dates: tuple[DateRecord, ...]
    shares: dict[str, float]
    failures: tuple[str, ...]
    georef: Georef | None = None

    @property
    def accepted(self) -> bool:
        """Whether every date was found and the land cover passes."""
        return not self.failures


def _date_record(role: str, path: Path) -> DateRecord:
    with rasterio.open(path) as src:
        tags = src.tags()
    return DateRecord(
        role=role,
        path=path,
        item_id=tags["item_id"],
        datetime=dt.datetime.fromisoformat(tags["datetime"]),
        platform=tags["platform"],
        hidden_pct=float(tags["chip_hidden_pct"]),
    )


def check_chip(
    chip: TrainingChip,
    config: TrainingConfig,
    series: SeriesConfig,
    data_dir: Path,
    candidates: Candidates = stac_scenes,
    landcover_url: str = WORLDCOVER_URL,
) -> ChipCheck:
    """Fetch a chip's series and land cover, and apply the acceptance rule.

    The series is the one a benchmark site gets: the chip's own scene, then one
    date per rule of the series configuration. Dates and land cover already in
    the cache are not fetched again.

    Args:
        chip: Chip to check.
        config: The training chips configuration.
        series: Series configuration; the sites it lists are not used.
        data_dir: Root of downloaded data.
        candidates: Scene search, replaced by a fake in tests.
        landcover_url: WorldCover tile URL template, replaced in tests.

    Returns:
        The dates found, the land-cover shares and why the chip is refused, if
        it is.
    """
    site, catalogue = chip.site, config.benchmark.catalogue
    failures = []
    try:
        fetch_series(site, catalogue, series, data_dir, candidates)
    except LookupError as exc:
        failures.append(str(exc))
    roles = (ANCHOR, *series.dates)
    paths = {
        role: series_path(site, catalogue, series, role, data_dir) for role in roles
    }
    dates = tuple(
        _date_record(role, path) for role, path in paths.items() if path.exists()
    )
    if len(dates) < len(roles):
        failures.append(f"{len(dates)} of the {len(roles)} dates of its series found")

    shares: dict[str, float] = {}
    georef = None
    if paths[ANCHOR].exists():
        with rasterio.open(paths[ANCHOR]) as src:
            georef, shape = Georef(src.crs, src.transform), src.shape
        cover = fetch_landcover(site.name, georef, shape, data_dir, landcover_url)
        shares = class_shares(read_landcover(cover))
        if rule := config.acceptance.get(chip.landscape):
            failures += rule.failures(shares, chip.landscape)
    return ChipCheck(chip, dates, shares, tuple(failures), georef)


def to_markdown(checks: Sequence[ChipCheck]) -> str:
    """Write what was fetched and how each chip fares against the rule.

    Args:
        checks: One check per chip.

    Returns:
        A table of land-cover shares, a table of dates, then one line per
        refused chip.
    """
    classes = [
        name
        for name in ("no data", *CLASSES.values())
        if any(name in check.shares for check in checks)
    ]
    lines = [
        "| chip | landscape | role | " + " | ".join(classes) + " | accepted |",
        "|---|---|---|" + "---:|" * len(classes) + "---|",
    ]
    for check in checks:
        chip = check.chip
        shares = " | ".join(
            f"{check.shares.get(name, 0.0):.1f}" if check.shares else "n/a"
            for name in classes
        )
        verdict = "yes" if check.accepted else "no"
        lines.append(
            f"| {chip.name} | {chip.landscape} | {chip.role} | {shares} | {verdict} |"
        )
    lines += [
        "",
        "Land cover: ESA WorldCover 2021, in percent of the chip's pixels.",
        "",
        "| chip | date | acquired | scene | satellite | hidden |",
        "|---|---|---|---|---|---:|",
    ]
    for check in checks:
        for date in check.dates:
            lines.append(
                f"| {check.chip.name} | {date.role} | {date.datetime.date()} "
                f"| {date.item_id} | {date.platform} | {date.hidden_pct:.2f} % |"
            )
    lines += [
        "",
        "Hidden: share of the chip under cloud, cloud shadow or no data, from "
        "the scene classification.",
    ]
    for check in checks:
        if not check.accepted:
            lines += ["", f"Refused: {check.chip.name}: {'; '.join(check.failures)}."]
    return "\n".join(lines) + "\n"


def manifest(checks: Sequence[ChipCheck], data_dir: Path) -> list[dict]:
    """Describe each chip and its dates, for the record that goes with the data.

    Args:
        checks: One check per chip.
        data_dir: Root of downloaded data, which file paths are given from.

    Returns:
        One JSON-ready entry per chip.
    """
    return [
        {
            "chip": check.chip.name,
            "landscape": check.chip.landscape,
            "role": check.chip.role,
            "lon": check.chip.site.lon,
            "lat": check.chip.site.lat,
            "chip_px": check.chip.site.chip_px,
            "band": check.chip.site.band,
            "crs": check.georef.crs.to_string() if check.georef else None,
            "transform": list(check.georef.transform)[:6] if check.georef else None,
            "accepted": check.accepted,
            "failures": list(check.failures),
            "landcover_pct": {k: round(v, 3) for k, v in check.shares.items()},
            "dates": [
                {
                    "role": date.role,
                    "file": date.path.relative_to(data_dir).as_posix(),
                    "item_id": date.item_id,
                    "datetime": date.datetime.isoformat(),
                    "platform": date.platform,
                    "hidden_pct": date.hidden_pct,
                }
                for date in check.dates
            ],
        }
        for check in checks
    ]


def export(checks: Sequence[ChipCheck], data_dir: Path, out: Path) -> int:
    """Copy the dates of accepted chips to a directory that works as a data dir.

    Files keep their path under ``data_dir``, so a run given ``out`` as its data
    directory finds every series in the cache and makes no network call. This is
    what is uploaded for the training runs.

    Args:
        checks: One check per chip.
        data_dir: Root of downloaded data.
        out: Directory to copy into.

    Returns:
        Bytes copied.

    Raises:
        ValueError: If a chip is refused: the set that is trained on is whole.
    """
    if refused := [check.chip.name for check in checks if not check.accepted]:
        raise ValueError(f"not exported: {', '.join(refused)} refused")
    copied = 0
    for check in checks:
        for date in check.dates:
            target = out / date.path.relative_to(data_dir)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(date.path, target)
            copied += target.stat().st_size
    return copied

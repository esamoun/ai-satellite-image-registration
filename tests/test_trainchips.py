import dataclasses
import datetime as dt
import json
from collections import Counter
from pathlib import Path

import pytest
import rasterio
from test_ingest import CENTRE, CRS, TRANSFORM, site_at
from test_landcover import fake_tile
from test_real import CATALOGUE, CONFIG, acquisition_scene, catalogue_of

from satreg.cli import main
from satreg.landcover import WORLDCOVER_URL, landcover_path
from satreg.real import ANCHOR
from satreg.sites import SitesConfig, load_sites
from satreg.trainchips import (
    LANDSCAPES,
    TRAIN,
    VALIDATION,
    LandcoverRule,
    TrainingChip,
    TrainingConfig,
    check_chip,
    export,
    load_training_chips,
    manifest,
    may_overlap,
    to_markdown,
)

CONFIGS = Path(__file__).parents[1] / "configs"

# A benchmark chip and a held-out site, both far from the fixture grid.
BENCHMARK = SitesConfig(
    CATALOGUE,
    {
        "beauce": site_at(*CENTRE, lon=1.50, lat=47.00),
        "alps": site_at(*CENTRE, name="alps", lon=6.87, lat=45.92, held_out=True),
    },
)
RULES = {
    "urban": LandcoverRule(minimum={"built-up": 55.0}),
    "coast": LandcoverRule(maximum={"permanent water bodies": 40.0}),
}

SITES_TOML = (
    '[stac]\nurl = "https://stac.example"\ncollection = "sentinel-2-c1-l2a"\n'
    "[sites.beauce]\nlon = 1.50\nlat = 47.00\nchip_px = 1024\n"
    "start = 2025-04-01\nend = 2025-09-30\nmax_cloud = 5.0\n"
    "[sites.alps]\nlon = 6.87\nlat = 45.92\nchip_px = 1024\n"
    "start = 2025-04-01\nend = 2025-09-30\nmax_cloud = 5.0\nheld_out = true\n"
)
DEFAULTS = (
    "[defaults]\nchip_px = 1024\nstart = 2025-04-01\nend = 2025-09-30\n"
    "max_cloud = 5.0\n"
)
PLAIN = (
    '[chips.plain]\nlandscape = "open fields"\nrole = "train"\n'
    "lon = 4.25\nlat = 48.85\n"
)


def chip(name="plain", role=TRAIN, landscape="open fields", **site):
    """A training chip on the fixture grid, where the fixture scenes are."""
    return TrainingChip(site_at(*CENTRE, name=name, **site), role, landscape)


def config_of(*chips):
    return TrainingConfig({c.name: c for c in chips}, RULES, BENCHMARK)


def load(tmp_path, text):
    (tmp_path / "sites.toml").write_text(SITES_TOML)
    path = tmp_path / "train-sites.toml"
    path.write_text(text)
    return load_training_chips(path, load_sites(tmp_path / "sites.toml"))


def test_a_chip_takes_the_defaults_unless_it_sets_its_own(tmp_path):
    config = load(
        tmp_path,
        DEFAULTS
        + PLAIN
        + "end = 2025-07-15\n"
        + '[chips.town]\nlandscape = "urban"\nrole = "validation"\n'
        "lon = 4.85\nlat = 45.75\n"
        '[acceptance.urban]\nmin = { "built-up" = 55.0 }\n',
    )

    plain, town = config.chips["plain"], config.chips["town"]
    assert (plain.role, plain.landscape) == (TRAIN, "open fields")
    assert (plain.site.name, plain.site.chip_px) == ("plain", 1024)
    assert plain.site.end == dt.date(2025, 7, 15)
    assert town.site.end == dt.date(2025, 9, 30)
    assert town.role == VALIDATION
    assert config.acceptance == {"urban": LandcoverRule(minimum={"built-up": 55.0})}


@pytest.mark.parametrize(
    ("text", "message"),
    [
        (DEFAULTS, r"needs \[chips"),
        (DEFAULTS + PLAIN.replace('role = "train"\n', ""), "plain: no role"),
        (DEFAULTS + PLAIN.replace("train", "test"), "role must be one of"),
        (DEFAULTS + PLAIN.replace("open fields", "desert"), "landscape must be one"),
        (DEFAULTS + PLAIN + "held_out = true\n", "never held out"),
        (DEFAULTS + PLAIN + "colour = 1\n", "plain: .*colour"),
        (DEFAULTS + PLAIN + "[series]\n", "unknown table 'series'"),
        (
            DEFAULTS + PLAIN + '[acceptance.urban]\nmin = { "concrete" = 55.0 }\n',
            "'concrete' is not a WorldCover class",
        ),
        (
            DEFAULTS + PLAIN + '[acceptance.urban]\nleast = { "built-up" = 55.0 }\n',
            "unknown key 'least'",
        ),
        (
            DEFAULTS + PLAIN + '[acceptance.desert]\nmin = { "built-up" = 55.0 }\n',
            "'desert', which is not one of",
        ),
        # The name of a benchmark site, even far from it.
        (DEFAULTS + PLAIN.replace("plain", "beauce"), "beauce is a benchmark site"),
        # 5 km from the Beauce chip: the two 10 km chips share ground.
        (
            DEFAULTS + PLAIN.replace("4.25", "1.55").replace("48.85", "47.03"),
            r"plain could overlap the benchmark chip beauce: .* 5\.\d km apart",
        ),
        (
            DEFAULTS + PLAIN.replace("4.25", "6.90").replace("48.85", "45.90"),
            "plain could overlap the held-out site alps",
        ),
        (
            DEFAULTS + PLAIN + PLAIN.replace("plain", "next").replace("4.25", "4.30"),
            "plain could overlap next",
        ),
    ],
)
def test_bad_training_config_is_rejected(tmp_path, text, message):
    with pytest.raises(ValueError, match=message):
        load(tmp_path, text)


def test_chips_are_told_apart_only_when_their_footprints_cannot_touch():
    here = site_at(*CENTRE, chip_px=1024, lon=4.0, lat=45.0)

    def east(km):
        # A degree of longitude is 78.8 km at 45° north.
        return dataclasses.replace(here, lon=4.0 + km / 78.8)

    # Side by side, 10.24 km wide each.
    assert may_overlap(here, east(10.0))
    # Apart, but closer than two half-diagonals: a rotated grid could touch.
    assert may_overlap(here, east(14.0))
    assert not may_overlap(here, east(15.0))


def test_the_repository_declares_twelve_chips_three_per_landscape():
    sites = load_sites(CONFIGS / "sites.toml")

    config = load_training_chips(CONFIGS / "train-sites.toml", sites)

    chips = config.chips.values()
    assert len(chips) == 12
    assert Counter(c.landscape for c in chips) == dict.fromkeys(LANDSCAPES, 3)
    validation = config.select(VALIDATION)
    assert sorted(c.landscape for c in validation) == sorted(LANDSCAPES)
    assert len(config.select(TRAIN)) == 8
    # Like the benchmark chips: same size, band and cloud rule.
    beauce = sites.sites["beauce"]
    for c in chips:
        assert (c.site.chip_px, c.site.band) == (beauce.chip_px, beauce.band)
        assert c.site.max_chip_cloud == beauce.max_chip_cloud
    assert set(config.acceptance) == {"urban", "coast"}


def test_pairs_are_asked_for_by_role():
    plain, town = chip(), chip("town", VALIDATION, "urban", lon=3.0)
    config = config_of(plain, town)

    assert config.select(TRAIN) == [plain]
    assert config.select(VALIDATION) == [town]
    assert config.select(VALIDATION, ["town"]) == [town]


@pytest.mark.parametrize(
    ("role", "name", "message"),
    [
        (TRAIN, "beauce", "beauce is a benchmark chip: no train pair"),
        (VALIDATION, "beauce", "beauce is a benchmark chip: no validation pair"),
        (TRAIN, "alps", "alps is a held-out site.*no train pair"),
        (VALIDATION, "alps", "alps is a held-out site.*no validation pair"),
        (TRAIN, "town", "town is a validation chip: no train pair"),
        (VALIDATION, "plain", "plain is a train chip: no validation pair"),
        (TRAIN, "nowhere", "unknown chip 'nowhere'"),
        ("test", "plain", "role must be one of"),
    ],
)
def test_asking_for_pairs_from_any_other_chip_raises(role, name, message):
    config = config_of(chip(), chip("town", VALIDATION, "urban", lon=3.0))

    with pytest.raises(ValueError, match=message):
        config.select(role, ["plain", name] if role == TRAIN else ["town", name])


@pytest.fixture
def scenes(tmp_path):
    """A search over an anchor and the two dates the fixture series takes."""
    d = dt.date
    return catalogue_of(
        acquisition_scene(tmp_path, d(2025, 7, 1), cloud_cover=0.1),
        acquisition_scene(tmp_path, d(2025, 6, 26)),
        acquisition_scene(tmp_path, d(2025, 9, 28), cloud_cover=30.0),
    )


def worldcover(tmp_path, west_class, east_class, shift=0.0):
    """A fake WorldCover tile around the fixture chip, split at its centre.

    Args:
        tmp_path: Where to write it.
        west_class: Class west of the split.
        east_class: Class east of it.
        shift: Degrees the split is moved east of the chip's centre; 0.02 puts
            the whole chip on the west class, -0.02 on the east class.

    Returns:
        The tile URL template.
    """
    site = site_at(*CENTRE)
    west, east = site.lon + shift - 0.04, site.lon + shift + 0.04
    bounds = (west, site.lat - 0.02, east, site.lat + 0.02)
    fake_tile(tmp_path / "N48E000.tif", bounds, west_class, east_class)
    return str(tmp_path / "{tile}.tif")


def check(tmp_path, scenes, chip, url):
    return check_chip(chip, config_of(chip), CONFIG, tmp_path / "data", scenes, url)


def test_a_chip_with_every_date_and_no_land_cover_rule_is_accepted(tmp_path, scenes):
    result = check(tmp_path, scenes, chip(), worldcover(tmp_path, 40, 10))

    assert result.accepted
    assert [d.role for d in result.dates] == [ANCHOR, "days", "season"]
    assert [d.datetime.date().isoformat() for d in result.dates] == [
        "2025-07-01",
        "2025-06-26",
        "2025-09-28",
    ]
    assert result.dates[0].item_id == "S2B_T31UCP_20250701"
    assert result.dates[0].platform == "sentinel-2b"
    assert result.dates[0].hidden_pct == 0.0
    assert list(result.shares) == ["tree cover", "cropland"]
    assert result.shares["cropland"] == pytest.approx(50, abs=2)
    assert sum(result.shares.values()) == pytest.approx(100)
    assert (result.georef.crs, result.georef.transform.a) == (CRS, TRANSFORM.a)


def test_an_urban_chip_needs_enough_built_up_and_is_reported_with_its_share(
    tmp_path, scenes
):
    town = chip("town", landscape="urban")

    half = check(tmp_path, scenes, town, worldcover(tmp_path, 50, 40))

    assert not half.accepted
    (failure,) = half.failures
    share = half.shares["built-up"]
    assert share == pytest.approx(50, abs=2)
    assert failure == (
        f"built-up covers {share:.1f} % of the chip, under the 55 % required of "
        "urban chips"
    )


def test_an_urban_chip_that_is_built_up_is_accepted(tmp_path, scenes):
    town = chip("town", landscape="urban")

    result = check(tmp_path, scenes, town, worldcover(tmp_path, 50, 40, shift=0.02))

    assert result.accepted
    assert result.shares == {"built-up": 100.0}


def test_a_coast_chip_may_not_be_mostly_water(tmp_path, scenes):
    shore = chip("shore", landscape="coast")

    half = check(tmp_path, scenes, shore, worldcover(tmp_path, 80, 10))

    assert not half.accepted
    assert half.failures == (
        f"permanent water bodies covers {half.shares['permanent water bodies']:.1f}"
        " % of the chip, over the 40 % allowed for coast chips",
    )


def test_a_coast_chip_without_water_passes_the_rule(tmp_path, scenes):
    shore = chip("shore", landscape="coast")

    result = check(tmp_path, scenes, shore, worldcover(tmp_path, 80, 10, shift=-0.02))

    assert result.accepted


def test_a_chip_whose_series_misses_a_date_is_refused(tmp_path):
    d = dt.date
    scenes = catalogue_of(
        acquisition_scene(tmp_path, d(2025, 7, 1), cloud_cover=0.1),
        acquisition_scene(tmp_path, d(2025, 6, 26)),
    )

    result = check(tmp_path, scenes, chip(), worldcover(tmp_path, 40, 10))

    assert not result.accepted
    assert "no scene within 30 days of 2025-09-30" in result.failures[0]
    assert result.failures[1] == "2 of the 3 dates of its series found"
    # What was found is still reported, land cover included.
    assert [d.role for d in result.dates] == [ANCHOR, "days"]
    assert result.shares


def test_the_tables_list_every_chip_its_shares_and_its_dates(tmp_path, scenes):
    url = worldcover(tmp_path, 50, 40)
    plain = check(tmp_path, scenes, chip(), url)
    town = check(tmp_path, scenes, chip("town", VALIDATION, "urban"), url)

    table = to_markdown([plain, town])

    assert "| chip | landscape | role | cropland | built-up | accepted |" in table
    assert f"| plain | open fields | train | {plain.shares['cropland']:.1f} " in table
    assert table.count("| yes |") == table.count("| no |") == 1
    assert (
        "| plain | season | 2025-09-28 | S2B_T31UCP_20250928 | sentinel-2b | 0.00 % |"
    ) in table
    assert "Refused: town: built-up covers" in table

    (entry, refused) = manifest([plain, town], tmp_path / "data")
    assert (entry["chip"], entry["role"], entry["accepted"]) == ("plain", TRAIN, True)
    assert entry["dates"][0]["file"].startswith("real/plain/B04_anchor_")
    assert entry["crs"] == CRS
    assert refused["failures"] == list(town.failures)
    json.dumps([entry, refused])


def test_an_export_is_a_data_directory_that_needs_no_fetch(tmp_path, scenes):
    plain = chip()
    url = worldcover(tmp_path, 40, 10)
    result = check(tmp_path, scenes, plain, url)
    out = tmp_path / "dataset"

    size = export([result], tmp_path / "data", out)

    files = sorted(out.rglob("*.tif"))
    assert len(files) == 3
    assert size == sum(f.stat().st_size for f in files)
    again = check_chip(plain, config_of(plain), CONFIG, out, catalogue_of(), url)
    assert [d.item_id for d in again.dates] == [d.item_id for d in result.dates]


def test_a_refused_chip_is_not_exported(tmp_path, scenes):
    town = chip("town", landscape="urban")
    result = check(tmp_path, scenes, town, worldcover(tmp_path, 50, 40))

    with pytest.raises(ValueError, match="town refused"):
        export([result], tmp_path / "data", tmp_path / "dataset")


def cached(tmp_path, scenes, landscape, url):
    """Configure one chip on the fixture grid, with all it needs in the cache.

    Returns:
        The arguments of ``fetch-train`` that read it without any fetch.
    """
    site = site_at(*CENTRE)
    (tmp_path / "sites.toml").write_text(SITES_TOML)
    train = tmp_path / "train-sites.toml"
    train.write_text(
        '[acceptance.urban]\nmin = { "built-up" = 55.0 }\n'
        + DEFAULTS.replace("1024", "64")
        + f'[chips.place]\nlandscape = "{landscape}"\nrole = "train"\n'
        f"lon = {site.lon}\nlat = {site.lat}\n"
    )
    series = tmp_path / "real.toml"
    series.write_text(
        '[series]\nsites = ["beauce"]\nmax_scene_cloud = 50.0\n[series.dates]\n'
        "days = { offset_days = 0, within_days = 15 }\n"
        "season = { offset_days = 91, within_days = 30 }\n"
    )
    data = tmp_path / "data"
    config = load_training_chips(train, load_sites(tmp_path / "sites.toml"))
    result = check_chip(config.chips["place"], config, CONFIG, data, scenes, url)
    # The command reads the land cover from WorldCover's own URL.
    with rasterio.open(result.dates[0].path) as src:
        shape = src.shape
    local, remote = (
        landcover_path("place", result.georef, shape, source, data)
        for source in (url, WORLDCOVER_URL)
    )
    local.rename(remote)
    return [
        "fetch-train",
        "--sites-config",
        str(tmp_path / "sites.toml"),
        "--train-config",
        str(train),
        "--series-config",
        str(series),
        "--data-dir",
        str(data),
        "--out",
        str(tmp_path / "out"),
    ]


def test_fetch_train_writes_the_tables_and_exports_the_chips(tmp_path, capsys, scenes):
    args = cached(tmp_path, scenes, "open fields", worldcover(tmp_path, 40, 10))
    dataset = tmp_path / "dataset"

    main(args + ["--export", str(dataset)])

    printed = capsys.readouterr().out
    assert "| place | open fields | train |" in printed
    assert "| place | days | 2025-06-26 | S2B_T31UCP_20250626 |" in printed
    assert f"Exported 1 chips to {dataset}" in printed
    out = tmp_path / "out"
    assert printed.startswith((out / "summary.md").read_text())
    (entry,) = json.loads((out / "chips.json").read_text())
    assert entry["accepted"] is True
    assert json.loads((dataset / "chips.json").read_text()) == [entry]
    assert all((dataset / date["file"]).is_file() for date in entry["dates"])


def test_fetch_train_reports_a_refused_chip_with_its_shares(tmp_path, capsys, scenes):
    args = cached(tmp_path, scenes, "urban", worldcover(tmp_path, 50, 40))

    with pytest.raises(SystemExit, match="place is refused: built-up covers 5"):
        main(args + ["--export", str(tmp_path / "dataset")])

    assert "| no |" in (tmp_path / "out" / "summary.md").read_text()
    assert not (tmp_path / "dataset").exists()


def test_fetch_train_refuses_a_chip_that_is_not_declared(tmp_path, scenes):
    args = cached(tmp_path, scenes, "open fields", worldcover(tmp_path, 40, 10))

    with pytest.raises(SystemExit, match="unknown chip 'beauce'"):
        main(args + ["--chip", "beauce"])

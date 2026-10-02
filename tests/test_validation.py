import datetime as dt
import json
import math
from pathlib import Path

import pytest
from test_ingest import CENTRE, site_at
from test_real import CONFIG, acquisition_scene, catalogue_of
from test_trainchips import BENCHMARK, RULES, SITES_TOML

from satreg.benchmark import BenchmarkConfig, PairResult, run_benchmark
from satreg.cli import load_run_config, main, parse_args
from satreg.cycle import REAL, TripletRow
from satreg.degrade import load_presets
from satreg.methods import load_methods
from satreg.real import ANCHOR
from satreg.sites import load_sites
from satreg.texture import fractal_texture
from satreg.trainchips import (
    TRAIN,
    VALIDATION,
    TrainingChip,
    TrainingConfig,
    load_training_chips,
)
from satreg.validation import (
    ALL_PRESETS,
    ALL_TRIPLETS,
    POOLED,
    closure_by_role,
    load_closure_series,
    load_validation_chips,
    pooled,
    subset_tracking,
    subsets_markdown,
)

CONFIGS = Path(__file__).parents[1] / "configs"
PRESETS = load_presets(CONFIGS / "degradations.toml")
ROW, COL = CENTRE


@pytest.fixture
def scenes(tmp_path):
    """A search over an anchor and the two dates the fixture series takes."""
    d = dt.date
    return catalogue_of(
        acquisition_scene(tmp_path, d(2025, 7, 1), cloud_cover=0.1),
        acquisition_scene(tmp_path, d(2025, 6, 26)),
        acquisition_scene(tmp_path, d(2025, 9, 28), cloud_cover=30.0),
    )


def chip(name, role, col):
    """A 64 px chip of the fixture grid, centred on a column of its middle row."""
    return TrainingChip(site_at(ROW, col, name=name), role, "forest")


def training_config():
    """A training chip declared first, then two validation chips, all apart."""
    chips = [
        chip("plain", TRAIN, 200),
        chip("town", VALIDATION, 80),
        chip("shore", VALIDATION, 320),
    ]
    return TrainingConfig({c.name: c for c in chips}, RULES, BENCHMARK)


def test_validation_pairs_are_cut_from_the_anchor_of_the_validation_chips(
    tmp_path, scenes
):
    anchors = load_validation_chips(training_config(), CONFIG, tmp_path, None, scenes)

    assert list(anchors) == ["town", "shore"]
    assert all(a.role == ANCHOR for a in anchors.values())
    assert anchors["town"].image.shape == (64, 64)
    assert anchors["town"].datetime.date() == dt.date(2025, 7, 1)


@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("plain", "plain is a train chip: no validation pair"),
        ("beauce", "beauce is a benchmark chip"),
        ("alps", "alps is a held-out site"),
        ("nowhere", "unknown chip 'nowhere'"),
    ],
)
def test_no_validation_pair_is_cut_from_any_other_chip(tmp_path, scenes, name, message):
    with pytest.raises(ValueError, match=message):
        load_validation_chips(training_config(), CONFIG, tmp_path, [name], scenes)

    assert scenes.calls == []


def test_closure_series_are_those_of_the_validation_then_the_training_chips(
    tmp_path, scenes
):
    loaded = load_closure_series(training_config(), CONFIG, tmp_path, None, scenes)

    assert {name: role for name, (role, _) in loaded.items()} == {
        "town": VALIDATION,
        "shore": VALIDATION,
        "plain": TRAIN,
    }
    assert list(loaded) == ["town", "shore", "plain"]
    assert [a.role for a in loaded["plain"][1]] == ["days", "anchor", "season"]


def test_closure_series_can_be_asked_for_by_name(tmp_path, scenes):
    loaded = load_closure_series(training_config(), CONFIG, tmp_path, ["plain"], scenes)

    assert list(loaded) == ["plain"]


@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("beauce", "beauce is a benchmark chip"),
        ("alps", "alps is a held-out site"),
        ("nowhere", "unknown chip 'nowhere'"),
    ],
)
def test_closure_is_not_read_on_a_benchmark_chip_or_a_held_out_site(
    tmp_path, scenes, name, message
):
    with pytest.raises(ValueError, match=message):
        load_closure_series(training_config(), CONFIG, tmp_path, [name], scenes)

    assert scenes.calls == []


def run(n_pairs, sites=("town", "shore")):
    """A small validation run on synthetic chips, with a classic method."""
    images = {name: fractal_texture(256, seed=i) for i, name in enumerate(sites)}
    methods = load_methods(CONFIGS / "methods.toml")
    config = BenchmarkConfig(
        n_pairs=n_pairs, size=64, scenarios=("translation", "affine"), seed=5
    )
    presets = {name: PRESETS[name] for name in ("clean", "hard")}
    chosen = {"phase_correlation": methods["phase_correlation"]}
    return run_benchmark(images, chosen, config, presets)


def test_the_pooled_table_has_one_row_per_scenario_and_preset_over_every_chip():
    rows = pooled(run(3))

    assert [(r.site, r.scenario, r.degradation, r.n_pairs) for r in rows] == [
        (POOLED, "translation", "clean", 6),
        (POOLED, "translation", "hard", 6),
        (POOLED, "affine", "clean", 6),
        (POOLED, "affine", "hard", 6),
    ]


def test_a_light_set_is_the_first_pairs_of_every_cell_of_the_full_set():
    full, light = run(5), run(2)

    assert light == [r for r in full if r.pair < 2]


def result(method, pair, epe, degradation="clean", site="town"):
    """One scored pair; a NaN error is a failed pair."""
    return PairResult(
        site=site,
        bands="",
        scenario="translation",
        degradation=degradation,
        method=method,
        device="cpu",
        pair=pair,
        cloud_fraction=0.0,
        truth="",
        estimate="",
        mean_epe=epe,
        share_below_0_1=0.0,
        share_below_0_5=0.0,
        failed=math.isnan(epe),
        error="",
        diagnostics="",
        time_ms=1.0,
        peak_mib=1.0,
    )


def test_a_light_set_is_compared_with_the_full_set_on_error_failures_and_gap():
    large = [0.1, 0.2, 0.3, 0.4]
    small = [0.2, 0.4, math.nan, 0.8]
    results = [result("large", i, e) for i, e in enumerate(large)]
    results += [result("small", i, e) for i, e in enumerate(small)]

    rows = subset_tracking(results, [2, 4, 9])

    # Sizes that are not smaller than the full set compare nothing.
    assert {r.pairs for r in rows} == {2}
    base, other = (r for r in rows if r.degradation == "clean")
    assert (base.method, other.method) == ("large", "small")
    assert base.mean_epe == pytest.approx(0.15)
    assert base.full_mean_epe == pytest.approx(0.25)
    assert math.isnan(base.gap) and math.isnan(base.full_gap)
    assert other.failure_rate == 0.0
    assert other.full_failure_rate == 0.25
    assert other.mean_epe == pytest.approx(0.3)
    assert other.full_mean_epe == pytest.approx(1.4 / 3)
    # The gap is over the pairs neither method fails: the third one is left out.
    assert other.gap == pytest.approx(0.15)
    assert other.full_gap == pytest.approx(0.7 / 3)
    assert 0 < other.gap_spread < 0.2
    assert 0 < base.epe_spread < 0.2


def test_light_sets_are_also_compared_over_every_preset_and_chip():
    results = [
        result("large", i, e, degradation, site)
        for site in ("town", "shore")
        for degradation, errors in (("clean", [0.1, 0.3]), ("hard", [0.5, 0.9]))
        for i, e in enumerate(errors)
    ]

    rows = subset_tracking(results, [1])

    assert [r.degradation for r in rows] == ["clean", "hard", ALL_PRESETS]
    assert [r.mean_epe for r in rows] == pytest.approx([0.1, 0.5, 0.3])
    assert [r.full_mean_epe for r in rows] == pytest.approx([0.2, 0.7, 0.45])
    table = subsets_markdown(rows)
    assert "| 1 | all | large | 0.0 % | 0.0 % | 0.3000 | 0.4500 |" in table
    assert table.count("n/a") == 3 * len(rows)


def triplet(site, closure, failed=False):
    return TripletRow(
        site=site,
        scenario=REAL,
        triplet="days-anchor-season",
        window=0,
        method="raft",
        device="cpu",
        cloud_fraction=0.0,
        mean_closure=closure,
        share_below_0_1=0.5,
        share_below_0_5=1.0,
        true_epe=math.nan,
        truth_closure=math.nan,
        failed=failed,
        error="",
        time_ms=1.0,
        peak_mib=1.0,
    )


def test_closure_is_pooled_over_the_chips_of_each_role():
    rows = [
        triplet("town", 0.1),
        triplet("shore", 0.3),
        triplet("plain", 0.6),
        triplet("plain", math.nan, failed=True),
    ]
    roles = {"town": VALIDATION, "shore": VALIDATION, "plain": TRAIN}

    validation, train = closure_by_role(rows, roles)

    assert (validation.site, validation.triplet) == ("validation chips", ALL_TRIPLETS)
    assert validation.n_triplets == 2
    assert validation.mean_closure == pytest.approx(0.2)
    assert train.site == "train chips"
    assert train.failure_rate == 0.5
    assert train.mean_closure == pytest.approx(0.6)


@pytest.fixture
def cached(tmp_path, scenes):
    """Configure a validation chip, in the cache, and a training chip that is not.

    Returns:
        The options of ``validate`` and ``validate-cycle`` that read it without
        any fetch.
    """
    site = site_at(*CENTRE)
    (tmp_path / "sites.toml").write_text(SITES_TOML)
    train = tmp_path / "train-sites.toml"
    train.write_text(
        "[defaults]\nchip_px = 256\nstart = 2025-04-01\nend = 2025-09-30\n"
        "max_cloud = 5.0\n"
        '[chips.town]\nlandscape = "urban"\nrole = "validation"\n'
        f"lon = {site.lon}\nlat = {site.lat}\n"
        '[chips.place]\nlandscape = "forest"\nrole = "train"\n'
        "lon = 3.0\nlat = 45.0\n"
    )
    series = tmp_path / "real.toml"
    series.write_text(
        '[series]\nsites = ["beauce"]\nmax_scene_cloud = 50.0\n[series.dates]\n'
        "days = { offset_days = 0, within_days = 15 }\n"
        "season = { offset_days = 91, within_days = 30 }\n"
    )
    town = TrainingChip(
        site_at(*CENTRE, chip_px=256, name="town", max_chip_cloud=site.max_chip_cloud),
        VALIDATION,
        "urban",
    )
    config = TrainingConfig({"town": town}, RULES, BENCHMARK)
    load_validation_chips(config, CONFIG, tmp_path / "data", None, scenes)
    return [
        "--sites-config",
        str(tmp_path / "sites.toml"),
        "--train-config",
        str(train),
        "--series-config",
        str(series),
        "--methods-config",
        str(CONFIGS / "methods.toml"),
        "--data-dir",
        str(tmp_path / "data"),
        "--out",
        str(tmp_path / "out"),
        "--methods",
        "phase_correlation",
    ]


SMALL = [
    "--degradations-config",
    str(CONFIGS / "degradations.toml"),
    "--degradations",
    "clean",
    "--scenarios",
    "translation",
    "--size",
    "64",
]


def test_validate_scores_the_validation_chips_and_writes_its_tables(
    tmp_path, capsys, cached
):
    main(["validate", "--pairs", "4", "--subset-sizes", "2"] + SMALL + cached)

    printed = capsys.readouterr().out
    out = tmp_path / "out"
    assert (out / "summary.md").read_text() == printed
    assert "4 pairs per chip, scenario and preset, seed 0" in printed
    assert (
        "| all chips | translation | clean | phase_correlation | cpu | 4 |" in printed
    )
    assert "| town | translation | clean | phase_correlation | cpu | 4 |" in printed
    assert "| 2 | clean | phase_correlation |" in printed
    assert len((out / "pairs.csv").read_text().splitlines()) == 1 + 4
    assert len((out / "pooled.csv").read_text().splitlines()) == 1 + 1
    assert len((out / "subsets.csv").read_text().splitlines()) == 1 + 2
    context = json.loads((out / "context.json").read_text())
    assert list(context["validation"]["chips"]) == ["town"]
    assert context["validation"]["pairs_per_cell"] == 4
    assert context["held_out_sites"] == []


def test_the_light_run_scores_the_first_pairs_of_the_full_one(tmp_path, capsys, cached):
    main(["validate", "--pairs", "4", "--subset-sizes", "2"] + SMALL + cached)
    main(["validate", "--pairs", "4", "--light", "--light-pairs", "2"] + SMALL + cached)

    printed = capsys.readouterr().out
    light = tmp_path / "out-light"
    assert "Light validation set: 2 pairs per chip" in printed
    assert "the first 2 pairs of every cell of the full set, which has 4" in printed
    assert not (light / "subsets.csv").exists()

    def outcomes(path):
        # Without the cost columns, which change from one run to the next.
        return [line.rsplit(",", 2)[0] for line in path.read_text().splitlines()]

    full = outcomes(tmp_path / "out" / "pairs.csv")
    assert outcomes(light / "pairs.csv") == full[:3]


@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("place", "place is a train chip: no validation pair"),
        ("beauce", "beauce is a benchmark chip"),
        ("alps", "alps is a held-out site"),
    ],
)
def test_validate_refuses_a_chip_that_is_not_a_validation_chip(
    tmp_path, cached, name, message
):
    with pytest.raises(SystemExit, match=message):
        main(["validate", "--chip", name] + SMALL + cached)

    assert not (tmp_path / "out").exists()


def test_validate_cycle_scores_the_real_triplets_of_the_chips(tmp_path, capsys, cached):
    main(["validate-cycle", "--chip", "town"] + cached)

    printed = capsys.readouterr().out
    out = tmp_path / "out"
    assert (out / "summary.md").read_text() == printed
    # Three dates, one triplet, one 256 px window.
    assert "| validation chips | all | phase_correlation | cpu | 1 |" in printed
    assert "| town | days-anchor-season | phase_correlation | cpu | 1 |" in printed
    assert "Validation chips: town." in printed
    assert "Simulated" not in printed and "simulated" not in printed
    assert len((out / "triplets.csv").read_text().splitlines()) == 1 + 1
    assert len((out / "by_role.csv").read_text().splitlines()) == 1 + 1
    context = json.loads((out / "context.json").read_text())
    assert context["validation"]["chips"] == {"town": "validation"}


@pytest.mark.parametrize("name", ["beauce", "alps"])
def test_validate_cycle_refuses_a_benchmark_chip_or_a_held_out_site(
    tmp_path, cached, name
):
    with pytest.raises(SystemExit, match=f"{name} is a .*validation chips only"):
        main(["validate-cycle", "--chip", name] + cached)

    assert not (tmp_path / "out").exists()


def test_validate_and_validate_cycle_read_their_own_table(tmp_path):
    config = tmp_path / "run.toml"
    config.write_text(
        '[validate]\npairs = 7\nlight_pairs = 3\nchips = ["town"]\n'
        '[validate_cycle]\nmethods = ["raft"]\nout = "outputs/vc"\n'
    )

    scoring = parse_args(["validate", "--config", str(config), "--seed", "4"])
    closing = parse_args(["validate-cycle", "--config", str(config)])

    assert (scoring.pairs, scoring.light_pairs, scoring.seed) == (7, 3, 4)
    assert scoring.chips == ["town"]
    assert closing.methods == ["raft"]
    assert closing.out == Path("outputs/vc")


def test_the_repository_validation_set_is_the_validation_chips_scored_as_n2():
    options = load_run_config(CONFIGS / "validation.toml", "validate")
    final = load_run_config(CONFIGS / "n2.toml")
    training = load_training_chips(
        CONFIGS / "train-sites.toml", load_sites(CONFIGS / "sites.toml")
    )

    assert options["chips"] == [c.name for c in training.select(VALIDATION)]
    assert options["methods"] == ["raft", "raft_small"]
    # The same cells as the final table: scenarios, presets, pairs, ranges.
    same = ["scenarios", "degradations", "pairs", "size", "seed", "failure_threshold"]
    same += [key for key in final if key.startswith(("max_", "local_"))]
    assert {key: options[key] for key in same} == {key: final[key] for key in same}
    assert 0 < options["light_pairs"] < options["pairs"]
    closing = load_run_config(CONFIGS / "validation.toml", "validate-cycle")
    assert closing["methods"] == options["methods"]
    assert "chips" not in closing

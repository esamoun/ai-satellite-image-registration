import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio
from test_ingest import CENTRE, CRS, TRANSFORM, site_at, write_cog

from satreg import cli
from satreg.cli import load_run_config, main, parse_args, site_images
from satreg.georef import NOMINAL
from satreg.ingest import cache_path
from satreg.methods import load_methods, missing_dependencies
from satreg.methods.arosics import Arosics
from satreg.real import ANCHOR, load_series_config, series_path
from satreg.sites import load_sites

CONFIGS = Path(__file__).parents[1] / "configs"
PRESETS = [
    "--degradations-config",
    str(CONFIGS / "degradations.toml"),
    "--methods-config",
    str(CONFIGS / "methods.toml"),
]


def test_benchmark_writes_its_tables_and_prints_the_summary(tmp_path, capsys):
    main(
        ["benchmark", "--pairs", "3", "--size", "64", "--out", str(tmp_path)] + PRESETS
    )

    printed = capsys.readouterr().out
    # Every configured preset, in file order.
    row = "| synthetic | translation | clean | phase_correlation | cpu | 3 | 0.0 % |"
    assert row in printed
    assert printed.index("| mild |") < printed.index("| hard |")
    assert (tmp_path / "summary.md").read_text() == printed
    assert (tmp_path / "pairs.csv").exists()
    assert (tmp_path / "summary.csv").exists()


def test_module_is_runnable():
    result = subprocess.run(
        [sys.executable, "-m", "satreg", "--help"], capture_output=True, text=True
    )

    assert result.returncode == 0
    assert "benchmark" in result.stdout


def _cached_site(tmp_path, extra=""):
    """Configure a site and put its chip in the cache, so no fetch happens."""
    site = site_at(*CENTRE, chip_px=128)
    config = tmp_path / "sites.toml"
    config.write_text(
        '[stac]\nurl = "https://stac.example"\ncollection = "sentinel-2-c1-l2a"\n'
        f"[sites.beauce]\nlon = {site.lon}\nlat = {site.lat}\nchip_px = 128\n"
        "start = 2025-04-01\nend = 2025-09-30\nmax_cloud = 5.0\n" + extra
    )
    catalogue = load_sites(config).catalogue
    chip = cache_path(site, catalogue, tmp_path / "data")
    chip.parent.mkdir(parents=True)
    texture = np.random.default_rng(0).integers(1, 10_000, (128, 128), np.uint16)
    write_cog(chip, texture)
    return ["--sites-config", str(config), "--data-dir", str(tmp_path / "data")]


@pytest.fixture
def cached_site(tmp_path):
    """A configured site whose chip is already in the cache."""
    return _cached_site(tmp_path)


@pytest.fixture
def held_out_site(tmp_path):
    """The same site, held out, whose chip is in the cache under the same key."""
    return _cached_site(tmp_path, "held_out = true\n")


def test_benchmark_runs_on_a_configured_site_from_the_cache(
    tmp_path, capsys, cached_site
):
    out = tmp_path / "out"
    main(
        ["benchmark", "--site", "beauce", "--pairs", "2", "--size", "64"]
        + ["--degradations", "clean"]
        + PRESETS
        + cached_site
        + ["--out", str(out)]
    )

    printed = capsys.readouterr().out
    assert "| beauce | translation | clean | phase_correlation | cpu | 2 |" in printed
    assert "synthetic" not in printed
    assert "mild" not in printed
    assert (out / "summary.md").read_text() == printed


def test_context_names_no_held_out_site_when_none_ran(tmp_path, cached_site):
    out = tmp_path / "out"
    main(
        ["benchmark", "--site", "beauce", "--pairs", "1", "--size", "64"]
        + ["--degradations", "clean", "--methods", "phase_correlation"]
        + PRESETS
        + cached_site
        + ["--out", str(out)]
    )

    assert json.loads((out / "context.json").read_text())["held_out_sites"] == []
    assert "Held-out" not in (out / "summary.md").read_text()


def test_a_held_out_site_is_refused_before_anything_runs(tmp_path, held_out_site):
    out = tmp_path / "out"

    with pytest.raises(SystemExit, match="'beauce' is held out.*--allow-held-out"):
        main(["benchmark", "--site", "beauce", "--out", str(out)] + held_out_site)
    assert not out.exists()


def test_a_run_allowed_on_a_held_out_site_says_so(tmp_path, capsys, held_out_site):
    out = tmp_path / "out"
    main(
        ["benchmark", "--site", "beauce", "--allow-held-out", "--pairs", "1"]
        + ["--size", "64", "--degradations", "clean"]
        + ["--methods", "phase_correlation"]
        + PRESETS
        + held_out_site
        + ["--out", str(out)]
    )

    printed = capsys.readouterr().out
    assert printed.endswith(
        "Held-out sites in this table: beauce. They are kept for the final "
        "evaluation: no threshold, preset or variant may be chosen on their rows.\n"
    )
    context = json.loads((out / "context.json").read_text())
    assert context["held_out_sites"] == ["beauce"]
    assert context["run"]["allow_held_out"] is True


def test_fetch_prints_the_cached_chip(capsys, cached_site):
    main(["fetch", "--site", "beauce"] + cached_site)

    assert capsys.readouterr().out.strip().endswith(".tif")


def test_unknown_site_is_reported_with_the_configured_ones(cached_site):
    with pytest.raises(SystemExit, match="unknown site 'alps'.*beauce"):
        main(["benchmark", "--site", "alps"] + cached_site)


def test_benchmark_sweeps_the_named_presets_in_the_order_given(tmp_path, capsys):
    main(
        ["benchmark", "--pairs", "2", "--size", "64", "--out", str(tmp_path)]
        + ["--degradations", "hard", "clean"]
        + PRESETS
    )

    printed = capsys.readouterr().out
    assert printed.index("| hard |") < printed.index("| clean |")
    assert "| mild |" not in printed
    assert "cloud_fraction" in (tmp_path / "pairs.csv").read_text().splitlines()[0]


def test_benchmark_runs_only_the_requested_scenarios(tmp_path, capsys):
    main(
        ["benchmark", "--pairs", "2", "--size", "64", "--out", str(tmp_path)]
        + ["--degradations", "clean", "--scenarios", "affine", "--max-rotation", "0.5"]
        + PRESETS
    )

    printed = capsys.readouterr().out
    assert "| synthetic | affine | clean | phase_correlation | cpu | 2 |" in printed
    assert "translation" not in printed


def test_benchmark_runs_the_dense_scenario(tmp_path, capsys):
    main(
        ["benchmark", "--pairs", "2", "--size", "64", "--out", str(tmp_path)]
        + ["--degradations", "clean", "--scenarios", "dense"]
        + ["--methods", "phase_correlation"]
        + ["--max-local-shift", "1.5", "--local-length", "32"]
        + PRESETS
    )

    printed = capsys.readouterr().out
    assert "| synthetic | dense | clean | phase_correlation | cpu | 2 |" in printed
    assert "| affine |" not in printed
    rows = (tmp_path / "pairs.csv").read_text().splitlines()
    assert all(",dense," in row for row in rows[1:])
    run = json.loads((tmp_path / "context.json").read_text())["run"]
    assert (run["max_local_shift"], run["local_length"]) == (1.5, 32.0)


def test_unknown_preset_is_reported_with_the_configured_ones(tmp_path):
    with pytest.raises(SystemExit, match="unknown degradation preset 'foggy'.*mild"):
        main(["benchmark", "--degradations", "foggy"] + PRESETS)


def test_missing_presets_file_is_reported(tmp_path):
    with pytest.raises(SystemExit, match="no degradation presets"):
        main(["benchmark", "--degradations-config", str(tmp_path / "none.toml")])


def test_benchmark_runs_sift_ransac_and_writes_its_diagnostics(tmp_path, capsys):
    main(
        ["benchmark", "--pairs", "2", "--size", "64", "--out", str(tmp_path)]
        + ["--degradations", "clean", "--methods", "sift_ransac"]
        + PRESETS
    )

    printed = capsys.readouterr().out
    assert "| synthetic | affine | clean | sift_ransac | cpu | 2 |" in printed
    assert "phase_correlation" not in printed
    assert '""inliers"": ' in (tmp_path / "pairs.csv").read_text()


def test_missing_method_parameters_file_is_reported(tmp_path):
    with pytest.raises(SystemExit, match="no method parameters"):
        main(
            ["benchmark", "--methods-config", str(tmp_path / "none.toml")] + PRESETS[:2]
        )


def without_arosics(method):
    # Other methods keep what this machine really lacks.
    return ["osgeo"] if isinstance(method, Arosics) else missing_dependencies(method)


def test_default_methods_leave_out_those_not_installed(tmp_path, capsys, monkeypatch):
    # The defaults are chosen in the methods package, when the parser is built.
    monkeypatch.setattr("satreg.methods.missing_dependencies", without_arosics)

    main(
        ["benchmark", "--pairs", "2", "--size", "64", "--out", str(tmp_path)]
        + ["--degradations", "clean"]
        + PRESETS
    )

    printed = capsys.readouterr().out
    assert "| phase_correlation |" in printed
    assert "arosics" not in printed


def test_default_methods_leave_out_roma_even_when_installed(monkeypatch):
    monkeypatch.setattr("satreg.methods.missing_dependencies", lambda method: [])

    args = parse_args(["benchmark"])

    assert "roma" not in args.methods
    assert "raft" in args.methods
    assert parse_args(["benchmark", "--methods", "roma"]).methods == ["roma"]


def test_requesting_a_method_not_installed_is_reported(monkeypatch):
    monkeypatch.setattr(cli, "missing_dependencies", without_arosics)

    with pytest.raises(SystemExit, match="arosics needs osgeo.*README"):
        main(["benchmark", "--methods", "arosics"] + PRESETS)


def test_device_option_moves_every_deep_learning_method(monkeypatch):
    monkeypatch.setattr(cli, "missing_dependencies", lambda method: [])
    monkeypatch.setattr(cli, "check_available", lambda device: None)
    names = ["raft", "lightglue_disk", "phase_correlation"]

    args = parse_args(["benchmark", "--methods", *names, "--device", "cuda"] + PRESETS)
    methods = cli.configured_methods(args)

    assert methods["raft"].device == "cuda"
    assert methods["lightglue_disk"].device == "cuda"
    # The variant keeps its other parameters.
    assert methods["lightglue_disk"].features == "disk"
    assert not hasattr(methods["phase_correlation"], "device")


def test_without_the_device_option_methods_keep_their_configured_device(
    monkeypatch,
):
    monkeypatch.setattr(cli, "missing_dependencies", lambda method: [])

    args = parse_args(["benchmark", "--methods", "raft"] + PRESETS)

    assert cli.configured_methods(args)["raft"].device == "cpu"


def test_a_device_the_machine_lacks_is_refused_before_the_first_pair(monkeypatch):
    monkeypatch.setattr(cli, "missing_dependencies", lambda method: [])

    def unavailable(device):
        raise RuntimeError(f"device {device} is not available on this machine")

    monkeypatch.setattr(cli, "check_available", unavailable)

    with pytest.raises(SystemExit, match="method raft: device cuda is not available"):
        main(["benchmark", "--methods", "raft", "--device", "cuda"] + PRESETS)


def test_synthetic_site_gets_the_nominal_grid():
    args = cli._parser().parse_args(["benchmark"])

    images, georefs = site_images(args)

    assert georefs == {"synthetic": NOMINAL}
    assert images["synthetic"].ndim == 2


def test_benchmark_runs_a_variant_declared_in_the_methods_config(tmp_path, capsys):
    main(
        ["benchmark", "--pairs", "2", "--size", "64", "--out", str(tmp_path)]
        + ["--degradations", "clean", "--methods", "phase_correlation_hann"]
        + PRESETS
    )

    assert "| synthetic | translation | clean | phase_correlation_hann | cpu | 2 |" in (
        capsys.readouterr().out
    )


def test_requesting_an_unknown_method_names_the_known_ones(tmp_path):
    with pytest.raises(
        SystemExit, match="unknown method 'orb'.*phase_correlation_hann"
    ):
        main(["benchmark", "--methods", "orb"] + PRESETS)


def write_run_config(path, **options):
    lines = ["[benchmark]"] + [f"{k} = {json.dumps(v)}" for k, v in options.items()]
    path.write_text("\n".join(lines) + "\n")
    return path


def test_run_config_sets_the_options(tmp_path, capsys):
    config = write_run_config(
        tmp_path / "run.toml",
        pairs=2,
        size=64,
        scenarios=["affine"],
        degradations=["clean"],
        methods=["phase_correlation"],
        out=str(tmp_path / "out"),
        degradations_config=PRESETS[1],
        methods_config=PRESETS[3],
    )

    main(["benchmark", "--config", str(config)])

    printed = capsys.readouterr().out
    assert "| synthetic | affine | clean | phase_correlation | cpu | 2 |" in printed
    assert "translation" not in printed
    assert (tmp_path / "out" / "summary.md").read_text() == printed


def test_command_line_overrides_the_run_config(tmp_path):
    config = write_run_config(tmp_path / "run.toml", pairs=50, seed=3)

    args = parse_args(["benchmark", "--config", str(config), "--pairs", "7"])

    assert args.pairs == 7
    assert args.seed == 3


def test_run_config_paths_are_read_as_paths(tmp_path):
    config = write_run_config(tmp_path / "run.toml", out="outputs/n1")

    args = parse_args(["benchmark", "--config", str(config)])

    assert args.out == Path("outputs/n1")


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("[benchmark]\nn_pairs = 5\n", "unknown benchmark option 'n_pairs'.*pairs"),
        ("[run]\npairs = 5\n", "needs a \\[benchmark\\] table"),
    ],
)
def test_bad_run_config_is_rejected(tmp_path, text, message):
    config = tmp_path / "run.toml"
    config.write_text(text)

    with pytest.raises(SystemExit, match=message):
        parse_args(["benchmark", "--config", str(config)])


def test_missing_run_config_is_reported(tmp_path):
    with pytest.raises(SystemExit, match="no run configuration"):
        parse_args(["benchmark", "--config", str(tmp_path / "none.toml")])


def test_repository_n1_config_is_valid():
    options = load_run_config(CONFIGS / "n1.toml")

    assert options["sites"] == ["beauce", "toulouse"]
    assert {"phase_correlation", "sift_ransac", "arosics"} <= set(options["methods"])


def test_repository_gpu_config_runs_the_deep_learning_methods_on_cuda():
    options = load_run_config(CONFIGS / "gpu.toml")
    methods = load_methods(CONFIGS / "methods.toml")

    assert options["device"] == "cuda"
    assert {"raft", "lightglue", "roma"} <= set(options["methods"])
    assert all(hasattr(methods[name], "device") for name in options["methods"])


def test_context_records_every_option_of_the_run(tmp_path):
    main(
        ["benchmark", "--pairs", "2", "--size", "64", "--out", str(tmp_path)]
        + ["--degradations", "clean", "--seed", "11"]
        + PRESETS
    )

    run = json.loads((tmp_path / "context.json").read_text())["run"]
    assert run["seed"] == 11
    assert run["pairs"] == 2
    assert run["out"] == str(tmp_path)
    assert run["config"] is None


SERIES_DATES = {
    ANCHOR: (dt.date(2025, 7, 1), "sentinel-2b"),
    "days": (dt.date(2025, 6, 26), "sentinel-2c"),
    "season": (dt.date(2025, 9, 28), "sentinel-2a"),
}


def _cached_series(tmp_path, extra=""):
    """Configure a site and a series, and put every date of it in the cache."""
    site = site_at(*CENTRE, chip_px=256)
    sites_config = tmp_path / "sites.toml"
    sites_config.write_text(
        '[stac]\nurl = "https://stac.example"\ncollection = "sentinel-2-c1-l2a"\n'
        f"[sites.beauce]\nlon = {site.lon}\nlat = {site.lat}\nchip_px = 256\n"
        "start = 2025-04-01\nend = 2025-09-30\nmax_cloud = 5.0\n" + extra
    )
    series_config = tmp_path / "real.toml"
    series_config.write_text(
        '[series]\nsites = ["beauce"]\n[series.dates]\n'
        "days = { offset_days = 0, within_days = 15 }\n"
        "season = { offset_days = 91, within_days = 30 }\n"
    )
    sites = load_sites(sites_config)
    config = load_series_config(series_config)
    base = np.random.default_rng(0).integers(1000, 5000, (256, 256), np.uint16)
    for i, (role, (day, platform)) in enumerate(SERIES_DATES.items()):
        path = series_path(
            sites.sites["beauce"], sites.catalogue, config, role, tmp_path / "data"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        scl = np.full((256, 256), 4, np.uint16)
        scl[0, : 10 * (i + 1)] = 9  # a few cloudy pixels, more each date
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            width=256,
            height=256,
            count=2,
            dtype=np.uint16,
            crs=CRS,
            transform=TRANSFORM,
            nodata=0,
        ) as dst:
            dst.write(base + 100 * i, 1)
            dst.write(scl, 2)
            dst.update_tags(
                role=role,
                item_id=f"S2_{day:%Y%m%d}",
                datetime=f"{day.isoformat()}T10:56:29+00:00",
                platform=platform,
            )
    return [
        "--sites-config",
        str(sites_config),
        "--series-config",
        str(series_config),
        "--data-dir",
        str(tmp_path / "data"),
    ]


@pytest.fixture
def cached_series(tmp_path):
    """A configured site whose series is already in the cache."""
    return _cached_series(tmp_path)


def test_real_pairs_lists_the_cached_pairs_without_any_search(capsys, cached_series):
    main(["real-pairs"] + cached_series)

    printed = capsys.readouterr().out
    assert (
        "| beauce | days-anchor | 2025-06-26 | 2025-07-01 | 5 "
        "| sentinel-2c/sentinel-2b | 0.03 % |"
    ) in printed
    assert "| beauce | anchor-season | 2025-07-01 | 2025-09-28 | 89 |" in printed
    assert printed.count("| beauce |") == 3
    assert printed.endswith("Triplets: beauce 1.\n")


def test_real_pairs_lists_a_held_out_site_as_such(tmp_path, capsys):
    main(["real-pairs"] + _cached_series(tmp_path, "held_out = true\n"))

    assert "| beauce (held out) | days-anchor |" in capsys.readouterr().out


def test_check_presets_writes_real_pairs_and_presets_side_by_side(
    tmp_path, capsys, cached_series
):
    out = tmp_path / "out"

    main(["check-presets", "--out", str(out)] + PRESETS[:2] + cached_series)

    printed = capsys.readouterr().out
    assert (out / "summary.md").read_text() == printed
    assert printed.index("| preset `clean` |") < printed.index("| preset `hard` |")
    # Role pairs are named in series order, whichever date came first.
    assert printed.index("| preset `hard` |") < printed.index("| anchor-days | 1 |")
    assert "| ↳ nominal | | | 15 (added) |" in printed
    assert "Sites: beauce." in printed
    assert "Held-out" not in printed
    csv = (out / "pairs.csv").read_text().splitlines()
    assert len(csv) == 1 + 3 + 3  # header, three real pairs, three presets


def test_check_presets_refuses_a_held_out_site_named_on_the_command_line(tmp_path):
    held_out = _cached_series(tmp_path, "held_out = true\n")

    with pytest.raises(SystemExit, match="'beauce' is held out.*--allow-held-out"):
        main(
            ["check-presets", "--site", "beauce", "--out", str(tmp_path / "out")]
            + held_out
        )
    assert not (tmp_path / "out").exists()


def test_check_presets_leaves_held_out_sites_out_unless_allowed(tmp_path, capsys):
    held_out = _cached_series(tmp_path, "held_out = true\n")
    out = tmp_path / "out"

    with pytest.raises(SystemExit, match="every site of the series is held out"):
        main(["check-presets", "--out", str(out)] + held_out)

    main(
        ["check-presets", "--allow-held-out", "--out", str(out)]
        + PRESETS[:2]
        + held_out
    )
    assert "Held-out sites in this table: beauce." in capsys.readouterr().out


def test_missing_series_config_is_reported(cached_site, tmp_path):
    missing = ["--series-config", str(tmp_path / "none.toml")]

    with pytest.raises(SystemExit, match="no series configuration"):
        main(["real-pairs"] + cached_site + missing)


def test_cycle_scores_the_real_triplets_and_writes_its_tables(
    tmp_path, capsys, cached_series
):
    out = tmp_path / "out"

    main(
        ["cycle", "--methods", "phase_correlation", "--simulated-triplets", "0"]
        + ["--out", str(out)]
        + PRESETS
        + cached_series
    )

    printed = capsys.readouterr().out
    assert (out / "summary.md").read_text() == printed
    # Three dates, one triplet, one 256 px window: three pairs registered once.
    assert "| beauce | days-anchor-season | phase_correlation | cpu | 1 |" in printed
    assert "| days-anchor | phase_correlation | 1 |" not in printed
    assert "| anchor-days | phase_correlation | 1 |" in printed
    assert "true EPE" not in printed
    assert len((out / "legs.csv").read_text().splitlines()) == 1 + 3
    assert len((out / "triplets.csv").read_text().splitlines()) == 1 + 1
    context = json.loads((out / "context.json").read_text())
    assert context["held_out_sites"] == []
    assert context["run"]["simulated_triplets"] == 0


def test_cycle_refuses_a_held_out_site_named_on_the_command_line(tmp_path):
    held_out = _cached_series(tmp_path, "held_out = true\n")

    with pytest.raises(SystemExit, match="'beauce' is held out.*--allow-held-out"):
        main(["cycle", "--site", "beauce", "--out", str(tmp_path / "out")] + held_out)
    assert not (tmp_path / "out").exists()

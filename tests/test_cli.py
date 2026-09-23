import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from test_ingest import CENTRE, site_at, write_cog

from satreg.cli import main
from satreg.ingest import cache_path
from satreg.sites import load_sites

PRESETS = [
    "--degradations-config",
    str(Path(__file__).parents[1] / "configs" / "degradations.toml"),
]


def test_benchmark_writes_its_tables_and_prints_the_summary(tmp_path, capsys):
    main(
        ["benchmark", "--pairs", "3", "--size", "64", "--out", str(tmp_path)] + PRESETS
    )

    printed = capsys.readouterr().out
    # Every configured preset, in file order.
    assert "| synthetic | clean | phase_correlation | 3 | 0.0 % |" in printed
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


@pytest.fixture
def cached_site(tmp_path):
    """A configured site whose chip is already in the cache, so no fetch happens."""
    site = site_at(*CENTRE, chip_px=128)
    config = tmp_path / "sites.toml"
    config.write_text(
        '[stac]\nurl = "https://stac.example"\ncollection = "sentinel-2-c1-l2a"\n'
        f"[sites.beauce]\nlon = {site.lon}\nlat = {site.lat}\nchip_px = 128\n"
        "start = 2025-04-01\nend = 2025-09-30\nmax_cloud = 5.0\n"
    )
    catalogue = load_sites(config).catalogue
    chip = cache_path(site, catalogue, tmp_path / "data")
    chip.parent.mkdir(parents=True)
    texture = np.random.default_rng(0).integers(1, 10_000, (128, 128), np.uint16)
    write_cog(chip, texture)
    return ["--sites-config", str(config), "--data-dir", str(tmp_path / "data")]


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
    assert "| beauce | clean | phase_correlation | 2 |" in printed
    assert "synthetic" not in printed
    assert "mild" not in printed
    assert (out / "summary.md").read_text() == printed


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


def test_unknown_preset_is_reported_with_the_configured_ones(tmp_path):
    with pytest.raises(SystemExit, match="unknown degradation preset 'foggy'.*mild"):
        main(["benchmark", "--degradations", "foggy"] + PRESETS)


def test_missing_presets_file_is_reported(tmp_path):
    with pytest.raises(SystemExit, match="no degradation presets"):
        main(["benchmark", "--degradations-config", str(tmp_path / "none.toml")])

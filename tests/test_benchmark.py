import csv
import math

import numpy as np
import pytest

from satreg.benchmark import (
    BenchmarkConfig,
    _rng,
    draw_pair,
    max_reach,
    run_benchmark,
)
from satreg.degrade import Clouds, Noise, Preset
from satreg.displacement import Affine, Displacement, Translation
from satreg.georef import NOMINAL
from satreg.methods.base import GeoreferencedMethod
from satreg.methods.phase_correlation import phase_correlation
from satreg.report import summarize, to_markdown, write_csv
from satreg.simulate import affine_reach
from satreg.texture import fractal_texture

CONFIG = BenchmarkConfig(
    n_pairs=4, size=64, max_shift=2.0, seed=0, scenarios=("translation",)
)
BOTH = BenchmarkConfig(n_pairs=4, size=64, max_shift=2.0, seed=0)
SITES = {"synthetic": fractal_texture(256, seed=0)}


def crashes(reference, moving):
    raise RuntimeError("no peak")


def far_off(reference, moving):
    return Translation(dx=50.0, dy=0.0)


def test_same_seed_gives_same_results():
    methods = {"phase_correlation": phase_correlation}

    first = run_benchmark(SITES, methods, CONFIG)
    second = run_benchmark(SITES, methods, CONFIG)

    assert first == second


def test_every_method_and_degradation_sees_the_same_pairs():
    degradations = {"a": lambda pair, rng: pair, "b": lambda pair, rng: pair}
    methods = {"crashes": crashes, "far_off": far_off}

    results = run_benchmark(SITES, methods, CONFIG, degradations)

    assert len(results) == 4 * 2 * 2
    truths = {(r.pair, r.truth) for r in results}
    assert len(truths) == CONFIG.n_pairs


def test_pairs_have_the_requested_size_and_bounded_shifts():
    pair = draw_pair(SITES["synthetic"], CONFIG, np.random.default_rng(0))

    assert pair.reference.shape == pair.moving.shape == (64, 64)
    assert abs(pair.truth.dx) <= 2.0 and abs(pair.truth.dy) <= 2.0


def test_site_too_small_for_the_window_is_rejected():
    with pytest.raises(ValueError, match="smaller than"):
        draw_pair(np.zeros((70, 70)), CONFIG, np.random.default_rng(0))


def test_crashing_and_wild_methods_are_failures_not_errors():
    results = run_benchmark(SITES, {"crashes": crashes, "far_off": far_off}, CONFIG)

    crashed = [r for r in results if r.method == "crashes"]
    wild = [r for r in results if r.method == "far_off"]
    assert all(r.failed and "RuntimeError: no peak" in r.error for r in crashed)
    assert all(math.isnan(r.mean_epe) for r in crashed)
    assert all(r.failed and r.error == "" and r.mean_epe > 40 for r in wild)


def test_summary_reports_failure_rate_and_averages_the_rest():
    methods = {"phase_correlation": phase_correlation, "crashes": crashes}
    summary = summarize(run_benchmark(SITES, methods, CONFIG))

    by_method = {row.method: row for row in summary}
    good, bad = by_method["phase_correlation"], by_method["crashes"]
    assert good.n_pairs == bad.n_pairs == 4
    assert good.failure_rate == 0.0
    assert good.mean_epe < 0.1
    assert good.share_below_0_1 == 1.0
    assert bad.failure_rate == 1.0
    assert math.isnan(bad.mean_epe)
    row = "| synthetic | translation | clean | crashes | 4 | 0.0 % |"
    assert row + " n/a | n/a | n/a | 100.0 % |" in to_markdown(summary)


def test_tables_are_written_as_csv(tmp_path):
    results = run_benchmark(SITES, {"phase_correlation": phase_correlation}, CONFIG)

    write_csv(results, tmp_path / "pairs.csv")
    write_csv(summarize(results), tmp_path / "out" / "summary.csv")

    with (tmp_path / "pairs.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 4
    assert rows[0]["method"] == "phase_correlation"
    assert (tmp_path / "out" / "summary.csv").read_text().startswith("site,")
    with pytest.raises(ValueError):
        write_csv([], tmp_path / "empty.csv")


def test_non_positive_pair_count_is_rejected():
    with pytest.raises(ValueError):
        run_benchmark(SITES, {}, BenchmarkConfig(n_pairs=0))


def test_cloud_fraction_is_reported_per_pair_and_averaged_per_row():
    degradations = {"clean": Preset(), "cloudy": Preset(clouds=Clouds(0.25))}
    methods = {"phase_correlation": phase_correlation}

    results = run_benchmark(SITES, methods, CONFIG, degradations)

    fractions = {r.degradation: r.cloud_fraction for r in results}
    assert fractions["clean"] == 0.0
    assert fractions["cloudy"] == pytest.approx(0.25, abs=1e-3)
    rows = {row.degradation: row for row in summarize(results)}
    assert rows["cloudy"].cloud_fraction == pytest.approx(0.25, abs=1e-3)
    assert "| synthetic | translation | cloudy | phase_correlation | 4 | 25.0 % |" in (
        to_markdown(summarize(results))
    )


def test_degraded_runs_are_reproducible_and_keep_the_clean_geometry():
    degradations = {"clean": Preset(), "noisy": Preset(noise=Noise(10))}
    methods = {"phase_correlation": phase_correlation}

    first = run_benchmark(SITES, methods, CONFIG, degradations)
    second = run_benchmark(SITES, methods, CONFIG, degradations)

    assert first == second
    truths = {}
    for r in first:
        truths.setdefault(r.pair, set()).add(r.truth)
    assert all(len(t) == 1 for t in truths.values())
    noisy = [r.mean_epe for r in first if r.degradation == "noisy"]
    clean = [r.mean_epe for r in first if r.degradation == "clean"]
    assert np.mean(noisy) > np.mean(clean)


def test_affine_pair_is_the_twin_of_the_translation_pair():
    translation = draw_pair(SITES["synthetic"], BOTH, _rng(0, "synthetic", 1))
    affine = draw_pair(
        SITES["synthetic"], BOTH, _rng(0, "synthetic", 1), scenario="affine"
    )

    assert isinstance(affine.truth, Affine)
    np.testing.assert_array_equal(affine.reference, translation.reference)
    centre = np.full(2, (BOTH.size - 1) / 2)
    moved = affine.truth.apply(centre) - centre
    np.testing.assert_allclose(moved, [translation.truth.dy, translation.truth.dx])


def test_affine_reach_stays_within_the_margin_bound():
    config = BenchmarkConfig(size=64, max_rotation_deg=1.0, max_shear=0.01)

    for seed in range(200):
        pair = draw_pair(
            SITES["synthetic"],
            config,
            np.random.default_rng(seed),
            scenario="affine",
        )
        assert affine_reach(pair.truth, pair.reference.shape) <= max_reach(config)


def test_scenario_is_a_column_of_the_results_and_the_summary():
    methods = {"phase_correlation": phase_correlation}

    results = run_benchmark(SITES, methods, BOTH, {"clean": Preset()})

    assert [r.scenario for r in results[:2]] == ["translation", "affine"]
    assert len(results) == 2 * BOTH.n_pairs
    summary = to_markdown(summarize(results))
    assert "| site | scenario | degradation |" in summary
    assert "| synthetic | affine | clean | phase_correlation | 4 |" in summary


def test_a_translation_estimate_is_worse_on_affine_pairs():
    config = BenchmarkConfig(n_pairs=4, size=96, max_shift=2.0, max_rotation_deg=1.0)
    methods = {"phase_correlation": phase_correlation}

    results = run_benchmark(SITES, methods, config, {"clean": Preset()})

    epe = {
        scenario: np.mean([r.mean_epe for r in results if r.scenario == scenario])
        for scenario in ("translation", "affine")
    }
    assert epe["affine"] > 3 * epe["translation"]


class _WrongOutside(Displacement):
    """Exact on the pair's valid pixels, 100 px off everywhere else."""

    def __init__(self, truth, valid):
        self.truth, self.valid = truth, valid

    def field(self, shape):
        field = self.truth.field(shape)
        field[:, ~self.valid] += 100.0
        return field


def test_errors_are_averaged_over_valid_pixels_only():
    seen = []

    def spy(pair, rng):
        seen.append(pair)
        return pair

    def wrong_outside(reference, moving):
        return _WrongOutside(seen[-1].truth, seen[-1].valid)

    results = run_benchmark(SITES, {"wrong_outside": wrong_outside}, BOTH, {"spy": spy})

    assert all(not pair.valid.all() for pair in seen)
    assert all(r.mean_epe == pytest.approx(0.0, abs=1e-9) for r in results)
    assert not any(r.failed for r in results)


@pytest.mark.parametrize(
    "bad",
    [
        {"scenarios": ("dense",)},
        {"scenarios": ()},
        {"max_rotation_deg": -1.0},
        {"max_scale_change": 1.0},
    ],
)
def test_invalid_scenario_settings_are_rejected(bad):
    with pytest.raises(ValueError):
        BenchmarkConfig(**bad)


class GridSpy(GeoreferencedMethod):
    """Records the grid of each pair it is given, and estimates nothing."""

    def __init__(self):
        self.seen = []

    def __call__(self, reference, moving, georef):
        self.seen.append((reference, georef))
        return Translation(dx=0.0, dy=0.0)


def test_georeferenced_methods_get_the_grid_of_the_window_each_pair_covers():
    # Every pixel holds its own index, so a reference tells where it was cut.
    site = np.arange(256 * 256, dtype=float).reshape(256, 256)
    spy = GridSpy()

    run_benchmark({"site": site}, {"spy": spy}, CONFIG, georefs={"site": NOMINAL})

    # Each pair is called several times, to time it and trace its memory.
    assert len({int(reference[0, 0]) for reference, _ in spy.seen}) == CONFIG.n_pairs
    for reference, georef in spy.seen:
        row, col = divmod(int(reference[0, 0]), 256)
        assert georef == NOMINAL.window(row, col)


def test_pairs_of_a_site_without_a_grid_have_none():
    spy = GridSpy()

    run_benchmark(SITES, {"spy": spy}, CONFIG)

    assert all(georef is None for _, georef in spy.seen)

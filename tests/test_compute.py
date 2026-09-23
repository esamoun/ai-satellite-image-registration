import csv
import dataclasses
import json
import math
import tracemalloc

import numpy as np
import pytest
from test_cli import PRESETS

from satreg import compute
from satreg.benchmark import BenchmarkConfig, run_benchmark
from satreg.cli import main
from satreg.compute import describe, environment, measure, peak_memory
from satreg.displacement import Translation
from satreg.methods import RegistrationFailure
from satreg.report import summarize, to_markdown, write_csv
from satreg.texture import fractal_texture

CONFIG = BenchmarkConfig(
    n_pairs=3, size=64, max_shift=2.0, scenarios=("translation",), warmup=0
)
SITES = {"synthetic": fractal_texture(256, seed=0)}
MIB = 2**20


class FakeClock:
    """A clock that only moves when told to."""

    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


@pytest.fixture
def clock(monkeypatch):
    fake = FakeClock()
    monkeypatch.setattr(compute, "perf_counter", fake)
    return fake


def test_time_is_the_median_over_repeats(clock):
    durations = iter([5.0, 1.0, 3.0])

    def call():
        clock.now += next(durations)

    assert measure(call, repeats=3).seconds == 3.0


def test_warmup_calls_are_made_but_not_timed(clock):
    calls = []

    def call():
        calls.append(clock.now)
        clock.now += 100.0 if len(calls) <= 2 else 1.0

    measured = measure(call, repeats=3, warmup=2)

    assert measured.seconds == 1.0
    # Two warm-up calls, three timed ones, one traced for memory.
    assert len(calls) == 6


def test_a_call_that_raises_is_measured_and_raises_on_result(clock):
    def call():
        clock.now += 2.0
        raise RegistrationFailure("too few inliers")

    measured = measure(call, repeats=2)

    assert measured.seconds == 2.0
    assert measured.value is None
    with pytest.raises(RegistrationFailure, match="too few inliers"):
        measured.result()


def test_invalid_repeat_counts_are_rejected():
    with pytest.raises(ValueError):
        measure(lambda: None, repeats=0)
    with pytest.raises(ValueError):
        measure(lambda: None, repeats=1, warmup=-1)


def test_peak_memory_counts_what_the_call_allocates_not_what_came_before():
    kept = np.ones(8 * MIB // 8)

    def call():
        return np.ones(2 * MIB // 8).sum()

    peak = peak_memory(call)

    assert 2 <= peak < 3
    assert kept.nbytes == 8 * MIB
    assert not tracemalloc.is_tracing()


def test_peak_memory_leaves_an_ongoing_trace_running():
    tracemalloc.start()
    try:
        peak = peak_memory(lambda: np.ones(MIB // 8).sum())
        assert tracemalloc.is_tracing()
    finally:
        tracemalloc.stop()
    assert 1 <= peak < 2


def test_measurement_wraps_only_the_method_call(clock):
    """Simulating and degrading a pair take 100 s here, the method 1 s."""

    def slow_degradation(pair, rng):
        clock.now += 100.0
        return pair

    def one_second(reference, moving):
        clock.now += 1.0
        return Translation(dx=0.0, dy=0.0)

    results = run_benchmark(
        SITES, {"one_second": one_second}, CONFIG, {"slow": slow_degradation}
    )

    assert [r.time_ms for r in results] == [1000.0] * CONFIG.n_pairs


def test_memory_wraps_only_the_method_call():
    """The degradation allocates 32 MiB and keeps it, the method 2 MiB."""
    kept = []

    def hoarding_degradation(pair, rng):
        kept.append(np.ones(32 * MIB // 8))
        return pair

    def two_mib(reference, moving):
        np.ones(2 * MIB // 8).sum()
        return Translation(dx=0.0, dy=0.0)

    results = run_benchmark(
        SITES, {"two_mib": two_mib}, CONFIG, {"hoard": hoarding_degradation}
    )

    assert all(2 <= r.peak_mib < 3 for r in results)


def test_each_method_is_warmed_up_once_per_run():
    calls = []

    def counted(reference, moving):
        calls.append(1)
        return Translation(dx=0.0, dy=0.0)

    config = BenchmarkConfig(
        n_pairs=3, size=64, scenarios=("translation",), warmup=2, repeats=3
    )
    run_benchmark(SITES, {"counted": counted}, config)

    # Two warm-up calls, then three timed and one traced call per pair.
    assert len(calls) == 2 + 3 * (3 + 1)


def test_failed_pairs_have_a_cost_too():
    def declines(reference, moving):
        raise RegistrationFailure("no")

    results = run_benchmark(SITES, {"declines": declines}, CONFIG)

    assert all(r.failed for r in results)
    assert all(r.time_ms >= 0 and not math.isnan(r.peak_mib) for r in results)
    row = summarize(results)[0]
    assert not math.isnan(row.time_ms) and not math.isnan(row.peak_mib)


@pytest.mark.parametrize("bad", [{"warmup": -1}, {"repeats": 0}])
def test_invalid_timing_settings_are_rejected(bad):
    with pytest.raises(ValueError):
        BenchmarkConfig(**bad)


def test_cost_columns_are_in_every_table(tmp_path):
    def still(reference, moving):
        return Translation(dx=0.0, dy=0.0)

    results = run_benchmark(SITES, {"still": still}, CONFIG)
    summary = summarize(results)
    write_csv(results, tmp_path / "pairs.csv")
    write_csv(summary, tmp_path / "summary.csv")

    for name in ("pairs.csv", "summary.csv"):
        with (tmp_path / name).open() as f:
            header = next(csv.reader(f))
        assert header[-2:] == ["time_ms", "peak_mib"]
    assert "| failures | time (ms) | memory (MiB) |" in to_markdown(summary)


def test_summary_takes_the_median_cost_over_pairs():
    def still(reference, moving):
        return Translation(dx=0.0, dy=0.0)

    results = run_benchmark(SITES, {"still": still}, CONFIG)
    times = [1.0, 7.0, 2.0]
    results = [
        dataclasses.replace(r, time_ms=t) for r, t in zip(results, times, strict=True)
    ]

    assert summarize(results)[0].time_ms == 2.0


def test_environment_names_the_machine_threads_and_libraries():
    context = environment()

    assert context["machine"]["cpu"]
    assert context["threads"]["cpu_count"] >= 1
    assert context["libraries"]["numpy"] == np.__version__
    assert "arosics" in context["libraries"]
    json.dumps(context)
    assert f"{context['threads']['usable_cpus']} CPUs" in describe(context)


def test_benchmark_writes_the_context_next_to_the_tables(tmp_path, capsys):
    main(
        [
            "benchmark",
            "--pairs",
            "2",
            "--size",
            "64",
            "--degradations",
            "clean",
            "--methods",
            "phase_correlation",
            "--repeats",
            "2",
            "--warmup",
            "0",
            "--out",
            str(tmp_path),
        ]
        + PRESETS
    )

    context = json.loads((tmp_path / "context.json").read_text())
    assert context["cost"]["repeats"] == 2
    assert context["cost"]["warmup"] == 0
    assert context["cost"]["process_peak_rss_mib"] > 0
    printed = capsys.readouterr().out
    assert f"Measured on {describe(context)}." in printed

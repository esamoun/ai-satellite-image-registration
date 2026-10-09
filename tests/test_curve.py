import ast
import dataclasses
import json
import math
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest

from satreg import curve
from satreg.benchmark import PairResult
from satreg.cli import (
    CURVE_COST,
    CURVE_FOOTPRINT,
    CURVE_FULL,
    CURVE_GPU,
    CURVE_TORCH,
    main,
)
from satreg.curve import (
    POINTS,
    REFINEMENTS,
    TRAINED_REFINEMENTS,
    Pair,
    Point,
    Run,
    largest_gap,
    score,
)
from satreg.footprint import Footprint
from satreg.methods import load_methods
from satreg.report import write_csv
from satreg.trainval import ALL_PRESETS

ROOT = Path(__file__).parents[1]
CONFIGS = ROOT / "configs"

# The small fine-tuned model with each refinement count: a curve of one line.
LINE = tuple(Point("small", True, count) for count in REFINEMENTS)
REFERENCE = "phase_correlation"
SHA = "ab" * 32

# Two pairs under each of two presets.
KEYS = tuple(
    ("lyon", "", "translation", preset, str(pair))
    for preset in ("clean", "hard")
    for pair in range(2)
)
# The error of each refinement count on the four pairs, in px: a NaN is a
# failed pair. Four refinements fail the last pair, which the others do not.
ERRORS = {
    4: (0.30, 0.50, 0.70, math.nan),
    8: (0.20, 0.30, 0.40, 0.90),
    12: (0.10, 0.20, 0.30, 0.80),
}
# What the same model does on the full run.
FULL_ERRORS = {
    4: (0.25, 0.45, 0.65, math.nan),
    8: (0.25, 0.35, 0.45, 0.95),
    12: (0.15, 0.25, 0.35, 0.85),
}
# The options that draw the pairs of the light runs.
LIGHT = {"chips": ["lyon"], "pairs": 2, "light": True, "light_pairs": 2, "seed": 0}


def rows(errors, time_ms=10.0, peak_mib=math.nan, shift=0.0):
    """A method's row on each pair; a NaN error is a failed pair."""
    return {
        key: Pair(math.isnan(error), error + shift, time_ms, peak_mib)
        for key, error in zip(KEYS, errors, strict=True)
    }


def held(point):
    """What the ONNX file of a point says of itself."""
    return {
        "model": point.model,
        "iterations": str(point.refinements),
        "fine_tuned": str(point.fine_tuned).lower(),
        "weights_sha256": SHA,
    }


def weights(points):
    """The weights a PyTorch run records for its fine-tuned methods."""
    return {point.torch: {"sha256": SHA} for point in points if point.fine_tuned}


def runs(points=LINE):
    """The cost run, the PyTorch run and the full run of a curve."""
    cost = Run(
        "cost",
        {
            **{
                point.onnx: rows(ERRORS[point.refinements], 100.0 * point.refinements)
                for point in points
            },
            REFERENCE: rows((0.5, math.nan, math.nan, 0.7), time_ms=2.0),
        },
        {
            "run": LIGHT,
            "devices": {point.onnx: "cpu" for point in points},
            "checkpoints": {point.onnx: {"holds": held(point)} for point in points},
        },
    )
    torch = Run(
        "torch",
        {
            point.torch: rows(
                ERRORS[point.refinements],
                50.0 * point.refinements,
                peak_mib=30.0,
                shift=1e-5,
            )
            for point in points
        },
        {
            "run": LIGHT,
            "devices": {point.torch: "cpu" for point in points},
            "checkpoints": weights(points),
        },
    )
    full = Run(
        "full",
        {point.torch: rows(FULL_ERRORS[point.refinements]) for point in points},
        {
            "run": {**LIGHT, "light": False},
            "devices": {point.torch: "mps" for point in points},
            "checkpoints": weights(points),
        },
    )
    return cost, torch, full


def footprint_of(method, rise=40.0, settled=3, processes=1, spread=0.0):
    return Footprint(
        method=method,
        size=256,
        calls=10,
        baseline_mib=100.0,
        first_mib=rise - 5.0,
        rise_mib=rise,
        process_mib=100.0 + rise,
        settled=settled,
        time_ms=10.0,
        processes=processes,
        lowest_mib=rise - spread / 4,
        highest_mib=rise + 3 * spread / 4,
        error="",
    )


def footprints(points=LINE):
    """The footprint of each point under both runtimes, and of the reference."""
    found = {}
    for point in points:
        found[point.onnx] = footprint_of(point.onnx, 10.0 * point.refinements)
        found[point.torch] = footprint_of(point.torch, 30.0 * point.refinements)
    found[REFERENCE] = footprint_of(REFERENCE, 1.5)
    return found


def changed(scored, **context):
    """A run with part of its context replaced."""
    return dataclasses.replace(scored, context={**scored.context, **context})


def test_a_point_is_named_as_its_method_under_each_runtime():
    trained = Point("large", False, TRAINED_REFINEMENTS)
    fewer = Point("small", True, 4)

    assert (trained.torch, trained.onnx) == ("raft", "raft_onnx")
    assert (fewer.torch, fewer.onnx) == ("raft_small_ft_r4", "raft_small_ft_r4_onnx")
    assert (trained.weights, fewer.weights) == ("pretrained", "fine-tuned")
    assert (trained.series, fewer.series) == (
        "RAFT large, pretrained",
        "RAFT small, fine-tuned",
    )


def test_the_curve_is_both_models_with_both_weights_and_each_refinement_count():
    assert len(POINTS) == len({point.torch for point in POINTS}) == 12
    assert {(point.model, point.fine_tuned, point.refinements) for point in POINTS} == {
        (model, fine_tuned, count)
        for model in ("large", "small")
        for fine_tuned in (False, True)
        for count in (4, 8, 12)
    }
    assert REFINEMENTS[-1] == TRAINED_REFINEMENTS


def test_the_points_are_the_methods_the_configuration_names():
    curve.check_methods(POINTS, load_methods(CONFIGS / "methods.toml"))


@pytest.mark.parametrize(
    "method",
    [
        SimpleNamespace(model="large", release="raft_small_ft", iterations=4),
        SimpleNamespace(model="small", release="", checkpoint="", iterations=4),
        SimpleNamespace(model="small", release="raft_small_ft", iterations=12),
        object(),
    ],
)
def test_a_method_that_is_not_the_model_of_its_name_is_refused(method):
    point = Point("small", True, 4)
    refusal = "method raft_small_ft_r4 is not RAFT small, fine-tuned, with 4 refinem"

    with pytest.raises(ValueError, match=refusal):
        curve.check_methods([point], {point.torch: method})
    with pytest.raises(ValueError, match="no method raft_small_ft_r4 in the methods"):
        curve.check_methods([point], {})


def test_a_score_leaves_failed_pairs_out_of_the_error_and_not_out_of_the_time():
    pairs = {
        ("a",): Pair(False, 0.2, 10.0, 5.0),
        ("b",): Pair(True, 3.0, 30.0, 7.0),
        ("c",): Pair(False, 0.4, 500.0, 9.0),
        ("d",): Pair(True, math.nan, 20.0, 6.0),
    }

    scored = score(pairs)

    assert (scored.pairs, scored.failures, scored.failure_rate) == (4, 2, 0.5)
    assert scored.mean_epe == pytest.approx(0.3)
    # The medians are over every pair, failed or not.
    assert (scored.time_ms, scored.peak_mib) == (25.0, 6.5)


def test_a_score_reads_the_pairs_it_is_told_to_keep():
    scored = score(rows(ERRORS[4]), lambda key: key[3] == "hard")

    assert (scored.pairs, scored.failures, scored.mean_epe) == (2, 1, 0.70)
    assert math.isnan(score(rows((math.nan,) * 4)).mean_epe)
    with pytest.raises(ValueError, match="no pair to read"):
        score(rows(ERRORS[4]), lambda key: False)


def test_the_largest_gap_is_over_the_pairs_both_runtimes_estimated():
    onnx, torch = rows((0.2, 0.4, 0.6, math.nan)), rows((0.2, 0.43, 0.59, 0.1))

    assert largest_gap(onnx, torch) == pytest.approx(0.03)
    assert math.isnan(largest_gap(rows((math.nan,) * 4), torch))
    with pytest.raises(ValueError, match="did not run on the same pairs"):
        largest_gap(onnx, {KEYS[0]: torch[KEYS[0]]})


def test_a_point_is_read_under_onnx_runtime_with_pytorch_beside_it():
    read = curve.read(LINE, *runs(), footprints())

    four = read.rows[0]
    assert [row.refinements for row in read.rows] == list(REFINEMENTS)
    assert (four.model, four.weights) == ("small", "fine-tuned")
    assert (four.method, four.torch_method) == (LINE[0].onnx, LINE[0].torch)
    # Error, failures and time of the curve are those of the ONNX Runtime run.
    assert (four.pairs, four.failure_rate, four.time_ms) == (4, 0.25, 400.0)
    assert four.mean_epe == pytest.approx(0.5)
    assert (four.memory_mib, four.process_mib) == (40.0, 140.0)
    # The same model under PyTorch, with the memory of a call its profiler reads.
    assert (four.torch_failure_rate, four.torch_time_ms) == (0.25, 200.0)
    assert four.torch_mean_epe == pytest.approx(0.50001)
    assert (four.torch_memory_mib, four.torch_process_mib) == (120.0, 220.0)
    assert four.torch_call_mib == 30.0
    assert four.largest_gap == pytest.approx(1e-5)
    # No run on a GPU was read.
    assert read.gpu == "" and math.isnan(four.gpu_time_ms)


def test_the_other_methods_of_the_cost_run_are_shown_beside_the_curve():
    known = footprints()

    read = curve.read(LINE, *runs(), known)

    (reference,) = read.references
    assert (reference.method, reference.pairs) == (REFERENCE, 4)
    assert (reference.failure_rate, reference.time_ms) == (0.5, 2.0)
    assert reference.mean_epe == pytest.approx(0.6)
    assert (reference.memory_mib, reference.process_mib) == (1.5, 101.5)
    assert read.footprints == known

    # Without a footprint the method is still scored, and has no memory.
    del known[REFERENCE]
    (bare,) = curve.read(LINE, *runs(), known).references
    assert math.isnan(bare.memory_mib) and math.isnan(bare.process_mib)
    assert bare.mean_epe == pytest.approx(0.6)


def test_fewer_refinements_are_read_against_the_trained_count_on_the_full_run():
    read = curve.read(LINE, *runs(), footprints())

    found = {(row.degradation, row.refinements): row for row in read.refinements}
    assert list(found) == [
        (preset, count)
        for preset in (ALL_PRESETS, "clean", "hard")
        for count in REFINEMENTS
    ]
    # Four refinements fail one pair of four: their gap is over the three
    # others, 0.1, 0.2 and 0.3 px above the trained count.
    four = found[ALL_PRESETS, 4]
    assert (four.pairs, four.failure_rate, four.common) == (4, 0.25, 3)
    assert four.mean_epe == pytest.approx(0.45)
    assert four.gap == pytest.approx(0.2)
    assert found[ALL_PRESETS, 8].gap == pytest.approx(0.1)
    assert found["clean", 4].gap == pytest.approx(0.15)
    assert (found["hard", 4].pairs, found["hard", 4].common) == (2, 1)
    assert found["hard", 4].gap == pytest.approx(0.3)
    assert found["clean", 8].mean_epe == pytest.approx(0.30)
    # The trained count is what the others are read against.
    trained = found[ALL_PRESETS, TRAINED_REFINEMENTS]
    assert (trained.pairs, trained.common) == (4, 4)
    assert math.isnan(trained.gap)


def test_a_run_on_a_gpu_adds_its_time():
    cost, torch, full = runs()
    gpu = Run(
        "gpu",
        {point.torch: rows(ERRORS[point.refinements], 3.0) for point in LINE},
        {"run": LIGHT, "devices": {point.torch: "cuda" for point in LINE}},
    )

    read = curve.read(LINE, cost, torch, full, footprints(), gpu)

    assert read.gpu == "cuda"
    assert [row.gpu_time_ms for row in read.rows] == [3.0, 3.0, 3.0]
    assert "| time on cuda (ms) |" in curve.to_markdown(read)

    other = changed(gpu, run={**LIGHT, "seed": 1})
    with pytest.raises(ValueError, match="cost and gpu did not score the same pairs"):
        curve.read(LINE, cost, torch, full, footprints(), other)
    on_cpu = changed(gpu, devices={**gpu.context["devices"], LINE[1].torch: "cpu"})
    with pytest.raises(ValueError, match="gpu did not run raft_small_ft_r8 on a GPU"):
        curve.read(LINE, cost, torch, full, footprints(), on_cpu)
    del gpu.pairs[LINE[0].torch]
    with pytest.raises(ValueError, match="gpu has no rows for raft_small_ft_r4"):
        curve.read(LINE, cost, torch, full, footprints(), gpu)


def test_a_point_without_its_footprint_is_refused():
    known = footprints()
    del known[LINE[1].onnx], known[LINE[2].torch]

    with pytest.raises(
        ValueError, match="no footprint for raft_small_ft_r8_onnx, raft_small_ft$"
    ):
        curve.read(LINE, *runs(), known)


def test_a_run_that_lacks_a_point_is_refused():
    for position, name in enumerate(("cost", "torch", "full")):
        read = list(runs())
        method = LINE[0].torch if position else LINE[0].onnx
        del read[position].pairs[method]

        with pytest.raises(ValueError, match=f"{name} has no rows for {method}$"):
            curve.check(LINE, *read)


def test_a_cost_run_off_the_cpu_is_refused():
    cost, torch, full = runs()
    elsewhere = changed(torch, devices={point.torch: "mps" for point in LINE})

    with pytest.raises(ValueError, match="torch did not run raft_small_ft_r4, .* cpu"):
        curve.check(LINE, cost, elsewhere, full)
    with pytest.raises(ValueError, match="cost did not run .* on the cpu"):
        curve.check(LINE, changed(cost, devices={}), torch, full)


def test_two_light_runs_that_did_not_score_the_same_pairs_are_refused():
    cost, torch, full = runs()
    other = changed(torch, run={**LIGHT, "seed": 1, "light_pairs": 5})

    with pytest.raises(
        ValueError,
        match="cost and torch did not score the same pairs: light_pairs, seed differ",
    ):
        curve.check(LINE, cost, other, full)


def test_a_light_set_is_not_read_as_the_full_validation_set():
    cost, torch, full = runs()

    with pytest.raises(ValueError, match="full is a light set, not the full valid"):
        curve.check(LINE, cost, torch, changed(full, run=LIGHT))


@pytest.mark.parametrize(
    "said", [{"model": "large"}, {"iterations": "12"}, {"fine_tuned": "false"}]
)
def test_an_onnx_file_that_holds_another_model_is_refused(said):
    cost, torch, full = runs()
    files = {point.onnx: {"holds": held(point)} for point in LINE}
    files[LINE[0].onnx] = {"holds": {**held(LINE[0]), **said}}
    refusal = (
        "cost: the file of raft_small_ft_r4_onnx is not RAFT small, fine-tuned, "
        "with 4 refinements"
    )

    with pytest.raises(ValueError, match=refusal):
        curve.check(LINE, changed(cost, checkpoints=files), torch, full)
    # A run that did not record what its files hold says nothing of them.
    with pytest.raises(ValueError, match=refusal):
        curve.check(LINE, changed(cost, checkpoints={}), torch, full)


def test_two_runtimes_that_did_not_run_the_same_weights_are_refused():
    cost, torch, full = runs()
    others = {point.torch: {"sha256": "cd" * 32} for point in LINE}
    refusal = (
        "raft_small_ft_r4_onnx and raft_small_ft_r4 did not run the same weights "
        "in cost, torch and full"
    )

    with pytest.raises(ValueError, match=refusal):
        curve.check(LINE, cost, changed(torch, checkpoints=others), full)
    with pytest.raises(ValueError, match=refusal):
        curve.check(LINE, cost, torch, changed(full, checkpoints={}))


def test_pretrained_points_need_no_recorded_weights():
    line = tuple(Point("large", False, count) for count in REFINEMENTS)

    read = curve.read(line, *runs(line), footprints(line))

    assert [row.method for row in read.rows] == [
        "raft_r4_onnx",
        "raft_r8_onnx",
        "raft_onnx",
    ]


def test_the_tables_show_the_curve_the_other_methods_and_the_refinements():
    table = curve.to_markdown(curve.read(LINE, *runs(), footprints()))

    assert "ONNX Runtime on the CPU, 4 pairs:" in table
    assert (
        "| RAFT small | fine-tuned | 4 | raft_small_ft_r4_onnx | 0.5000 | 25.0 % | "
        "400.0 | 40.0 | 140.0 |"
    ) in table
    assert (
        "| RAFT small | fine-tuned | 4 | raft_small_ft_r4 | 0.5000 | 25.0 % | 200.0 "
        "| 120.0 | 220.0 | 30.0 | 1.0e-05 |"
    ) in table
    assert "| phase_correlation | 0.6000 | 50.0 % | 2.0 | 1.5 | 101.5 |" in table
    assert "under PyTorch on the full validation set, 4 pairs:" in table
    assert (
        "| model | weights | refinements | all: EPE (px) | failures | against 12 "
        "(px) | clean: EPE (px) | failures | against 12 (px) | hard: EPE (px) | "
        "failures | against 12 (px) |"
    ) in table
    assert (
        "| RAFT small | fine-tuned | 4 | 0.4500 | 25.0 % | +0.2000 | 0.3500 | "
        "0.0 % | +0.1500 | 0.6500 | 50.0 % | +0.3000 |"
    ) in table
    assert (
        "| RAFT small | fine-tuned | 12 | 0.4000 | 0.0 % | n/a | 0.2000 | 0.0 % | "
        "n/a | 0.6000 | 0.0 % | n/a |"
    ) in table
    assert "| time on" not in table
    assert "had not settled" not in table
    assert "from one process to another" not in table


def test_a_footprint_read_while_its_method_raised_is_refused():
    known = footprints()
    known[REFERENCE] = dataclasses.replace(known[REFERENCE], error="call 2: no")

    with pytest.raises(
        ValueError, match=f"a call raised while the footprint was read for {REFERENCE}"
    ):
        curve.read(LINE, *runs(), known)


def test_footprints_read_on_another_size_or_number_of_calls_are_refused():
    for other in ({"size": 512}, {"calls": 30}):
        known = footprints()
        known[LINE[0].torch] = dataclasses.replace(known[LINE[0].torch], **other)

        with pytest.raises(ValueError, match="were not all read on one pair size"):
            curve.read(LINE, *runs(), known)


def test_a_footprint_the_curve_does_not_show_is_not_checked():
    known = footprints()
    known["roma"] = dataclasses.replace(footprint_of("roma"), size=512, error="no")

    curve.read(LINE, *runs(), known)


def test_the_tables_say_which_footprints_had_not_settled():
    known = footprints()
    known[LINE[0].onnx] = footprint_of(LINE[0].onnx, settled=10)

    table = curve.to_markdown(curve.read(LINE, *runs(), known))

    assert (
        "Memory had not settled for raft_small_ft_r4_onnx: the last call still "
        "raised the mark."
    ) in table


def test_the_tables_say_how_far_a_footprint_moves_between_processes():
    known = footprints()
    known[LINE[0].onnx] = footprint_of(LINE[0].onnx, processes=3, spread=6.0)
    known[LINE[1].torch] = footprint_of(LINE[1].torch, processes=3, spread=20.5)

    table = curve.to_markdown(curve.read(LINE, *runs(), known))

    assert (
        "profiler reads. Each method was read in 3 processes and the median "
        "reading is given; from one process to another the memory added moves "
        "by up to 20.5 MiB (raft_small_ft_r8)."
    ) in table


def test_the_tables_stand_without_another_method():
    cost, torch, full = runs()
    del cost.pairs[REFERENCE]

    table = curve.to_markdown(curve.read(LINE, cost, torch, full, footprints()))

    assert "The other methods" not in table


def test_the_figure_is_saved_as_an_image(tmp_path):
    path = tmp_path / "figures" / "curve.png"

    curve.figure(curve.read(LINE, *runs(), footprints()), path)

    assert path.read_bytes().startswith(b"\x89PNG")


def pair_result(method, key, pair, device="cpu"):
    """A row of pairs.csv, as validate writes it."""
    site, bands, scenario, degradation, number = key
    return PairResult(
        site=site,
        bands=bands,
        scenario=scenario,
        degradation=degradation,
        method=method,
        device=device,
        pair=number,
        cloud_fraction=0.0,
        truth="",
        estimate="",
        mean_epe=pair.mean_epe,
        share_below_0_1=0.0,
        share_below_0_5=0.0,
        failed=pair.failed,
        error="",
        diagnostics="",
        time_ms=pair.time_ms,
        peak_mib=pair.peak_mib,
    )


def write_run(path, run, config, device="cpu", **recorded):
    """Write a run as validate leaves it, scored from a run configuration."""
    results = [
        pair_result(method, key, pair, device)
        for method, pairs in run.pairs.items()
        for key, pair in pairs.items()
    ]
    write_csv(results, path / "pairs.csv")
    context = {
        "recorded_at": "2026-10-08T10:00:00+00:00",
        "code": {"commit": "abcdef0123", "dirty": False},
        "machine": {"chip": "Apple M1"},
        **run.context,
        **recorded,
        "run": {**run.context["run"], "config": str(config)},
    }
    (path / "context.json").write_text(json.dumps(context))


def scored_curve(tmp_path):
    """Write the directories make curve leaves for the curve to read."""
    out = tmp_path / "curve"
    config = tmp_path / "curve.toml"
    config.write_text('[validate]\npairs = 2\nseed = 0\nmethods = ["raft"]\n')
    cost, torch, full = runs(POINTS)
    write_run(out / CURVE_COST, cost, config, threads={"onnxruntime": 4})
    write_run(out / CURVE_TORCH, torch, config)
    write_run(out / CURVE_FULL, full, config, device="mps")
    known = footprints(POINTS)
    write_csv(list(known.values()), out / CURVE_FOOTPRINT / "footprints.csv")
    return ["curve", "--out", str(out), "--methods-config", str(CONFIGS / METHODS)]


METHODS = "methods.toml"


def test_read_run_reads_back_what_validate_wrote(tmp_path):
    cost, _, _ = runs()
    write_run(tmp_path, cost, tmp_path / "curve.toml")

    read = curve.read_run(tmp_path)

    assert read.name == str(tmp_path)
    assert list(read.pairs) == [*(point.onnx for point in LINE), REFERENCE]
    assert [
        (pair.failed, pair.mean_epe, pair.time_ms)
        for pair in read.pairs[LINE[1].onnx].values()
    ] == [(False, error, 800.0) for error in ERRORS[8]]
    assert list(read.pairs[LINE[1].onnx]) == list(KEYS)
    # A failed pair without an estimate, and a method without a memory figure.
    failed = read.pairs[LINE[0].onnx][KEYS[-1]]
    assert failed.failed and math.isnan(failed.mean_epe) and math.isnan(failed.peak_mib)
    assert read.context["devices"] == cost.context["devices"]


def test_read_run_refuses_a_pair_scored_twice(tmp_path):
    cost, _, _ = runs()
    twice = [pair_result(REFERENCE, KEYS[0], cost.pairs[REFERENCE][KEYS[0]])] * 2
    write_csv(twice, tmp_path / "pairs.csv")
    (tmp_path / "context.json").write_text("{}")

    with pytest.raises(ValueError, match="two rows for phase_correlation on lyon, "):
        curve.read_run(tmp_path)


def test_curve_writes_the_tables_the_figure_and_what_they_were_read_from(
    tmp_path, capsys
):
    args = scored_curve(tmp_path)
    out = tmp_path / "curve"

    main(args)

    printed = capsys.readouterr().out
    assert printed == (out / "summary.md").read_text()
    assert printed.startswith("The cost curve of RAFT: the large and the small model")
    assert f"`{out / CURVE_COST}`" in printed and "4, 8, 12 refinements" in printed
    assert "| RAFT large | pretrained | 12 | raft_onnx | 0.3500 | 0.0 % |" in printed
    assert "| phase_correlation | 0.6000 | 50.0 % | 2.0 | 1.5 | 101.5 |" in printed
    for table, lines in (("points", 12), ("references", 1), ("refinements", 36)):
        assert len((out / f"{table}.csv").read_text().splitlines()) == lines + 1
    assert (out / "curve.png").read_bytes().startswith(b"\x89PNG")
    context = json.loads((out / "context.json").read_text())
    # The files of both runtimes, and where each table was read from.
    assert context["checkpoints"]["raft_ft"] == {"sha256": SHA}
    assert context["checkpoints"]["raft_ft_onnx"]["holds"]["weights_sha256"] == SHA
    assert context["threads"] == {"onnxruntime": 4}
    assert list(context["read"]) == [CURVE_FULL, CURVE_COST, CURVE_TORCH]
    assert context["read"][CURVE_COST]["code"] == {
        "commit": "abcdef0123",
        "dirty": False,
    }


def test_curve_reads_the_gpu_run_when_there_is_one(tmp_path, capsys):
    args = scored_curve(tmp_path)
    out = tmp_path / "curve"
    _, torch, _ = runs(POINTS)
    on_gpu = changed(torch, devices={point.torch: "cuda" for point in POINTS})
    write_run(out / CURVE_GPU, on_gpu, tmp_path / "curve.toml", device="cuda")

    main(args)

    assert "| time on cuda (ms) |" in capsys.readouterr().out
    context = json.loads((out / "context.json").read_text())
    assert CURVE_GPU in context["read"]


@pytest.mark.parametrize("missing", [CURVE_FULL, CURVE_COST, CURVE_TORCH])
def test_curve_refuses_to_read_without_a_run(tmp_path, missing):
    args = scored_curve(tmp_path)
    (tmp_path / "curve" / missing / "pairs.csv").unlink()

    with pytest.raises(SystemExit, match="satreg: no pairs.csv and .* run make curve"):
        main(args)

    assert not (tmp_path / "curve" / "summary.md").exists()


def test_curve_refuses_to_read_without_the_footprints(tmp_path):
    args = scored_curve(tmp_path)
    (tmp_path / "curve" / CURVE_FOOTPRINT / "footprints.csv").unlink()

    with pytest.raises(SystemExit, match="satreg: no footprints at .* run make curve"):
        main(args)


def test_curve_refuses_a_run_that_was_not_scored_as_its_configuration_says(tmp_path):
    args = scored_curve(tmp_path)
    path = tmp_path / "curve" / CURVE_TORCH / "context.json"
    context = json.loads(path.read_text())
    context["run"]["seed"] = 1
    path.write_text(json.dumps(context))

    with pytest.raises(SystemExit, match="was not run as .*curve.toml says: seed"):
        main(args)


def test_curve_refuses_runs_that_cannot_be_read_together(tmp_path):
    args = scored_curve(tmp_path)
    path = tmp_path / "curve" / CURVE_TORCH / "context.json"
    context = json.loads(path.read_text())
    context["devices"]["raft"] = "mps"
    path.write_text(json.dumps(context))

    with pytest.raises(SystemExit, match="satreg: .* did not run raft on the cpu"):
        main(args)

    assert not (tmp_path / "curve" / "summary.md").exists()


def test_the_cost_runs_score_the_pairs_of_the_validation_set():
    paths = [CONFIGS / "curve.toml", CONFIGS / "validation.toml"]
    cost, validation = (tomllib.loads(path.read_text())["validate"] for path in paths)

    # Every option that draws the pairs, and every file they are drawn from.
    drawn = [option for option in curve.PAIRS_OPTIONS if option != "light"]
    drawn += [option for option in cost if option.endswith(("_config", "_dir"))]
    assert {option: cost[option] for option in drawn} == {
        option: validation[option] for option in drawn
    }
    assert (cost["warmup"], cost["repeats"]) == (1, 3)
    # The curve is read on the CPU, with the classic methods beside it.
    assert cost["device"] == curve.COST_DEVICE
    assert cost["methods"] == [
        *(point.onnx for point in POINTS),
        "phase_correlation",
        "sift_ransac",
        "arosics",
    ]


def test_make_curve_scores_what_the_reading_reads():
    recipe = (ROOT / "Makefile").read_text()
    torch = " ".join(point.torch for point in POINTS)
    onnx = " ".join(point.onnx for point in POINTS)

    assert f"CURVE_TORCH = {torch}\n" in recipe
    assert f"CURVE_ONNX = {onnx}\n" in recipe
    assert f"--methods $(CURVE_TORCH) --out $(CURVE)/{CURVE_FULL}\n" in recipe
    # A light run writes beside the directory it is given.
    light = "satreg validate --config configs/curve.toml --light"
    assert CURVE_COST == "onnx-light" and CURVE_TORCH == "torch-light"
    assert f"{light} --out $(CURVE)/onnx\n" in recipe
    assert f"{light} --methods $(CURVE_TORCH) --out $(CURVE)/torch\n" in recipe
    assert f"--out $(CURVE)/{CURVE_FOOTPRINT}\n" in recipe
    assert "satreg curve --out $(CURVE)\n" in recipe


def test_the_kaggle_procedure_runs_the_curve_s_pytorch_methods_on_the_gpu():
    procedure = (ROOT / "docs" / "kaggle.md").read_text()
    cell = procedure.split("```python\nCOMMAND")[1].split("```")[0]
    set_there = {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in ast.parse("COMMAND" + cell).body
    }

    assert set_there["COMMAND"] == "validate"
    assert ROOT / set_there["CONFIG"] == CONFIGS / "curve.toml"
    assert set_there["OPTIONS"] == [
        "--light",
        "--methods",
        *(point.torch for point in POINTS),
    ]
    # The run comes back under the name the reading looks for.
    assert f"outputs/curve-light outputs/curve/{CURVE_GPU}\n" in procedure

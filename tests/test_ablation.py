import dataclasses
import hashlib
import json
import math
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest

from satreg import ablation, trainval
from satreg.ablation import (
    ALL,
    BETTER,
    EQUAL,
    WORSE,
    Paired,
    Score,
    beats,
    choose,
    closure_reading,
    compare,
)
from satreg.benchmark import PairResult
from satreg.cli import ABLATION_BASELINE, ABLATION_VARIANTS, _checkpoints, main
from satreg.cycle import REAL, TripletRow
from satreg.methods import load_methods
from satreg.report import write_csv
from satreg.train import BEST, LOG, VALIDATIONS, LogRow, _write_log, load_train_config
from satreg.trainchips import TRAIN, VALIDATION
from satreg.trainpairs import load_pairs_config
from satreg.trainval import ALL_PRESETS, ValidationRow

CONFIGS = Path(__file__).parents[1] / "configs"
SAME_DATE, CROSS_DATE = ABLATION_VARIANTS


def scores(*values):
    """Scores of consecutive items; a NaN is a failed item."""
    return {(str(i),): Score(math.isnan(v), v) for i, v in enumerate(values)}


def paired(failures, reference_failures, mean, reference_mean):
    return Paired(10, failures, reference_failures, 8, mean, reference_mean)


def test_the_means_of_a_paired_reading_are_over_the_items_neither_fails():
    # Each method's own mean leaves out its own failures only: 0.2 and 0.3 px.
    reading = compare(scores(0.1, 0.3, math.nan, 0.2), scores(0.2, math.nan, 0.5, 0.2))

    assert (reading.items, reading.failures, reading.reference_failures) == (4, 1, 1)
    assert reading.common == 2
    assert reading.mean == pytest.approx(0.15)
    assert reading.reference_mean == pytest.approx(0.2)
    assert reading.difference == pytest.approx(-0.05)


def test_a_paired_reading_can_keep_some_items_only():
    reading = compare(scores(0.1, 0.9), scores(0.2, 0.3), lambda key: key == ("1",))

    assert (reading.items, reading.mean, reading.reference_mean) == (1, 0.9, 0.3)


def test_two_methods_are_compared_on_the_same_items_or_not_at_all():
    with pytest.raises(ValueError, match="did not run on the same items"):
        compare(scores(0.1, 0.2), scores(0.1))
    with pytest.raises(ValueError, match="no item to compare on"):
        compare(scores(0.1), scores(0.1), lambda key: False)


def test_items_that_all_fail_leave_no_mean():
    reading = compare(scores(math.nan), scores(0.2))

    assert reading.common == 0
    assert math.isnan(reading.mean) and math.isnan(reading.reference_mean)
    assert not beats(reading)
    assert closure_reading(compare(scores(math.nan), scores(math.nan))) == EQUAL


@pytest.mark.parametrize(
    ("reading", "expected"),
    [
        # Fewer failures and a lower mean, by any margin.
        (paired(1, 2, 0.0999, 0.1), True),
        (paired(2, 2, 0.05, 0.1), True),
        # A lower mean bought with one more failure.
        (paired(3, 2, 0.05, 0.1), False),
        # Fewer failures, but no lower a mean.
        (paired(0, 2, 0.1, 0.1), False),
        (paired(0, 2, 0.2, 0.1), False),
    ],
)
def test_beating_is_failing_no_more_and_a_lower_mean_error(reading, expected):
    assert beats(reading) is expected


@pytest.mark.parametrize(
    ("reading", "expected"),
    [
        # The failure count comes first, whatever the means.
        (paired(1, 2, 0.5, 0.1), BETTER),
        (paired(3, 2, 0.1, 0.5), WORSE),
        # As many failures: the mean closure over the triplets neither fails.
        (paired(2, 2, 0.1, 0.2), BETTER),
        (paired(2, 2, 0.3, 0.2), WORSE),
        (paired(2, 2, 0.2, 0.2), EQUAL),
    ],
)
def test_a_closure_is_read_on_failures_then_on_the_mean(reading, expected):
    assert closure_reading(reading) == expected


BEATS, LOSES = paired(1, 2, 0.05, 0.1), paired(3, 2, 0.05, 0.1)
VARIANTS = ("simple", "mixed")


def test_nothing_is_retained_if_neither_variant_beats_the_pretrained_model():
    # The closure favours the second variant: it does not get to decide.
    choice = choose(
        VARIANTS, {"simple": LOSES, "mixed": LOSES}, paired(0, 5, 0.1, 0.2), BEATS
    )

    assert (choice.retained, choice.eligible) == (None, ())
    assert "nothing is retained" in choice.reason


@pytest.mark.parametrize("winner", VARIANTS)
def test_the_only_variant_that_beats_the_pretrained_model_is_retained(winner):
    validation = {v: BEATS if v == winner else LOSES for v in VARIANTS}
    # Closure and mean error favour the first variant, whichever is eligible.
    choice = choose(VARIANTS, validation, paired(5, 0, 0.3, 0.1), LOSES)

    assert (choice.retained, choice.eligible) == (winner, (winner,))
    assert f"Only {winner} beats the pretrained model" in choice.reason


@pytest.mark.parametrize(
    ("closure", "retained"),
    [
        (paired(1, 2, 0.3, 0.1), "mixed"),
        (paired(2, 2, 0.1, 0.2), "mixed"),
        (paired(3, 2, 0.1, 0.3), "simple"),
        (paired(2, 2, 0.3, 0.2), "simple"),
    ],
)
def test_two_eligible_variants_are_chosen_on_the_closure(closure, retained):
    both = {"simple": BEATS, "mixed": BEATS}
    # The mean error on the validation set says the opposite, and loses.
    accuracy = paired(0, 0, 0.2, 0.1) if retained == "mixed" else BEATS

    choice = choose(VARIANTS, both, closure, accuracy)

    assert (choice.retained, choice.eligible) == (retained, VARIANTS)
    assert f"{retained} closes better" in choice.reason


def test_an_equal_closure_leaves_the_choice_to_the_mean_error_then_to_the_simpler():
    both = {"simple": BEATS, "mixed": BEATS}
    tie = paired(2, 2, 0.2, 0.2)

    assert choose(VARIANTS, both, tie, paired(0, 0, 0.1, 0.2)).retained == "mixed"
    assert choose(VARIANTS, both, tie, paired(0, 0, 0.3, 0.2)).retained == "simple"
    nothing = choose(VARIANTS, both, tie, paired(0, 0, 0.2, 0.2))
    assert nothing.retained == "simple"
    assert "the simpler recipe" in nothing.reason


def pair_result(method, pair, epe, scenario="translation", degradation="clean"):
    """One scored pair; a NaN error is a failed pair."""
    return PairResult(
        site="lyon",
        bands="",
        scenario=scenario,
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


def triplet_row(method, site, window, closure, failed=False):
    return TripletRow(
        site=site,
        scenario=REAL,
        triplet="days-anchor-season",
        window=window,
        method=method,
        device="cpu",
        cloud_fraction=0.0,
        mean_closure=closure,
        share_below_0_1=0.0,
        share_below_0_5=0.0,
        true_epe=math.nan,
        truth_closure=math.nan,
        failed=failed,
        error="",
        time_ms=1.0,
        peak_mib=1.0,
    )


# Mean error of each method on two pairs of four cells, and closure on two
# windows of a validation chip and a training chip (None: a failed triplet).
PAIRS = {
    ABLATION_BASELINE: [0.10, 0.20, 0.10, 0.20, 0.30, math.nan, 0.30, 0.40],
    SAME_DATE: [0.05, 0.10, 0.05, 0.10, 0.20, 0.50, 0.20, 0.30],
    CROSS_DATE: [0.08, 0.12, 0.08, 0.12, 0.25, math.nan, 0.25, 0.35],
}
CELLS = [
    ("translation", "clean"),
    ("translation", "hard"),
    ("dense", "clean"),
    ("dense", "hard"),
]
TRIPLETS = {
    ABLATION_BASELINE: {"lyon": [0.3, None], "milan": [0.3, 0.3]},
    SAME_DATE: {"lyon": [0.2, None], "milan": [0.2, 0.2]},
    CROSS_DATE: {"lyon": [0.15, 0.4], "milan": [0.1, 0.1]},
}
ROLES = {"lyon": VALIDATION, "milan": TRAIN}


def pair_results(pairs=PAIRS):
    return [
        pair_result(method, i % 2, epe, *CELLS[i // 2])
        for method, epes in pairs.items()
        for i, epe in enumerate(epes)
    ]


def triplet_rows():
    return [
        triplet_row(method, site, window, closure or 3.0, failed=closure is None)
        for method, sites in TRIPLETS.items()
        for site, closures in sites.items()
        for window, closure in enumerate(closures)
    ]


def test_scores_are_read_back_from_the_tables_a_run_writes(tmp_path):
    write_csv(pair_results(), tmp_path / "pairs.csv")
    write_csv(triplet_rows(), tmp_path / "triplets.csv")

    pairs = ablation.read_pairs(tmp_path / "pairs.csv")
    triplets = ablation.read_triplets(tmp_path / "triplets.csv")

    assert list(pairs) == list(triplets) == [ABLATION_BASELINE, *ABLATION_VARIANTS]
    key = ("lyon", "", "translation", "hard", "1")
    assert pairs[SAME_DATE][key] == Score(False, 0.10)
    assert pairs[CROSS_DATE]["lyon", "", "dense", "clean", "1"].failed
    assert triplets[ABLATION_BASELINE]["lyon", REAL, "days-anchor-season", "1"].failed
    assert triplets[CROSS_DATE]["milan", REAL, "days-anchor-season", "0"].value == 0.1


def test_a_method_scored_twice_on_a_pair_is_refused(tmp_path):
    write_csv([pair_result("raft", 0, 0.1)] * 2, tmp_path / "pairs.csv")

    with pytest.raises(ValueError, match="two rows for raft on lyon"):
        ablation.read_pairs(tmp_path / "pairs.csv")


def read_tables(tmp_path):
    write_csv(pair_results(), tmp_path / "pairs.csv")
    write_csv(triplet_rows(), tmp_path / "triplets.csv")
    return (
        ablation.read_pairs(tmp_path / "pairs.csv"),
        ablation.read_triplets(tmp_path / "triplets.csv"),
    )


def test_the_validation_set_is_read_by_cell_then_as_a_whole(tmp_path):
    pairs, _ = read_tables(tmp_path)

    rows = ablation.validation_rows(pairs, SAME_DATE, ABLATION_BASELINE)

    assert [(r.scope, r.degradation) for r in rows] == [*CELLS, (ALL, ALL)]
    assert {(r.measure, r.method, r.reference) for r in rows} == {
        ("validation", SAME_DATE, ABLATION_BASELINE)
    }
    dense = rows[2]
    # The pair the pretrained model fails is left out of both means.
    assert (dense.items, dense.failures, dense.reference_failures) == (2, 0, 1)
    assert (dense.common, dense.mean, dense.reference_mean) == (1, 0.20, 0.30)
    whole = rows[-1]
    assert (whole.items, whole.common) == (8, 7)
    assert whole.difference == pytest.approx(1.0 / 7 - 1.6 / 7)


def test_closure_is_read_on_the_validation_chips_then_on_the_training_chips(tmp_path):
    _, triplets = read_tables(tmp_path)

    validation, train = ablation.closure_rows(
        triplets, ROLES, CROSS_DATE, ABLATION_BASELINE
    )

    assert (validation.scope, train.scope) == ("validation chips", "training chips")
    assert (validation.items, validation.failures, validation.reference_failures) == (
        2,
        0,
        1,
    )
    assert (validation.common, validation.mean, validation.reference_mean) == (
        1,
        0.15,
        0.3,
    )
    assert (train.items, train.common) == (2, 2)
    assert train.difference == pytest.approx(-0.2)


def training_run(path, method, cross_date, steps=4, budget=4, kept=0.2):
    """Write what a training leaves in its directory, and read it back."""
    path.mkdir(parents=True)
    (path / BEST).write_bytes(method.encode())
    context = {
        "train": {"model": "large", "steps": budget, "batch_size": 8},
        "pairs": {"cross_date": cross_date, "seed": 0},
        "ranges": {"gain": [0.6, 1.67]},
        "chips": ["milan"],
        "commit": "abcdef0123",
        "sessions": [{"code": {"commit": "abcdef0123", "dirty": False}}],
    }
    (path / "context.json").write_text(json.dumps(context))
    _write_log(
        [LogRow(s, 1.0 / s, 0.5, 1e-4, 3.0, 0.5) for s in range(1, steps + 1)],
        path / LOG,
    )
    trainval.write_validations(
        [
            ValidationRow(0, ALL_PRESETS, 6, 0.5, 0.4, 0.1, 9.0),
            ValidationRow(2, ALL_PRESETS, 6, kept, 0.2, 0.0, 9.0),
            ValidationRow(4, ALL_PRESETS, 6, kept + 0.1, 0.3, 0.0, 9.0),
        ],
        path / VALIDATIONS,
    )
    sha256 = hashlib.sha256(method.encode()).hexdigest()
    return ablation.read_training(method, path / BEST, sha256)


def runs(tmp_path, **options):
    return (
        training_run(tmp_path / "large-same-date", SAME_DATE, 0.0),
        training_run(tmp_path / "large-cross-date", CROSS_DATE, 0.5, **options),
    )


def test_a_training_is_read_from_the_directory_of_its_kept_weights(tmp_path):
    run, _ = runs(tmp_path)

    assert (run.method, run.path) == (SAME_DATE, tmp_path / "large-same-date")
    assert (run.steps, run.budget, run.kept.step) == (4, 4, 2)


def test_weights_that_are_not_a_run_s_kept_ones_are_refused(tmp_path):
    with pytest.raises(ValueError, match="reads a run's kept weights, best.pt"):
        ablation.read_training("raft_ft", tmp_path / "checkpoint.pt", "")
    with pytest.raises(ValueError, match="not a training run: no context.json"):
        ablation.read_training("raft_ft", tmp_path / BEST, "")


def test_the_two_runs_of_the_ablation_differ_by_the_cross_date_share_alone(tmp_path):
    same, cross = runs(tmp_path)

    assert ablation.differences(same, cross) == ["pairs.cross_date"]
    other = dataclasses.replace(
        cross, context={**cross.context, "train": {"steps": 8}, "chips": []}
    )
    assert ablation.differences(same, other) == [
        "train.batch_size",
        "train.model",
        "train.steps",
        "pairs.cross_date",
        "chips",
    ]


def test_the_ablation_reads_both_variants_and_applies_the_rule(tmp_path):
    pairs, triplets = read_tables(tmp_path)

    read = ablation.read(pairs, triplets, ROLES, ABLATION_BASELINE, runs(tmp_path))

    assert read.variants == ABLATION_VARIANTS
    # 3 comparisons, each of 4 cells and the whole set, and of 2 roles.
    assert len(read.rows) == 3 * (5 + 2)
    assert len(read.of("validation", CROSS_DATE, SAME_DATE)) == 5
    # Both beat the pretrained model; on the validation chip the cross-date
    # variant fails no triplet where the same-date one fails one.
    assert read.choice.eligible == ABLATION_VARIANTS
    assert read.choice.retained == CROSS_DATE


def test_a_run_without_a_method_of_the_ablation_is_refused(tmp_path):
    pairs, triplets = read_tables(tmp_path)
    del triplets[CROSS_DATE]

    with pytest.raises(ValueError, match=f"closure run has no row for {CROSS_DATE}"):
        ablation.read(pairs, triplets, ROLES, ABLATION_BASELINE, runs(tmp_path))


def test_the_report_gives_the_runs_the_tables_and_what_the_rule_gives(tmp_path):
    pairs, triplets = read_tables(tmp_path)
    read = ablation.read(pairs, triplets, ROLES, ABLATION_BASELINE, runs(tmp_path))

    report = ablation.to_markdown(read)

    assert f"| | {SAME_DATE} | {CROSS_DATE} |" in report
    assert "| cross-date share | 0 | 0.5 |" in report
    assert "| steps done / budget | 4 / 4 | 4 / 4 |" in report
    assert "| kept step | 2 | 2 |" in report
    assert "not given alike: pairs.cross_date. The two training losses" in report
    assert (
        f"{SAME_DATE} beats raft on the validation set: it fails 0 pairs where "
        "raft fails 1, and over the 7 pairs neither fails its mean error is "
        "0.1429 px where raft's is 0.2286 px." in report
    )
    assert "| dense | clean | 2 | 1 | 0 | 1 | 0.3000 | 0.2000 | -0.1000 |" in report
    assert "| validation chips | 2 | 1 | 0 | 1 | 0.3000 | 0.1500 | -0.1500 |" in report
    assert (
        f"The closure of {CROSS_DATE} is better than {SAME_DATE} on the validation "
        "chips and better than it on the training chips." in report
    )
    assert report.endswith(f"**What the rule gives.** {read.choice.reason}\n")
    assert f"{CROSS_DATE} closes better than {SAME_DATE}" in read.choice.reason


@pytest.mark.parametrize(
    "difference, written",
    [(-0.1, "-0.1000"), (0.0003, "+0.0003"), (0.0, "0.0000"), (-2e-5, "-2e-05")],
)
def test_a_difference_too_small_for_four_decimals_keeps_its_sign(difference, written):
    assert ablation._px(difference, signed=True) == written


def test_the_report_says_when_the_runs_are_not_the_ablation_s(tmp_path):
    pairs, triplets = read_tables(tmp_path)
    same, cross = runs(tmp_path, steps=3)
    cross = dataclasses.replace(
        cross, context={**cross.context, "pairs": same.context["pairs"]}
    )

    report = ablation.to_markdown(
        ablation.read(pairs, triplets, ROLES, ABLATION_BASELINE, (same, cross))
    )

    assert "not given alike: none. The ablation expects pairs.cross_date" in report
    assert f"{CROSS_DATE} stopped at step 3 of 4: it did not run to its" in report


def test_the_curves_of_the_two_runs_are_saved_as_a_figure(tmp_path):
    ablation.curves(runs(tmp_path), tmp_path / "figures" / "curves.png")

    assert (tmp_path / "figures" / "curves.png").stat().st_size > 10_000


def scored_runs(tmp_path, trainings):
    """Write the directories validate and validate-cycle leave for the ablation."""
    weights = {
        run.method: {"path": str(run.path / BEST), "sha256": run.sha256}
        for run in trainings
    }
    context = {
        "recorded_at": "2026-10-05T10:00:00+00:00",
        "code": {"commit": "abcdef0123", "dirty": False},
        "checkpoints": weights,
        "validation": {"chips": ROLES},
    }
    for name, table, rows in (
        ("validation", "pairs.csv", pair_results()),
        ("validation-cycle", "triplets.csv", triplet_rows()),
    ):
        write_csv(rows, tmp_path / name / table)
        (tmp_path / name / "context.json").write_text(json.dumps(context))
    return [
        "ablation",
        "--validation",
        str(tmp_path / "validation"),
        "--closure",
        str(tmp_path / "validation-cycle"),
        "--out",
        str(tmp_path / "ablation"),
    ]


def test_ablation_writes_the_report_its_rows_the_curves_and_the_choice(
    tmp_path, capsys
):
    trainings = runs(tmp_path)

    main(scored_runs(tmp_path, trainings))

    out = tmp_path / "ablation"
    printed = capsys.readouterr().out
    assert printed == (out / "summary.md").read_text()
    assert printed.startswith("The ablation: RAFT large fine-tuned on same-date")
    assert "**What the rule gives.** Both variants beat the pretrained" in printed
    assert len((out / "comparisons.csv").read_text().splitlines()) == 1 + 21
    assert (out / "curves.png").is_file()
    context = json.loads((out / "context.json").read_text())
    assert context["choice"]["retained"] == CROSS_DATE
    assert context["choice"]["eligible"] == list(ABLATION_VARIANTS)
    assert context["checkpoints"][SAME_DATE]["sha256"] == trainings[0].sha256
    assert context["read"]["closure"]["code"]["commit"] == "abcdef0123"


def test_ablation_refuses_two_runs_that_did_not_score_the_same_weights(tmp_path):
    args = scored_runs(tmp_path, runs(tmp_path))
    closure = tmp_path / "validation-cycle" / "context.json"
    context = json.loads(closure.read_text())
    context["checkpoints"][CROSS_DATE]["sha256"] = "0" * 64
    closure.write_text(json.dumps(context))

    with pytest.raises(SystemExit, match=f"same weights for {CROSS_DATE}"):
        main(args)


def test_ablation_needs_the_two_scored_runs(tmp_path):
    args = ["ablation", "--validation", str(tmp_path), "--closure", str(tmp_path)]

    with pytest.raises(SystemExit, match=r"no pairs.csv and context.json in .*: run"):
        main(args)


def test_ablation_refuses_a_run_of_methods_without_weights(tmp_path):
    args = scored_runs(tmp_path, runs(tmp_path))

    with pytest.raises(SystemExit, match="names no checkpoint for raft_small"):
        main([*args, "--variants", "raft_small", CROSS_DATE])


def test_a_run_names_the_weights_of_its_fine_tuned_methods_by_hash(tmp_path):
    weights = tmp_path / BEST
    weights.write_bytes(b"weights")
    methods = {
        "raft": SimpleNamespace(checkpoint=""),
        "phase_correlation": SimpleNamespace(),
        "raft_ft": SimpleNamespace(checkpoint=str(weights)),
    }

    assert _checkpoints(methods) == {
        "raft_ft": {
            "path": str(weights),
            "sha256": hashlib.sha256(b"weights").hexdigest(),
        }
    }


def test_the_two_training_configs_differ_by_the_cross_date_share_alone():
    paths = [CONFIGS / "train-same-date.toml", CONFIGS / "train-cross-date.toml"]
    same, cross = (tomllib.loads(path.read_text()) for path in paths)

    assert same["train"] == cross["train"]
    assert same["pairs"].pop("cross_date") == 0.0
    assert cross["pairs"].pop("cross_date") == 0.5
    assert same["pairs"] == cross["pairs"]
    assert [load_pairs_config(p).cross_date for p in paths] == [0.0, 0.5]


@pytest.mark.parametrize("name", ["train-same-date.toml", "train-cross-date.toml"])
def test_a_training_of_the_ablation_has_the_budget_that_was_decided(name):
    run = load_train_config(CONFIGS / name)
    timed = load_train_config(CONFIGS / "train-timing.toml")

    # 10,000 steps of 8 new pairs, validated every 500 and saved every 250.
    assert (run.model, run.steps, run.batch_size, run.n_pairs) == ("large", 10000, 8, 0)
    assert (run.validate_every, run.checkpoint_every) == (500, 250)
    assert (run.device, run.workers) == ("cuda", 3)
    # The recipe is the one the timing run measured.
    intervals = {"steps": 10000, "validate_every": 500, "checkpoint_every": 250}
    assert run == dataclasses.replace(timed, **intervals)
    pairs, timed_pairs = (
        load_pairs_config(CONFIGS / n) for n in (name, "train-timing.toml")
    )
    assert dataclasses.replace(pairs, cross_date=0.5) == timed_pairs


def test_the_variants_of_the_ablation_run_the_weights_each_training_kept():
    methods = load_methods(CONFIGS / "methods.toml")

    assert [
        (methods[v].model, methods[v].checkpoint, methods[v].iterations)
        for v in ABLATION_VARIANTS
    ] == [
        ("large", "outputs/train/large-same-date/best.pt", 12),
        ("large", "outputs/train/large-cross-date/best.pt", 12),
    ]
    assert methods[ABLATION_BASELINE].checkpoint == ""

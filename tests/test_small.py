import dataclasses
import json
import math
import tomllib

import pytest
from test_ablation import (
    CONFIGS,
    ROLES,
    ROOT,
    pair_results,
    paired,
    scored_runs,
    training_run,
    triplet_rows,
)

from satreg import ablation, small
from satreg.ablation import CLOSURE, VALIDATION_SET
from satreg.cli import (
    ABLATION_CLOSURE,
    ABLATION_VALIDATION,
    SMALL_LARGE,
    SMALL_LARGE_PRETRAINED,
    SMALL_METHOD,
    SMALL_PRETRAINED,
    main,
)
from satreg.methods import load_methods
from satreg.report import write_csv
from satreg.small import GAIN, NO_GAIN, WORSE
from satreg.train import load_train_config
from satreg.trainpairs import load_pairs_config

METHODS = (SMALL_PRETRAINED, SMALL_METHOD, SMALL_LARGE_PRETRAINED, SMALL_LARGE)

# Mean error of each method on two pairs of four cells, and closure on two
# windows of a validation chip and a training chip (None: a failed triplet).
PAIRS = {
    SMALL_PRETRAINED: [0.20, 0.30, 0.20, 0.30, 0.40, math.nan, 0.40, math.nan],
    SMALL_METHOD: [0.15, 0.20, 0.15, 0.20, 0.30, math.nan, 0.30, 0.50],
    SMALL_LARGE_PRETRAINED: [0.10, 0.20, 0.10, 0.20, 0.30, math.nan, 0.30, 0.40],
    SMALL_LARGE: [0.08, 0.12, 0.08, 0.12, 0.25, math.nan, 0.25, 0.35],
}
TRIPLETS = {
    SMALL_PRETRAINED: {"lyon": [0.5, None], "milan": [0.5, 0.5]},
    SMALL_METHOD: {"lyon": [0.4, 0.6], "milan": [0.2, 0.2]},
    SMALL_LARGE_PRETRAINED: {"lyon": [0.3, None], "milan": [0.3, 0.3]},
    SMALL_LARGE: {"lyon": [0.15, 0.4], "milan": [0.1, 0.1]},
}


@pytest.mark.parametrize(
    ("reading", "word", "ending"),
    [
        # Fewer failures and a lower mean, by any margin.
        (paired(1, 2, 0.0999, 0.1), GAIN, "it beats raft_small."),
        (paired(2, 2, 0.05, 0.1), GAIN, "it beats raft_small."),
        # The same the other way round.
        (paired(2, 1, 0.1, 0.0999), WORSE, "raft_small beats it."),
        (paired(2, 2, 0.1, 0.05), WORSE, "raft_small beats it."),
        # A lower mean bought with one more failure, and the reverse.
        (paired(3, 2, 0.05, 0.1), NO_GAIN, "neither beats the other."),
        (paired(1, 2, 0.1, 0.05), NO_GAIN, "neither beats the other."),
        # Nothing separates them, or no pair to take a mean over.
        (paired(2, 2, 0.1, 0.1), NO_GAIN, "neither beats the other."),
        (paired(2, 2, math.nan, math.nan), NO_GAIN, "neither beats the other."),
    ],
)
def test_a_training_is_a_gain_no_gain_or_worse_by_the_criterion_of_n3(
    reading, word, ending
):
    verdict = small.judge("trained", "raft_small", reading)

    assert verdict.word == word
    assert verdict.reason.endswith(ending)
    assert verdict.reason.startswith(
        f"trained fails {reading.failures} pairs where raft_small fails "
        f"{reading.reference_failures}, and over the 8 pairs neither fails"
    )


def runs(tmp_path, **options):
    """The training of RAFT small, then the retained one of RAFT large."""
    return (
        training_run(
            tmp_path / "small-cross-date", SMALL_METHOD, 0.5, model="small", **options
        ),
        training_run(tmp_path / "large-cross-date", SMALL_LARGE, 0.5),
    )


def test_the_training_of_raft_small_differs_from_the_large_one_by_the_model(tmp_path):
    trained, large = runs(tmp_path)

    assert ablation.differences(trained, large) == ["train.model"]
    assert small.departures(trained, large) == []


def test_another_recipe_than_the_large_one_is_a_departure(tmp_path):
    trained, large = runs(tmp_path)
    recipe = {**trained.context["train"], "batch_size": 16}
    trained = dataclasses.replace(trained, context={**trained.context, "train": recipe})

    assert small.departures(trained, large) == [
        "the two runs differ by more than the model (train.batch_size)"
    ]


def test_weights_of_the_other_model_are_a_departure(tmp_path):
    trained, large = runs(tmp_path)

    # The two weights swapped in the methods config.
    swapped = small.departures(
        dataclasses.replace(large, method=SMALL_METHOD),
        dataclasses.replace(trained, method=SMALL_LARGE),
    )

    assert swapped == [
        f"{SMALL_METHOD} was trained as RAFT large, not small",
        f"{SMALL_LARGE} was trained as RAFT small, not large",
    ]


def test_a_training_stopped_short_of_its_budget_is_a_departure(tmp_path):
    assert small.departures(*runs(tmp_path, steps=3)) == [
        f"{SMALL_METHOD} stopped at step 3 of 4"
    ]


def read_tables(tmp_path):
    write_csv(pair_results(PAIRS), tmp_path / "pairs.csv")
    write_csv(triplet_rows(TRIPLETS), tmp_path / "triplets.csv")
    return (
        ablation.read_pairs(tmp_path / "pairs.csv"),
        ablation.read_triplets(tmp_path / "triplets.csv"),
    )


def read(tmp_path, trainings=None):
    return small.read(
        *read_tables(tmp_path),
        ROLES,
        SMALL_PRETRAINED,
        SMALL_LARGE_PRETRAINED,
        trainings or runs(tmp_path),
    )


def test_the_fine_tuned_small_is_read_next_to_the_three_other_methods(tmp_path):
    reading = read(tmp_path)

    assert reading.method == SMALL_METHOD
    assert reading.comparisons == (
        (SMALL_METHOD, SMALL_PRETRAINED),
        (SMALL_METHOD, SMALL_LARGE),
        (SMALL_METHOD, SMALL_LARGE_PRETRAINED),
        (SMALL_PRETRAINED, SMALL_LARGE_PRETRAINED),
    )
    # 4 comparisons, each of 4 cells and the whole set, of 2 roles and of the
    # validation chip.
    assert len(reading.rows) == 4 * (5 + 2 + 1)
    whole = reading.of(VALIDATION_SET, SMALL_METHOD, SMALL_PRETRAINED)[-1]
    # It fails one pair where the pretrained small fails two.
    assert (whole.failures, whole.reference_failures, whole.common) == (1, 2, 6)
    assert whole.mean == pytest.approx(1.3 / 6)
    assert whole.reference_mean == pytest.approx(0.3)
    assert reading.departures == ()
    assert reading.verdict.word == GAIN


def test_the_verdict_is_read_next_to_the_pretrained_small_and_no_other(tmp_path):
    # The fine-tuned small is behind RAFT large, fine-tuned or not: a gain all
    # the same.
    reading = read(tmp_path)

    for large in (SMALL_LARGE, SMALL_LARGE_PRETRAINED):
        whole = reading.of(VALIDATION_SET, SMALL_METHOD, large)[-1]
        assert not ablation.beats(ablation.paired_of(whole))
    assert reading.verdict.word == GAIN
    assert reading.verdict.reason.endswith(f"it beats {SMALL_PRETRAINED}.")


def test_a_run_without_one_of_the_four_methods_is_refused(tmp_path):
    pairs, triplets = read_tables(tmp_path)
    del pairs[SMALL_PRETRAINED]

    with pytest.raises(
        ValueError, match=f"validation run has no row for {SMALL_PRETRAINED}"
    ):
        small.read(
            pairs,
            triplets,
            ROLES,
            SMALL_PRETRAINED,
            SMALL_LARGE_PRETRAINED,
            runs(tmp_path),
        )


def test_the_report_gives_the_runs_the_four_readings_and_the_verdict(tmp_path):
    reading = read(tmp_path)

    report = small.to_markdown(reading)

    assert f"| | {SMALL_METHOD} | {SMALL_LARGE} |" in report
    assert "| steps done / budget | 4 / 4 | 4 / 4 |" in report
    assert "not given alike: train.model. The device and" in report
    for lead, (method, reference) in zip(small.LEADS, reading.comparisons, strict=True):
        assert (
            f"**{lead}.**\n\n{method} next to {reference}, on the validation set:"
            in report
        )
    assert (
        f"{SMALL_METHOD} beats {SMALL_PRETRAINED} on the validation set: it fails "
        f"1 pairs where {SMALL_PRETRAINED} fails 2, and over the 6 pairs neither "
        f"fails its mean error is 0.2167 px where {SMALL_PRETRAINED}'s is 0.3000 px."
        in report
    )
    assert f"{SMALL_METHOD} does not beat {SMALL_LARGE} on the validation" in report
    assert "| validation chips | 2 | 1 | 0 | 1 | 0.5000 | 0.4000 | -0.1000 |" in report
    assert (
        f"Its closure is better than {SMALL_PRETRAINED} on the validation chips "
        "and better than it on the training chips." in report
    )
    assert report.endswith(
        f"**Verdict: gain.** On the validation set, {reading.verdict.reason}\n"
    )


def test_no_verdict_is_given_to_a_run_that_is_not_the_training(tmp_path):
    reading = read(tmp_path, runs(tmp_path, steps=3))

    report = small.to_markdown(reading)

    stopped = f"{SMALL_METHOD} stopped at step 3 of 4"
    assert reading.verdict is None
    assert reading.departures == (stopped,)
    # The tables are still there, and no word is read from them.
    assert reading.of(CLOSURE, SMALL_METHOD, SMALL_PRETRAINED)
    assert "**Verdict" not in report
    assert report.endswith(
        f"and this is not it: {stopped}. The tables above give none.\n"
    )


def scored(tmp_path, trainings):
    """Write the directories make small leaves for the reading."""
    return scored_runs(tmp_path, trainings, "small", METHODS, PAIRS, TRIPLETS)


def test_small_writes_the_report_its_rows_the_curves_and_the_verdict(tmp_path, capsys):
    trainings = runs(tmp_path)

    main(scored(tmp_path, trainings))

    out = tmp_path / "small"
    printed = capsys.readouterr().out
    assert printed == (out / "summary.md").read_text()
    assert printed.startswith(f"RAFT small fine-tuned ({SMALL_METHOD}) with the pairs")
    assert "**Verdict: gain.** On the validation set," in printed
    assert len((out / "comparisons.csv").read_text().splitlines()) == 1 + 32
    assert (out / "curves.png").is_file()
    context = json.loads((out / "context.json").read_text())
    assert context["departures"] == []
    assert context["verdict"]["word"] == GAIN
    assert list(context["checkpoints"]) == [SMALL_METHOD, SMALL_LARGE]
    assert context["checkpoints"][SMALL_METHOD]["sha256"] == trainings[0].sha256
    assert context["read"]["validation"]["code"]["commit"] == "abcdef0123"


def test_small_writes_no_verdict_for_a_training_stopped_short(tmp_path, capsys):
    main(scored(tmp_path, runs(tmp_path, steps=3)))

    stopped = f"{SMALL_METHOD} stopped at step 3 of 4"
    assert "**No verdict.**" in capsys.readouterr().out
    context = json.loads((tmp_path / "small" / "context.json").read_text())
    assert (context["verdict"], context["departures"]) == (None, [stopped])


def test_small_needs_the_two_scored_runs(tmp_path):
    with pytest.raises(
        SystemExit, match=r"no pairs.csv and context.json in .*: run make small"
    ):
        main(["small", "--out", str(tmp_path)])


def test_small_refuses_a_run_that_did_not_score_the_trained_small(tmp_path):
    args = scored(tmp_path, runs(tmp_path))
    path = tmp_path / "small" / ABLATION_VALIDATION / "context.json"
    context = json.loads(path.read_text())
    del context["checkpoints"][SMALL_METHOD]
    path.write_text(json.dumps(context))

    with pytest.raises(SystemExit, match=f"names no checkpoint for {SMALL_METHOD}"):
        main(args)


def test_small_refuses_weights_rewritten_since_they_were_scored(tmp_path):
    trainings = runs(tmp_path)
    args = scored(tmp_path, trainings)
    (trainings[0].path / "best.pt").write_bytes(b"later weights")

    with pytest.raises(SystemExit, match=f"not the file {SMALL_METHOD} was scored"):
        main(args)


def test_make_small_scores_what_the_reading_reads():
    recipe = (ROOT / "Makefile").read_text()

    assert f"SMALL_METHODS = {' '.join(METHODS)}\n" in recipe
    assert f"--out $(SMALL)/{ABLATION_VALIDATION}\n" in recipe
    assert f"--out $(SMALL)/{ABLATION_CLOSURE}\n" in recipe
    assert "satreg small --out $(SMALL)\n" in recipe


def test_the_small_training_config_is_the_retained_large_one_but_for_the_model():
    paths = [CONFIGS / "train-small.toml", CONFIGS / "train-cross-date.toml"]
    trained, large = (tomllib.loads(path.read_text()) for path in paths)

    assert (trained["train"].pop("model"), large["train"].pop("model")) == (
        "small",
        "large",
    )
    assert trained == large
    # The recipe, the budget and the seed, as the loaders read them.
    recipes = [load_train_config(path) for path in paths]
    assert dataclasses.replace(recipes[1], model="small") == recipes[0]
    assert (recipes[0].steps, recipes[0].batch_size) == (10000, 8)
    assert load_pairs_config(paths[0]) == load_pairs_config(paths[1])
    assert (load_pairs_config(paths[0]).cross_date, trained["pairs"]["seed"]) == (
        0.5,
        0,
    )


def test_the_fine_tuned_small_runs_the_weights_its_training_kept():
    methods = load_methods(CONFIGS / "methods.toml")

    trained, pretrained = methods[SMALL_METHOD], methods[SMALL_PRETRAINED]
    assert (trained.model, trained.checkpoint, trained.iterations) == (
        "small",
        "outputs/train/small-cross-date/best.pt",
        12,
    )
    assert (pretrained.model, pretrained.checkpoint) == ("small", "")
    # It is read next to the variant the ablation retained.
    assert methods[SMALL_LARGE].checkpoint == "outputs/train/large-cross-date/best.pt"
    assert methods[SMALL_LARGE_PRETRAINED].model == "large"

import math
from pathlib import Path

import pytest
from test_raft import needs_raft

from satreg.benchmark import BenchmarkConfig, run_benchmark
from satreg.degrade import load_presets
from satreg.methods.raft import Raft
from satreg.texture import fractal_texture
from satreg.trainval import (
    ALL_PRESETS,
    LightValidation,
    ValidationRow,
    best,
    read_validations,
    selection_score,
    to_markdown,
    write_validations,
)

CONFIGS = Path(__file__).parents[1] / "configs"
PRESETS = load_presets(CONFIGS / "degradations.toml")


def test_the_selection_score_is_the_mean_error_of_every_pair():
    assert selection_score([0.1, 0.3], threshold=1.0) == pytest.approx(0.2)


def test_a_failed_pair_counts_for_the_threshold_however_far_off_it_is():
    near = selection_score([0.2, 2.0], threshold=1.0)
    far = selection_score([0.2, 30.0], threshold=1.0)
    crashed = selection_score([0.2, math.nan], threshold=1.0)

    assert near == far == crashed == pytest.approx(0.6)


def test_failing_more_pairs_never_lowers_the_score():
    # The table's mean error leaves failed pairs out: 0.1 px for the second
    # network against 0.2 px for the first, which fails none.
    assert selection_score([0.1, 0.3], 1.0) < selection_score([0.1, 5.0], 1.0)


def test_a_score_needs_a_pair():
    with pytest.raises(ValueError, match="no pair to score"):
        selection_score([], threshold=1.0)


def row(step, score, degradation=ALL_PRESETS):
    return ValidationRow(step, degradation, 6, score, score / 2, 0.25, 1.5)


def test_the_kept_validation_has_the_lowest_score_over_all_presets():
    rows = [
        row(0, 0.5),
        row(10, 0.4),
        row(20, 0.1, "clean"),
        row(20, 0.3),
        row(30, 0.35),
    ]

    assert best(rows) == row(20, 0.3)


def test_the_pretrained_weights_are_never_kept():
    assert best([row(0, 0.1), row(10, 0.4)]) == row(10, 0.4)
    assert best([row(0, 0.1)]) is None
    assert best([]) is None


def test_the_earliest_of_equal_validations_is_kept():
    assert best([row(10, 0.4), row(20, 0.4)]) == row(10, 0.4)


def test_validations_are_read_back_as_written(tmp_path):
    rows = [row(0, 0.5, "clean"), row(0, 0.5), row(10, 1 / 3, "clean"), row(10, 1 / 3)]
    path = tmp_path / "validation.csv"

    write_validations(rows, path)

    assert read_validations(path) == rows
    assert read_validations(tmp_path / "none.csv") == []


def test_the_table_has_one_line_per_step_and_marks_the_kept_one():
    rows = [
        row(0, 0.2, "clean"),
        row(0, 0.6, "hard"),
        row(0, 0.4),
        row(10, 0.1, "clean"),
        row(10, 0.5, "hard"),
        row(10, 0.3),
    ]

    lines = to_markdown(rows).splitlines()

    assert lines[0] == (
        "| step | score (px) | clean: EPE (px) | failures | hard: EPE (px) | failures |"
    )
    assert lines[2] == "| 0 | 0.4000 | 0.100 | 25.0 % | 0.300 | 25.0 % |"
    assert lines[3] == "| 10 (kept) | 0.3000 | 0.050 | 25.0 % | 0.250 | 25.0 % |"
    assert len(lines) == 4


@needs_raft
def test_the_light_set_scores_a_network_as_the_benchmark_scores_its_method():
    images = {"town": fractal_texture(256, seed=1)}
    config = BenchmarkConfig(
        n_pairs=2, size=128, scenarios=("translation", "dense"), seed=5
    )
    presets = {name: PRESETS[name] for name in ("clean", "hard")}
    method = Raft(model="small")
    light = LightValidation(images, config, presets, method.iterations, "cpu")

    rows = light(method.network(), step=7)

    results = run_benchmark(images, {"raft_small": method}, config, presets)
    assert [d for d, _ in light.pairs] == [r.degradation for r in results]
    errors = [epe for _, epe in light.errors(method.network())]
    assert errors == pytest.approx([r.mean_epe for r in results], abs=1e-5)
    assert [(r.step, r.degradation, r.pairs) for r in rows] == [
        (7, "clean", 4),
        (7, "hard", 4),
        (7, ALL_PRESETS, 8),
    ]
    assert rows[-1].score == pytest.approx(
        selection_score(errors, config.failure_threshold), abs=1e-5
    )

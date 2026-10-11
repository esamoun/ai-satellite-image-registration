import csv
import dataclasses
import json
import math
import tomllib
from pathlib import Path

import numpy as np
import pytest
from test_ablation import pair_result, triplet_row

from satreg import final
from satreg import weights as published
from satreg.ablation import ALL, BETTER, EQUAL, PAIR_KEY, WORSE, Score
from satreg.cli import FINAL_WEIGHTS, main
from satreg.final import EVERY_SITE, HELD_OUT, LARGE, SEEN, SMALL, STAND_IN
from satreg.report import write_csv

SITES = ("beauce", "alps", "libya4")
TARGET = ("alps", "libya4")
CELLS = (("translation", "clean"), ("translation", "hard"), ("dense", "clean"))
DRAWS = 4
# The mean error of each method on a pair, in px, before what the pair adds.
BASE = {"raft": 0.30, "raft_ft": 0.20, "raft_small": 0.50, "raft_small_ft": 0.45}
CLOSURE = {"raft": 0.40, "raft_ft": 0.30, "raft_small": 0.60, "raft_small_ft": 0.60}


def keys(sites=SITES, cells=CELLS, draws=DRAWS):
    return [
        (site, "", scenario, preset, str(pair))
        for site in sites
        for pair in range(draws)
        for scenario, preset in cells
    ]


def table(change=None, sites=SITES, cells=CELLS, draws=DRAWS):
    """Pairs of the four RAFT methods: an error by method, cell and draw.

    ``change`` takes a method and a pair's key and returns its error, or
    ``None`` to leave it; a NaN is a failed pair.
    """
    pairs = {}
    for method, base in BASE.items():
        pairs[method] = {}
        for key in keys(sites, cells, draws):
            epe = base + 0.01 * cells.index(key[2:4]) + 0.001 * int(key[4])
            changed = None if change is None else change(method, key)
            epe = epe if changed is None else changed
            pairs[method][key] = Score(math.isnan(epe), epe)
    return pairs


def closures(change=None, sites=SITES, windows=2):
    """Real triplets of the four methods, and a simulated one nobody reads."""
    triplets = {}
    for method, base in CLOSURE.items():
        triplets[method] = {}
        for site in sites:
            for window in range(windows):
                key = (site, "real", "days-anchor-season", str(window))
                value = base if change is None else change(method, key)
                value = base if value is None else value
                triplets[method][key] = Score(math.isnan(value), value)
            # A simulated triplet every method fails.
            triplets[method][(site, "translation", "0", "0")] = Score(True, 9.0)
    return triplets


def read(pairs=None, triplets=None, **options):
    options = {"resamples": 400, **options}
    return final.read(pairs or table(), triplets or closures(), TARGET, **options)


def test_a_resample_is_decided_by_its_seed():
    pairs = table()
    args = (pairs["raft_ft"], pairs["raft"], keys())

    first = final.resampled(*args, resamples=50, seed=3)

    assert first.shape == (50,)
    assert np.array_equal(first, final.resampled(*args, resamples=50, seed=3))
    assert not np.array_equal(first, final.resampled(*args, resamples=50, seed=4))


def test_a_difference_that_is_the_same_on_every_pair_has_no_width():
    pairs = table()

    low, high = final.interval(
        final.resampled(pairs["raft_ft"], pairs["raft"], keys(), resamples=200)
    )

    assert low == pytest.approx(-0.10) and high == pytest.approx(-0.10)


def test_a_resample_reads_the_difference_over_the_pairs_neither_fails():
    # The fine-tuned model is 1 px worse on the pairs one of the two fails.
    lost = set(keys()[:6])

    def change(method, key):
        if key not in lost:
            return None
        failed = method == ("raft" if int(key[4]) % 2 else "raft_ft")
        return math.nan if failed else {"raft_ft": 1.3, "raft": 0.3}.get(method)

    pairs = table(change)

    differences = final.resampled(pairs["raft_ft"], pairs["raft"], keys(), None, 300)

    assert differences == pytest.approx(-0.10)


def test_resamples_with_no_pair_neither_fails_are_left_out_of_the_interval():
    differences = np.array([math.nan, -0.2, -0.1, math.nan, 0.0])

    assert final.interval(differences, level=100.0) == (-0.2, 0.0)
    assert all(math.isnan(end) for end in final.interval(np.array([math.nan])))


def test_resampling_draws_is_wider_when_the_pairs_of_a_draw_move_together():
    # The gain of a draw is the same under every cell: 36 pairs, 12 draws.
    gains = {draw: i for i, draw in enumerate(sorted(map(final.draw_of, keys())))}

    def change(method, key):
        if method != "raft_ft":
            return 0.5
        return 0.5 - 0.01 * gains[final.draw_of(key)]

    pairs = table(change)
    args = (pairs["raft_ft"], pairs["raft"], keys())

    by_pair = final.interval(final.resampled(*args, None, 2000))
    by_draw = final.interval(final.resampled(*args, final.draw_of, 2000))

    assert by_draw[1] - by_draw[0] > 1.5 * (by_pair[1] - by_pair[0])
    assert by_draw[0] < by_pair[0] < by_pair[1] < by_draw[1]


def test_in_a_cell_a_draw_is_a_pair_and_the_two_intervals_are_the_same():
    pairs = table(lambda method, key: 0.5 + 0.02 * int(key[4]) * (method == "raft"))

    rows = read(pairs).pairs_of(LARGE, HELD_OUT, cells=True)

    assert [(row.scenario, row.degradation) for row in rows] == list(CELLS)
    for row in rows:
        assert (row.pairs, row.draws) == (2 * DRAWS, 2 * DRAWS)
        assert (row.low, row.high) == (row.draws_low, row.draws_high)


def test_the_criterion_is_read_on_the_held_out_sites_then_on_each_then_the_others():
    found = read()

    assert found.scopes == {
        HELD_OUT: TARGET,
        "alps": ("alps",),
        "libya4": ("libya4",),
        SEEN: ("beauce",),
        "beauce": ("beauce",),
    }
    assert found.target == HELD_OUT and not found.rehearsal
    # Per model: a row over every pair and a row per cell, for each scope.
    assert len(found.criterion) == 2 * 5 * (1 + len(CELLS))
    (row,) = found.pairs_of(LARGE, HELD_OUT)
    assert (row.method, row.reference) == LARGE
    assert (row.scenario, row.degradation) == (ALL, ALL)
    assert (row.pairs, row.draws) == (2 * DRAWS * len(CELLS), 2 * DRAWS)
    assert (row.failures, row.reference_failures, row.common) == (0, 0, row.pairs)
    assert row.mean == pytest.approx(0.2115) and row.difference == pytest.approx(-0.1)
    assert row.reference_mean == pytest.approx(0.3115)
    assert row.beats and found.answer
    (small,) = found.pairs_of(SMALL, "alps")
    assert small.pairs == DRAWS * len(CELLS) and small.beats
    assert small.difference == pytest.approx(-0.05)


def test_the_figures_of_the_criterion_are_those_of_the_held_out_pairs_alone():
    def change(method, key):
        # On the seen site the fine-tuned model is far worse, and fails.
        if key[0] == "beauce" and method == "raft_ft":
            return math.nan if key[4] == "0" else 2.0
        # On alps the pretrained model fails a pair the mean then leaves out.
        if key == ("alps", "", "dense", "clean", "1") and method == "raft":
            return math.nan
        return None

    found = read(table(change))

    (row,) = found.pairs_of(LARGE, HELD_OUT)
    assert (row.failures, row.reference_failures, row.common) == (0, 1, row.pairs - 1)
    assert row.beats and found.answer
    (seen,) = found.pairs_of(LARGE, SEEN)
    assert (seen.failures, seen.reference_failures) == (len(CELLS), 0)
    assert not seen.beats and seen.difference > 1


@pytest.mark.parametrize(
    ("ft", "beats"),
    [
        # A lower mean bought with one more failed pair is not a yes.
        ({0: math.nan}, False),
        # As many failures and a mean lower by any margin is.
        ({}, True),
    ],
)
def test_beating_is_failing_no_more_pairs_and_a_lower_mean(ft, beats):
    first = keys(TARGET)[0]

    def change(method, key):
        if key == first and method == "raft_ft":
            return ft.get(0)
        return None

    assert read(table(change)).answer is beats


def test_closure_is_read_on_real_triplets_of_every_site_then_by_scope():
    def change(method, key):
        # The fine-tuned model fails a triplet of beauce the other closes.
        if method == "raft_ft" and key[0] == "beauce" and key[3] == "0":
            return math.nan
        return None

    found = read(triplets=closures(change))

    rows = [row for row in found.closure if (row.method, row.reference) == LARGE]
    assert [row.sites for row in rows] == [EVERY_SITE, *found.scopes]
    every = found.triplets_of(LARGE, EVERY_SITE)
    # Two windows a site, and the simulated triplets left out.
    assert (every.triplets, every.failures, every.reference_failures) == (6, 1, 0)
    assert every.reading == WORSE and every.common == 5
    held_out = found.triplets_of(LARGE, HELD_OUT)
    assert (held_out.triplets, held_out.reading) == (4, BETTER)
    assert held_out.difference == pytest.approx(-0.10)
    assert found.triplets_of(SMALL, EVERY_SITE).reading == EQUAL


def test_the_verdict_answers_first_and_reads_the_closure_in_the_same_paragraph():
    text = final.verdict(read())

    assert text.startswith(
        "**Yes**: on the 24 simulated pairs of the held-out sites (alps, libya4), "
        "raft_ft beats raft. It fails 0 pairs where raft fails 0, and over the 24 "
        "pairs neither fails its mean EPE is 0.2115 px where raft's is 0.3115 px, "
        "a difference of -0.1000 px (95 % interval -0.1000 to -0.1000 px by "
        "resampling the pairs, -0.1000 to -0.1000 px by resampling the 8 draws "
        "they come from). On the real triplets of every site, the closure of "
        "raft_ft is better than raft's: it fails 0 of 6 triplets where raft fails "
        "0, and over the 6 neither fails its mean closure is 0.3000 px where "
        "raft's is 0.4000 px."
    )
    assert text.count("\n") == 1 and "weak" not in text and "carry" not in text


def test_a_no_says_which_half_of_the_criterion_is_missed():
    first = keys(TARGET)[0]
    more_failures = table(
        lambda method, key: math.nan if (method, key) == ("raft_ft", first) else None
    )
    higher_mean = table(lambda method, key: 0.6 if method == "raft_ft" else None)

    assert (
        "raft_ft does not beat raft. It fails 1 pairs where raft fails 0"
        in final.verdict(read(more_failures))
    )
    assert "The criterion asks for both, and it fails more pairs. On the real" in (
        final.verdict(read(more_failures))
    )
    text = final.verdict(read(higher_mean))
    assert text.startswith("**No**: ")
    assert "asks for both, and its mean EPE is not lower. On the real" in text


def test_a_yes_by_a_few_thousandths_or_with_an_interval_at_zero_is_a_weak_yes():
    # 0.004 px better on every pair: under the 0.005 px of a weak yes.
    flat = {"raft": 0.30, "raft_ft": 0.296}
    thin = table(lambda method, key: flat.get(method))
    # Better on average, but worse on a quarter of the draws: the intervals
    # reach zero.
    split = {"raft": (0.30, 0.30), "raft_ft": (0.34, 0.27)}
    mixed = table(
        lambda method, key: (
            split[method][bool(int(key[4]))] if method in split else None
        )
    )

    for pairs in (thin, mixed):
        found = read(pairs, resamples=2000)
        (row,) = found.pairs_of(LARGE, HELD_OUT)
        assert row.beats and final.is_weak(row)
        assert "It is a weak yes: the difference is under 0.005 px or one of its" in (
            final.verdict(found)
        )
    assert not final.is_weak(read().pairs_of(LARGE, HELD_OUT)[0])


def test_a_yes_with_a_worse_closure_did_not_carry_to_real_pairs():
    worse = closures(lambda method, key: 0.5 if method == "raft_ft" else None)

    text = final.verdict(read(triplets=worse))

    assert text.startswith("**Yes**") and "raft_ft is worse than raft's" in text
    assert text.endswith("The gain on simulated pairs did not carry to real ones.\n")


def test_the_report_gives_the_verdict_then_each_model_by_sites_and_by_cell():
    def change(method, key):
        lost = key[:4] == ("libya4", "", "dense", "clean")
        return 0.4 if lost and method == "raft_ft" else None

    text = final.to_markdown(read(table(change)))

    assert text.startswith("**Yes**: on the 24 simulated pairs of the held-out sites")
    assert "**The criterion: raft_ft next to raft, RAFT large.**" in text
    assert "**RAFT small, raft_small_ft next to raft_small: read the same way" in text
    assert "| held-out sites | 24 | 0 | 0 | 24 | 0.3115 | 0.2413 | -0.0702 | " in text
    for heading in ("the held-out sites", "alps", "libya4"):
        assert f"\nBy cell, on {heading}:\n\n| scenario | degradation |" in text
    assert "By cell, on beauce" not in text
    assert "| dense | clean | 4 | 0 | 0 | 4 | 0.3215 | 0.4000 | +0.0785 | " in text
    assert (
        "Cells of the held-out sites where raft_ft does not beat raft: dense, "
        "clean on libya4 (0 failed pairs where raft fails 0, +0.0785 px).\n"
    ) in text
    assert "raft_small_ft beats raft_small in every cell of the held-out sites" in text
    assert "**Closure of the real triplets, raft_ft next to raft.**" in text
    assert "| every site | 6 | 0 | 0 | 6 | 0.4000 | 0.3000 | -0.1000 | better |" in text
    assert "400 resamples with seed 0" in text and "Rehearsal" not in text


def test_a_rehearsal_says_so_before_anything_else():
    found = final.read(table(), closures(), ("beauce",), rehearsal=True, resamples=50)

    text = final.to_markdown(found)

    assert found.target == STAND_IN and list(found.scopes)[0] == STAND_IN
    assert text.startswith("**Rehearsal.** Seen sites stand in for the held-out ones")
    assert "Nothing below is a result" in text.split("\n\n")[0]
    assert "simulated pairs of the stand-in sites (beauce)" in text


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda p, t: p.pop("raft_small"), "the table has no rows for raft_small"),
        (lambda p, t: t.pop("raft_ft"), "the closure run has no rows for raft_ft"),
        (
            lambda p, t: [m.pop(k) for m in t.values() for k in list(m) if "alps" in k],
            "are not of the same sites: beauce, alps, libya4 and beauce, libya4",
        ),
        (
            lambda p, t: p["raft"].pop(keys()[0]),
            "did not run on the same",
        ),
    ],
)
def test_tables_that_cannot_be_read_together_are_refused(change, message):
    pairs, triplets = table(), closures()
    change(pairs, triplets)

    with pytest.raises(ValueError, match=message):
        final.read(pairs, triplets, TARGET, resamples=10)


def test_a_criterion_needs_sites_the_table_has():
    with pytest.raises(ValueError, match="no site to read the criterion on"):
        final.read(table(), closures(), (), resamples=10)
    with pytest.raises(ValueError, match="the table has no pairs of vosges"):
        final.read(table(), closures(), ("vosges",), resamples=10)


# The command, on the directories `make n3` leaves.

MACHINE = {
    "machine": {"system": "macOS", "cpu": "Apple M1", "memory_gib": 8.0},
    "threads": {"usable_cpus": 8},
}
RUN = {
    "sites": list(SITES),
    "scenarios": ["translation", "dense"],
    "degradations": ["clean", "hard"],
    "pairs": DRAWS,
    "seed": 0,
}
RUN_CELLS = (
    ("translation", "clean"),
    ("translation", "hard"),
    ("dense", "clean"),
    ("dense", "hard"),
)


def released(methods=FINAL_WEIGHTS):
    """What a run records of the published weights it downloaded."""
    return {
        method: {
            "release": published.lookup(release).tag,
            "asset": published.lookup(release).asset,
            "sha256": published.lookup(release).sha256,
        }
        for method, release in methods.items()
    }


def rows_of(pairs, device):
    return [
        dataclasses.replace(
            pair_result(method, int(key[4]), score.value, key[2], key[3]),
            site=key[0],
            device=device,
        )
        for method, of_method in pairs.items()
        for key, score in of_method.items()
    ]


def scored_final(tmp_path, held_out=TARGET, sites=SITES, pairs=None, triplets=None):
    """Write the merged table and the closure run `satreg final` reads."""
    config = tmp_path / "n3.toml"
    options = "\n".join(f"{name} = {json.dumps(value)}" for name, value in RUN.items())
    config.write_text(
        f'[benchmark]\n{options}\nmethods = ["raft"]\n'
        f"[cycle]\nsites = {json.dumps(list(SITES))}\nsimulated_triplets = 1\n"
    )
    pairs = pairs or table(sites=sites, cells=RUN_CELLS)
    classic = {"phase_correlation": pairs["raft"]}
    run = {**RUN, "sites": list(sites), "config": str(config)}
    parts = [
        {
            "path": "outputs/n3-m1",
            "devices": ["cpu"],
            "context": {
                **MACHINE,
                "recorded_at": "2026-10-12T08:00:00+00:00",
                "code": {"commit": "abcdef0123", "dirty": False},
                "devices": {"phase_correlation": "cpu"},
                "checkpoints": {},
                "held_out_sites": list(held_out),
                "run": {**run, "methods": ["phase_correlation"]},
            },
        },
        {
            "path": "outputs/kaggle/outputs/n3-gpu",
            "devices": ["cuda"],
            "context": {
                **MACHINE,
                "gpu": {"name": "Tesla T4", "memory_gib": 15.0, "cuda": "12.4"},
                "recorded_at": "2026-10-12T09:00:00+00:00",
                "code": {"commit": "abcdef0123", "dirty": False},
                "devices": dict.fromkeys(BASE, "cuda"),
                "checkpoints": released(),
                "held_out_sites": list(held_out),
                "run": {**run, "methods": list(BASE), "device": "cuda"},
            },
        },
    ]
    merged = tmp_path / "n3"
    write_csv([*rows_of(classic, "cpu"), *rows_of(pairs, "cuda")], merged / "pairs.csv")
    (merged / "context.json").write_text(json.dumps({"merged": parts}))

    closed = tmp_path / "n3-cycle"
    triplets = triplets or closures(sites=sites)
    write_csv(
        [
            dataclasses.replace(
                triplet_row(method, key[0], int(key[3]), score.value, score.failed),
                scenario=key[1],
                triplet=key[2],
            )
            for method, of_method in triplets.items()
            for key, score in of_method.items()
        ],
        closed / "triplets.csv",
    )
    context = {
        **MACHINE,
        "recorded_at": "2026-10-12T10:00:00+00:00",
        "code": {"commit": "abcdef0123", "dirty": False},
        "devices": dict.fromkeys(BASE, "cpu"),
        "checkpoints": released(),
        "held_out_sites": list(held_out),
        "run": {
            "config": str(config),
            "sites": list(sites),
            "simulated_triplets": 1,
            "methods": list(BASE),
        },
    }
    (closed / "context.json").write_text(json.dumps(context))
    out = tmp_path / "n3-final"
    return [
        "final",
        *("--table", str(merged), "--closure", str(closed)),
        *("--resamples", "200", "--out", str(out)),
    ]


def rewrite(path, change):
    context = json.loads(path.read_text())
    change(context)
    path.write_text(json.dumps(context))


def test_final_writes_the_verdict_its_rows_and_what_they_were_read_from(
    tmp_path, capsys
):
    args = scored_final(tmp_path)
    out = tmp_path / "n3-final"

    main(args)

    printed = capsys.readouterr().out
    assert printed == (out / "summary.md").read_text()
    assert printed.startswith("The final evaluation of N3: fine-tuned RAFT next to")
    assert (
        "\n\n**Yes**: on the 32 simulated pairs of the held-out sites (alps" in printed
    )
    assert "scored on Apple M1, 8 GiB, 8 CPUs, macOS; GPU Tesla T4" in printed
    assert "(cuda), and the triplets on Apple M1, 8 GiB, 8 CPUs, macOS." in printed
    sha = published.lookup("raft_large_ft").sha256
    asset = published.lookup("raft_large_ft").asset
    assert f"raft_ft is `{asset}` of release `weights-n3`, SHA-256 `{sha}`" in printed
    assert printed.endswith(
        "Held-out sites in this table: alps, libya4. They are kept for the final "
        "evaluation: no threshold, preset or variant may be chosen on their rows.\n"
    )
    with (out / "criterion.csv").open(newline="") as f:
        criterion = list(csv.DictReader(f))
    assert len(criterion) == 2 * 5 * (1 + len(RUN_CELLS))
    assert criterion[0]["sites"] == HELD_OUT and criterion[0]["beats"] == "True"
    assert criterion[0]["pairs"] == "32" and criterion[0]["draws"] == "8"
    assert len((out / "closure.csv").read_text().splitlines()) == 2 * 6 + 1
    context = json.loads((out / "context.json").read_text())
    assert context["answer"] is True and context["rehearsal"] is False
    assert context["held_out_sites"] == list(TARGET)
    assert context["checkpoints"]["raft_ft"]["sha256"] == sha
    assert context["run"]["resamples"] == 200 and context["run"]["seed"] == 0
    assert list(context["read"]) == [
        "outputs/n3-m1",
        "outputs/kaggle/outputs/n3-gpu",
        str(tmp_path / "n3-cycle"),
    ]
    assert context["read"]["outputs/kaggle/outputs/n3-gpu"]["gpu"]["name"] == "Tesla T4"


def test_final_reads_the_criterion_where_the_run_was_told_the_sites_are_held_out(
    tmp_path,
):
    args = scored_final(tmp_path, held_out=())

    with pytest.raises(SystemExit, match="has no held-out site to read the criterion"):
        main(args)

    assert not (tmp_path / "n3-final").exists()


def test_final_rehearses_on_seen_sites_and_answers_nothing(tmp_path, capsys):
    seen = ("beauce", "toulouse")
    args = scored_final(tmp_path, held_out=(), sites=seen)
    # A rehearsal has fewer pairs than its configuration says.
    for part in (0, 1):
        rewrite(
            tmp_path / "n3" / "context.json",
            lambda context, part=part: context["merged"][part]["context"]["run"].update(
                repeats=1
            ),
        )

    main([*args, "--rehearsal", "toulouse"])

    printed = capsys.readouterr().out
    assert "\n\n**Rehearsal.** Seen sites stand in for the held-out ones" in printed
    assert "simulated pairs of the stand-in sites (toulouse)" in printed
    assert "Held-out sites in this table" not in printed
    context = json.loads((tmp_path / "n3-final" / "context.json").read_text())
    assert context["answer"] is None and context["rehearsal"] is True


def test_a_rehearsal_refuses_tables_that_have_held_out_rows(tmp_path):
    args = scored_final(tmp_path)

    with pytest.raises(
        SystemExit, match="a rehearsal reads no held-out site, .* of alps, libya4"
    ):
        main([*args, "--rehearsal", "beauce"])


def test_final_refuses_a_table_cut_short_of_its_configuration(tmp_path):
    args = scored_final(tmp_path)

    def fewer(context):
        context["merged"][1]["context"]["run"]["pairs"] = 2

    rewrite(tmp_path / "n3" / "context.json", fewer)

    with pytest.raises(SystemExit, match="n3-gpu was not run as .*n3.toml says: pairs"):
        main(args)


def test_final_refuses_a_table_that_lacks_pairs_its_run_was_to_score(tmp_path):
    short = table(sites=SITES, cells=RUN_CELLS, draws=DRAWS - 1)
    args = scored_final(tmp_path, pairs=short)

    with pytest.raises(SystemExit, match="has 24 pairs of alps, libya4 for raft_ft"):
        main(args)


@pytest.mark.parametrize("run", ["n3", "n3-cycle"])
def test_final_refuses_fine_tuned_weights_that_are_not_the_published_ones(
    tmp_path, run
):
    args = scored_final(tmp_path)

    def other(context):
        context = context["merged"][1]["context"] if run == "n3" else context
        context["checkpoints"]["raft_ft"]["sha256"] = "ab" * 32

    rewrite(tmp_path / run / "context.json", other)

    with pytest.raises(
        SystemExit, match="did not run raft_ft with the published weights raft_large_ft"
    ):
        main(args)


def test_final_reads_a_model_and_its_reference_from_one_run(tmp_path):
    args = scored_final(tmp_path)

    def split(context):
        del context["merged"][1]["context"]["devices"]["raft"]

    rewrite(tmp_path / "n3" / "context.json", split)

    with pytest.raises(SystemExit, match="does not have raft_ft, raft, .* one run"):
        main(args)


def test_final_refuses_a_table_that_was_not_merged_and_a_missing_run(tmp_path):
    args = scored_final(tmp_path)
    (tmp_path / "n3-cycle" / "triplets.csv").unlink()
    with pytest.raises(SystemExit, match="no triplets.csv and context.json in"):
        main(args)

    rewrite(tmp_path / "n3" / "context.json", lambda context: context.pop("merged"))
    with pytest.raises(SystemExit, match="is not a table satreg merge wrote"):
        main(args)

    (tmp_path / "n3" / "pairs.csv").unlink()
    with pytest.raises(SystemExit, match="no pairs.csv and context.json in"):
        main(args)


def test_final_refuses_a_closure_run_of_other_held_out_sites(tmp_path):
    args = scored_final(tmp_path)
    rewrite(
        tmp_path / "n3-cycle" / "context.json",
        lambda context: context.update(held_out_sites=["alps"]),
    )

    with pytest.raises(SystemExit, match="are not of the same held-out sites"):
        main(args)


def test_the_keys_of_a_draw_are_the_site_and_the_pair_number():
    assert PAIR_KEY == ("site", "bands", "scenario", "degradation", "pair")
    assert final.draw_of(("alps", "", "dense", "hard", "7")) == ("alps", "7")


# The recipes of the final evaluation and of its rehearsal.

ROOT = Path(__file__).parents[1]
# The sites configs/sites.toml keeps for the final evaluation.
KEPT = tuple(
    name
    for name, site in tomllib.loads((ROOT / "configs" / "sites.toml").read_text())[
        "sites"
    ].items()
    if site.get("held_out")
)


def variable(name):
    """The words of a Makefile variable written on one line."""
    recipe = (ROOT / "Makefile").read_text()
    return recipe.split(f"\n{name} = ")[1].splitlines()[0].split()


def commands(target):
    """The commands of a Makefile target, one string each."""
    recipe = (ROOT / "Makefile").read_text()
    body = recipe.split(f"\n{target}:")[1].split("\n\n")[0]
    return [line.strip() for line in body.splitlines()[1:]]


def configured(command):
    """The table of the config a command names, for the subcommand it runs."""
    words = command.split()
    path = ROOT / words[words.index("--config") + 1]
    return tomllib.loads(path.read_text())[words[1].replace("-", "_")]


def test_make_n3_allows_the_held_out_sites_where_a_config_names_them():
    targets = (ROOT / "Makefile").read_text().split("\nn3: ")[1].splitlines()[0].split()
    lines = [command for target in targets for command in commands(target)]

    assert sorted(KEPT) == ["alps", "libya4"]
    reading = [line for line in lines if "--config" in line]
    assert {line.split()[3] for line in reading} == {
        "configs/n3.toml",
        "configs/n3-bands.toml",
        "configs/n3-curve.toml",
    }
    for line in reading:
        held_out = set(configured(line)["sites"]) & set(KEPT)
        assert ("--allow-held-out" in line) == bool(held_out), line
    # Nothing is narrowed or moved: the configs describe the whole run.
    for line in reading:
        assert "--site " not in line and "--pairs" not in line, line
    assert "--rehearsal" not in " ".join(lines)
    assert targets.index("n3-merge") < targets.index("n3-final")
    assert targets.index("n3-cycle") < targets.index("n3-final")


def test_the_rehearsal_runs_every_config_of_n3_and_reads_no_held_out_site():
    lines = commands("n3-dry")
    recipe = " ".join(lines)
    seen, stand_in = variable("N3_SEEN"), variable("N3_STAND_IN")

    assert not set(seen) & set(KEPT)
    assert set(stand_in) <= set(seen)
    assert "--allow-held-out" not in recipe
    assert not any(site in recipe for site in KEPT)
    # A command whose config names a held-out site is given seen ones.
    reading = [line for line in lines if "--config" in line]
    for line in reading:
        if set(configured(line)["sites"]) & set(KEPT):
            assert "$(N3_DRY_SITES)" in line or "$(N3_DRY_CURVE_SITES)" in line, line
    assert variable("N3_DRY_SITES") == ["$(addprefix", "--site", ",$(N3_SEEN))"]
    assert variable("N3_DRY_CURVE_SITES") == [
        "$(addprefix",
        "--site",
        ",$(N3_STAND_IN))",
    ]
    assert {line.split()[3] for line in reading} == {
        f"configs/{path.name}" for path in (ROOT / "configs").glob("n3*.toml")
    }
    # Each command of the final evaluation is rehearsed, and writes apart.
    assert sorted({line.split()[1] for line in lines}) == sorted(
        {
            line.split()[1]
            for target in ("n3-m1", "n3-merge", "n3-cycle", "n3-final")
            + ("n3-bands", "n3-false-change", "n3-curve")
            for line in commands(target)
        }
    )
    for line in lines:
        assert "--out $(N3_DRY)/" in line, line
    assert "satreg final" in recipe and "--rehearsal $(N3_STAND_IN)" in recipe
    assert "satreg curve --benchmark --rehearsal" in recipe

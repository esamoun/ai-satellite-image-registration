import dataclasses
import json
import math
from pathlib import Path

import numpy as np
import pytest

from satreg import footprint
from satreg.cli import main, parse_args
from satreg.displacement import Translation
from satreg.footprint import CALLS, PROCESSES, Footprint
from satreg.georef import NOMINAL
from satreg.methods.base import GeoreferencedMethod
from satreg.report import write_csv

METHODS_CONFIG = Path(__file__).parents[1] / "configs" / "methods.toml"

SIZE = 64


def method_named(monkeypatch, method):
    """Make ``toy`` the one method of any methods' configuration."""
    monkeypatch.setattr(footprint, "load_methods", lambda path: {"toy": method})


def rising(monkeypatch, marks):
    """Make the process's high-water mark read these values, in turn."""
    left = iter(marks)
    monkeypatch.setattr(footprint, "process_peak_rss_mib", lambda: next(left))


def test_the_pair_is_of_the_side_asked_and_is_not_blank():
    reference, moving = footprint.pair(SIZE)

    assert reference.shape == moving.shape == (SIZE, SIZE)
    assert reference.std() > 0
    assert not np.array_equal(reference, moving)


def test_a_footprint_is_the_rise_of_the_mark_over_the_calls(monkeypatch):
    calls = []
    method_named(monkeypatch, lambda reference, moving: calls.append(reference.shape))
    # The baseline, then the mark after each of four calls.
    rising(monkeypatch, [100.0, 130.0, 142.5, 142.5, 142.5])

    read = footprint.measure("toy", METHODS_CONFIG, SIZE, 4)

    assert calls == [(SIZE, SIZE)] * 4
    assert dataclasses.replace(read, time_ms=0.0) == Footprint(
        method="toy",
        size=SIZE,
        calls=4,
        baseline_mib=100.0,
        first_mib=30.0,
        rise_mib=42.5,
        process_mib=142.5,
        # The second call was the last to raise the mark: it has settled.
        settled=2,
        time_ms=0.0,
        # One process: its rise is the lowest and the highest there is.
        processes=1,
        lowest_mib=42.5,
        highest_mib=42.5,
        error="",
    )
    assert read.time_ms >= 0


def test_a_mark_the_last_call_still_raised_has_not_settled(monkeypatch):
    method_named(monkeypatch, lambda reference, moving: None)
    rising(monkeypatch, [100.0, 110.0, 120.0])
    assert footprint.measure("toy", METHODS_CONFIG, SIZE, 2).settled == 2

    rising(monkeypatch, [100.0, 100.0, 100.0])
    assert footprint.measure("toy", METHODS_CONFIG, SIZE, 2).settled == 0


def test_a_single_call_has_no_time_and_none_is_refused(monkeypatch):
    method_named(monkeypatch, lambda reference, moving: None)

    # The first call loads the model: its time is not the method's.
    assert math.isnan(footprint.measure("toy", METHODS_CONFIG, SIZE, 1).time_ms)
    with pytest.raises(ValueError, match="calls must be at least 1, got 0"):
        footprint.measure("toy", METHODS_CONFIG, SIZE, 0)
    with pytest.raises(ValueError, match="calls must be at least 1, got 0"):
        footprint.footprints(["toy"], METHODS_CONFIG, SIZE, 0)
    with pytest.raises(ValueError, match="processes must be at least 1, got 0"):
        footprint.footprints(["toy"], METHODS_CONFIG, SIZE, 1, processes=0)


def test_a_method_that_raises_is_still_read_and_says_so(monkeypatch):
    def broken(reference, moving):
        raise RuntimeError("no estimate")

    method_named(monkeypatch, broken)

    read = footprint.measure("toy", METHODS_CONFIG, SIZE, 2)

    assert read.error == "call 1: RuntimeError: no estimate"
    assert read.calls == 2
    assert read.rise_mib >= 0


def test_a_method_that_raises_after_its_first_call_says_so_too(monkeypatch):
    calls = []

    def tiring(reference, moving):
        calls.append(len(calls) + 1)
        if len(calls) >= 3:
            raise ValueError(f"gave up on call {len(calls)}")

    method_named(monkeypatch, tiring)

    read = footprint.measure("toy", METHODS_CONFIG, SIZE, 4)

    # The first call that raised is the one named, and the others are still made.
    assert read.error == "call 3: ValueError: gave up on call 3"
    assert calls == [1, 2, 3, 4]


def test_the_runtime_of_a_method_is_imported_before_the_baseline(monkeypatch):
    order = []

    class Toy:
        runtime = ("a_runtime", "its_other_half")

        def __call__(self, reference, moving):
            order.append("call")

    def mark():
        order.append("mark")
        return 100.0

    method_named(monkeypatch, Toy())
    monkeypatch.setattr(footprint.importlib, "import_module", order.append)
    monkeypatch.setattr(footprint, "process_peak_rss_mib", mark)

    footprint.measure("toy", METHODS_CONFIG, SIZE, 1)

    assert order == ["a_runtime", "its_other_half", "mark", "call", "mark"]


def test_a_method_that_needs_the_map_grid_is_given_a_nominal_one(monkeypatch):
    given = []

    class Toy(GeoreferencedMethod):
        def __call__(self, reference, moving, georef):
            given.append(georef)
            return Translation(0.0, 0.0)

    method_named(monkeypatch, Toy())

    assert footprint.measure("toy", METHODS_CONFIG, SIZE, 1).error == ""
    assert given == [NOMINAL]


def test_a_platform_without_a_high_water_mark_is_refused(monkeypatch):
    method_named(monkeypatch, lambda reference, moving: None)
    monkeypatch.setattr(footprint, "process_peak_rss_mib", lambda: None)

    with pytest.raises(ValueError, match="no resident high-water mark to read"):
        footprint.measure("toy", METHODS_CONFIG, SIZE, 1)


def reading(rise, method="toy"):
    return Footprint(
        method, SIZE, 2, 100.0, rise, rise, 100.0 + rise, 1, 5.0, 1, rise, rise, ""
    )


def test_the_reading_kept_is_the_median_one_with_the_range_beside_it():
    low, middle, high = reading(40.0), reading(42.0), reading(55.0)

    assert footprint.kept([high, low, middle]) == dataclasses.replace(
        middle, processes=3, lowest_mib=40.0, highest_mib=55.0
    )
    # An even number has two middle readings: the lower one is kept.
    assert footprint.kept([high, low]) == dataclasses.replace(
        low, processes=2, lowest_mib=40.0, highest_mib=55.0
    )
    assert footprint.kept([middle]) == middle


class Recorded:
    """Stands in for the pool of one new process: reads what it is told to."""

    rises = iter(())
    started = []

    def __init__(self, max_workers, mp_context):
        self.started.append((max_workers, mp_context.get_start_method()))

    def __enter__(self):
        return self

    def __exit__(self, *raised):
        return False

    def submit(self, measure, name, methods_config, size, calls):
        assert (measure, size, calls) == (footprint.measure, SIZE, 2)
        return Done(reading(next(self.rises), name))


@dataclasses.dataclass
class Done:
    read: Footprint

    def result(self):
        return self.read


def test_every_method_is_read_once_before_any_is_read_again(monkeypatch):
    monkeypatch.setattr(footprint, "ProcessPoolExecutor", Recorded)
    # In the order read: a, b, then a, b, then a, b.
    monkeypatch.setattr(Recorded, "rises", iter([30.0, 5.0, 10.0, 7.0, 20.0, 6.0]))
    monkeypatch.setattr(Recorded, "started", [])

    rows = footprint.footprints(["a", "b"], METHODS_CONFIG, SIZE, 2, processes=3)

    # Six processes, one worker each, started and never forked.
    assert Recorded.started == [(1, "spawn")] * 6
    assert [
        (row.method, row.rise_mib, row.lowest_mib, row.highest_mib, row.processes)
        for row in rows
    ] == [("a", 20.0, 10.0, 30.0, 3), ("b", 6.0, 5.0, 7.0, 3)]


def test_each_method_is_read_in_processes_of_its_own():
    names = ["sift_ransac", "phase_correlation"]

    rows = footprint.footprints(names, METHODS_CONFIG, SIZE, calls=2, processes=2)

    assert [row.method for row in rows] == names
    for row in rows:
        assert (row.size, row.calls, row.processes, row.error) == (SIZE, 2, 2, "")
        assert row.baseline_mib > 0
        assert 0 <= row.first_mib <= row.rise_mib
        assert row.process_mib == pytest.approx(row.baseline_mib + row.rise_mib)
        assert row.lowest_mib <= row.rise_mib <= row.highest_mib
        assert row.settled in (0, 1, 2)
        assert row.time_ms > 0


ROWS = [
    Footprint(
        "raft_onnx", 256, 10, 170.25, 60.0, 89.5, 259.75, 6, 681.4, 3, 84.0, 97.25, ""
    ),
    Footprint(
        "arosics",
        256,
        10,
        250.0,
        2.0,
        2.0,
        252.0,
        10,
        3.2,
        1,
        2.0,
        2.0,
        "call 1: ValueError: no",
    ),
]


def test_footprints_are_read_back_from_the_table_the_command_writes(tmp_path):
    write_csv(ROWS, tmp_path / "footprints.csv")

    assert footprint.read(tmp_path / "footprints.csv") == {
        "raft_onnx": ROWS[0],
        "arosics": ROWS[1],
    }


def test_the_table_gives_each_method_a_line_and_names_what_raised():
    assert footprint.to_markdown(ROWS).splitlines()[2:] == [
        "| raft_onnx | 89.5 | 84.0 to 97.2 | 60.0 | 259.8 | 170.2 | 6 of 10 | 681 |",
        "| arosics | 2.0 | 2.0 to 2.0 | 2.0 | 252.0 | 250.0 | 10 of 10 | 3 |",
        "",
        "arosics raised on call 1: ValueError: no",
    ]


def footprint_args(tmp_path, *options):
    return [
        "footprint",
        "--methods-config",
        str(METHODS_CONFIG),
        "--out",
        str(tmp_path / "footprint"),
        *options,
    ]


def test_footprint_writes_the_table_its_rows_and_the_context(tmp_path, capsys):
    out = tmp_path / "footprint"
    options = ["--methods", "phase_correlation", "--size", str(SIZE), "--calls", "2"]
    options += ["--processes", "2"]

    main(footprint_args(tmp_path, *options))

    assert {p.name for p in out.iterdir()} == {
        "footprints.csv",
        "summary.md",
        "context.json",
    }
    printed = capsys.readouterr().out
    assert printed == (out / "summary.md").read_text()
    assert f"2 times on one {SIZE} px pair" in printed
    assert "Each method is read in 2 new processes" in printed
    (read,) = footprint.read(out / "footprints.csv").values()
    assert (read.method, read.calls, read.processes) == ("phase_correlation", 2, 2)
    assert read.error == ""
    context = json.loads((out / "context.json").read_text())
    assert context["devices"] == {"phase_correlation": "cpu"}
    assert context["run"]["size"] == SIZE


def test_footprint_refuses_what_it_cannot_read(tmp_path):
    with pytest.raises(SystemExit, match="satreg: unknown method 'nothing'"):
        main(footprint_args(tmp_path, "--methods", "nothing"))
    with pytest.raises(SystemExit, match="satreg: calls must be at least 1, got 0"):
        main(footprint_args(tmp_path, "--methods", "phase_correlation", "--calls", "0"))
    with pytest.raises(SystemExit, match="satreg: processes must be at least 1"):
        main(
            footprint_args(
                tmp_path, "--methods", "phase_correlation", "--processes", "0"
            )
        )

    assert not (tmp_path / "footprint").exists()


def test_the_footprint_is_read_over_ten_calls_in_three_processes_at_256_px():
    args = parse_args(["footprint", "--methods", "raft"])

    assert (args.calls, args.processes, args.size) == (CALLS, PROCESSES, 256)
    assert (CALLS, PROCESSES) == (10, 3)

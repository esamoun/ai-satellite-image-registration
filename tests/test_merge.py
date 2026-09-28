import csv
import json

import pytest
from test_cli import PRESETS

from satreg.cli import main
from satreg.merge import MergeError, merge, read_run

GPU = {
    "name": "Tesla T4",
    "memory_gib": 14.7,
    "count": 2,
    "capability": "7.5",
    "cuda": "12.4",
    "cudnn": 90100,
}


def benchmark_run(directory, *options):
    """Run a small benchmark of phase correlation into a directory."""
    main(
        ["benchmark", "--pairs", "2", "--size", "64", "--degradations", "clean"]
        + ["--methods", "phase_correlation", "--out", str(directory)]
        + list(options)
        + PRESETS
    )
    return directory


def rewrite_csv(path, change):
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    rows = [change(dict(row)) for row in rows]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def as_if_on(directory, device, gpu=None, meter="cuda"):
    """Make a run look as if it had been measured on another device."""

    def on_device(row):
        row["device"] = device
        return row

    for name in ("summary.csv", "pairs.csv"):
        rewrite_csv(directory / name, on_device)
    context = json.loads((directory / "context.json").read_text())
    context["devices"] = {method: device for method in context["devices"]}
    context["cost"]["memory"] = {method: meter for method in context["devices"]}
    context["gpu"] = gpu
    (directory / "context.json").write_text(json.dumps(context))
    return directory


@pytest.fixture
def two_devices(tmp_path):
    cpu = benchmark_run(tmp_path / "m1")
    cuda = as_if_on(benchmark_run(tmp_path / "kaggle"), "cuda", GPU)
    return cpu, cuda


def test_merged_table_has_a_row_per_device_side_by_side(two_devices, tmp_path):
    table = merge(two_devices, tmp_path / "merged")

    lines = [line for line in table.splitlines() if "| phase_correlation |" in line]
    scenarios = [line.split(" | ")[1] for line in lines]
    assert scenarios == ["translation"] * 2 + ["affine"] * 2 + ["dense"] * 2
    assert [line.split(" | ")[4] for line in lines] == ["cpu", "cuda"] * 3
    assert "| device |" in table
    assert (tmp_path / "merged" / "summary.md").read_text() == table


def test_merged_footnote_names_the_machine_and_commit_of_each_device(
    two_devices, tmp_path
):
    table = merge(two_devices, tmp_path / "merged")

    footnote = table.split("Measured by device: ")[1]
    cpu, cuda = footnote.split("; cuda rows on ")
    assert cpu.startswith("cpu rows on ")
    assert "GPU Tesla T4, 15 GiB, CUDA 12.4" in cuda
    commit = json.loads((two_devices[0] / "context.json").read_text())["code"]
    assert f"commit {commit['commit'][:7]}" in cpu
    assert "tracemalloc, which misses native allocations for " in footnote
    assert "phase_correlation on cpu; the peak held by CUDA tensors" in footnote
    assert footnote.endswith(
        "tensors for phase_correlation on cuda. Details in `context.json`.\n"
    )


def test_merged_footnote_names_the_held_out_sites(two_devices, tmp_path):
    for run in two_devices:
        context = json.loads((run / "context.json").read_text())
        context["held_out_sites"] = ["alps"]
        (run / "context.json").write_text(json.dumps(context))

    table = merge(two_devices, tmp_path / "merged")

    assert table.endswith(
        "Held-out sites in this table: alps. They are kept for the final "
        "evaluation: no threshold, preset or variant may be chosen on their rows.\n"
    )


def test_merged_files_keep_every_row_and_each_run_context(two_devices, tmp_path):
    merge(two_devices, tmp_path / "merged")

    with (tmp_path / "merged" / "pairs.csv").open(newline="") as f:
        pairs = list(csv.DictReader(f))
    assert [row["device"] for row in pairs] == ["cpu"] * 6 + ["cuda"] * 6
    merged = read_run(tmp_path / "merged")
    assert [row.device for row in merged.summary] == ["cpu", "cuda"] * 3
    context = json.loads((tmp_path / "merged" / "context.json").read_text())
    assert [run["devices"] for run in context["merged"]] == [["cpu"], ["cuda"]]
    assert context["merged"][1]["context"]["gpu"] == GPU


def test_a_device_measured_by_two_runs_is_refused(tmp_path):
    first = benchmark_run(tmp_path / "a")
    second = benchmark_run(tmp_path / "b")

    with pytest.raises(MergeError, match="both measured cpu"):
        merge([first, second], tmp_path / "merged")


def test_runs_on_other_pairs_are_refused(tmp_path):
    cpu = benchmark_run(tmp_path / "m1")
    cuda = as_if_on(benchmark_run(tmp_path / "kaggle", "--seed", "1"), "cuda")

    with pytest.raises(MergeError, match="differ on seed: 0 against 1"):
        merge([cpu, cuda], tmp_path / "merged")


def test_a_single_run_is_refused(tmp_path):
    with pytest.raises(MergeError, match="at least two runs"):
        merge([benchmark_run(tmp_path / "m1")], tmp_path / "merged")


def test_a_directory_that_is_no_run_is_refused(tmp_path):
    with pytest.raises(MergeError, match="not a benchmark run"):
        merge([benchmark_run(tmp_path / "m1"), tmp_path], tmp_path / "merged")


def test_rows_written_before_the_device_column_run_where_the_context_says(
    two_devices, tmp_path
):
    cpu, cuda = two_devices

    def without_device(row):
        del row["device"]
        return row

    for directory in (cpu, cuda):
        for name in ("summary.csv", "pairs.csv"):
            rewrite_csv(directory / name, without_device)
    context = json.loads((cpu / "context.json").read_text())
    del context["devices"]
    (cpu / "context.json").write_text(json.dumps(context))

    merge([cpu, cuda], tmp_path / "merged")

    merged = read_run(tmp_path / "merged")
    assert [row.device for row in merged.summary] == ["cpu", "cuda"] * 3


def test_merge_command_prints_the_table(two_devices, tmp_path, capsys):
    out = tmp_path / "merged"
    main(["merge", *map(str, two_devices), "--out", str(out)])

    assert capsys.readouterr().out == (out / "summary.md").read_text()


def test_merge_command_reports_runs_it_cannot_merge(tmp_path):
    run = benchmark_run(tmp_path / "m1")

    with pytest.raises(SystemExit, match="satreg: .* both measured cpu"):
        main(["merge", str(run), str(run), "--out", str(tmp_path / "merged")])


def test_rows_written_before_the_bands_column_are_single_band(two_devices, tmp_path):
    cpu, cuda = two_devices

    def without_bands(row):
        del row["bands"]
        return row

    for name in ("summary.csv", "pairs.csv"):
        rewrite_csv(cpu / name, without_bands)
    context = json.loads((cpu / "context.json").read_text())
    del context["run"]["band_pairs"]
    (cpu / "context.json").write_text(json.dumps(context))

    merge([cpu, cuda], tmp_path / "merged")

    merged = read_run(tmp_path / "merged")
    assert {row.bands for row in merged.summary} == {""}
    assert "| bands |" not in (tmp_path / "merged" / "summary.md").read_text()


def test_runs_on_other_band_pairs_are_refused(two_devices):
    cpu, cuda = two_devices
    context = json.loads((cuda / "context.json").read_text())
    context["run"]["band_pairs"] = [["B04", "B08"]]
    (cuda / "context.json").write_text(json.dumps(context))

    with pytest.raises(MergeError, match="band_pairs"):
        merge([cpu, cuda], cpu.parent / "merged")

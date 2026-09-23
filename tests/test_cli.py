import subprocess
import sys

from satreg.cli import main


def test_benchmark_writes_its_tables_and_prints_the_summary(tmp_path, capsys):
    main(["benchmark", "--pairs", "3", "--size", "64", "--out", str(tmp_path)])

    printed = capsys.readouterr().out
    assert "| synthetic | clean | phase_correlation | 3 |" in printed
    assert (tmp_path / "summary.md").read_text() == printed
    assert (tmp_path / "pairs.csv").exists()
    assert (tmp_path / "summary.csv").exists()


def test_module_is_runnable():
    result = subprocess.run(
        [sys.executable, "-m", "satreg", "--help"], capture_output=True, text=True
    )

    assert result.returncode == 0
    assert "benchmark" in result.stdout

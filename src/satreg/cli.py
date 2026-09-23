"""Command-line entry point: ``satreg benchmark``."""

import argparse
import logging
from collections.abc import Sequence
from pathlib import Path

from .benchmark import BenchmarkConfig, run_benchmark
from .methods import METHODS
from .metrics import FAILURE_EPE_PX
from .report import summarize, to_markdown, write_csv
from .texture import fractal_texture

# Side of the synthetic site image. Large enough to cut varied windows from it.
SYNTHETIC_SITE_PX = 1024


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="satreg", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    bench = commands.add_parser(
        "benchmark", help="score methods on simulated pairs and write the table"
    )
    defaults = BenchmarkConfig()
    bench.add_argument("--pairs", type=int, default=defaults.n_pairs)
    bench.add_argument("--size", type=int, default=defaults.size)
    bench.add_argument("--max-shift", type=float, default=defaults.max_shift)
    bench.add_argument("--seed", type=int, default=defaults.seed)
    bench.add_argument(
        "--failure-threshold",
        type=float,
        default=FAILURE_EPE_PX,
        help="mean end-point error above which a pair failed, in px",
    )
    bench.add_argument(
        "--methods",
        nargs="+",
        choices=sorted(METHODS),
        default=sorted(METHODS),
    )
    bench.add_argument("--out", type=Path, default=Path("outputs/benchmark"))
    return parser


def benchmark(args: argparse.Namespace) -> str:
    """Run the benchmark on the synthetic site and write its tables.

    Args:
        args: Parsed ``benchmark`` arguments.

    Returns:
        The results table as markdown.
    """
    config = BenchmarkConfig(
        n_pairs=args.pairs,
        size=args.size,
        max_shift=args.max_shift,
        seed=args.seed,
        failure_threshold=args.failure_threshold,
    )
    sites = {"synthetic": fractal_texture(SYNTHETIC_SITE_PX, seed=args.seed)}
    methods = {name: METHODS[name] for name in args.methods}

    results = run_benchmark(sites, methods, config)
    summary = summarize(results)
    table = to_markdown(summary)

    write_csv(results, args.out / "pairs.csv")
    write_csv(summary, args.out / "summary.csv")
    (args.out / "summary.md").write_text(table)
    return table


def main(argv: Sequence[str] | None = None) -> None:
    """Parse arguments and run the requested command."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = _parser().parse_args(argv)
    if args.command == "benchmark":
        print(benchmark(args), end="")

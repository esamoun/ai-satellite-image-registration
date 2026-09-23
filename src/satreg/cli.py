"""Command-line entry point: ``satreg fetch`` and ``satreg benchmark``."""

import argparse
import logging
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from .benchmark import SCENARIOS, BenchmarkConfig, run_benchmark
from .degrade import Preset, load_presets
from .ingest import fetch_chip, read_chip
from .methods import METHODS
from .metrics import FAILURE_EPE_PX
from .report import summarize, to_markdown, write_csv
from .sites import SitesConfig, load_sites
from .texture import fractal_texture

# Built-in site that needs no configuration and no network.
SYNTHETIC_SITE = "synthetic"

# Side of the synthetic site image. Large enough to cut varied windows from it.
SYNTHETIC_SITE_PX = 1024

DEFAULT_SITES_CONFIG = Path("configs/sites.toml")
DEFAULT_DEGRADATIONS_CONFIG = Path("configs/degradations.toml")
DEFAULT_DATA_DIR = Path("data")


def _add_data_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--sites-config",
        type=Path,
        default=DEFAULT_SITES_CONFIG,
        help="TOML file declaring the sites and the STAC catalogue",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="where downloaded chips are cached",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="satreg", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    fetch = commands.add_parser(
        "fetch", help="download and cache the Sentinel-2 chip of each site"
    )
    fetch.add_argument(
        "--site",
        action="append",
        dest="sites",
        metavar="NAME",
        help="site to fetch, repeatable (default: every configured site)",
    )
    _add_data_arguments(fetch)

    bench = commands.add_parser(
        "benchmark", help="score methods on simulated pairs and write the table"
    )
    defaults = BenchmarkConfig()
    bench.add_argument(
        "--site",
        action="append",
        dest="sites",
        metavar="NAME",
        help=f"site to cut pairs from, repeatable (default: {SYNTHETIC_SITE}, "
        "which is generated offline)",
    )
    _add_data_arguments(bench)
    bench.add_argument(
        "--degradations",
        nargs="+",
        metavar="PRESET",
        help="degradation presets to run (default: every configured preset)",
    )
    bench.add_argument(
        "--degradations-config",
        type=Path,
        default=DEFAULT_DEGRADATIONS_CONFIG,
        help="TOML file declaring the degradation presets",
    )
    bench.add_argument("--pairs", type=int, default=defaults.n_pairs)
    bench.add_argument("--size", type=int, default=defaults.size)
    bench.add_argument(
        "--scenarios",
        nargs="+",
        choices=SCENARIOS,
        default=list(defaults.scenarios),
        help="geometric models to simulate (default: all)",
    )
    bench.add_argument(
        "--max-shift",
        type=float,
        default=defaults.max_shift,
        help="largest shift of the pair centre, per component, in px",
    )
    bench.add_argument(
        "--max-rotation",
        type=float,
        default=defaults.max_rotation_deg,
        help="largest affine rotation, in degrees",
    )
    bench.add_argument(
        "--max-scale-change",
        type=float,
        default=defaults.max_scale_change,
        help="largest affine scale change, as a fraction (0.002 is 0.2 %%)",
    )
    bench.add_argument(
        "--max-shear",
        type=float,
        default=defaults.max_shear,
        help="largest affine shear, in px per px",
    )
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


def _configured_site(config: SitesConfig, name: str) -> None:
    if name not in config.sites:
        known = ", ".join(sorted(config.sites))
        raise SystemExit(f"satreg: unknown site {name!r} (configured: {known})")


def fetch(args: argparse.Namespace) -> list[Path]:
    """Fetch the chips of the requested sites into the cache.

    Args:
        args: Parsed ``fetch`` arguments.

    Returns:
        Path of each site's chip.
    """
    config = load_sites(args.sites_config)
    names = args.sites or list(config.sites)
    for name in names:
        _configured_site(config, name)
    return [
        fetch_chip(config.sites[name], config.catalogue, args.data_dir)
        for name in names
    ]


def site_images(args: argparse.Namespace) -> dict[str, np.ndarray]:
    """Load the image of every site the benchmark runs on.

    Configured sites come from the chip cache, fetched first if not cached. The
    configuration file is only read when a configured site is requested, so the
    synthetic site runs anywhere.

    Args:
        args: Parsed ``benchmark`` arguments.

    Returns:
        Site name to 2-D image.
    """
    images = {}
    config = None
    for name in args.sites or [SYNTHETIC_SITE]:
        if name == SYNTHETIC_SITE:
            images[name] = fractal_texture(SYNTHETIC_SITE_PX, seed=args.seed)
            continue
        config = config or load_sites(args.sites_config)
        _configured_site(config, name)
        chip = fetch_chip(config.sites[name], config.catalogue, args.data_dir)
        images[name] = read_chip(chip)
    return images


def degradation_presets(args: argparse.Namespace) -> dict[str, Preset]:
    """Load the degradation presets the benchmark runs over.

    Args:
        args: Parsed ``benchmark`` arguments.

    Returns:
        Preset name to preset, in the order requested, or in file order when no
        preset is named.
    """
    try:
        presets = load_presets(args.degradations_config)
    except FileNotFoundError:
        raise SystemExit(
            f"satreg: no degradation presets at {args.degradations_config} "
            "(run from the repository root or pass --degradations-config)"
        ) from None
    names = args.degradations or list(presets)
    unknown = [name for name in names if name not in presets]
    if unknown:
        known = ", ".join(presets)
        raise SystemExit(
            f"satreg: unknown degradation preset {unknown[0]!r} (configured: {known})"
        )
    return {name: presets[name] for name in names}


def benchmark(args: argparse.Namespace) -> str:
    """Run the benchmark on the requested sites and write its tables.

    Args:
        args: Parsed ``benchmark`` arguments.

    Returns:
        The results table as markdown.
    """
    config = BenchmarkConfig(
        n_pairs=args.pairs,
        size=args.size,
        max_shift=args.max_shift,
        max_rotation_deg=args.max_rotation,
        max_scale_change=args.max_scale_change,
        max_shear=args.max_shear,
        scenarios=tuple(dict.fromkeys(args.scenarios)),
        seed=args.seed,
        failure_threshold=args.failure_threshold,
    )
    degradations = degradation_presets(args)
    sites = site_images(args)
    methods = {name: METHODS[name] for name in args.methods}

    results = run_benchmark(sites, methods, config, degradations)
    summary = summarize(results)
    table = to_markdown(summary)

    write_csv(results, args.out / "pairs.csv")
    write_csv(summary, args.out / "summary.csv")
    (args.out / "summary.md").write_text(table)
    return table


def main(argv: Sequence[str] | None = None) -> None:
    """Parse arguments and run the requested command."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    # rasterio logs its session setup at INFO, which is noise here.
    logging.getLogger("rasterio").setLevel(logging.WARNING)
    args = _parser().parse_args(argv)
    if args.command == "fetch":
        for path in fetch(args):
            print(path)
    elif args.command == "benchmark":
        print(benchmark(args), end="")

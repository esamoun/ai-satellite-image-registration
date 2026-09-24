"""Command-line entry point: ``satreg fetch`` and ``satreg benchmark``."""

import argparse
import json
import logging
import tomllib
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from .benchmark import SCENARIOS, BenchmarkConfig, run_benchmark
from .compute import MEMORY_READINGS, describe, environment, process_peak_rss_mib
from .degrade import Preset, load_presets
from .georef import NOMINAL, Georef
from .ingest import fetch_chip, read_chip, read_georef
from .methods import (
    METHODS,
    Method,
    cost_meter,
    load_methods,
    missing_dependencies,
)
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
DEFAULT_METHODS_CONFIG = Path("configs/methods.toml")
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


def _parser(run_config: dict[str, object] | None = None) -> argparse.ArgumentParser:
    """Build the argument parser.

    Args:
        run_config: Defaults for ``benchmark`` options, by destination name, as
            read by ``load_run_config``. Options given on the command line still
            win.

    Returns:
        The parser.
    """
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
        "--config",
        type=Path,
        help="TOML file whose [benchmark] table sets any of the options below, "
        "by their name with underscores; options given here override it",
    )
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
    bench.add_argument(
        "--max-local-shift",
        type=float,
        default=defaults.max_local_shift,
        help="largest magnitude of the local field of a dense pair, in px: "
        "orthorectification residuals such as relief seen through an elevation "
        "model error",
    )
    bench.add_argument(
        "--local-length",
        type=float,
        default=defaults.local_length,
        help="correlation length of the local field of a dense pair, in px",
    )
    bench.add_argument("--seed", type=int, default=defaults.seed)
    bench.add_argument(
        "--failure-threshold",
        type=float,
        default=FAILURE_EPE_PX,
        help="mean end-point error above which a pair failed, in px",
    )
    bench.add_argument(
        "--warmup",
        type=int,
        default=defaults.warmup,
        help="untimed calls of each method before timing it",
    )
    bench.add_argument(
        "--repeats",
        type=int,
        default=defaults.repeats,
        help="timed calls of a method on each pair, whose median is reported",
    )
    bench.add_argument(
        "--methods",
        nargs="+",
        metavar="METHOD",
        default=[
            name for name in sorted(METHODS) if not missing_dependencies(METHODS[name])
        ],
        help=f"methods to run, among {', '.join(sorted(METHODS))} and the variants "
        "declared in the methods config (default: every built-in method whose "
        "dependencies are installed)",
    )
    bench.add_argument(
        "--methods-config",
        type=Path,
        default=DEFAULT_METHODS_CONFIG,
        help="TOML file setting the methods' parameters",
    )
    bench.add_argument("--out", type=Path, default=Path("outputs/benchmark"))
    if run_config:
        bench.set_defaults(**run_config)
    return parser


def load_run_config(path: Path) -> dict[str, object]:
    """Read the ``[benchmark]`` table of a run configuration file.

    Args:
        path: TOML file with a ``[benchmark]`` table. Its keys are ``benchmark``
            options by destination name (``max_shift`` for ``--max-shift``).
            Paths are read relative to the working directory, like the
            command-line options.

    Returns:
        Option destination to value.

    Raises:
        SystemExit: If the file is missing, has no ``[benchmark]`` table, or sets
            an option that does not exist.
    """
    try:
        with path.open("rb") as f:
            raw = tomllib.load(f)
    except FileNotFoundError:
        raise SystemExit(f"satreg: no run configuration at {path}") from None
    if "benchmark" not in raw:
        raise SystemExit(f"satreg: {path} needs a [benchmark] table")
    options = set(vars(_parser().parse_args(["benchmark"]))) - {"command", "config"}
    unknown = sorted(set(raw["benchmark"]) - options)
    if unknown:
        raise SystemExit(
            f"satreg: {path}: unknown benchmark option {unknown[0]!r} "
            f"(options: {', '.join(sorted(options))})"
        )
    return raw["benchmark"]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the command line, with defaults from ``--config`` if it is given.

    Args:
        argv: Arguments, without the program name; ``sys.argv`` if ``None``.

    Returns:
        The parsed arguments.
    """
    args = _parser().parse_args(argv)
    if getattr(args, "config", None) is None:
        return args
    return _parser(load_run_config(args.config)).parse_args(argv)


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


def site_images(
    args: argparse.Namespace,
) -> tuple[dict[str, np.ndarray], dict[str, Georef]]:
    """Load the image and map grid of every site the benchmark runs on.

    Configured sites come from the chip cache, fetched first if not cached, on
    the chip's own grid. The synthetic site gets a nominal grid. The
    configuration file is only read when a configured site is requested, so the
    synthetic site runs anywhere.

    Args:
        args: Parsed ``benchmark`` arguments.

    Returns:
        Site name to 2-D image, and site name to its map grid.
    """
    images, georefs = {}, {}
    config = None
    for name in args.sites or [SYNTHETIC_SITE]:
        if name == SYNTHETIC_SITE:
            images[name] = fractal_texture(SYNTHETIC_SITE_PX, seed=args.seed)
            georefs[name] = NOMINAL
            continue
        config = config or load_sites(args.sites_config)
        _configured_site(config, name)
        chip = fetch_chip(config.sites[name], config.catalogue, args.data_dir)
        images[name] = read_chip(chip)
        georefs[name] = read_georef(chip)
    return images, georefs


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


def configured_methods(args: argparse.Namespace) -> dict[str, Method]:
    """Build the methods the benchmark runs, with their configured parameters.

    Args:
        args: Parsed ``benchmark`` arguments.

    Returns:
        Method name to method, in the order requested.
    """
    try:
        methods = load_methods(args.methods_config)
    except FileNotFoundError:
        raise SystemExit(
            f"satreg: no method parameters at {args.methods_config} "
            "(run from the repository root or pass --methods-config)"
        ) from None
    for name in args.methods:
        if name not in methods:
            raise SystemExit(
                f"satreg: unknown method {name!r} (known: {', '.join(methods)})"
            )
        if missing := missing_dependencies(methods[name]):
            raise SystemExit(
                f"satreg: method {name} needs {', '.join(missing)}, not installed "
                "(see the README)"
            )
    return {name: methods[name] for name in args.methods}


def memory_note(meters: dict[str, str]) -> str:
    """Say how the memory column was read, naming methods read another way.

    Args:
        meters: Meter name of each method, in table order.

    Returns:
        A clause for the table's footnote, e.g. ``"memory is the peak traced by
        tracemalloc, which misses native allocations"``.
    """
    by_meter: dict[str, list[str]] = {}
    for method, meter in meters.items():
        by_meter.setdefault(meter, []).append(method)
    if len(by_meter) == 1:
        return f"memory is {MEMORY_READINGS[next(iter(by_meter))]}"
    return "memory is " + "; ".join(
        f"{MEMORY_READINGS[meter]} for {', '.join(methods)}"
        for meter, methods in by_meter.items()
    )


def benchmark(args: argparse.Namespace) -> str:
    """Run the benchmark on the requested sites and write its tables.

    Args:
        args: Parsed ``benchmark`` arguments.

    Returns:
        The results table as markdown, followed by the machine it was measured on.
    """
    config = BenchmarkConfig(
        n_pairs=args.pairs,
        size=args.size,
        max_shift=args.max_shift,
        max_rotation_deg=args.max_rotation,
        max_scale_change=args.max_scale_change,
        max_shear=args.max_shear,
        max_local_shift=args.max_local_shift,
        local_length=args.local_length,
        scenarios=tuple(dict.fromkeys(args.scenarios)),
        seed=args.seed,
        failure_threshold=args.failure_threshold,
        warmup=args.warmup,
        repeats=args.repeats,
    )
    degradations = degradation_presets(args)
    sites, georefs = site_images(args)
    methods = configured_methods(args)

    results = run_benchmark(sites, methods, config, degradations, georefs)
    summary = summarize(results)
    context = environment()
    meters = {name: cost_meter(method).name for name, method in methods.items()}
    context["cost"] = {
        "warmup": config.warmup,
        "repeats": config.repeats,
        "process_peak_rss_mib": process_peak_rss_mib(),
        "memory": meters,
    }
    # Where each method ran: the deep-learning ones name their device, the
    # others run on the CPU.
    context["devices"] = {
        name: getattr(method, "device", "cpu") for name, method in methods.items()
    }
    # Every option the run used, whether from the command line, a run config or
    # a default, so the tables can be reproduced from this file alone.
    context["run"] = {k: v for k, v in sorted(vars(args).items()) if k != "command"}
    table = to_markdown(summary) + (
        f"\nMeasured on {describe(context)}. Time is the median of {config.repeats} "
        f"calls per pair, after {config.warmup} warm-up call(s) per method; "
        f"{memory_note(meters)}. Details in `context.json`.\n"
    )

    write_csv(results, args.out / "pairs.csv")
    write_csv(summary, args.out / "summary.csv")
    (args.out / "summary.md").write_text(table)
    # Paths in the run options are written as text.
    context_json = json.dumps(context, indent=2, default=str)
    (args.out / "context.json").write_text(context_json + "\n")
    return table


def main(argv: Sequence[str] | None = None) -> None:
    """Parse arguments and run the requested command."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    # rasterio logs its session setup at INFO, which is noise here.
    logging.getLogger("rasterio").setLevel(logging.WARNING)
    args = parse_args(argv)
    if args.command == "fetch":
        for path in fetch(args):
            print(path)
    elif args.command == "benchmark":
        print(benchmark(args), end="")

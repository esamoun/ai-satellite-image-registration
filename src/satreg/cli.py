"""Command-line entry point: ``satreg fetch``, ``satreg benchmark``, ``satreg
merge``, ``satreg real-pairs`` and ``satreg check-presets``."""

import argparse
import dataclasses
import json
import logging
import tomllib
from collections.abc import Sequence
from pathlib import Path
from time import perf_counter

import numpy as np

from .benchmark import SCENARIOS, BenchmarkConfig, method_device, run_benchmark
from .compute import describe, environment, process_peak_rss_mib
from .degrade import Preset, load_presets
from .georef import NOMINAL, Georef
from .ingest import fetch_chip, read_chip, read_georef
from .merge import MergeError, merge
from .methods import (
    METHODS,
    OPT_IN,
    Method,
    cost_meter,
    default_methods,
    load_methods,
    missing_dependencies,
)
from .methods.deep import DEVICES, check_available
from .metrics import FAILURE_EPE_PX
from .presetcheck import preset_row, real_row, role_order
from .presetcheck import summarize as summarize_appearance
from .presetcheck import to_markdown as appearance_markdown
from .real import (
    ANCHOR,
    SeriesConfig,
    fetch_series,
    load_series,
    load_series_config,
    pairs,
    read_acquisition,
    triplets,
)
from .report import held_out_note, memory_note, summarize, to_markdown, write_csv
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
DEFAULT_SERIES_CONFIG = Path("configs/real.toml")


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
        "--allow-held-out",
        action="store_true",
        help="run on sites the sites config holds out for the final evaluation; "
        "the table and context.json name them",
    )
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
        default=default_methods(),
        help=f"methods to run, among {', '.join(sorted(METHODS))} and the variants "
        "declared in the methods config (default: every built-in method whose "
        f"dependencies are installed, except {', '.join(sorted(OPT_IN))})",
    )
    bench.add_argument(
        "--methods-config",
        type=Path,
        default=DEFAULT_METHODS_CONFIG,
        help="TOML file setting the methods' parameters",
    )
    bench.add_argument(
        "--device",
        choices=DEVICES,
        help="device every deep-learning method runs on, in place of the one its "
        "parameters name (default: those parameters); the other methods run on "
        "the CPU",
    )
    bench.add_argument("--out", type=Path, default=Path("outputs/benchmark"))
    if run_config:
        bench.set_defaults(**run_config)

    merging = commands.add_parser(
        "merge",
        help="merge the tables of runs made on different devices into one, "
        "without running anything",
    )
    merging.add_argument(
        "runs",
        nargs="+",
        type=Path,
        metavar="RUN",
        help="directory a benchmark run wrote (its --out), at least two",
    )
    merging.add_argument("--out", type=Path, default=Path("outputs/merged"))

    real = commands.add_parser(
        "real-pairs",
        help="fetch the dates of each site's series and list its real pairs",
    )
    _add_series_arguments(real)

    check = commands.add_parser(
        "check-presets",
        help="measure real pairs and the degradation presets the same way, and "
        "write them side by side",
    )
    _add_series_arguments(check)
    check.add_argument(
        "--allow-held-out",
        action="store_true",
        help="measure sites the sites config holds out; by default they are left "
        "out, since no preset may be chosen on them",
    )
    check.add_argument(
        "--degradations-config",
        type=Path,
        default=DEFAULT_DEGRADATIONS_CONFIG,
        help="TOML file declaring the degradation presets",
    )
    check.add_argument("--seed", type=int, default=0, help="seed of the preset noise")
    check.add_argument("--out", type=Path, default=Path("outputs/presets-check"))
    return parser


def _add_series_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--series-config",
        type=Path,
        default=DEFAULT_SERIES_CONFIG,
        help="TOML file declaring which dates each site's series takes",
    )
    parser.add_argument(
        "--site",
        action="append",
        dest="sites",
        metavar="NAME",
        help="site of the series, repeatable (default: every site of the series "
        "config)",
    )
    _add_data_arguments(parser)


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


def held_out_sites(args: argparse.Namespace) -> list[str]:
    """Check the benchmark's sites, and name the held-out ones among them.

    The configuration file is only read when a configured site is requested, so
    the synthetic site runs anywhere.

    Args:
        args: Parsed ``benchmark`` arguments.

    Returns:
        The requested sites marked held out, in the order requested.

    Raises:
        SystemExit: If a site is not configured, or is held out and
            ``--allow-held-out`` is not given.
    """
    names = [name for name in args.sites or [] if name != SYNTHETIC_SITE]
    if not names:
        return []
    config = load_sites(args.sites_config)
    for name in names:
        _configured_site(config, name)
    held_out = [name for name in names if config.sites[name].held_out]
    if held_out and not args.allow_held_out:
        raise SystemExit(
            f"satreg: site {held_out[0]!r} is held out for the final evaluation "
            f"({args.sites_config}); pass --allow-held-out to run it"
        )
    return held_out


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
        Method name to method, in the order requested, each deep-learning one on
        ``args.device`` if it is set.
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
    chosen = {name: methods[name] for name in args.methods}
    if args.device:
        chosen = {
            name: dataclasses.replace(method, device=args.device)
            if hasattr(method, "device")
            else method
            for name, method in chosen.items()
        }
    # A device the machine lacks would fail every pair of the method, one by
    # one, and leave a table of failures: refused before the first pair.
    for name, method in chosen.items():
        if (device := method_device(method)) != "cpu":
            try:
                check_available(device)
            except RuntimeError as exc:
                raise SystemExit(f"satreg: method {name}: {exc}") from None
    return chosen


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
    held_out = held_out_sites(args)
    sites, georefs = site_images(args)
    methods = configured_methods(args)

    started = perf_counter()
    results = run_benchmark(sites, methods, config, degradations, georefs)
    run_seconds = perf_counter() - started
    summary = summarize(results)
    context = environment()
    meters = {name: cost_meter(method).name for name, method in methods.items()}
    context["cost"] = {
        "warmup": config.warmup,
        "repeats": config.repeats,
        "process_peak_rss_mib": process_peak_rss_mib(),
        "memory": meters,
        # The whole run, pairs simulated and scored included, but not the
        # chips fetched before it.
        "run_seconds": run_seconds,
    }
    # Where each method ran: the deep-learning ones name their device, the
    # others run on the CPU.
    context["devices"] = {name: method_device(m) for name, m in methods.items()}
    # Sites kept for the final evaluation, so a table that looked at them says so.
    context["held_out_sites"] = held_out
    # Every option the run used, whether from the command line, a run config or
    # a default, so the tables can be reproduced from this file alone.
    context["run"] = {k: v for k, v in sorted(vars(args).items()) if k != "command"}
    table = to_markdown(summary) + (
        f"\nMeasured on {describe(context)}. Time is the median of {config.repeats} "
        f"calls per pair, after {config.warmup} warm-up call(s) per method; "
        f"{memory_note(meters)}. Details in `context.json`.\n"
    )
    table += held_out_note(held_out)

    write_csv(results, args.out / "pairs.csv")
    write_csv(summary, args.out / "summary.csv")
    (args.out / "summary.md").write_text(table)
    # Paths in the run options are written as text.
    context_json = json.dumps(context, indent=2, default=str)
    (args.out / "context.json").write_text(context_json + "\n")
    return table


def _series(args: argparse.Namespace) -> tuple[SitesConfig, SeriesConfig, list[str]]:
    """Read the configurations of a series command, and check its sites."""
    sites = load_sites(args.sites_config)
    try:
        series = load_series_config(args.series_config)
    except FileNotFoundError:
        raise SystemExit(
            f"satreg: no series configuration at {args.series_config} "
            "(run from the repository root or pass --series-config)"
        ) from None
    names = args.sites or list(series.sites)
    for name in names:
        _configured_site(sites, name)
    return sites, series, names


def real_pairs(args: argparse.Namespace) -> str:
    """Fetch the series of the requested sites and list their pairs.

    Held-out sites are fetched and listed too: this is metadata, which the final
    evaluation needs. Nothing is measured on them.

    Args:
        args: Parsed ``real-pairs`` arguments.

    Returns:
        A markdown table of the pairs, then the number of triplets per site.
    """
    sites, series, names = _series(args)
    lines = [
        "| site | pair | reference | moving | gap (days) | satellites | clouds |",
        "|---|---|---|---|---:|---|---:|",
    ]
    counts = []
    for name in names:
        site = sites.sites[name]
        paths = fetch_series(site, sites.catalogue, series, args.data_dir)
        acquisitions = [read_acquisition(path) for path in paths.values()]
        label = f"{name} (held out)" if site.held_out else name
        for pair in pairs(acquisitions):
            lines.append(
                f"| {label} | {pair.roles[0]}-{pair.roles[1]} "
                f"| {pair.dates[0].date()} | {pair.dates[1].date()} "
                f"| {pair.gap_days} | {'/'.join(pair.platforms)} "
                f"| {100 * pair.cloud_fraction:.2f} % |"
            )
        counts.append(f"{label} {len(triplets(acquisitions))}")
    return "\n".join(lines) + "\n\nTriplets: " + ", ".join(counts) + ".\n"


def check_presets(args: argparse.Namespace) -> str:
    """Measure the real pairs and the presets, and write them side by side.

    Held-out sites of the series config are left out unless
    ``--allow-held-out`` is given.

    Args:
        args: Parsed ``check-presets`` arguments.

    Returns:
        The summary table as markdown.

    Raises:
        SystemExit: If a site named on the command line is held out and
            ``--allow-held-out`` is not given.
    """
    sites, series, names = _series(args)
    held_out = [name for name in names if sites.sites[name].held_out]
    if args.sites and held_out and not args.allow_held_out:
        raise SystemExit(
            f"satreg: site {held_out[0]!r} is held out for the final evaluation "
            f"({args.sites_config}); pass --allow-held-out to measure it"
        )
    if not args.allow_held_out:
        names = [name for name in names if name not in held_out]
        held_out = []
    if not names:
        raise SystemExit(
            "satreg: every site of the series is held out; pass --allow-held-out "
            "to measure them"
        )
    try:
        presets = load_presets(args.degradations_config)
    except FileNotFoundError:
        raise SystemExit(
            f"satreg: no degradation presets at {args.degradations_config}"
        ) from None

    rows = []
    for name in names:
        site = sites.sites[name]
        acquisitions = load_series(site, sites.catalogue, series, args.data_dir)
        anchor = next(a for a in acquisitions if a.role == ANCHOR)
        rows += [real_row(name, pair) for pair in pairs(acquisitions)]
        rows += [
            preset_row(name, anchor.image, preset_name, preset, args.seed)
            for preset_name, preset in presets.items()
        ]
    summary = summarize_appearance(rows, role_order(list(series.dates)))
    table = appearance_markdown(summary, presets) + (
        f"\nSites: {', '.join(names)}. Median [min, max] across sites of each "
        "pair's median over its clear 256 px windows. Presets are measured on "
        "zero-shift windows of each anchor chip, without their clouds, whose "
        "nominal cover is shown instead. SNR is the lower of the two images', by "
        "Immerkær's estimator, which reads fine texture as noise: a lower bound, "
        "to compare between rows only. Per-pair rows in `pairs.csv`.\n"
    )
    table += held_out_note(held_out)
    write_csv(rows, args.out / "pairs.csv")
    (args.out / "summary.md").write_text(table)
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
    elif args.command == "merge":
        try:
            print(merge(args.runs, args.out), end="")
        except MergeError as exc:
            raise SystemExit(f"satreg: {exc}") from None
    elif args.command == "real-pairs":
        print(real_pairs(args), end="")
    elif args.command == "check-presets":
        print(check_presets(args), end="")

"""Command-line entry point: ``satreg fetch``, ``satreg benchmark``, ``satreg
merge``, ``satreg real-pairs``, ``satreg check-presets``, ``satreg cycle``,
``satreg false-change``, ``satreg fetch-train``, ``satreg train-pairs``,
``satreg validate`` and ``satreg validate-cycle``."""

import argparse
import dataclasses
import json
import logging
import tomllib
from collections.abc import Sequence
from pathlib import Path
from time import perf_counter

import numpy as np

from . import cycle, falsechange, trainchips, trainpairs, validation
from .benchmark import (
    SCENARIOS,
    BenchmarkConfig,
    PairResult,
    method_device,
    run_benchmark,
)
from .compute import describe, environment, process_peak_rss_mib
from .degrade import Preset, load_presets
from .georef import NOMINAL, Georef
from .ingest import (
    TEN_METRE_BANDS,
    check_bands,
    fetch_bands,
    fetch_chip,
    read_bands,
    read_chip,
    read_georef,
)
from .landcover import EROSION_PX, fetch_landcover, read_landcover, stable_ground
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
    Acquisition,
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
DEFAULT_TRAIN_CONFIG = Path("configs/train-sites.toml")
DEFAULT_PAIRS_CONFIG = Path("configs/train-pairs.toml")

# Commands a run configuration file can set, and the table each one reads.
RUN_TABLES = {
    "benchmark": "benchmark",
    "cycle": "cycle",
    "false-change": "false_change",
    "validate": "validate",
    "validate-cycle": "validate_cycle",
}


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


def _add_config_argument(parser: argparse.ArgumentParser, command: str) -> None:
    parser.add_argument(
        "--config",
        type=Path,
        help=f"TOML file whose [{RUN_TABLES[command]}] table sets any of the "
        "options below, by their name with underscores; options given here "
        "override it",
    )


def _parser(
    run_config: dict[str, object] | None = None, command: str = "benchmark"
) -> argparse.ArgumentParser:
    """Build the argument parser.

    Args:
        run_config: Defaults for the options of ``command``, by destination name,
            as read by ``load_run_config``. Options given on the command line
            still win.
        command: The command ``run_config`` sets, one of ``RUN_TABLES``.

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
    _add_config_argument(bench, "benchmark")
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
        "--band-pair",
        action="append",
        nargs=2,
        dest="band_pairs",
        metavar=("REFERENCE", "MOVING"),
        help="simulate inter-band pairs, the reference image cut from one band "
        "and the moving image from another of the same scene, repeatable; bands "
        f"among {', '.join(TEN_METRE_BANDS)} (default: single-band pairs from "
        "each site's own band)",
    )
    _add_scoring_arguments(bench, defaults)
    bench.add_argument("--out", type=Path, default=Path("outputs/benchmark"))

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

    closing = commands.add_parser(
        "cycle",
        help="register the real triplets of each site and score how well each "
        "method's displacements close, next to simulated triplets",
    )
    _add_config_argument(closing, "cycle")
    _add_series_arguments(closing)
    closing.add_argument(
        "--allow-held-out",
        action="store_true",
        help="run on sites the sites config holds out; by default they are left "
        "out, and a table that has them says so",
    )
    closing.add_argument(
        "--simulated-triplets",
        type=int,
        default=5,
        help="simulated triplets per site, scenario and preset, cut from the "
        "site's anchor chip, whose closure is shown next to their true error "
        "(0: none)",
    )
    closing.add_argument(
        "--scenarios",
        nargs="+",
        choices=SCENARIOS,
        default=list(SCENARIOS),
        help="geometric models of the simulated triplets (default: all)",
    )
    closing.add_argument(
        "--degradations",
        nargs="+",
        metavar="PRESET",
        help="degradation presets of the simulated triplets (default: all)",
    )
    closing.add_argument(
        "--degradations-config",
        type=Path,
        default=DEFAULT_DEGRADATIONS_CONFIG,
        help="TOML file declaring the degradation presets",
    )
    _add_closure_arguments(closing, defaults)
    closing.add_argument(
        "--seed",
        type=int,
        default=defaults.seed,
        help="seed of the simulated triplets",
    )
    closing.add_argument("--out", type=Path, default=Path("outputs/cycle"))

    changes = commands.add_parser(
        "false-change",
        help="count the false changes each method's residual misregistration "
        "leaves for a change detector, on simulated pairs and on the stable "
        "ground of real ones",
    )
    _add_config_argument(changes, "false-change")
    _add_series_arguments(changes)
    changes.add_argument(
        "--allow-held-out",
        action="store_true",
        help="run on sites the sites config holds out (default: left out)",
    )
    changes.add_argument(
        "--methods",
        nargs="+",
        metavar="METHOD",
        default=default_methods(),
        help="methods to run (default: as for benchmark)",
    )
    changes.add_argument(
        "--methods-config",
        type=Path,
        default=DEFAULT_METHODS_CONFIG,
        help="TOML file setting the methods' parameters",
    )
    changes.add_argument(
        "--device",
        choices=DEVICES,
        help="device every deep-learning method runs on (default: as configured)",
    )
    changes.add_argument(
        "--pairs",
        type=int,
        default=defaults.n_pairs,
        help="simulated pairs per site, scenario and preset, cut from the site's "
        "anchor chip (0: none)",
    )
    changes.add_argument(
        "--scenarios",
        nargs="+",
        choices=SCENARIOS,
        default=list(falsechange.SCENARIOS),
        help="geometric models of the simulated pairs; the reference curve is "
        "drawn on translation pairs (default: translation and affine)",
    )
    changes.add_argument(
        "--degradations",
        nargs="+",
        metavar="PRESET",
        help="degradation presets of the simulated pairs (default: all)",
    )
    changes.add_argument(
        "--degradations-config",
        type=Path,
        default=DEFAULT_DEGRADATIONS_CONFIG,
        help="TOML file declaring the degradation presets",
    )
    changes.add_argument("--seed", type=int, default=defaults.seed)
    changes.add_argument(
        "--failure-threshold",
        type=float,
        default=FAILURE_EPE_PX,
        help="mean end-point error above which a simulated pair failed, in px",
    )
    changes.add_argument(
        "--warmup",
        type=int,
        default=defaults.warmup,
        help="untimed calls of each method before timing it",
    )
    changes.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="timed calls of a method on each pair, whose median is reported",
    )
    changes.add_argument("--out", type=Path, default=Path("outputs/false-change"))
    train = commands.add_parser(
        "fetch-train",
        help="fetch the series of the training and validation chips, and check "
        "each chip against the acceptance rule",
    )
    _add_training_arguments(
        train, "chip to fetch, repeatable (default: every chip of the train config)"
    )
    train.add_argument("--out", type=Path, default=Path("outputs/train-chips"))
    train.add_argument(
        "--export",
        type=Path,
        metavar="DIR",
        help="also copy the accepted chips to DIR, laid out as a data directory, "
        "with the manifest: what is uploaded for the training runs",
    )
    drawn = commands.add_parser(
        "train-pairs",
        help="draw training pairs, save them as a contact sheet and measure how "
        "fast they are made",
    )
    drawn.add_argument(
        "--pairs-config",
        type=Path,
        default=DEFAULT_PAIRS_CONFIG,
        help="TOML file whose [pairs] table says what training pairs are made of",
    )
    drawn.add_argument(
        "--degradations-config",
        type=Path,
        default=DEFAULT_DEGRADATIONS_CONFIG,
        help="TOML file whose [training] table gives the degradation ranges",
    )
    _add_training_arguments(
        drawn,
        "training chip to cut pairs from, repeatable (default: every training chip)",
    )
    drawn.add_argument(
        "--n-pairs", type=int, default=200, help="pairs to draw and time"
    )
    drawn.add_argument(
        "--sheet-pairs",
        type=int,
        default=36,
        help="how many of them, the first ones, go on the contact sheet",
    )
    drawn.add_argument(
        "--cross-date",
        type=float,
        help="share of cross-date pairs (default: the pairs config's)",
    )
    drawn.add_argument(
        "--seed", type=int, help="seed of the pairs (default: the pairs config's)"
    )
    drawn.add_argument("--out", type=Path, default=Path("outputs/train-pairs"))

    validating = commands.add_parser(
        "validate",
        help="score methods on the validation set: simulated pairs cut from the "
        "validation chips, scored as benchmark scores its own",
    )
    _add_config_argument(validating, "validate")
    _add_training_arguments(
        validating,
        "validation chip to cut pairs from, repeatable (default: every validation "
        "chip)",
    )
    _add_scoring_arguments(validating, defaults)
    validating.add_argument(
        "--light",
        action="store_true",
        help="run the light validation set, the first --light-pairs pairs of every "
        "cell, and write it next to --out, in a directory named after it with "
        "-light",
    )
    validating.add_argument(
        "--light-pairs",
        type=int,
        default=10,
        help="pairs per chip, scenario and preset of the light validation set",
    )
    validating.add_argument(
        "--subset-sizes",
        nargs="+",
        type=int,
        default=[5, 10, 20, 50],
        metavar="PAIRS",
        help="light sets to compare with the full one, in pairs per cell",
    )
    validating.add_argument("--out", type=Path, default=Path("outputs/validation"))

    validating_closure = commands.add_parser(
        "validate-cycle",
        help="score how well each method's displacements close on the real "
        "triplets of the training and validation chips",
    )
    _add_config_argument(validating_closure, "validate-cycle")
    _add_training_arguments(
        validating_closure,
        "training or validation chip to run, repeatable (default: every chip of "
        "the train config)",
    )
    _add_closure_arguments(validating_closure, defaults)
    validating_closure.add_argument(
        "--out", type=Path, default=Path("outputs/validation-cycle")
    )
    if run_config:
        {
            "benchmark": bench,
            "cycle": closing,
            "false-change": changes,
            "validate": validating,
            "validate-cycle": validating_closure,
        }[command].set_defaults(**run_config)
    return parser


def _add_scoring_arguments(
    parser: argparse.ArgumentParser, defaults: BenchmarkConfig
) -> None:
    """Add the options of a command that scores methods on simulated pairs."""
    parser.add_argument(
        "--degradations",
        nargs="+",
        metavar="PRESET",
        help="degradation presets to run (default: every configured preset)",
    )
    parser.add_argument(
        "--degradations-config",
        type=Path,
        default=DEFAULT_DEGRADATIONS_CONFIG,
        help="TOML file declaring the degradation presets",
    )
    parser.add_argument("--pairs", type=int, default=defaults.n_pairs)
    parser.add_argument("--size", type=int, default=defaults.size)
    parser.add_argument(
        "--scenarios",
        nargs="+",
        choices=SCENARIOS,
        default=list(defaults.scenarios),
        help="geometric models to simulate (default: all)",
    )
    parser.add_argument(
        "--max-shift",
        type=float,
        default=defaults.max_shift,
        help="largest shift of the pair centre, per component, in px",
    )
    parser.add_argument(
        "--max-rotation",
        type=float,
        default=defaults.max_rotation_deg,
        help="largest affine rotation, in degrees",
    )
    parser.add_argument(
        "--max-scale-change",
        type=float,
        default=defaults.max_scale_change,
        help="largest affine scale change, as a fraction (0.002 is 0.2 %%)",
    )
    parser.add_argument(
        "--max-shear",
        type=float,
        default=defaults.max_shear,
        help="largest affine shear, in px per px",
    )
    parser.add_argument(
        "--max-local-shift",
        type=float,
        default=defaults.max_local_shift,
        help="largest magnitude of the local field of a dense pair, in px: "
        "orthorectification residuals such as relief seen through an elevation "
        "model error",
    )
    parser.add_argument(
        "--local-length",
        type=float,
        default=defaults.local_length,
        help="correlation length of the local field of a dense pair, in px",
    )
    parser.add_argument("--seed", type=int, default=defaults.seed)
    parser.add_argument(
        "--failure-threshold",
        type=float,
        default=FAILURE_EPE_PX,
        help="mean end-point error above which a pair failed, in px",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=defaults.warmup,
        help="untimed calls of each method before timing it",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=defaults.repeats,
        help="timed calls of a method on each pair, whose median is reported",
    )
    parser.add_argument(
        "--methods",
        nargs="+",
        metavar="METHOD",
        default=default_methods(),
        help=f"methods to run, among {', '.join(sorted(METHODS))} and the variants "
        "declared in the methods config (default: every built-in method whose "
        f"dependencies are installed, except {', '.join(sorted(OPT_IN))})",
    )
    parser.add_argument(
        "--methods-config",
        type=Path,
        default=DEFAULT_METHODS_CONFIG,
        help="TOML file setting the methods' parameters",
    )
    parser.add_argument(
        "--device",
        choices=DEVICES,
        help="device every deep-learning method runs on, in place of the one its "
        "parameters name (default: those parameters); the other methods run on "
        "the CPU",
    )


def _add_closure_arguments(
    parser: argparse.ArgumentParser, defaults: BenchmarkConfig
) -> None:
    """Add the options of a command that scores closure on real triplets."""
    parser.add_argument(
        "--methods",
        nargs="+",
        metavar="METHOD",
        default=default_methods(),
        help="methods to run (default: as for benchmark)",
    )
    parser.add_argument(
        "--methods-config",
        type=Path,
        default=DEFAULT_METHODS_CONFIG,
        help="TOML file setting the methods' parameters",
    )
    parser.add_argument(
        "--device",
        choices=DEVICES,
        help="device every deep-learning method runs on (default: as configured)",
    )
    parser.add_argument(
        "--failure-threshold",
        type=float,
        default=FAILURE_EPE_PX,
        help="mean closure residual above which a triplet failed, in px",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=defaults.warmup,
        help="untimed calls of each method before timing it",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="timed calls of a method on each pair, whose median is reported",
    )


def _add_training_arguments(parser: argparse.ArgumentParser, chip_help: str) -> None:
    """Add the options of a command that reads the training chips."""
    parser.add_argument(
        "--train-config",
        type=Path,
        default=DEFAULT_TRAIN_CONFIG,
        help="TOML file declaring the training and validation chips",
    )
    parser.add_argument(
        "--series-config",
        type=Path,
        default=DEFAULT_SERIES_CONFIG,
        help="TOML file declaring which dates a series takes",
    )
    parser.add_argument(
        "--chip", action="append", dest="chips", metavar="NAME", help=chip_help
    )
    _add_data_arguments(parser)


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


def load_run_config(path: Path, command: str = "benchmark") -> dict[str, object]:
    """Read the table of one command in a run configuration file.

    Args:
        path: TOML file with a table named after the command (``[benchmark]``,
            ``[cycle]``, ``[false_change]``, ``[validate]``,
            ``[validate_cycle]``). Its keys are that command's options
            by destination name (``max_shift`` for ``--max-shift``). Paths are
            read relative to the working directory, like the command-line
            options. The file's other tables are not read.
        command: The command, one of ``RUN_TABLES``.

    Returns:
        Option destination to value.

    Raises:
        SystemExit: If the file is missing, has no table for the command, or sets
            an option the command does not have.
    """
    table = RUN_TABLES[command]
    try:
        with path.open("rb") as f:
            raw = tomllib.load(f)
    except FileNotFoundError:
        raise SystemExit(f"satreg: no run configuration at {path}") from None
    if table not in raw:
        raise SystemExit(f"satreg: {path} needs a [{table}] table")
    options = set(vars(_parser().parse_args([command]))) - {"command", "config"}
    unknown = sorted(set(raw[table]) - options)
    if unknown:
        raise SystemExit(
            f"satreg: {path}: unknown {command} option {unknown[0]!r} "
            f"(options: {', '.join(sorted(options))})"
        )
    return raw[table]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the command line, with defaults from ``--config`` if it is given.

    Args:
        argv: Arguments, without the program name; ``sys.argv`` if ``None``.

    Returns:
        The parsed arguments.
    """
    command_line = _parser().parse_args(argv)
    if getattr(command_line, "config", None) is None:
        return command_line
    run_config = load_run_config(command_line.config, command_line.command)
    args = _parser(run_config, command_line.command).parse_args(argv)
    # A repeatable option (--site, --band-pair) appends to its default, which is
    # now the config's list. Given on the command line, it replaces that list,
    # as every other option replaces its key. Without a config, such an option
    # has no default: a value means the command line gave it.
    defaults = vars(_parser().parse_args([command_line.command]))
    for dest, value in vars(command_line).items():
        if value is not None and defaults.get(dest) is None:
            setattr(args, dest, value)
    return args


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


def band_list(args: argparse.Namespace) -> list[str]:
    """Check the benchmark's band pairs, and list the bands they need.

    Args:
        args: Parsed ``benchmark`` arguments.

    Returns:
        Every band of the band pairs, once, in order of first mention; empty for
        a single-band run.

    Raises:
        SystemExit: If a band is not a 10 m band, or band pairs are asked of the
            synthetic site, which has a single band.
    """
    bands = list(dict.fromkeys(b for pair in args.band_pairs or [] for b in pair))
    if not bands:
        return []
    try:
        check_bands(bands)
    except ValueError as exc:
        raise SystemExit(f"satreg: {exc}") from None
    if SYNTHETIC_SITE in (args.sites or [SYNTHETIC_SITE]):
        raise SystemExit(
            f"satreg: the {SYNTHETIC_SITE} site has no bands; band pairs need "
            "configured sites"
        )
    return bands


def site_images(
    args: argparse.Namespace,
) -> tuple[dict[str, np.ndarray], dict[str, Georef], dict[str, dict[str, np.ndarray]]]:
    """Load the image, map grid and bands of every site the benchmark runs on.

    Configured sites come from the chip cache, fetched first if not cached, on
    the chip's own grid. Their bands, for a run with band pairs, come from a
    multi-band chip of the same scene and window. The synthetic site gets a
    nominal grid. The configuration file is only read when a configured site is
    requested, so the synthetic site runs anywhere.

    Args:
        args: Parsed ``benchmark`` arguments.

    Returns:
        Site name to 2-D image, site name to its map grid, and site name to band
        name to 2-D band (empty for a single-band run).
    """
    wanted = band_list(args)
    images, georefs, bands = {}, {}, {}
    config = None
    for name in args.sites or [SYNTHETIC_SITE]:
        if name == SYNTHETIC_SITE:
            images[name] = fractal_texture(SYNTHETIC_SITE_PX, seed=args.seed)
            georefs[name] = NOMINAL
            continue
        config = config or load_sites(args.sites_config)
        _configured_site(config, name)
        site = config.sites[name]
        chip = fetch_chip(site, config.catalogue, args.data_dir)
        images[name] = read_chip(chip)
        georefs[name] = read_georef(chip)
        if wanted:
            stack = fetch_bands(site, config.catalogue, args.data_dir, wanted)
            bands[name] = read_bands(stack)
    return images, georefs, bands


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


def _benchmark_config(args: argparse.Namespace) -> BenchmarkConfig:
    """Build the run parameters of a command that scores simulated pairs."""
    band_pairs = getattr(args, "band_pairs", None) or []
    return BenchmarkConfig(
        n_pairs=args.pairs,
        size=args.size,
        max_shift=args.max_shift,
        max_rotation_deg=args.max_rotation,
        max_scale_change=args.max_scale_change,
        max_shear=args.max_shear,
        max_local_shift=args.max_local_shift,
        local_length=args.local_length,
        scenarios=tuple(dict.fromkeys(args.scenarios)),
        band_pairs=tuple(dict.fromkeys(tuple(p) for p in band_pairs)),
        seed=args.seed,
        failure_threshold=args.failure_threshold,
        warmup=args.warmup,
        repeats=args.repeats,
    )


def _run_context(
    args: argparse.Namespace,
    config: BenchmarkConfig,
    methods: dict[str, Method],
    run_seconds: float,
    held_out: list[str],
) -> tuple[dict[str, object], dict[str, str]]:
    """Describe a run for its ``context.json``.

    Args:
        args: Parsed arguments of the command.
        config: Run parameters, for the warm-up and repeats.
        methods: The methods that ran.
        run_seconds: How long the run took, without the chips fetched before it.
        held_out: Held-out sites the run looked at.

    Returns:
        The context, and each method's memory meter by method name.
    """
    context = environment()
    meters = {name: cost_meter(method).name for name, method in methods.items()}
    context["cost"] = {
        "warmup": config.warmup,
        "repeats": config.repeats,
        "process_peak_rss_mib": process_peak_rss_mib(),
        "memory": meters,
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
    return context, meters


def _write_context(context: dict[str, object], out: Path) -> None:
    # Paths in the run options are written as text.
    context_json = json.dumps(context, indent=2, default=str)
    (out / "context.json").write_text(context_json + "\n")


def _score(
    args: argparse.Namespace,
    config: BenchmarkConfig,
    degradations: dict[str, Preset],
    sites: dict[str, np.ndarray],
    georefs: dict[str, Georef],
    bands: dict[str, dict[str, np.ndarray]],
    methods: dict[str, Method],
    held_out: list[str],
) -> tuple[list[PairResult], dict[str, object], str]:
    """Simulate and score pairs: what ``benchmark`` and ``validate`` both run.

    Args:
        args: Parsed arguments of the command.
        config: Run parameters.
        degradations: Preset name to preset.
        sites: Site name to the image pairs are cut from.
        georefs: Site name to its map grid.
        bands: Site name to band name to band, empty for a single-band run.
        methods: Method name to method.
        held_out: Held-out sites among ``sites``.

    Returns:
        Per-pair results, the run's context, and the footnote of its table: how
        and on what machine cost was measured.
    """
    started = perf_counter()
    results = run_benchmark(sites, methods, config, degradations, georefs, bands)
    # The whole run, pairs simulated and scored included.
    run_seconds = perf_counter() - started
    context, meters = _run_context(args, config, methods, run_seconds, held_out)
    footnote = (
        f"\nMeasured on {describe(context)}. Time is the median of {config.repeats} "
        f"calls per pair, after {config.warmup} warm-up call(s) per method; "
        f"{memory_note(meters)}. Details in `context.json`.\n"
    )
    return results, context, footnote


def benchmark(args: argparse.Namespace) -> str:
    """Run the benchmark on the requested sites and write its tables.

    Args:
        args: Parsed ``benchmark`` arguments.

    Returns:
        The results table as markdown, followed by the machine it was measured on.
    """
    config = _benchmark_config(args)
    degradations = degradation_presets(args)
    held_out = held_out_sites(args)
    sites, georefs, bands = site_images(args)
    methods = configured_methods(args)

    results, context, footnote = _score(
        args, config, degradations, sites, georefs, bands, methods, held_out
    )
    summary = summarize(results)
    table = to_markdown(summary) + footnote + held_out_note(held_out)

    write_csv(results, args.out / "pairs.csv")
    write_csv(summary, args.out / "summary.csv")
    (args.out / "summary.md").write_text(table)
    _write_context(context, args.out)
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


def _open_sites(
    args: argparse.Namespace, sites: SitesConfig, names: list[str]
) -> tuple[list[str], list[str]]:
    """Leave held-out sites out of a series command, unless it may use them.

    Args:
        args: Parsed arguments, with ``sites``, ``sites_config`` and
            ``allow_held_out``.
        sites: The sites configuration.
        names: The series' sites the command would use.

    Returns:
        The sites to use, and the held-out ones among them.

    Raises:
        SystemExit: If a site named on the command line is held out and
            ``--allow-held-out`` is not given, or no site is left.
    """
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
    return names, held_out


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
    names, held_out = _open_sites(args, sites, names)
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


def _closure(
    series: dict[str, list[Acquisition]],
    methods: dict[str, Method],
    config: BenchmarkConfig,
    degradations: dict[str, Preset],
) -> tuple[list[cycle.LegRow], list[cycle.TripletRow], float]:
    """Score closure on each series: what ``cycle`` and ``validate-cycle`` run.

    Args:
        series: Site or chip name to its acquisitions.
        methods: Method name to method.
        config: Run parameters; ``n_pairs`` is the number of simulated triplets.
        degradations: Presets of the simulated triplets, cut from each anchor;
            none if empty.

    Returns:
        Leg rows, triplet rows, and how long the run took, in seconds.

    Raises:
        SystemExit: If no window of any triplet is clear.
    """
    started = perf_counter()
    legs, rows = [], []
    warmed: set[str] = set()
    for name, acquisitions in series.items():
        more_legs, more_rows = cycle.run_real(
            name, acquisitions, methods, config, warmed
        )
        legs += more_legs
        rows += more_rows
        if not degradations:
            continue
        anchor = next(a for a in acquisitions if a.role == ANCHOR)
        more_legs, more_rows = cycle.run_simulated(
            name,
            anchor.image.astype(float),
            methods,
            config,
            degradations,
            anchor.georef,
            warmed,
        )
        legs += more_legs
        rows += more_rows
    run_seconds = perf_counter() - started
    if not rows:
        raise SystemExit(
            f"satreg: no {cycle.WINDOW_PX} px window of any triplet is clear on "
            "its three dates"
        )
    return legs, rows, run_seconds


def _closure_note(
    config: BenchmarkConfig,
    meters: dict[str, str],
    context: dict[str, object],
    simulated: bool,
) -> str:
    """Say how the closure tables were measured."""
    return (
        "Each triplet of dates A < B < C is "
        f"registered A to B, B to C and A to C on each {cycle.WINDOW_PX} px window "
        f"hidden at most {100 * cycle.MAX_WINDOW_CLOUD:.0f} % on its three dates; "
        "the closure is the distance between A to B then B to C, and A to C, "
        "over pixels clear on all three. A triplet fails if a leg does, or if its "
        f"mean closure exceeds {config.failure_threshold} px; closure columns "
        "average the others. "
        + (
            "Simulated triplets show the true end-point error of "
            "their legs, and the closure of their true legs, which is what composing "
            "alone leaves. "
            if simulated
            else ""
        )
        + f"Time is the median of {config.repeats} call(s) per pair, "
        f"after {config.warmup} warm-up call(s) per method; "
        f"{memory_note(meters)}. Measured on {describe(context)}.\n"
    )


def _motion_note(
    legs: Sequence[cycle.LegRow], series: SeriesConfig, simulated: bool
) -> str:
    """Render the displacements found between real dates, and how to read them."""
    motion = cycle.motion_summary(legs, role_order(list(series.dates)))
    return (
        cycle.motion_markdown(motion)
        + "\nDisplacements the methods find between real dates, across sites and "
        "windows"
        + (
            ", next to the truths of the simulated pairs from A (the benchmark ranges)"
            if simulated
            else ""
        )
        + ". Translation is the median of the displacement over the window; "
        f"the non-translation part is the {cycle.NON_TRANSLATION_PERCENTILE}th "
        "percentile of what is left. Median (max) over registrations.\n"
    )


def cycle_consistency(args: argparse.Namespace) -> str:
    """Score the closure of each site's real triplets, and of simulated ones.

    Args:
        args: Parsed ``cycle`` arguments.

    Returns:
        The closure tables and the displacements table, as markdown.

    Raises:
        SystemExit: As ``check-presets`` does for held-out sites, or if a method
            or preset is unknown.
    """
    sites, series, names = _series(args)
    names, held_out = _open_sites(args, sites, names)
    methods = configured_methods(args)
    degradations = degradation_presets(args) if args.simulated_triplets else {}
    config = BenchmarkConfig(
        n_pairs=args.simulated_triplets,
        size=cycle.WINDOW_PX,
        scenarios=tuple(dict.fromkeys(args.scenarios)),
        seed=args.seed,
        failure_threshold=args.failure_threshold,
        warmup=args.warmup,
        repeats=args.repeats,
    )
    loaded = {
        name: load_series(sites.sites[name], sites.catalogue, series, args.data_dir)
        for name in names
    }
    legs, rows, run_seconds = _closure(loaded, methods, config, degradations)

    summary = cycle.summarize(rows)
    context, meters = _run_context(args, config, methods, run_seconds, held_out)
    table = (
        cycle.to_markdown(summary)
        + f"\nSites: {', '.join(names)}. "
        + _closure_note(config, meters, context, simulated=True)
        + held_out_note(held_out)
        + "\n"
        + _motion_note(legs, series, simulated=True)
    )

    write_csv(legs, args.out / "legs.csv")
    write_csv(rows, args.out / "triplets.csv")
    write_csv(summary, args.out / "summary.csv")
    (args.out / "summary.md").write_text(table)
    _write_context(context, args.out)
    return table


def false_change(args: argparse.Namespace) -> str:
    """Count false changes after each method's correction, simulated and real.

    Args:
        args: Parsed ``false-change`` arguments.

    Returns:
        The summary tables as markdown.

    Raises:
        SystemExit: As ``check-presets`` does for held-out sites, or if a method
            or preset is unknown.
    """
    sites, series, names = _series(args)
    names, held_out = _open_sites(args, sites, names)
    methods = configured_methods(args)
    degradations = degradation_presets(args) if args.pairs else {}
    config = BenchmarkConfig(
        n_pairs=args.pairs,
        scenarios=tuple(dict.fromkeys(args.scenarios)),
        seed=args.seed,
        failure_threshold=args.failure_threshold,
        warmup=args.warmup,
        repeats=args.repeats,
    )

    started = perf_counter()
    curve, simulated, real = [], [], []
    stable_share = {}
    warmed: set[str] = set()
    for name in names:
        site = sites.sites[name]
        acquisitions = load_series(site, sites.catalogue, series, args.data_dir)
        anchor = next(a for a in acquisitions if a.role == ANCHOR)
        cover = fetch_landcover(name, anchor.georef, anchor.image.shape, args.data_dir)
        stable = stable_ground(read_landcover(cover))
        stable_share[name] = float(stable.mean())
        real += falsechange.run_real(
            name, acquisitions, stable, methods, config, warmed
        )
        if not degradations:
            continue
        more_curve, more_rows = falsechange.run_simulated(
            name,
            anchor.image.astype(float),
            methods,
            config,
            degradations,
            anchor.georef,
            warmed=warmed,
        )
        curve += more_curve
        simulated += more_rows
    run_seconds = perf_counter() - started

    points = falsechange.curve_summary(curve)
    sim_summary = falsechange.simulated_summary(simulated, points)
    by_site = falsechange.real_summary(real, "site")
    usable = [k for k, v in stable_share.items() if v >= falsechange.MIN_STABLE_SHARE]
    by_pair = falsechange.real_summary(
        [r for r in real if r.site in usable],
        "pair",
        role_order(list(series.dates)),
    )
    context = environment()
    meters = {name: cost_meter(method).name for name, method in methods.items()}
    context["cost"] = {
        "warmup": config.warmup,
        "repeats": config.repeats,
        "process_peak_rss_mib": process_peak_rss_mib(),
        "memory": meters,
        "run_seconds": run_seconds,
    }
    context["devices"] = {name: method_device(m) for name, m in methods.items()}
    context["held_out_sites"] = held_out
    context["stable_share"] = stable_share
    context["run"] = {k: v for k, v in sorted(vars(args).items()) if k != "command"}

    detector = (
        "A pixel has changed where the moving image, matched to the reference's "
        "mean and standard deviation and resampled onto its grid, differs from "
        f"it by more than {falsechange.K_SIGMA:g} times the noise of the "
        "difference (Immerkær's estimator on each image). Every correction, "
        "no correction included, goes through the same resampling (Fourier x4 "
        "then cubic spline) and the same threshold."
    )
    shares = ", ".join(f"{k} {100 * v:.1f} %" for k, v in stable_share.items())
    table = ""
    if sim_summary:
        table += (
            "## Simulated pairs\n\n"
            + falsechange.simulated_markdown(sim_summary)
            + "\nFalse change is the share of the pair's clear pixels flagged "
            "as changed: on a simulated pair the ground never changes. Residual "
            "is the mean end-point error of the method's estimate; the reference "
            "curve corrects each translation pair with its truth shifted by that "
            "much, and *curve at residual* is what it gives there. *Curve at 0* "
            "is the floor that blur, noise and radiometry leave with a perfect "
            f"registration. Means over non-failed pairs (end-point error over "
            f"{config.failure_threshold} px, or an error); *none* is never "
            "failed. Figure: `false_change.png`.\n\n"
        )
    if by_site:
        table += (
            "## Real pairs, stable ground\n\n"
            + falsechange.real_markdown(by_site)
            + "\n"
            + falsechange.real_markdown(by_pair)
            + f"\nStable ground is ESA WorldCover 2021 built-up and bare / sparse "
            f"vegetation, eroded by {EROSION_PX} px; share of each chip: {shares}. "
            "The table by pair pools the sites where it is at least "
            f"{100 * falsechange.MIN_STABLE_SHARE:.0f} % of the chip "
            f"({', '.join(usable) or 'none'}): elsewhere it is a few roads and "
            "villages, which a level matched on the fields around them does not "
            "level. "
            f"Windows of {falsechange.WINDOW_PX} px hidden at most "
            f"{100 * falsechange.MAX_WINDOW_CLOUD:.0f} % on both dates, hidden "
            f"pixels grown by {falsechange.CLOUD_DILATION_PX} px and a "
            f"{falsechange.BORDER_PX} px border left out. Counts are pooled over "
            "windows before dividing. *Other ground* mixes true and false "
            "changes, for scale.\n\n"
        )
    table += detector + f" Measured on {describe(context)}.\n" + held_out_note(held_out)

    args.out.mkdir(parents=True, exist_ok=True)
    if curve:
        write_csv(curve, args.out / "curve.csv")
        write_csv(points, args.out / "curve_summary.csv")
        write_csv(simulated, args.out / "simulated.csv")
        write_csv(sim_summary, args.out / "simulated_summary.csv")
        falsechange.plot(points, sim_summary, args.out / "false_change.png")
    if real:
        write_csv(real, args.out / "real.csv")
        write_csv(by_site + by_pair, args.out / "real_summary.csv")
    (args.out / "summary.md").write_text(table)
    context_json = json.dumps(context, indent=2, default=str)
    (args.out / "context.json").write_text(context_json + "\n")
    return table


def _training(
    args: argparse.Namespace,
) -> tuple[trainchips.TrainingConfig, SeriesConfig]:
    """Read the configurations of a command that reads the training chips."""
    sites = load_sites(args.sites_config)
    try:
        config = trainchips.load_training_chips(args.train_config, sites)
        series = load_series_config(args.series_config)
    except FileNotFoundError as exc:
        raise SystemExit(
            f"satreg: no configuration at {exc.filename} (run from the repository "
            "root or pass --train-config and --series-config)"
        ) from None
    except ValueError as exc:
        raise SystemExit(f"satreg: {exc}") from None
    return config, series


def fetch_train(args: argparse.Namespace) -> str:
    """Fetch the series of the training and validation chips, and check them.

    Args:
        args: Parsed ``fetch-train`` arguments.

    Returns:
        A markdown table of each chip's land cover and verdict, then one of its
        dates. Also written to ``args.out`` with a ``chips.json`` manifest.

    Raises:
        SystemExit: If a chip is refused by the acceptance rule; the tables are
            written first, and the message gives the chip's shares.
    """
    config, series = _training(args)
    names = args.chips or list(config.chips)
    for name in names:
        if name not in config.chips:
            known = ", ".join(config.chips)
            raise SystemExit(f"satreg: unknown chip {name!r} (declared: {known})")

    checks = [
        trainchips.check_chip(config.chips[name], config, series, args.data_dir)
        for name in names
    ]
    table = trainchips.to_markdown(checks)
    manifest = json.dumps(trainchips.manifest(checks, args.data_dir), indent=2)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.md").write_text(table)
    (args.out / "chips.json").write_text(manifest + "\n")

    if refused := [check for check in checks if not check.accepted]:
        print(table, end="")
        raise SystemExit(
            "satreg: "
            + "\n".join(
                f"{check.chip.name} is refused: {'; '.join(check.failures)}"
                for check in refused
            )
        )
    if args.export:
        size = trainchips.export(checks, args.data_dir, args.export)
        (args.export / "chips.json").write_text(manifest + "\n")
        table += (
            f"\nExported {len(checks)} chips to {args.export}: {size / 1e6:.0f} MB.\n"
        )
    return table


def train_pairs(args: argparse.Namespace) -> str:
    """Draw training pairs, save a contact sheet and measure their throughput.

    Args:
        args: Parsed ``train-pairs`` arguments.

    Returns:
        A markdown table of the pairs drawn, by kind and scenario, with the
        time they take. Also written to ``args.out`` with ``pairs.csv``, one
        row per pair, and ``contact-sheet.png``.

    Raises:
        SystemExit: If a configuration is missing or invalid, a chip asked for
            is not a training chip, or no pair is asked for.
    """
    if args.n_pairs < 1 or not 0 <= args.sheet_pairs <= args.n_pairs:
        raise SystemExit("satreg: need --n-pairs >= 1 and --sheet-pairs within it")
    config, series = _training(args)
    try:
        pairs_config = trainpairs.load_pairs_config(args.pairs_config)
        ranges = trainpairs.load_ranges(args.degradations_config)
        overrides = {
            key: value
            for key in ("cross_date", "seed")
            if (value := getattr(args, key)) is not None
        }
        pairs_config = dataclasses.replace(pairs_config, **overrides)
        chips = trainpairs.load_training_series(
            config, series, args.data_dir, args.chips
        )
        generator = trainpairs.PairGenerator(chips, pairs_config, ranges)
    except FileNotFoundError as exc:
        raise SystemExit(
            f"satreg: no configuration at {exc.filename} (run from the repository "
            "root or pass --pairs-config and --degradations-config)"
        ) from None
    except ValueError as exc:
        raise SystemExit(f"satreg: {exc}") from None

    pairs, rows = trainpairs.timed_pairs(generator, range(args.n_pairs))
    context = environment()
    table = (
        f"{args.n_pairs} training pairs of {pairs_config.size} px from "
        f"{len(chips)} chips ({', '.join(chips)}), seed {pairs_config.seed}, "
        f"cross-date share {pairs_config.cross_date:g}.\n\n"
        + trainpairs.to_markdown(rows)
        + f"\nMeasured on {describe(context)}.\n"
    )
    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(rows, args.out / "pairs.csv")
    if args.sheet_pairs:
        sheet = args.out / "contact-sheet.png"
        trainpairs.contact_sheet(pairs[: args.sheet_pairs], sheet)
        table += f"\nContact sheet of the first {args.sheet_pairs} pairs: {sheet}\n"
    (args.out / "summary.md").write_text(table)
    context["pairs"] = dataclasses.asdict(pairs_config)
    context["ranges"] = dataclasses.asdict(ranges)
    context_json = json.dumps(context, indent=2, default=str)
    (args.out / "context.json").write_text(context_json + "\n")
    return table


def validate(args: argparse.Namespace) -> str:
    """Score methods on the validation set and write its tables.

    The pairs are cut from the validation chips, simulated and scored by the
    code ``benchmark`` runs: a validation row reads like a row of the final
    table. No benchmark chip and no held-out site is read.

    Args:
        args: Parsed ``validate`` arguments.

    Returns:
        The table over every chip, the table by chip and, for the full set, how
        light sets compare with it, as markdown.

    Raises:
        SystemExit: If a configuration is missing or invalid, or a chip asked
            for is not a validation chip.
    """
    training, series = _training(args)
    config = _benchmark_config(args)
    out = args.out
    if args.light:
        if not 0 < args.light_pairs <= args.pairs:
            raise SystemExit("satreg: need --light-pairs between 1 and --pairs")
        config = dataclasses.replace(config, n_pairs=args.light_pairs)
        # The run's context records where the light set went, not the full one.
        out = args.out = out.with_name(out.name + "-light")
    degradations = degradation_presets(args)
    try:
        anchors = validation.load_validation_chips(
            training, series, args.data_dir, args.chips
        )
    except ValueError as exc:
        raise SystemExit(f"satreg: {exc}") from None
    methods = configured_methods(args)

    results, context, footnote = _score(
        args,
        config,
        degradations,
        {name: anchor.image for name, anchor in anchors.items()},
        {name: anchor.georef for name, anchor in anchors.items()},
        {},
        methods,
        [],
    )
    context["validation"] = {
        "chips": {name: anchor.item_id for name, anchor in anchors.items()},
        "pairs_per_cell": config.n_pairs,
        "light": args.light,
    }
    summary = summarize(results)
    pooled = validation.pooled(results)
    table = (
        f"{'Light validation' if args.light else 'Validation'} set: "
        f"{config.n_pairs} pairs per chip, scenario and preset, seed {config.seed}, "
        f"cut from the validation chips {', '.join(anchors)}."
        + (
            f" These are the first {config.n_pairs} pairs of every cell of the "
            f"full set, which has {args.pairs}."
            if args.light
            else ""
        )
        + "\n\nOver every chip:\n\n"
        + to_markdown(pooled)
        + "\nBy chip:\n\n"
        + to_markdown(summary)
        + footnote
    )
    subsets = (
        [] if args.light else validation.subset_tracking(results, args.subset_sizes)
    )
    if subsets:
        table += (
            "\nLight sets, the first pairs of every cell, next to the full set:\n\n"
            + validation.subsets_markdown(subsets)
            + "\nOver every chip and scenario. EPE is the mean error over "
            "non-failed pairs; gap is the mean difference of error with "
            f"{next(iter(methods))} over the pairs neither fails. Spread is the "
            f"standard deviation of the figure over {validation.SUBSET_DRAWS} "
            "random sets of as many pair indices: how far a light set of that "
            "size strays from the full one.\n"
        )

    write_csv(results, out / "pairs.csv")
    write_csv(summary, out / "summary.csv")
    write_csv(pooled, out / "pooled.csv")
    if subsets:
        write_csv(subsets, out / "subsets.csv")
    (out / "summary.md").write_text(table)
    _write_context(context, out)
    return table


def validate_cycle(args: argparse.Namespace) -> str:
    """Score closure on the real triplets of the training and validation chips.

    It is the closure ``cycle`` scores, on other chips: those of the train
    config. No benchmark chip and no held-out site is read.

    Args:
        args: Parsed ``validate-cycle`` arguments.

    Returns:
        The closure table by role, the one by chip and the displacements table,
        as markdown.

    Raises:
        SystemExit: If a configuration is missing or invalid, or a chip asked
            for is not a chip of the train config.
    """
    training, series = _training(args)
    methods = configured_methods(args)
    config = BenchmarkConfig(
        n_pairs=0,
        size=cycle.WINDOW_PX,
        failure_threshold=args.failure_threshold,
        warmup=args.warmup,
        repeats=args.repeats,
    )
    try:
        loaded = validation.load_closure_series(
            training, series, args.data_dir, args.chips
        )
    except ValueError as exc:
        raise SystemExit(f"satreg: {exc}") from None
    roles = {name: role for name, (role, _) in loaded.items()}
    legs, rows, run_seconds = _closure(
        {name: dates for name, (_, dates) in loaded.items()}, methods, config, {}
    )

    summary = cycle.summarize(rows)
    by_role = validation.closure_by_role(rows, roles)
    context, meters = _run_context(args, config, methods, run_seconds, [])
    context["validation"] = {"chips": roles}
    chips = {
        validation.ROLE_LABELS[role]: ", ".join(n for n in roles if roles[n] == role)
        for role in dict.fromkeys(roles.values())
    }
    table = (
        "Closure on real triplets, every triplet and window of a role's chips "
        "together:\n\n"
        + cycle.to_markdown(by_role)
        + "\n"
        + " ".join(f"{label.capitalize()}: {names}." for label, names in chips.items())
        + " Choices are made on the validation chips; the training chips are the "
        "ones a fine-tuned model has seen, and are reported, not chosen on. "
        + _closure_note(config, meters, context, simulated=False)
        + "\nBy chip and triplet:\n\n"
        + cycle.to_markdown(summary)
        + "\n"
        + _motion_note(legs, series, simulated=False)
    )

    write_csv(legs, args.out / "legs.csv")
    write_csv(rows, args.out / "triplets.csv")
    write_csv(summary, args.out / "summary.csv")
    write_csv(by_role, args.out / "by_role.csv")
    (args.out / "summary.md").write_text(table)
    _write_context(context, args.out)
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
    elif args.command == "cycle":
        print(cycle_consistency(args), end="")
    elif args.command == "false-change":
        print(false_change(args), end="")
    elif args.command == "fetch-train":
        print(fetch_train(args), end="")
    elif args.command == "train-pairs":
        print(train_pairs(args), end="")
    elif args.command == "validate":
        print(validate(args), end="")
    elif args.command == "validate-cycle":
        print(validate_cycle(args), end="")

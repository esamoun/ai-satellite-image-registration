"""Command-line entry point: ``satreg fetch``, ``satreg benchmark``, ``satreg
merge``, ``satreg real-pairs``, ``satreg check-presets``, ``satreg cycle``,
``satreg false-change``, ``satreg fetch-train``, ``satreg train-pairs``,
``satreg train``, ``satreg validate``, ``satreg validate-cycle``, ``satreg
ablation``, ``satreg small``, ``satreg fetch-weights``, ``satreg
export-weights``, ``satreg export``, ``satreg footprint``, ``satreg curve``,
``satreg final`` and ``satreg register``."""

import argparse
import dataclasses
import json
import logging
import tomllib
from collections.abc import Sequence
from pathlib import Path
from time import perf_counter

import numpy as np

from . import (
    ablation,
    curve,
    cycle,
    falsechange,
    final,
    footprint,
    onnxexport,
    quantize,
    register,
    small,
    trainchips,
    trainpairs,
    trainval,
    validation,
)
from . import train as training
from . import weights as published
from .benchmark import (
    SCENARIOS,
    BenchmarkConfig,
    PairResult,
    method_device,
    run_benchmark,
    simulated_pairs,
)
from .compute import (
    code_version,
    describe,
    environment,
    file_sha256,
    process_peak_rss_mib,
)
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
    RegistrationFailure,
    cost_meter,
    default_methods,
    load_methods,
    missing_dependencies,
)
from .methods.deep import DEVICES, check_available, missing_modules
from .methods.raft import Raft
from .methods.raft_onnx import RaftOnnx
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
DEFAULT_RUN_CONFIG = Path("configs/train-overfit.toml")
DEFAULT_VALIDATION_CONFIG = Path("configs/validation.toml")
DEFAULT_TRAIN_OUT = Path("outputs/train")
DEFAULT_ABLATION_OUT = Path("outputs/ablation")
DEFAULT_SMALL_OUT = Path("outputs/small")
DEFAULT_RELEASE_OUT = Path("outputs/release")
DEFAULT_ONNX_OUT = Path("outputs/onnx")
DEFAULT_CURVE_OUT = Path("outputs/curve")

# The pretrained model and the two variants of the ablation, the same-date one
# first (configs/methods.toml), and where `make ablation` scores the three,
# under the directory the ablation is written to.
ABLATION_BASELINE = "raft"
ABLATION_VARIANTS = ("raft_ft_same_date", "raft_ft_cross_date")
ABLATION_VALIDATION = "validation"
ABLATION_CLOSURE = "validation-cycle"
# Options those two runs may be given apart from their run configuration: which
# methods are scored, on what device and where to. The others say what the
# methods are scored on.
ABLATION_FREE = ("methods", "device", "out")

# The four methods `satreg small` reads (configs/methods.toml): RAFT small
# fine-tuned and pretrained, RAFT large fine-tuned (the retained variant of the
# ablation) and pretrained. `make small` scores them where `make ablation`
# scores its three, under the directory the reading is written to.
SMALL_METHOD = "raft_small_ft_cross_date"
SMALL_PRETRAINED = "raft_small"
SMALL_LARGE = "raft_ft_cross_date"
SMALL_LARGE_PRETRAINED = "raft"

# The four models `satreg export` writes to ONNX unless told otherwise: RAFT
# large and small, pretrained and with the published fine-tuned weights
# (configs/methods.toml).
EXPORT_METHODS = ("raft", "raft_small", "raft_ft", "raft_small_ft")

# Where `make curve` scores the points of the cost curve, under the directory
# the curve is written to: the PyTorch methods on the full validation set, the
# ONNX Runtime methods then the PyTorch ones on the light set and on the CPU,
# and each method's memory footprint. A run of the PyTorch methods on the light
# set and on a GPU is read from the last one if it is there.
CURVE_FULL = "validation"
CURVE_COST = "onnx-light"
CURVE_TORCH = "torch-light"
CURVE_FOOTPRINT = "footprint"
CURVE_GPU = "gpu-light"
# The same two runs when `satreg benchmark` scored them (`satreg curve
# --benchmark`): the pairs are the benchmark's, and the PyTorch run is also the
# one the refinement counts are read on.
CURVE_BENCHMARK_COST = "onnx"
CURVE_BENCHMARK_TORCH = "torch"

# The final evaluation (N3): where `make n3` writes the merged table, the
# closure run and the reading, and the published weights the two fine-tuned
# methods must have run.
DEFAULT_FINAL_TABLE = Path("outputs/n3")
DEFAULT_FINAL_CLOSURE = Path("outputs/n3-cycle")
DEFAULT_FINAL_OUT = Path("outputs/n3-final")
FINAL_WEIGHTS = {"raft_ft": "raft_large_ft", "raft_small_ft": "raft_small_ft"}
# Options a rehearsal of the final evaluation may change besides
# ``ABLATION_FREE``: it runs on seen sites, with fewer pairs and timed calls.
REHEARSAL_FREE = ("sites", "pairs", "simulated_triplets", "repeats")

# Where the int8 files are read: their scores next to the float files', and in
# directories of it the table of the files and their memory.
DEFAULT_QUANTIZATION_OUT = Path("outputs/quantization")
QUANTIZATION_FILES = "files"
QUANTIZATION_FOOTPRINT = "footprint"

# Commands a run configuration file can set, and the table each one reads.
RUN_TABLES = {
    "benchmark": "benchmark",
    "cycle": "cycle",
    "false-change": "false_change",
    "validate": "validate",
    "validate-cycle": "validate_cycle",
    "quantize": "quantize",
    "int8": "int8",
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
    changes.add_argument(
        "--real",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="run the real pairs of each site, which needs its land cover "
        "(--no-real: simulated pairs only)",
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

    tuning = commands.add_parser(
        "train",
        help="fine-tune RAFT on training pairs and write a checkpoint the "
        "local fine-tuned methods load",
    )
    tuning.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_RUN_CONFIG,
        help="TOML file whose [train] table sets the run and whose [pairs] table "
        "says what its pairs are made of",
    )
    tuning.add_argument(
        "--degradations-config",
        type=Path,
        default=DEFAULT_DEGRADATIONS_CONFIG,
        help="TOML file whose [training] table gives the degradation ranges",
    )
    _add_training_arguments(
        tuning,
        "training chip to cut pairs from, repeatable (default: every training chip)",
    )
    tuning.add_argument(
        "--model",
        choices=sorted(training.METHOD_NAMES),
        help="model to train (default: the config's)",
    )
    tuning.add_argument(
        "--device", choices=DEVICES, help="device to train on (default: the config's)"
    )
    tuning.add_argument(
        "--workers",
        type=int,
        help="processes that prepare the pairs ahead of the loop (default: the "
        "config's)",
    )
    tuning.add_argument(
        "--validation-config",
        type=Path,
        default=DEFAULT_VALIDATION_CONFIG,
        help="TOML file whose [validate] table declares the validation set; a run "
        "with validate_every scores its light set, on the chips of --data-dir",
    )
    tuning.add_argument(
        "--max-minutes",
        type=float,
        metavar="MINUTES",
        help="stop at the first step that ends after this long, leaving a "
        "checkpoint, before the session's own limit cuts the run; --resume goes "
        "on from there",
    )
    tuning.add_argument(
        "--resume",
        action="store_true",
        help="go on from the checkpoint in --out instead of starting a run",
    )
    tuning.add_argument(
        "--stop-at",
        type=int,
        metavar="STEP",
        help="stop at this step, short of the run's last, as a session that ends "
        "does; --resume goes on from there",
    )
    tuning.add_argument(
        "--out",
        type=Path,
        help="where the checkpoint, the log and the run's description go (default: "
        f"{DEFAULT_TRAIN_OUT}/NAME, NAME being the fine-tuned method of the model, "
        "raft_ft or raft_small_ft; the methods raft_ft_local and "
        "raft_small_ft_local load the checkpoint from there)",
    )

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
    reading = commands.add_parser(
        "ablation",
        help="read the two fine-tuned variants of the ablation next to the "
        "pretrained model, from the tables validate and validate-cycle wrote "
        "for the three, and apply the rule that chooses between them",
    )
    reading.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_ABLATION_OUT,
        help="directory of the ablation: the tables are read from its "
        f"{ABLATION_VALIDATION}/ and {ABLATION_CLOSURE}/, where make ablation "
        "scores the three methods, and the report is written to it",
    )
    reading_small = commands.add_parser(
        "small",
        help="read the fine-tuned RAFT small next to the pretrained one and to "
        "RAFT large, from the tables validate and validate-cycle wrote for the "
        "four, and say whether the training was a gain, no gain or worse",
    )
    reading_small.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_SMALL_OUT,
        help="directory of the reading: the tables are read from its "
        f"{ABLATION_VALIDATION}/ and {ABLATION_CLOSURE}/, where make small "
        "scores the four methods, and the report is written to it",
    )
    fetching = commands.add_parser(
        "fetch-weights",
        help="download the published fine-tuned weights and their ONNX exports "
        "to PyTorch's cache and check each file against the SHA-256 pinned in "
        "the code",
    )
    fetching.add_argument(
        "names",
        nargs="*",
        metavar="NAME",
        help="files to fetch, fine-tuned weights or their ONNX exports (default: "
        f"all of {', '.join([*published.RELEASED, *published.RELEASED_ONNX])})",
    )
    fetching.add_argument(
        "--from",
        dest="source",
        type=Path,
        metavar="DIR",
        help="take the files from this directory instead of the release, with "
        "the same check: what export-weights wrote, or a mounted dataset",
    )
    exporting = commands.add_parser(
        "export-weights",
        help="copy the kept weights of the retained trainings to the files a "
        "release publishes, with a description of each, without publishing",
    )
    exporting.add_argument(
        "--runs",
        type=Path,
        default=DEFAULT_TRAIN_OUT,
        help="directory of the trainings, each with its best.pt",
    )
    exporting.add_argument(
        "--onnx",
        type=Path,
        default=DEFAULT_ONNX_OUT,
        help="directory of the ONNX exports, as satreg export wrote them",
    )
    exporting.add_argument("--out", type=Path, default=DEFAULT_RELEASE_OUT)
    to_onnx = commands.add_parser(
        "export",
        help="write RAFT methods to ONNX files, one per method and refinement "
        "count, and check each against PyTorch on one pair",
    )
    to_onnx.add_argument(
        "--methods",
        nargs="+",
        default=list(EXPORT_METHODS),
        metavar="METHOD",
        help="RAFT methods of the methods' configuration to export: their "
        "model and weights are written, not their refinement count",
    )
    to_onnx.add_argument(
        "--refinements",
        nargs="+",
        type=int,
        default=list(onnxexport.REFINEMENTS),
        metavar="N",
        help="refinement counts, one file each: the loop is unrolled in the file",
    )
    to_onnx.add_argument("--methods-config", type=Path, default=DEFAULT_METHODS_CONFIG)
    to_onnx.add_argument("--out", type=Path, default=DEFAULT_ONNX_OUT)
    quantizing = commands.add_parser(
        "quantize",
        help="write int8 copies of exported RAFT files: static ones, whose "
        "scales are set on pairs of the validation set, and dynamic ones",
    )
    _add_config_argument(quantizing, "quantize")
    _add_training_arguments(
        quantizing,
        "validation chip to cut calibration pairs from, repeatable (default: "
        "every validation chip)",
    )
    _add_drawing_arguments(quantizing, defaults)
    quantizing.add_argument(
        "--static",
        nargs="+",
        default=[],
        metavar="FILE",
        help="exports to write a static int8 copy of, by name without suffix",
    )
    quantizing.add_argument(
        "--dynamic",
        nargs="+",
        default=[],
        metavar="FILE",
        help="exports to write a dynamic int8 copy of",
    )
    quantizing.add_argument(
        "--calibration-pair",
        type=int,
        default=quantize.CALIBRATION_PAIR,
        help="index, in every chip, scenario and preset of the validation set, "
        "of the pair the static copies are calibrated on",
    )
    quantizing.add_argument(
        "--onnx",
        type=Path,
        default=DEFAULT_ONNX_OUT,
        help="directory of the exports, as satreg export wrote them; the int8 "
        "copies are written next to them",
    )
    quantizing.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_QUANTIZATION_OUT / QUANTIZATION_FILES,
        help="directory the table of the copies and the context are written to",
    )
    reading_int8 = commands.add_parser(
        "int8",
        help="score int8 ONNX methods next to the float method each was made "
        "from, on the first pairs of every cell of the validation set: error, "
        "failures, time, and how far the flow moved",
    )
    _add_config_argument(reading_int8, "int8")
    _add_training_arguments(
        reading_int8,
        "validation chip to cut pairs from, repeatable (default: every "
        "validation chip)",
    )
    _add_scoring_arguments(reading_int8, defaults)
    reading_int8.add_argument(
        "--footprints",
        type=Path,
        help="footprints.csv of satreg footprint for these methods, for the "
        f"memory column (default: {QUANTIZATION_FOOTPRINT}/footprints.csv "
        "under --out, if it is there)",
    )
    reading_int8.add_argument("--out", type=Path, default=DEFAULT_QUANTIZATION_OUT)
    footprinting = commands.add_parser(
        "footprint",
        help="read what calling each method adds to the memory of a process "
        "of its own, the figure the cost curve gives for memory",
    )
    footprinting.add_argument(
        "--methods", nargs="+", required=True, metavar="METHOD", help="methods to read"
    )
    footprinting.add_argument(
        "--methods-config", type=Path, default=DEFAULT_METHODS_CONFIG
    )
    footprinting.add_argument(
        "--size", type=int, default=256, help="side of the pair, in px"
    )
    footprinting.add_argument(
        "--calls",
        type=int,
        default=footprint.CALLS,
        help="calls each method makes on the pair, in each process",
    )
    footprinting.add_argument(
        "--processes",
        type=int,
        default=footprint.PROCESSES,
        help="new processes each method is read in; the median reading is kept",
    )
    footprinting.add_argument(
        "--out", type=Path, default=DEFAULT_CURVE_OUT / CURVE_FOOTPRINT
    )
    reading_curve = commands.add_parser(
        "curve",
        help="read the cost curve of RAFT, large and small, pretrained and "
        "fine-tuned, by refinement count, from the tables validate and "
        "footprint wrote",
    )
    reading_curve.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_CURVE_OUT,
        help="directory of the curve: the tables are read from its "
        f"{CURVE_FULL}/, {CURVE_COST}/, {CURVE_TORCH}/ and {CURVE_FOOTPRINT}/, "
        "where make curve writes them, and the curve is written to it",
    )
    reading_curve.add_argument(
        "--methods-config", type=Path, default=DEFAULT_METHODS_CONFIG
    )
    reading_curve.add_argument(
        "--benchmark",
        action="store_true",
        help="read runs of satreg benchmark in place of runs of satreg validate: "
        f"the ONNX Runtime methods in {CURVE_BENCHMARK_COST}/ and the PyTorch "
        f"ones in {CURVE_BENCHMARK_TORCH}/ under --out, on the same pairs, "
        "where make n3-curve writes them",
    )
    reading_curve.add_argument(
        "--gpu",
        type=Path,
        metavar="RUN",
        help="directory of the run of the PyTorch methods on a GPU, on the same "
        f"pairs (default: {CURVE_GPU}/ under --out, if it is there and "
        "--benchmark is not given)",
    )
    reading_curve.add_argument(
        "--rehearsal",
        action="store_true",
        help="with --benchmark, read a rehearsal of the final evaluation: runs "
        "on seen sites, with fewer pairs than their configuration says",
    )
    reading_final = commands.add_parser(
        "final",
        help="read the final evaluation of N3: the criterion on the simulated "
        "pairs of the held-out sites, with its interval, and the closure of "
        "the real triplets, from the tables merge and cycle wrote",
    )
    reading_final.add_argument(
        "--table",
        type=Path,
        default=DEFAULT_FINAL_TABLE,
        help="directory of the merged table of the final evaluation",
    )
    reading_final.add_argument(
        "--closure",
        type=Path,
        default=DEFAULT_FINAL_CLOSURE,
        help="directory of its closure run",
    )
    reading_final.add_argument(
        "--rehearsal",
        nargs="+",
        metavar="SITE",
        help="rehearse the reading on tables of seen sites only, these sites "
        "standing in for the held-out ones: the report is not a result",
    )
    reading_final.add_argument(
        "--resamples",
        type=int,
        default=final.RESAMPLES,
        help="resamples of each interval of a difference of mean error",
    )
    reading_final.add_argument(
        "--seed", type=int, default=final.SEED, help="seed of the resamples"
    )
    reading_final.add_argument("--out", type=Path, default=DEFAULT_FINAL_OUT)
    registering = commands.add_parser(
        "register",
        help="register a pair of images you supply with the method you name, "
        "and write the displacement and the corrected moving image",
    )
    registering.add_argument(
        "reference", nargs="?", type=Path, metavar="REF", help="reference image"
    )
    registering.add_argument(
        "moving",
        nargs="?",
        type=Path,
        metavar="MOVING",
        help="moving image, of the same shape: both are GeoTIFF or PNG, and "
        f"at most {register.MAX_SIDE_PX} px a side",
    )
    registering.add_argument(
        "--method",
        metavar="NAME",
        help="method to run; there is no default, and without it the command "
        "lists the methods that can run here and stops",
    )
    registering.add_argument(
        "--out",
        type=Path,
        metavar="DIR",
        help=f"directory to write {register.DISPLACEMENT_FILE}, "
        f"{register.CORRECTED_FILE} and, for a dense displacement, "
        f"{register.FLOW_FILE} to; an earlier result there is replaced",
    )
    registering.add_argument(
        "--band",
        type=int,
        metavar="N",
        help="band to register in a file that has several, counted from 1",
    )
    registering.add_argument(
        "--window",
        nargs=3,
        type=int,
        metavar=("ROW", "COL", "SIZE"),
        help="register one square window cut from both images: its top-left "
        "pixel and its side, in px",
    )
    registering.add_argument(
        "--methods-config", type=Path, default=DEFAULT_METHODS_CONFIG
    )
    if run_config:
        {
            "benchmark": bench,
            "cycle": closing,
            "false-change": changes,
            "validate": validating,
            "validate-cycle": validating_closure,
            "quantize": quantizing,
            "int8": reading_int8,
        }[command].set_defaults(**run_config)
    return parser


def _add_drawing_arguments(
    parser: argparse.ArgumentParser, defaults: BenchmarkConfig
) -> None:
    """Add the options that say how simulated pairs are drawn."""
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


def _add_scoring_arguments(
    parser: argparse.ArgumentParser, defaults: BenchmarkConfig
) -> None:
    """Add the options of a command that scores methods on simulated pairs."""
    _add_drawing_arguments(parser, defaults)
    parser.add_argument("--pairs", type=int, default=defaults.n_pairs)
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
            ``[validate_cycle]``, ``[quantize]``, ``[int8]``). Its keys are that
            command's options by destination name (``max_shift`` for
            ``--max-shift``). Paths are read relative to the working directory,
            like the command-line options. The file's other tables are not read.
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
    # The train command reads its configuration file itself.
    if (
        command_line.command not in RUN_TABLES
        or getattr(command_line, "config", None) is None
    ):
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
        # A fine-tuned method without its weights would fail every pair.
        checkpoint = getattr(methods[name], "checkpoint", "")
        if checkpoint and not Path(checkpoint).is_file():
            raise SystemExit(
                f"satreg: method {name} needs its checkpoint at {checkpoint}, not "
                "there: train it with satreg train (see the README)"
            )
        file = getattr(methods[name], "file", "")
        if file and not Path(file).is_file():
            raise SystemExit(
                f"satreg: method {name} needs its ONNX file at {file}, not there: "
                "write it with satreg export (see the README)"
            )
        # The same for published weights that cannot be had: downloaded here,
        # once, if they are not in the cache.
        if release := getattr(methods[name], "release", ""):
            try:
                published.fetch(release)
            except (published.WeightsUnavailable, published.WeightsRefused) as exc:
                raise SystemExit(f"satreg: method {name}: {exc}") from None
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
    context["checkpoints"] = _checkpoints(methods)
    # Sites kept for the final evaluation, so a table that looked at them says so.
    context["held_out_sites"] = held_out
    # Every option the run used, whether from the command line, a run config or
    # a default, so the tables can be reproduced from this file alone.
    context["run"] = {k: v for k, v in sorted(vars(args).items()) if k != "command"}
    return context, meters


def _checkpoints(methods: dict[str, Method]) -> dict[str, dict[str, object]]:
    """Name the files the methods of a run took their model from, by hash.

    A checkpoint's path says which training it comes from and not which
    weights: a run that goes on rewrites the file. The hash does. Published
    files are named by their release and asset, not by where the cache is on
    the machine that ran. An ONNX file also says which model it holds.

    Args:
        methods: The methods that ran.

    Returns:
        Method name to the path, or the release and asset, and the SHA-256 of
        its file, for the methods that have one; and under ``holds``, for an
        ONNX file, the model, weights and refinements written in it.
    """
    recorded: dict[str, dict[str, object]] = {}
    for name, method in methods.items():
        path = getattr(method, "checkpoint", "") or getattr(method, "file", "")
        if path:
            recorded[name] = {"path": path, "sha256": file_sha256(Path(path))}
        elif release := getattr(method, "release", ""):
            weights = published.lookup(release)
            recorded[name] = {
                "release": weights.tag,
                "asset": weights.asset,
                "sha256": file_sha256(published.fetch(release)),
            }
        if isinstance(method, RaftOnnx):
            recorded[name]["holds"] = method.described()
    return recorded


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
        if args.real:
            cover = fetch_landcover(
                name, anchor.georef, anchor.image.shape, args.data_dir
            )
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
    context["checkpoints"] = _checkpoints(methods)
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


def _light_validation(
    args: argparse.Namespace,
    config: trainchips.TrainingConfig,
    series: SeriesConfig,
    run: training.TrainConfig,
) -> tuple[trainval.LightValidation, dict[str, object]]:
    """Draw the light validation set a training scores its network on.

    It is the set ``validate --light`` scores with the same validation config:
    same chips, pairs, presets and failure threshold. The chips are read from
    the training's data directory.

    Args:
        args: Parsed ``train`` arguments.
        config: The training chips configuration.
        series: Series configuration.
        run: The training run, for its refinements and its device.

    Returns:
        The set, and what the run's context says of it.

    Raises:
        SystemExit: If the validation config is missing or invalid.
        ValueError: If one of its chips is not a validation chip.
    """
    table = load_run_config(args.validation_config, "validate")
    options = _parser(table, "validate").parse_args(["validate"])
    scoring = dataclasses.replace(
        _benchmark_config(options), n_pairs=options.light_pairs
    )
    presets = degradation_presets(options)
    anchors = validation.load_validation_chips(
        config, series, args.data_dir, options.chips
    )
    images = {name: anchor.image for name, anchor in anchors.items()}
    light = trainval.LightValidation(
        images, scoring, presets, run.iterations, run.device
    )
    described = {
        "config": str(args.validation_config),
        "chips": {name: anchor.item_id for name, anchor in anchors.items()},
        "pairs_per_cell": scoring.n_pairs,
        "pairs": len(light.pairs),
        "presets": list(presets),
        "failure_threshold": scoring.failure_threshold,
        "every": run.validate_every,
    }
    return light, described


def train(args: argparse.Namespace) -> str:
    """Fine-tune RAFT on training pairs and write its checkpoint.

    Args:
        args: Parsed ``train`` arguments.

    Returns:
        A markdown summary of the session: the run, its loss by stretch of
        steps and where the checkpoint is. Also written to the output
        directory with ``log.csv``, one row per step, and ``context.json``,
        the run's configuration and the commit and machine of each session.

    Raises:
        SystemExit: If a configuration is missing or invalid, a chip asked for
            is not a training chip, the device is not available, or the
            checkpoint to start or resume from is not as expected.
    """
    config, series = _training(args)
    try:
        run = training.load_train_config(args.config)
        overrides = {
            key: value
            for key in ("model", "device", "workers")
            if (value := getattr(args, key)) is not None
        }
        run = dataclasses.replace(run, **overrides)
        pairs_config = trainpairs.load_pairs_config(args.config)
        ranges = trainpairs.load_ranges(args.degradations_config)
        chips = trainpairs.load_training_series(
            config, series, args.data_dir, args.chips
        )
        generator = trainpairs.PairGenerator(chips, pairs_config, ranges)
        light, validated = None, None
        if run.validate_every:
            light, validated = _light_validation(args, config, series, run)
    except FileNotFoundError as exc:
        raise SystemExit(
            f"satreg: no configuration at {exc.filename} (run from the repository "
            "root or pass --config and --degradations-config)"
        ) from None
    except ValueError as exc:
        raise SystemExit(f"satreg: {exc}") from None
    if missing := missing_modules():
        raise SystemExit(
            f"satreg: training needs {', '.join(missing)}, not installed "
            "(see the README)"
        )
    if args.stop_at is not None and args.stop_at < 1:
        raise SystemExit("satreg: need --stop-at >= 1")
    if args.max_minutes is not None and args.max_minutes <= 0:
        raise SystemExit("satreg: need --max-minutes > 0")
    budget = None if args.max_minutes is None else 60 * args.max_minutes

    out = args.out or DEFAULT_TRAIN_OUT / training.METHOD_NAMES[run.model]
    code = code_version() or {}
    described = {
        "pairs": dataclasses.asdict(pairs_config),
        "ranges": dataclasses.asdict(ranges),
        "chips": list(chips),
        "commit": code.get("commit"),
        "dirty": code.get("dirty"),
    }
    try:
        result = training.train(
            generator, run, out, described, args.resume, args.stop_at, light, budget
        )
    except (FileNotFoundError, FileExistsError, ValueError, RuntimeError) as exc:
        raise SystemExit(f"satreg: {exc}") from None
    # After the training: the GPU and PyTorch are described once it is loaded.
    context = environment()

    name = training.LOCAL_METHOD_NAMES[run.model]
    session = [r for r in result.log if r.step > result.first_step]
    seconds = sum(r.seconds for r in session)
    cycled = (
        f"the first {run.n_pairs} pairs, over and over" if run.n_pairs else "new pairs"
    )
    table = (
        f"RAFT {run.model} fine-tuned on {cycled}, of {pairs_config.size} px, from "
        f"{len(chips)} chips ({', '.join(chips)}): steps {result.first_step + 1} to "
        f"{result.last_step} of {run.steps}, batches of {run.batch_size}, on "
        f"{run.device}, in {seconds:.0f} s.\n\n" + training.log_markdown(result.log)
    )
    if result.epe_after is not None:

        def errors(values: list[float]) -> str:
            each = ", ".join(f"{v:.3f}" for v in values)
            return f"{np.nanmean(values):.4f} px (pair by pair: {each})"

        table += (
            f"\nMean end-point error on those {run.n_pairs} pairs, over the pixels "
            "of the loss mask, as at inference:\n\n"
        )
        if result.epe_before is not None:
            table += f"- pretrained weights: {errors(result.epe_before)}\n"
        table += f"- after step {result.last_step}: {errors(result.epe_after)}\n"
    speed = training.timing(session, run.batch_size)
    if speed is not None:
        memory = (
            ""
            if result.peak_mib is None
            else f" Peak GPU memory, weights included: {result.peak_mib:.0f} MiB."
        )
        table += (
            f"\nSpeed of this session, over {speed.steps} steps: "
            f"{speed.seconds_per_step:.3f} s per step (median), "
            f"{speed.pairs_per_second:.1f} pairs per second, "
            f"{100 * speed.pair_share:.0f} % of the time spent getting the pairs, "
            f"with {run.workers} worker process(es).{memory}\n"
        )
    kept = result.best
    if result.validations:
        seconds = np.mean([r.seconds for r in result.validations])
        table += (
            f"\nLight validation set ({validated['pairs']} pairs), every "
            f"{run.validate_every} steps; step 0 is the pretrained weights. The "
            "score is the mean error over every pair, a failed pair counting for "
            f"{validated['failure_threshold']:g} px; EPE is over non-failed pairs. "
            f"A validation took {seconds:.0f} s on average.\n\n"
            + trainval.to_markdown(result.validations)
        )
        if kept is not None:
            table += (
                f"\nKept: step {kept.step}, score {kept.score:.4f} px, in "
                f"{out / training.BEST}.\n"
            )
    table += (
        f"\nCheckpoint: {result.checkpoint}, which the method {name} loads if "
        f"that is its path in the methods config.\n"
        f"\nMeasured on {describe(context)}.\n"
    )
    (out / "summary.md").write_text(table)
    # One entry per session: the commit and the machine may change on resuming.
    context_path = out / "context.json"
    sessions = json.loads(context_path.read_text())["sessions"] if args.resume else []
    context["steps"] = [result.first_step, result.last_step]
    context["epe"] = {"before": result.epe_before, "after": result.epe_after}
    context["timing"] = None if speed is None else dataclasses.asdict(speed)
    context["peak_gpu_mib"] = result.peak_mib
    context["workers"] = run.workers
    if result.validations:
        described["validation"] = {
            **validated,
            "kept": None if kept is None else dataclasses.asdict(kept),
        }
    described = {"train": dataclasses.asdict(run), **described}
    _write_context({**described, "sessions": [*sessions, context]}, out)
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


def _as_configured(
    path: Path | str,
    context: dict[str, object],
    command: str,
    recipe: str,
    free: Sequence[str] = ABLATION_FREE,
) -> None:
    """Check that a run was given the options of its run configuration.

    Args:
        path: Directory of the run, for the messages.
        context: The run's context.
        command: The command that wrote it, one of ``RUN_TABLES``.
        recipe: The ``make`` target that scores the run.
        free: Options the run may have been given another value for.

    Raises:
        SystemExit: If the run was not run from a run configuration, or was
            given an option that is not the one of its configuration, other
            than ``free``: a run of fewer pairs is not the validation set.
    """
    run = context.get("run", {})
    if not run.get("config"):
        raise SystemExit(
            f"satreg: {path} was not run from a run configuration: run make "
            f"{recipe} (see the README)"
        )
    configured = load_run_config(Path(run["config"]), command)
    unlike = sorted(
        option
        for option, value in configured.items()
        if option not in free and run.get(option) != value
    )
    if unlike:
        raise SystemExit(
            f"satreg: {path} was not run as {run['config']} says: "
            f"{', '.join(unlike)} differ"
        )


def _scored_run(
    path: Path,
    table: str,
    command: str,
    recipe: str,
    free: Sequence[str] = ABLATION_FREE,
) -> tuple[Path, dict[str, object]]:
    """Find the per-item table and the context of a run a report reads.

    Args:
        path: Directory of the run.
        table: Its per-item table, ``pairs.csv`` or ``triplets.csv``.
        command: The command that wrote it, one of ``RUN_TABLES``.
        recipe: The ``make`` target that scores the run.
        free: Options the run may have been given another value for.

    Returns:
        The path of the table and the run's context.

    Raises:
        SystemExit: If the run is missing, or was not run as its run
            configuration says: see ``_as_configured``.
    """
    if not (path / table).is_file() or not (path / "context.json").is_file():
        raise SystemExit(
            f"satreg: no {table} and context.json in {path}: run make {recipe} "
            "(see the README)"
        )
    context = json.loads((path / "context.json").read_text())
    _as_configured(path, context, command, recipe, free)
    return path / table, context


def _scored_trainings(
    methods: Sequence[str],
    validated: Path,
    closed: Path,
    scored: dict[str, object],
    closure: dict[str, object],
) -> list[ablation.TrainingRun]:
    """Read the trainings whose kept weights two scored runs used.

    Args:
        methods: The fine-tuned methods.
        validated: Directory of the validation run.
        closed: Directory of the closure run.
        scored: The context of the validation run.
        closure: The context of the closure run.

    Returns:
        The training of each method, in the order given.

    Raises:
        ValueError: If a run names no weights for a method, the two runs did
            not score the same weights, or those are not a training's kept
            weights or no longer the ones on disk.
    """
    weights = scored.get("checkpoints", {})
    runs = []
    for method in methods:
        if method not in weights:
            raise ValueError(
                f"{validated} names no checkpoint for {method}: it is not a "
                "run of the methods read here"
            )
        # The file, not its path: the two runs may name it differently.
        again = closure.get("checkpoints", {}).get(method, {})
        if weights[method]["sha256"] != again.get("sha256"):
            raise ValueError(
                f"{validated} and {closed} did not score the same weights for {method}"
            )
        runs.append(
            ablation.read_training(
                method, Path(weights[method]["path"]), weights[method]["sha256"]
            )
        )
    return runs


def _read_context(
    args: argparse.Namespace,
    methods: Sequence[str],
    scored: dict[str, object],
    closure: dict[str, object],
) -> dict[str, object]:
    """Describe a report read from two scored runs, for its ``context.json``.

    Args:
        args: Parsed arguments of the command.
        methods: The fine-tuned methods read.
        scored: The context of the validation run.
        closure: The context of the closure run.

    Returns:
        The code, the options, the weights read and what the two runs recorded
        about themselves.
    """
    return {
        "code": code_version(),
        "run": {k: v for k, v in sorted(vars(args).items()) if k != "command"},
        "checkpoints": {m: scored["checkpoints"][m] for m in methods},
        # The code and the time of the two runs the tables come from.
        "read": {
            name: {"code": run.get("code"), "recorded_at": run.get("recorded_at")}
            for name, run in (("validation", scored), ("closure", closure))
        },
    }


def read_ablation(args: argparse.Namespace) -> str:
    """Read the ablation's two variants next to the pretrained model.

    Nothing is run: the pairs and triplets are those ``validate`` and
    ``validate-cycle`` scored for the three methods, and the trainings are read
    from the directories of the weights those runs used.

    Args:
        args: Parsed ``ablation`` arguments.

    Returns:
        The report, as markdown.

    Raises:
        SystemExit: If a run is missing, was not run as its configuration
            says, is not the full validation set or the closure of every chip
            of the trainings, the two runs did not score the same weights,
            those weights are no longer the ones on disk, or a run does not
            hold the three methods.
    """
    validated, closed = args.out / ABLATION_VALIDATION, args.out / ABLATION_CLOSURE
    pairs, scored = _scored_run(validated, "pairs.csv", "validate", "ablation")
    triplets, closure = _scored_run(
        closed, "triplets.csv", "validate-cycle", "ablation"
    )
    try:
        runs = _scored_trainings(ABLATION_VARIANTS, validated, closed, scored, closure)
        read = ablation.read(
            ablation.read_pairs(pairs),
            ablation.read_triplets(triplets),
            ablation.check_scored(scored, closure, runs),
            ABLATION_BASELINE,
            (runs[0], runs[1]),
        )
    except ValueError as exc:
        raise SystemExit(f"satreg: {exc}") from None

    table = (
        "The ablation: RAFT large fine-tuned on same-date pairs only "
        f"({read.variants[0]}) and on same-date and cross-date pairs "
        f"({read.variants[1]}), next to the pretrained model ({read.baseline}). "
        f"Validation set of `{validated}`, real triplets of `{closed}`. The rule "
        "that chooses is in docs/decisions.md, written before either training "
        "ran.\n\n" + ablation.to_markdown(read)
    )
    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(read.rows, args.out / "comparisons.csv")
    ablation.curves(read.runs, args.out / "curves.png")
    (args.out / "summary.md").write_text(table)
    context = {
        **_read_context(args, read.variants, scored, closure),
        # No choice if the rule is not applied; why is in `departures`.
        "departures": list(read.departures),
        "choice": None if read.choice is None else dataclasses.asdict(read.choice),
    }
    _write_context(context, args.out)
    return table


def read_small(args: argparse.Namespace) -> str:
    """Read the fine-tuned RAFT small next to the pretrained one and RAFT large.

    Nothing is run: the pairs and triplets are those ``validate`` and
    ``validate-cycle`` scored for the four methods, and the two trainings are
    read from the directories of the weights those runs used.

    Args:
        args: Parsed ``small`` arguments.

    Returns:
        The report, as markdown.

    Raises:
        SystemExit: If a run is missing, was not run as its configuration
            says, is not the full validation set or the closure of every chip
            of the trainings, the two runs did not score the same weights,
            those weights are no longer the ones on disk, or a run does not
            hold the four methods.
    """
    validated, closed = args.out / ABLATION_VALIDATION, args.out / ABLATION_CLOSURE
    pairs, scored = _scored_run(validated, "pairs.csv", "validate", "small")
    triplets, closure = _scored_run(closed, "triplets.csv", "validate-cycle", "small")
    trained = (SMALL_METHOD, SMALL_LARGE)
    try:
        runs = _scored_trainings(trained, validated, closed, scored, closure)
        read = small.read(
            ablation.read_pairs(pairs),
            ablation.read_triplets(triplets),
            ablation.check_scored(scored, closure, runs),
            SMALL_PRETRAINED,
            SMALL_LARGE_PRETRAINED,
            (runs[0], runs[1]),
        )
    except ValueError as exc:
        raise SystemExit(f"satreg: {exc}") from None

    table = (
        f"RAFT small fine-tuned ({read.method}) with the pairs and the recipe of "
        f"the retained RAFT large ({SMALL_LARGE}), next to the pretrained RAFT "
        f"small ({read.pretrained}) and to RAFT large, fine-tuned and pretrained "
        f"({read.large_pretrained}). Validation set of `{validated}`, real "
        f"triplets of `{closed}`. What a gain, no gain and worse are is in "
        "docs/decisions.md, written before the training ran.\n\n"
        + small.to_markdown(read)
    )
    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(read.rows, args.out / "comparisons.csv")
    ablation.curves(read.runs, args.out / "curves.png")
    (args.out / "summary.md").write_text(table)
    context = {
        **_read_context(args, trained, scored, closure),
        # No verdict for a run that is not the training; why is in `departures`.
        "departures": list(read.departures),
        "verdict": None if read.verdict is None else dataclasses.asdict(read.verdict),
    }
    _write_context(context, args.out)
    return table


def fetch_weights(args: argparse.Namespace) -> list[Path]:
    """Put the published weights and ONNX files in PyTorch's cache, checked.

    Args:
        args: Parsed ``fetch-weights`` arguments.

    Returns:
        The file of each name asked for, in the cache.

    Raises:
        SystemExit: If a name is not one of the published files, or a file
            cannot be had or is not the one the code pins.
    """
    try:
        return [
            published.fetch(name, args.source)
            for name in args.names or [*published.RELEASED, *published.RELEASED_ONNX]
        ]
    except (
        ValueError,
        published.WeightsUnavailable,
        published.WeightsRefused,
    ) as exc:
        raise SystemExit(f"satreg: {exc}") from None


def export_weights(args: argparse.Namespace) -> str:
    """Write the files of a release of the fine-tuned weights, unpublished.

    Args:
        args: Parsed ``export-weights`` arguments.

    Returns:
        The release's notes and the commands that publish it, as text. The
        notes are also written to the output directory, as ``notes.md``.

    Raises:
        SystemExit: If PyTorch is not installed, or a training's kept weights
            or an ONNX export are missing or are not the file the code pins.
    """
    if missing := missing_modules():
        raise SystemExit(
            f"satreg: export-weights needs {', '.join(missing)}, not installed "
            "(see the README)"
        )
    try:
        cards = [
            published.export(name, args.runs, args.out) for name in published.RELEASED
        ]
        onnx_cards = [
            published.export_onnx(name, args.onnx, args.out)
            for name in published.RELEASED_ONNX
        ]
    except (FileNotFoundError, ValueError, published.WeightsRefused) as exc:
        raise SystemExit(f"satreg: {exc}") from None
    notes = published.notes(cards, onnx_cards)
    (args.out / "notes.md").write_text(notes)
    # One release holds them all today; one set of commands per tag if that
    # changes. The ONNX files came after the weights: they are added to a
    # release that is there, whose notes are then replaced.
    commands = []
    for tag in dict.fromkeys(w.tag for w in published.RELEASED.values()):
        files = [
            str(args.out / name)
            for weights in published.RELEASED.values()
            if weights.tag == tag
            for name in (weights.asset, weights.card)
        ]
        exports = [
            str(args.out / exported.asset)
            for exported in published.RELEASED_ONNX.values()
            if exported.tag == tag
        ]
        notes_file = args.out / "notes.md"
        commands.append(
            f"    gh release create {tag} {' '.join(files + exports)} "
            f"--title {tag} --notes-file {notes_file}\n"
        )
        if exports:
            commands.append(
                "\nor, if the release is there without its ONNX files,\n\n"
                f"    gh release upload {tag} {' '.join(exports)}\n"
                f"    gh release edit {tag} --notes-file {notes_file}\n"
            )
    return (
        f"{notes}\nWritten to {args.out}. Nothing is published: the release is "
        "created by hand, with\n\n" + "".join(commands)
    )


def export_onnx(args: argparse.Namespace) -> str:
    """Write RAFT methods to ONNX files and check each against PyTorch.

    Args:
        args: Parsed ``export`` arguments.

    Returns:
        The files written, as a markdown table. It is also written to the
        output directory, with the files, their table as CSV and the context.

    Raises:
        SystemExit: If PyTorch, onnx or ONNX Runtime is not installed, a
            method is not a RAFT one, a refinement count is below one, or a
            file's flow is too far from PyTorch's.
    """
    if missing := [*missing_modules(), *onnxexport.missing_modules()]:
        raise SystemExit(
            f"satreg: export needs {', '.join(missing)}, not installed (see the README)"
        )
    if low := [count for count in args.refinements if count < 1]:
        raise SystemExit(f"satreg: need --refinements of at least 1, got {low[0]}")
    # The graph is traced on the CPU, the device its files run on.
    options = argparse.Namespace(
        methods=args.methods, methods_config=args.methods_config, device="cpu"
    )
    methods = configured_methods(options)
    if others := [name for name, m in methods.items() if not isinstance(m, Raft)]:
        raise SystemExit(
            f"satreg: export writes RAFT methods under PyTorch, not {', '.join(others)}"
        )
    rows = []
    try:
        for name, method in methods.items():
            for count in dict.fromkeys(args.refinements):
                rows.append(onnxexport.export_checked(method, name, count, args.out))
    except onnxexport.ParityError as exc:
        raise SystemExit(f"satreg: {exc}") from None
    table = (
        f"RAFT exported to ONNX (opset {onnxexport.OPSET}), one file per model, "
        "weights and refinement count, the image size left free. Parity is the "
        "largest difference between the file's flow under ONNX Runtime and "
        f"PyTorch's on one {onnxexport.PARITY_SIDE} px pair, on the CPU; a file "
        f"over {onnxexport.PARITY_TOLERANCE_PX:g} px is refused.\n\n"
        + onnxexport.to_markdown(rows)
    )
    write_csv(rows, args.out / "exports.csv")
    (args.out / "summary.md").write_text(table)
    context = environment()
    context["run"] = {k: v for k, v in sorted(vars(args).items()) if k != "command"}
    context["checkpoints"] = _checkpoints(methods)
    context["export"] = {
        "opset": onnxexport.OPSET,
        "trace_side": onnxexport.TRACE_SIDE,
        "parity_tolerance_px": onnxexport.PARITY_TOLERANCE_PX,
        "parity_side": onnxexport.PARITY_SIDE,
    }
    _write_context(context, args.out)
    return table


def _validation_chips(args: argparse.Namespace) -> dict[str, Acquisition]:
    """Load the validation chips a command cuts its pairs from, and no other."""
    training, series = _training(args)
    try:
        return validation.load_validation_chips(
            training, series, args.data_dir, args.chips
        )
    except ValueError as exc:
        raise SystemExit(f"satreg: {exc}") from None


def quantize_files(args: argparse.Namespace) -> str:
    """Write int8 copies of exported RAFT files.

    The static copies are calibrated on one pair of every chip, scenario and
    preset of the validation set. No benchmark chip and no held-out site is
    read.

    Args:
        args: Parsed ``quantize`` arguments.

    Returns:
        The files written, as a markdown table. It is also written to the
        output directory, with the table as CSV and the context.

    Raises:
        SystemExit: If onnx or ONNX Runtime is not installed, no file is
            named, an export is missing, or a configuration is missing or
            invalid.
    """
    if missing := quantize.missing_modules():
        raise SystemExit(
            f"satreg: quantize needs {', '.join(missing)}, not installed "
            "(see the README)"
        )
    if not args.static and not args.dynamic:
        raise SystemExit("satreg: quantize needs --static or --dynamic files")
    if args.calibration_pair < 0:
        raise SystemExit("satreg: need a --calibration-pair of at least 0")
    wanted = [
        (name, kind)
        for kind, names in (
            (quantize.STATIC, args.static),
            (quantize.DYNAMIC, args.dynamic),
        )
        for name in dict.fromkeys(names)
    ]
    for name, _ in wanted:
        if not (args.onnx / f"{name}.onnx").is_file():
            raise SystemExit(
                f"satreg: no export at {args.onnx / f'{name}.onnx'}: write it "
                "with satreg export (see the README)"
            )
    pairs, anchors = [], {}
    if args.static:
        anchors = _validation_chips(args)
        # Only how the pairs are drawn is read: nothing is timed or scored.
        drawing = argparse.Namespace(
            **vars(args), pairs=1, failure_threshold=FAILURE_EPE_PX, warmup=0, repeats=1
        )
        pairs = quantize.calibration_pairs(
            {name: anchor.image for name, anchor in anchors.items()},
            _benchmark_config(drawing),
            degradation_presets(args),
            args.calibration_pair,
        )
    rows = [
        quantize.quantize(
            args.onnx / f"{name}.onnx", kind, args.onnx, pairs, args.calibration_pair
        )
        for name, kind in wanted
    ]
    table = (
        "Exported RAFT files copied to 8-bit integers, written next to them. A "
        "static copy computes every convolution on integers, with one scale "
        "per output channel, but the ones that read the flow or write its "
        "update and its upsampling weights"
        + (
            f"; its scales are set by {quantize.CALIBRATION_METHOD} on "
            f"{len(pairs)} pairs, pair {args.calibration_pair} of every chip, "
            f"scenario and preset of the validation set ({', '.join(anchors)})"
            if pairs
            else ""
        )
        + ". A dynamic copy stores the weights of its convolutions as integers "
        "and works out the other scales at each call. The correlation lookup, "
        "`GridSample`, has no integer version in ONNX Runtime and stays in "
        "float in both.\n\n" + quantize.files_markdown(rows)
    )
    write_csv(rows, args.out / "files.csv")
    (args.out / "summary.md").write_text(table)
    context = environment()
    context["run"] = {k: v for k, v in sorted(vars(args).items()) if k != "command"}
    context["calibration"] = {
        "method": quantize.CALIBRATION_METHOD,
        "pairs": len(pairs),
        "pair_index": args.calibration_pair,
        "chips": {name: anchor.item_id for name, anchor in anchors.items()},
        "float_convolutions": list(quantize.FLOW_EDGES),
    }
    _write_context(context, args.out)
    return table


def read_int8(args: argparse.Namespace) -> str:
    """Score int8 ONNX methods next to the float method each was made from.

    The pairs are the first of every cell of the validation set, drawn and
    scored as ``validate`` does. Each int8 method runs right after its float
    twin on every pair: their times are read in the same minute, on the same
    machine in the same state.

    Args:
        args: Parsed ``int8`` arguments.

    Returns:
        The reading, as markdown. It is also written to the output directory,
        with its pairs and its lines as CSV and the context.

    Raises:
        SystemExit: If a method is not an int8 ONNX method with a float twin
            in the methods' configuration, a file was calibrated on a pair
            the reading would score, or a configuration is missing or invalid.
    """
    names = list(dict.fromkeys(args.methods))
    if others := [name for name in names if quantize.kind_of(name) == quantize.FLOAT]:
        raise SystemExit(
            f"satreg: int8 reads int8 methods, named after their float twin "
            f"with {' or '.join(quantize.SUFFIXES.values())}: not {others[0]}"
        )
    # Each float twin once, before its copies.
    ordered = list(
        dict.fromkeys(
            method for name in names for method in (quantize.float_twin(name), name)
        )
    )
    options = argparse.Namespace(
        methods=ordered, methods_config=args.methods_config, device=None
    )
    methods = configured_methods(options)
    if others := [name for name, m in methods.items() if not isinstance(m, RaftOnnx)]:
        raise SystemExit(f"satreg: int8 reads ONNX methods, not {', '.join(others)}")
    for name in names:
        calibrated = methods[name].described().get("calibration_pair_index")
        if calibrated is not None and int(calibrated) < args.pairs:
            raise SystemExit(
                f"satreg: {name} was calibrated on pair {calibrated} of every "
                f"cell, which --pairs {args.pairs} would score"
            )
    anchors = _validation_chips(args)
    config = _benchmark_config(args)
    degradations = degradation_presets(args)
    started = perf_counter()
    rows = quantize.read_pairs(
        methods,
        simulated_pairs(
            {name: anchor.image for name, anchor in anchors.items()},
            config,
            degradations,
        ),
        config,
    )
    run_seconds = perf_counter() - started
    context, _ = _run_context(args, config, methods, run_seconds, [])
    footprints = args.footprints or (
        args.out / QUANTIZATION_FOOTPRINT / "footprints.csv"
    )
    memory = {}
    if footprints.is_file():
        memory = {
            name: read.rise_mib for name, read in footprint.read(footprints).items()
        }
    elif args.footprints:
        raise SystemExit(f"satreg: no footprints at {footprints}")
    megabytes = {}
    for name, method in methods.items():
        path = method.file or published.fetch(method.release)
        megabytes[name] = Path(path).stat().st_size / 1e6
    readings = quantize.summarize(rows, megabytes, memory)
    table = (
        f"Int8 copies of exported RAFT files next to the float file each was "
        f"made from, on the first {config.n_pairs} pairs of every chip, scenario "
        f"and preset of the validation set ({', '.join(anchors)}), seed "
        f"{config.seed}: {readings[0].pairs} pairs.\n\n"
        + quantize.to_markdown(readings)
        + "\nEPE is the mean end-point error over the pairs not failed. Time "
        "is the median over the pairs; its share of float is that time over "
        "the float file's. Flow moved is the distance between the flow of "
        "the int8 file and of its float file, averaged over the valid pixels "
        "of a pair, then over the pairs; the worst pair is the one where it is "
        "largest."
        + (
            " Memory is what calling the method adds to a process of its own "
            "(`satreg footprint`)."
            if memory
            else ""
        )
        + "\n\nBy preset:\n\n"
        + quantize.by_degradation(rows)
        + f"\nMeasured on {describe(context)}, ONNX Runtime on the CPU. On every "
        "pair each float file runs, then its int8 copies: the times of a line "
        "and of its float file are read seconds apart. A pair's time is the "
        f"median of {config.repeats} call(s), after {config.warmup} warm-up "
        "call(s) per method. Details in `context.json`.\n"
    )
    write_csv(rows, args.out / "pairs.csv")
    write_csv(readings, args.out / "summary.csv")
    (args.out / "summary.md").write_text(table)
    context["validation"] = {
        "chips": {name: anchor.item_id for name, anchor in anchors.items()},
        "pairs_per_cell": config.n_pairs,
    }
    context["footprints"] = str(footprints) if memory else None
    context["megabytes"] = megabytes
    _write_context(context, args.out)
    return table


def read_footprints(args: argparse.Namespace) -> str:
    """Read what each method adds to the memory of a process of its own.

    Args:
        args: Parsed ``footprint`` arguments.

    Returns:
        The footprints, as a markdown table. It is also written to the output
        directory, with the footprints as CSV and the context.

    Raises:
        SystemExit: If a method is unknown or cannot run, or the platform has
            no resident high-water mark to read.
    """
    # The methods run on the device their configuration names, the CPU.
    options = argparse.Namespace(
        methods=args.methods, methods_config=args.methods_config, device=None
    )
    methods = configured_methods(options)
    try:
        rows = footprint.footprints(
            args.methods, args.methods_config, args.size, args.calls, args.processes
        )
    except ValueError as exc:
        raise SystemExit(f"satreg: {exc}") from None
    table = (
        f"What calling each method {args.calls} times on one {args.size} px pair "
        "adds to the memory of a process that does nothing else: the rise of "
        "its resident high-water mark above the baseline, the mark with the "
        "method's runtime imported and the pair built. A lower bound on what "
        "the method touched, weights included, and not the memory of one "
        f"call. Each method is read in {args.processes} new processes: its line "
        "is the reading whose rise is the median, with the lowest and the "
        "highest rise beside it.\n\n" + footprint.to_markdown(rows)
    )
    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(rows, args.out / "footprints.csv")
    (args.out / "summary.md").write_text(table)
    context = environment()
    context["run"] = {k: v for k, v in sorted(vars(args).items()) if k != "command"}
    context["devices"] = {name: method_device(m) for name, m in methods.items()}
    context["checkpoints"] = _checkpoints(methods)
    _write_context(context, args.out)
    return table


def read_curve(args: argparse.Namespace) -> str:
    """Read the cost curve from the runs ``make curve`` or ``make n3-curve`` scored.

    Nothing is run: the pairs are those ``validate`` scored for the points
    under PyTorch and under ONNX Runtime, and the memory is what ``footprint``
    read. With ``--benchmark`` the pairs are those ``benchmark`` scored, the
    same under both runtimes, and the refinement counts are read on them too.

    Args:
        args: Parsed ``curve`` arguments.

    Returns:
        The curve, as markdown.

    Raises:
        SystemExit: If a run or the footprints are missing, a run was not run
            as its configuration says, a rehearsal has rows of a held-out
            site, or the runs cannot be read together: see ``curve.check``.
    """
    if args.rehearsal and not args.benchmark:
        raise SystemExit("satreg: --rehearsal reads runs of --benchmark")
    command, recipe, free = "validate", "curve", ABLATION_FREE
    cost, torch, full = (args.out / n for n in (CURVE_COST, CURVE_TORCH, CURVE_FULL))
    gpu = args.gpu
    if args.benchmark:
        command, recipe = "benchmark", "n3-curve"
        cost, torch = (
            args.out / name for name in (CURVE_BENCHMARK_COST, CURVE_BENCHMARK_TORCH)
        )
        full = torch
        if args.rehearsal:
            free = (*ABLATION_FREE, *REHEARSAL_FREE)
    elif gpu is None and (args.out / CURVE_GPU / "pairs.csv").is_file():
        gpu = args.out / CURVE_GPU
    paths = {"full": full, "cost": cost, "torch": torch}
    if gpu is not None:
        paths["gpu"] = gpu
    held_out: list[str] = []
    for path in paths.values():
        _, scored = _scored_run(path, "pairs.csv", command, recipe, free)
        held_out += [
            name for name in scored.get("held_out_sites", []) if name not in held_out
        ]
    if args.rehearsal and held_out:
        raise SystemExit(
            f"satreg: a rehearsal reads no held-out site, and the runs have rows "
            f"of {', '.join(held_out)}"
        )
    footprints = args.out / CURVE_FOOTPRINT / "footprints.csv"
    if not footprints.is_file():
        raise SystemExit(
            f"satreg: no footprints at {footprints}: run make {recipe} (see the README)"
        )
    try:
        methods = load_methods(args.methods_config)
    except FileNotFoundError:
        raise SystemExit(
            f"satreg: no method parameters at {args.methods_config} "
            "(run from the repository root or pass --methods-config)"
        ) from None
    runs = {role: curve.read_run(path) for role, path in paths.items()}
    try:
        curve.check_methods(curve.POINTS, methods)
        read = curve.read(
            curve.POINTS,
            runs["cost"],
            runs["torch"],
            runs["full"],
            footprint.read(footprints),
            runs.get("gpu"),
        )
    except ValueError as exc:
        raise SystemExit(f"satreg: {exc}") from None

    table = (
        "The cost curve of RAFT: the large and the small model, pretrained and "
        "fine-tuned, with "
        f"{', '.join(str(count) for count in curve.REFINEMENTS)} refinements. "
    )
    if args.benchmark:
        sites = ", ".join(runs["cost"].context["run"]["sites"])
        pairs = f"pairs of {sites}"
        if args.rehearsal:
            table = (
                "**Rehearsal.** These runs check that the final evaluation's "
                "commands work, on seen sites and a few pairs: nothing here is a "
                "result, and no choice is made on it.\n\n" + table
            )
        table += (
            f"Error, failures and time are read on the benchmark's {pairs}, "
            f"under ONNX Runtime in `{cost}` and the same models under PyTorch on "
            f"the same pairs in `{torch}`, and memory in `{footprints.parent}`. "
            "How each is measured is in docs/decisions.md.\n\n"
            + curve.to_markdown(read, full="the same pairs")
            + held_out_note(held_out)
        )
    else:
        pairs = "validation pairs"
        table += (
            f"Error, failures and time are read on the light validation set of "
            f"`{cost}`, the same models under PyTorch on that of "
            f"`{torch}`, memory in `{footprints.parent}`, and the "
            f"refinement counts on the full validation set of `{full}`. "
            "How each is measured is in docs/decisions.md.\n\n"
            + curve.to_markdown(read)
        )
    write_csv(read.rows, args.out / "points.csv")
    write_csv(read.references, args.out / "references.csv")
    write_csv(read.refinements, args.out / "refinements.csv")
    curve.figure(read, args.out / "curve.png", pairs)
    (args.out / "summary.md").write_text(table)
    cost = runs["cost"].context
    context = {
        "code": code_version(),
        "run": {k: v for k, v in sorted(vars(args).items()) if k != "command"},
        # The files the points ran: the ONNX ones, and the weights under PyTorch.
        "checkpoints": {
            **runs["full"].context.get("checkpoints", {}),
            **cost.get("checkpoints", {}),
        },
        "held_out_sites": held_out,
        "machine": cost.get("machine"),
        "threads": cost.get("threads"),
        "libraries": cost.get("libraries"),
        "cost": cost.get("cost"),
        # The code and the time of the runs the tables come from.
        "read": {
            paths[role].name: {
                "code": run.context.get("code"),
                "recorded_at": run.context.get("recorded_at"),
                "machine": run.context.get("machine"),
            }
            for role, run in runs.items()
        },
    }
    _write_context(context, args.out)
    return table


def _published_weights(
    path: Path | str, context: dict[str, object]
) -> dict[str, dict[str, object]]:
    """Check that a run scored the published fine-tuned weights.

    Args:
        path: Directory of the run, for the message.
        context: The run's context.

    Returns:
        What the run recorded of the weights of each fine-tuned method.

    Raises:
        SystemExit: If a fine-tuned method did not run the published weights:
            the final evaluation is of those and no others.
    """
    recorded = context.get("checkpoints", {})
    for method, release in FINAL_WEIGHTS.items():
        if recorded.get(method, {}).get("sha256") != published.lookup(release).sha256:
            raise SystemExit(
                f"satreg: {path} did not run {method} with the published weights "
                f"{release}"
            )
    return {method: recorded[method] for method in FINAL_WEIGHTS}


def read_final(args: argparse.Namespace) -> str:
    """Read the final evaluation of N3: the criterion, then the closure.

    Nothing is run: the pairs are those of the table ``merge`` wrote from the
    two runs of ``benchmark``, and the triplets those ``cycle`` scored. The
    criterion is read on the sites the run of the RAFT methods marked held
    out, or in a rehearsal on the seen sites named in their place.

    Args:
        args: Parsed ``final`` arguments.

    Returns:
        The report, as markdown: the verdict first.

    Raises:
        SystemExit: If a run is missing, the table is not a merged one, a run
            was not run as its configuration says, the four RAFT methods are
            not in one run of the table, a fine-tuned method did not run the
            published weights, the table has no held-out site, a rehearsal has
            one, or the runs cannot be read together: see ``final.read``.
    """
    rehearsal = bool(args.rehearsal)
    free = (*ABLATION_FREE, *REHEARSAL_FREE) if rehearsal else ABLATION_FREE
    pairs = args.table / "pairs.csv"
    if not pairs.is_file() or not (args.table / "context.json").is_file():
        raise SystemExit(
            f"satreg: no pairs.csv and context.json in {args.table}: run make n3 "
            "(see the README)"
        )
    parts = json.loads((args.table / "context.json").read_text()).get("merged")
    if not parts:
        raise SystemExit(
            f"satreg: {args.table} is not a table satreg merge wrote: run make n3 "
            "(see the README)"
        )
    for part in parts:
        _as_configured(part["path"], part["context"], "benchmark", "n3", free)
    methods = [method for model in final.MODELS for method in model]
    scored = [
        part
        for part in parts
        if all(method in part["context"].get("devices", {}) for method in methods)
    ]
    if len(scored) != 1:
        raise SystemExit(
            f"satreg: {args.table} does not have {', '.join(methods)} from one run: "
            "a model and its reference are read on one machine"
        )
    table = scored[0]["context"]
    triplets, closure = _scored_run(args.closure, "triplets.csv", "cycle", "n3", free)
    weights = _published_weights(scored[0]["path"], table)
    _published_weights(args.closure, closure)

    held_out = list(table.get("held_out_sites", []))
    looked = [part["context"].get("held_out_sites", []) for part in parts]
    looked.append(closure.get("held_out_sites", []))
    if rehearsal:
        if seen := sorted({name for names in looked for name in names}):
            raise SystemExit(
                "satreg: a rehearsal reads no held-out site, and the runs have "
                f"rows of {', '.join(seen)}"
            )
        target = list(dict.fromkeys(args.rehearsal))
    elif not held_out:
        raise SystemExit(
            f"satreg: {args.table} has no held-out site to read the criterion on "
            "(--rehearsal names seen sites to stand in for them)"
        )
    elif any(names != held_out for names in looked):
        raise SystemExit(
            f"satreg: the runs of {args.table} and {args.closure} are not of the "
            "same held-out sites"
        )
    else:
        target = held_out
    try:
        read = final.read(
            ablation.read_pairs(pairs),
            ablation.read_triplets(triplets),
            target,
            rehearsal,
            args.resamples,
            args.seed,
        )
    except ValueError as exc:
        raise SystemExit(f"satreg: {exc}") from None
    # Every pair the run was to score: a table cut short is not the criterion.
    run = table["run"]
    expected = (
        len(target) * len(run["scenarios"]) * len(run["degradations"]) * run["pairs"]
    )
    if (found := read.pairs_of(final.LARGE, read.target)[0].pairs) != expected:
        raise SystemExit(
            f"satreg: {args.table} has {found} pairs of {', '.join(target)} for "
            f"{final.LARGE[0]}, not the {expected} its run was to score"
        )

    devices = ", ".join(dict.fromkeys(table["devices"][m] for m in methods))
    report = (
        "The final evaluation of N3: fine-tuned RAFT next to the pretrained "
        f"model, on the simulated pairs of `{args.table}` and the real triplets "
        f"of `{args.closure}`. The criterion and the reading of the closure are "
        "in docs/decisions.md, written before any training ran, and the freeze "
        "before these tables were made.\n\n"
        + final.to_markdown(read)
        + f"\nThe pairs of the four RAFT methods were scored on {describe(table)} "
        f"({devices}), and the triplets on {describe(closure)}. The fine-tuned "
        "weights are the published ones: "
        + "; ".join(
            f"{method} is `{found['asset']}` of release `{found['release']}`, "
            f"SHA-256 `{found['sha256']}`"
            for method, found in weights.items()
        )
        + ".\n"
        + held_out_note(held_out)
    )
    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(read.criterion, args.out / "criterion.csv")
    write_csv(read.closure, args.out / "closure.csv")
    (args.out / "summary.md").write_text(report)
    context = {
        "code": code_version(),
        "run": {k: v for k, v in sorted(vars(args).items()) if k != "command"},
        "checkpoints": weights,
        "held_out_sites": held_out,
        "rehearsal": rehearsal,
        # A rehearsal answers nothing.
        "answer": None if rehearsal else read.answer,
        # The code, the time and the machine of the runs the tables come from.
        "read": {
            str(path): {
                "code": run.get("code"),
                "recorded_at": run.get("recorded_at"),
                "machine": run.get("machine"),
                "gpu": run.get("gpu"),
            }
            for path, run in (
                *((part["path"], part["context"]) for part in parts),
                (args.closure, closure),
            )
        },
    }
    _write_context(context, args.out)
    return report


def _no_method(args: argparse.Namespace) -> str:
    """What ``register`` says when no method is named: those that can run here."""
    try:
        methods = load_methods(args.methods_config)
    except FileNotFoundError:
        raise SystemExit(
            f"satreg: no method parameters at {args.methods_config} "
            "(run from the repository root or pass --methods-config)"
        ) from None
    here, after_download = register.available(methods)
    lines = [
        "satreg: register runs the method named with --method NAME and has no default.",
        "Methods that can run here: " + (", ".join(here) or "none"),
    ]
    if after_download:
        lines.append(
            "Methods that first download their published file: "
            + ", ".join(after_download)
        )
    return "\n".join(lines)


def register_pair(args: argparse.Namespace) -> str:
    """Register a supplied pair with one method and write the result.

    Args:
        args: Parsed ``register`` arguments.

    Returns:
        What was estimated and written, for the terminal.
    """
    if args.method is None:
        raise SystemExit(_no_method(args))
    if args.reference is None or args.moving is None or args.out is None:
        raise SystemExit(
            "satreg: register takes two images and a directory to write to: "
            "satreg register REF MOVING --method NAME --out DIR"
        )
    try:
        pair = register.read_pair(
            args.reference,
            args.moving,
            band=args.band,
            window=tuple(args.window) if args.window else None,
        )
    except register.Refused as exc:
        raise SystemExit(f"satreg: {exc}") from None
    chosen = argparse.Namespace(
        methods=[args.method], methods_config=args.methods_config, device=None
    )
    method = configured_methods(chosen)[args.method]
    notes = []
    if note := register.padding_note(method, pair.reference.shape):
        notes.append(note)
        logging.warning(note)
    # From here on the directory holds the result of this call or nothing.
    register.clear(args.out)
    try:
        registration = register.register(args.method, method, pair)
    except register.Refused as exc:
        raise SystemExit(f"satreg: {exc}") from None
    except RegistrationFailure as exc:
        seen = ", ".join(f"{key} = {value:g}" for key, value in exc.diagnostics.items())
        raise SystemExit(
            f"satreg: {args.method} could not register this pair: {exc}"
            + (f" ({seen})" if seen else "")
            + ". Nothing was written"
        ) from None
    result = register.write(args.out, pair, registration, notes)
    found = result["displacement"]
    if found["model"] == "translation":
        summary = f"dx = {found['dx']:+.3f} px, dy = {found['dy']:+.3f} px"
    elif found["model"] == "affine":
        summary = f"matrix {found['matrix']}, offset {found['offset']} (rows, columns)"
    else:
        summary = (
            f"mean dx = {found['mean_dx']:+.3f} px, mean dy = "
            f"{found['mean_dy']:+.3f} px, up to {found['max_px']:.3f} px"
        )
    written = [register.DISPLACEMENT_FILE, register.CORRECTED_FILE]
    if found["model"] == "dense":
        written.append(register.FLOW_FILE)
    lines = [
        f"{args.method}: {found['model']} displacement, {summary}",
        f"call: {registration.duration_s:.2f} s, the method's loading included",
        f"written to {args.out}: {', '.join(written)}",
    ]
    if left_out := result["corrected"]["no_data_px"]:
        lines.append(
            f"{left_out} px of the corrected image lie outside the moving image "
            "and hold no data"
        )
    return "\n".join(lines) + "\n"


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
    elif args.command == "train":
        print(train(args), end="")
    elif args.command == "validate":
        print(validate(args), end="")
    elif args.command == "validate-cycle":
        print(validate_cycle(args), end="")
    elif args.command == "ablation":
        print(read_ablation(args), end="")
    elif args.command == "small":
        print(read_small(args), end="")
    elif args.command == "fetch-weights":
        for path in fetch_weights(args):
            print(path)
    elif args.command == "export-weights":
        print(export_weights(args), end="")
    elif args.command == "export":
        print(export_onnx(args), end="")
    elif args.command == "quantize":
        print(quantize_files(args), end="")
    elif args.command == "int8":
        print(read_int8(args), end="")
    elif args.command == "footprint":
        print(read_footprints(args), end="")
    elif args.command == "curve":
        print(read_curve(args), end="")
    elif args.command == "final":
        print(read_final(args), end="")
    elif args.command == "register":
        print(register_pair(args), end="")

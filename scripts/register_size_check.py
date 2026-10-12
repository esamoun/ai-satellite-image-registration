"""Size check (2026-10-12): what does a pair above 256 px cost `satreg register`?

Every published figure is on 256 px windows. Before `satreg register` takes an
image whole, this reads what a method's calls and the correction that follows
add to a process's memory, and how long they take, at 256, 512 and 1,024 px on
this machine. The limit above which the command refuses an image comes from
these figures (docs/decisions.md).

The pair is a window of the Beauce benchmark chip, a seen site, and the same
window shifted by the simulator. The chip is 1,024 px a side, so the margin
the shift needs is mirrored rather than read. Each method is read in a new
process of its own at each size, as `satreg footprint` does. The error to the
known shift is that of one clean pair: a check that the method still answers
at that size, not a published accuracy.

Memory is the rise of the process's highest physical footprint, the figure
macOS charges a process with, compressed and swapped pages included. The
resident high-water mark `satreg footprint` reads is kept beside it: on an
8 GB machine it stops rising once the system compresses, and reads 3,100 to
3,800 MiB for RAFT at 1,024 px where the footprint is 5,300 to 5,700 MiB. Off
macOS only the resident mark is read.

    python scripts/register_size_check.py
"""

import argparse
import ctypes
import gc
import importlib
import json
import multiprocessing
import os
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from pathlib import Path
from time import perf_counter

import numpy as np

from satreg import falsechange
from satreg.compute import environment, process_peak_rss_mib
from satreg.ingest import cache_path, read_chip, read_georef
from satreg.methods import load_methods
from satreg.methods.base import GeoreferencedMethod
from satreg.simulate import margin_for, simulate_translation
from satreg.sites import load_sites

SITE = "beauce"
SIZES = [256, 512, 1024]
SHIFT = (1.37, -2.61)
CALLS = 3
METHODS = [
    "phase_correlation",
    "sift_ransac",
    "arosics",
    "lightglue",
    "roma",
    "raft_small_ft_onnx",
    "raft_ft_r4_onnx",
    "raft_ft_onnx_int8",
    "raft_ft_onnx",
    "raft_ft",
]
METHODS_CONFIG = Path("configs/methods.toml")
SITES_CONFIG = Path("configs/sites.toml")
OUT = Path("outputs/register-size")
MIB = 2**20
# proc_pid_rusage, flavor RUSAGE_INFO_V4: the structure read as 64-bit words,
# and the word that holds ri_lifetime_max_phys_footprint (<sys/resource.h>).
RUSAGE_INFO_V4 = 4
RUSAGE_WORDS = 64
LIFETIME_MAX_PHYS_FOOTPRINT = 30


def peak_memory_mib() -> float:
    """Highest memory this process was charged with so far, in MiB.

    Returns:
        On macOS the highest physical footprint, which counts the pages the
        system compressed or swapped; elsewhere the resident high-water mark.
    """
    if sys.platform == "darwin":
        usage = (ctypes.c_uint64 * RUSAGE_WORDS)()
        libproc = ctypes.CDLL("/usr/lib/libproc.dylib")
        if not libproc.proc_pid_rusage(os.getpid(), RUSAGE_INFO_V4, usage):
            return usage[LIFETIME_MAX_PHYS_FOOTPRINT] / MIB
    return process_peak_rss_mib()


def measure(name: str, size: int) -> dict[str, object]:
    """Register one pair in this process and read what it cost.

    Args:
        name: Name of the method in ``METHODS_CONFIG``.
        size: Side of the pair, in px.

    Returns:
        The rise of the highest memory after the calls and after the
        correction, the times, and the error to the known shift.
    """
    method = load_methods(METHODS_CONFIG)[name]
    for module in getattr(method, "runtime", ()):
        importlib.import_module(module)
    config = load_sites(SITES_CONFIG)
    chip = cache_path(config.sites[SITE], config.catalogue, Path("data"))
    dx, dy = SHIFT
    margin = margin_for(max(abs(dx), abs(dy)))
    window = read_chip(chip)[:size, :size].astype(float)
    pair = simulate_translation(
        np.pad(window, margin, mode="symmetric"), dx=dx, dy=dy, margin=margin
    )
    images = (pair.reference, pair.moving)
    if isinstance(method, GeoreferencedMethod):
        images = (*images, read_georef(chip))
    del window
    gc.collect()
    baseline = peak_memory_mib()
    seconds, estimate, error = [], None, ""
    for call in range(CALLS):
        started = perf_counter()
        try:
            estimate = method(*images)
        except Exception as exc:
            error = error or f"call {call + 1}: {type(exc).__name__}: {exc}"
        seconds.append(perf_counter() - started)
    called = peak_memory_mib()
    row: dict[str, object] = {
        "method": name,
        "size": size,
        "baseline_mib": baseline,
        "calls_rise_mib": called - baseline,
        "first_call_s": seconds[0],
        "call_s": statistics.median(seconds[1:]),
        "error": error,
    }
    if estimate is None:
        return row
    displacement = getattr(estimate, "displacement", estimate)
    field = displacement.field(pair.reference.shape)
    row["epe_px"] = float(np.hypot(field[0] - dy, field[1] - dx).mean())
    started = perf_counter()
    falsechange.correct(pair.moving, displacement)
    row["correction_s"] = perf_counter() - started
    row["total_rise_mib"] = peak_memory_mib() - baseline
    row["process_mib"] = peak_memory_mib()
    row["resident_mib"] = process_peak_rss_mib()
    return row


def to_markdown(rows: list[dict[str, object]]) -> str:
    """One line per method and size, as a Markdown table under what it reads."""
    dx, dy = SHIFT
    lines = [
        f"What registering one pair costs a process, by the side of the pair: a "
        f"window of the {SITE} benchmark chip and the same window shifted by "
        f"({dx}, {dy}) px, each method read in a new process at each size. Times: "
        f"the first call, which loads the model, the median of the {CALLS - 1} "
        "calls after it, and the correction of the moving image. Memory: the rise "
        "of the process's highest physical footprint above its mark before the "
        "first call, after the calls and after the correction, then the whole "
        "process, with its resident high-water mark beside it. The error is that "
        "of this one clean pair: a check that the method still answers at that "
        "size, not a published accuracy.",
        "",
        "| method | side (px) | first call (s) | call (s) | correction (s) | "
        "memory added by the calls (MiB) | with the correction (MiB) | "
        "whole process (MiB) | resident mark (MiB) | error on the pair (px) |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        if "epe_px" not in row:
            lines.append(f"| {row['method']} | {row['size']} | {row['error']} |")
            continue
        lines.append(
            f"| {row['method']} | {row['size']} | {row['first_call_s']:.2f} | "
            f"{row['call_s']:.2f} | {row['correction_s']:.2f} | "
            f"{row['calls_rise_mib']:.0f} | {row['total_rise_mib']:.0f} | "
            f"{row['process_mib']:.0f} | {row['resident_mib']:.0f} | "
            f"{row['epe_px']:.3f} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    """Read every method at every size, each in a new process, and write them."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--methods", nargs="+", default=METHODS)
    parser.add_argument("--sizes", nargs="+", type=int, default=SIZES)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    spawn = multiprocessing.get_context("spawn")
    rows = []
    for size in args.sizes:
        for name in args.methods:
            try:
                with ProcessPoolExecutor(max_workers=1, mp_context=spawn) as fresh:
                    row = fresh.submit(measure, name, size).result()
            except BrokenProcessPool:
                row = {"method": name, "size": size, "error": "the process died"}
            rows.append(row)
            print(json.dumps(row), flush=True)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "readings.json").write_text(
        json.dumps({"environment": environment(), "readings": rows}, indent=2) + "\n"
    )
    (args.out / "readings.md").write_text(to_markdown(rows))
    print(to_markdown(rows))


if __name__ == "__main__":
    main()

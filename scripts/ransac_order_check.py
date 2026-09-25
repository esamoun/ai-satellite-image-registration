"""Check (2026-09-25): is LightGlue's CPU/GPU gap on hard pairs RANSAC's noise?

Throwaway: reruns LightGlue on the hard pairs of configs/gpu.toml, on the CPU,
with the matches handed to RANSAC in shuffled orders, then counts the pairs that
switch between success and failure against the CPU run, next to the count the
change of device gives. Findings are in docs/failures.md. Needs the ``dl``
extra, and the CPU and GPU runs of docs/kaggle.md.

    python scripts/ransac_order_check.py --orders 1 2 3 4 5
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from satreg import cli
from satreg.methods import ransac

METHODS = ["lightglue", "lightglue_disk"]
KEYS = ["scenario", "method", "pair"]


def shuffled_fit(seed: int):
    """``ransac.fit_affine`` with the matches permuted by ``seed`` first."""
    fit = ransac.fit_affine

    def call(ref_points, mov_points, *args, **kwargs):
        perm = np.random.default_rng(seed).permutation(len(ref_points))
        return fit(
            np.asarray(ref_points)[perm], np.asarray(mov_points)[perm], *args, **kwargs
        )

    return call


def run(seed: int, out: Path) -> None:
    """Run the hard LightGlue pairs on the CPU, matches shuffled by ``seed``."""
    original = ransac.fit_affine
    ransac.fit_affine = shuffled_fit(seed)
    try:
        cli.main(
            [
                "benchmark",
                "--config", "configs/gpu.toml",
                "--device", "cpu",
                "--degradations", "hard",
                "--methods", *METHODS,
                # RANSAC's result does not depend on the repeat: one call is enough.
                "--repeats", "1",
                "--warmup", "0",
                "--out", str(out),
            ]
        )  # fmt: skip
    finally:
        ransac.fit_affine = original


def failed(path: Path) -> pd.Series:
    """Whether each hard LightGlue pair of a run failed."""
    rows = pd.read_csv(path / "pairs.csv")
    rows = rows[(rows.degradation == "hard") & rows.method.isin(METHODS)]
    return rows.set_index(KEYS)["failed"].astype(bool)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--orders", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    parser.add_argument("--cpu", type=Path, default=Path("outputs/gpu-m1"))
    parser.add_argument("--gpu", type=Path, default=Path("outputs/kaggle/outputs/gpu"))
    parser.add_argument("--out", type=Path, default=Path("outputs/ransac-order"))
    args = parser.parse_args()

    cpu = failed(args.cpu)
    runs = {"gpu": failed(args.gpu)}
    for seed in args.orders:
        out = args.out / f"order-{seed}"
        run(seed, out)
        runs[f"order {seed}"] = failed(out)

    for method in METHODS:
        base = cpu.xs(method, level="method")
        print(f"{method}: {len(base)} hard pairs, {base.mean():.0%} failed on the CPU")
        for name, other in runs.items():
            other = other.xs(method, level="method").reindex(base.index)
            print(
                f"  {name:>8}: {(other != base).sum():2d} pairs switch, "
                f"{other.mean():.0%} failed"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())

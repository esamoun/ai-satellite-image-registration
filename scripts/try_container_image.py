"""Try the container image: does what was built register a pair and benchmark?

Run after `make container-image`, by CI on every push and by hand on a laptop.
Every command runs in a container with no network (`--network none`), as the
user who calls this script, and writes to a directory of the host:

1. `satreg register` with no method lists what can run. It must be the
   methods of the small benchmark and no other: a method that needs PyTorch,
   AROSICS or a file that is not there is not listed, and one of the config
   whose file is missing is not either.
2. `satreg register` on the Beauce demo pair, with a classic method and with a
   fine-tuned RAFT model under ONNX Runtime. Each displacement must be within
   the benchmark's failure threshold of the pair's true shift, which
   `examples/manifest.json` gives.
3. `satreg benchmark --config configs/container-image.toml`, whose table must
   have one row per preset and method.

A command that loads a model must not print a telemetry message: ONNX Runtime's
telemetry is turned off in the container image, and says so when it is not.

The script needs Python 3.11 and Docker, and nothing of the package: it reads
the repository's files and what the containers wrote. It stops at the first
check that fails, with a non-zero exit code.

    python scripts/try_container_image.py --tag satreg:local
    python scripts/try_container_image.py --pairs 2 --repeats 1
"""

import argparse
import csv
import json
import math
import os
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "configs/container-image.toml"

# The demo pair registered, by its entry in examples/manifest.json.
SITE, PRESET, SCENARIO = "beauce", "clean", "translation"

# One method of each kind: a classic one and a fine-tuned RAFT model.
REGISTERED = ("phase_correlation", "raft_ft_onnx")

# How `satreg register` with no method starts the line of what can run.
LISTED = "Methods that can run here: "

# Where the host directory is mounted in the container.
MOUNT = "/out"

# What ONNX Runtime's messages about its telemetry have in common.
TELEMETRY = "telemetry"


class Failed(Exception):
    """A check of the container image did not hold."""


def docker(*args: str) -> subprocess.CompletedProcess[str]:
    """Run a docker command and capture what it prints."""
    return subprocess.run(["docker", *args], capture_output=True, text=True)


def satreg(tag: str, out: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a `satreg` command in a container with no network.

    Args:
        tag: Tag of the container image.
        out: Host directory mounted at ``MOUNT``, which the command writes to.
        args: Arguments of `satreg`.

    Returns:
        The finished process, with what it printed.
    """
    print(f"\n$ satreg {' '.join(args)}", flush=True)
    done = docker(
        *["run", "--rm", "--network", "none"],
        *["--user", f"{os.getuid()}:{os.getgid()}"],
        *["--volume", f"{out.resolve()}:{MOUNT}"],
        *[tag, *args],
    )
    print(done.stdout + done.stderr, end="", flush=True)
    return done


def check_no_telemetry(done: subprocess.CompletedProcess[str], command: str) -> None:
    """A command printed nothing about telemetry, which is turned off."""
    if TELEMETRY in (done.stdout + done.stderr).lower():
        raise Failed(f"{command} printed a telemetry message")


def check_listing(tag: str, out: Path, methods: list[str]) -> None:
    """`satreg register` with no method lists the config's methods, and only them."""
    done = satreg(tag, out, "register")
    if done.returncode == 0:
        raise Failed("register with no method should exit with an error code")
    printed = done.stdout + done.stderr
    listed = [
        line.removeprefix(LISTED).split(", ")
        for line in printed.splitlines()
        if line.startswith(LISTED)
    ]
    if len(listed) != 1:
        raise Failed("register with no method did not list the methods")
    if absent := sorted(set(methods) - set(listed[0])):
        raise Failed(f"not listed as able to run: {', '.join(absent)}")
    if extra := sorted(set(listed[0]) - set(methods)):
        raise Failed(f"listed, though not in {CONFIG}: {', '.join(extra)}")


def true_shift() -> tuple[dict, float, float]:
    """The demo pair registered and its true shift, from the examples' manifest."""
    manifest = json.loads((ROOT / "examples" / "manifest.json").read_text())
    (pair,) = [
        pair
        for pair in manifest["pairs"]
        if (pair["site"], pair["preset"], pair["scenario"]) == (SITE, PRESET, SCENARIO)
    ]
    return pair, pair["truth"]["dx"], pair["truth"]["dy"]


def check_register(tag: str, out: Path, method: str, threshold: float) -> None:
    """One method registers the demo pair within the failure threshold."""
    pair, dx, dy = true_shift()
    done = satreg(
        tag,
        out,
        *["register", f"examples/{pair['reference']}", f"examples/{pair['moving']}"],
        *["--method", method, "--out", f"{MOUNT}/register-{method}"],
    )
    if done.returncode != 0:
        raise Failed(f"register --method {method} exited with {done.returncode}")
    check_no_telemetry(done, f"register --method {method}")
    written = out / f"register-{method}"
    for name in ("displacement.json", "corrected.tif"):
        if not (written / name).is_file():
            raise Failed(f"register --method {method} wrote no {name}")
    found = json.loads((written / "displacement.json").read_text())["displacement"]
    # A dense displacement is read by its mean, which a pure shift equals.
    dense = found["model"] == "dense"
    if dense and not (written / found["file"]).is_file():
        raise Failed(f"register --method {method} wrote no {found['file']}")
    error = math.hypot(
        found["mean_dx" if dense else "dx"] - dx,
        found["mean_dy" if dense else "dy"] - dy,
    )
    print(f"{method}: {error:.4f} px from the true shift ({dx} px, {dy} px)")
    if not error < threshold:
        raise Failed(f"{method} is {error:.3f} px off, over the {threshold} px limit")


def check_benchmark(tag: str, out: Path, config: dict, flags: list[str]) -> None:
    """The small benchmark runs and gives one row per preset and method."""
    done = satreg(
        tag,
        out,
        *["benchmark", "--config", CONFIG, "--out", f"{MOUNT}/benchmark", *flags],
    )
    if done.returncode != 0:
        raise Failed(f"benchmark exited with {done.returncode}")
    check_no_telemetry(done, "benchmark")
    summary = out / "benchmark" / "summary.csv"
    if not summary.is_file():
        raise Failed("benchmark wrote no summary.csv")
    with summary.open(newline="") as table:
        rows = {(row["degradation"], row["method"]) for row in csv.DictReader(table)}
    expected = {
        (preset, method)
        for preset in config["degradations"]
        for method in config["methods"]
    }
    if rows != expected:
        raise Failed(
            f"the benchmark's table has {len(rows)} rows, {len(expected)} expected"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--tag", default="satreg:local", help="tag of the container image to try"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "outputs" / "container-image",
        help="host directory the containers write to",
    )
    parser.add_argument(
        "--pairs", type=int, help="pairs a cell of the benchmark, for a shorter run"
    )
    parser.add_argument(
        "--repeats", type=int, help="timed calls a pair, for a shorter run"
    )
    args = parser.parse_args()
    # Options of `satreg benchmark` that override the config's keys.
    flags = [
        text
        for option, value in (("--pairs", args.pairs), ("--repeats", args.repeats))
        if value is not None
        for text in (option, str(value))
    ]
    config = tomllib.loads((ROOT / CONFIG).read_text())["benchmark"]
    args.out.mkdir(parents=True, exist_ok=True)

    inspected = docker(
        *["image", "inspect", args.tag],
        *["--format", "{{.Os}}/{{.Architecture}} {{.Size}}"],
    )
    if inspected.returncode != 0:
        print(f"no container image {args.tag}: {inspected.stderr.strip()}")
        return 1
    platform, size = inspected.stdout.split()
    print(f"{args.tag}: {platform}, {int(size) / 1e6:.0f} MB")
    print(docker("image", "ls", args.tag).stdout, end="")

    try:
        check_listing(args.tag, args.out, config["methods"])
        for method in REGISTERED:
            check_register(args.tag, args.out, method, config["failure_threshold"])
        check_benchmark(args.tag, args.out, config, flags)
    except Failed as exc:
        print(f"\nFAILED: {exc}")
        return 1
    print(f"\nThe container image {args.tag} registers and benchmarks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

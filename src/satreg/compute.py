"""Measure what a method call costs, and record the machine it was measured on.

Time is wall-clock, the median over repeated calls on the same pair. Memory is
the peak traced by ``tracemalloc`` during one more call, made apart from the
timed ones because tracing slows Python code down. ``tracemalloc`` sees
allocations made through Python's allocators, which include NumPy's array
buffers, but not memory that native code (OpenCV, GDAL, FFT or BLAS scratch)
allocates for itself. ``docs/decisions.md`` measures how much that misses.
"""

import importlib.metadata
import os
import platform
import statistics
import subprocess
import sys
import tracemalloc
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter

MIB = 2**20

# Distributions whose versions change the numbers, compiled code first.
LIBRARIES = (
    "numpy",
    "scipy",
    "scikit-image",
    "opencv-python-headless",
    "rasterio",
    "arosics",
    "GDAL",
)

# Environment variables that cap the threads of native libraries.
THREAD_VARIABLES = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)


@dataclass(frozen=True)
class Measured:
    """A method call's outcome and its cost.

    Attributes:
        value: What the first timed call returned, ``None`` if it raised.
        error: What the first timed call raised, ``None`` if it returned.
        seconds: Median wall-clock time over the timed calls.
        peak_mib: Peak memory traced during the memory call, in MiB, above what
            was allocated before it.
    """

    value: object
    error: Exception | None
    seconds: float
    peak_mib: float

    def result(self) -> object:
        """Return the outcome of the call, raising what it raised."""
        if self.error is not None:
            raise self.error
        return self.value


def _attempt(call: Callable[[], object]) -> tuple[object, Exception | None]:
    # A call that raises still costs time and memory, so its cost is measured
    # like any other.
    try:
        return call(), None
    except Exception as exc:
        return None, exc


def peak_memory(call: Callable[[], object]) -> float:
    """Run a call once and return the peak memory it allocated, in MiB.

    Args:
        call: Call to measure. What it returns or raises is discarded.

    Returns:
        Peak traced memory during the call, above what was allocated before it.
        Native allocations that bypass Python's allocators are not counted.
    """
    tracing = tracemalloc.is_tracing()
    if not tracing:
        tracemalloc.start()
    try:
        tracemalloc.reset_peak()
        before, _ = tracemalloc.get_traced_memory()
        _attempt(call)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        if not tracing:
            tracemalloc.stop()
    return (peak - before) / MIB


def measure(call: Callable[[], object], repeats: int, warmup: int = 0) -> Measured:
    """Time a call, then measure its peak memory.

    The call is made ``warmup`` times untimed, ``repeats`` times timed, and once
    more under ``tracemalloc``. Only the call is measured: whatever prepares its
    inputs happens before this function is entered.

    Args:
        call: Call to measure, with its inputs bound.
        repeats: Timed calls, at least one.
        warmup: Untimed calls made first, to pay one-off costs such as lazy
            imports and library initialisation.

    Returns:
        The outcome of the first timed call, the median time and the peak memory.

    Raises:
        ValueError: If ``repeats`` is below one or ``warmup`` is negative.
    """
    if repeats < 1:
        raise ValueError(f"repeats must be at least 1, got {repeats}")
    if warmup < 0:
        raise ValueError(f"warmup must be non-negative, got {warmup}")
    for _ in range(warmup):
        _attempt(call)
    outcomes, seconds = [], []
    for _ in range(repeats):
        start = perf_counter()
        outcomes.append(_attempt(call))
        seconds.append(perf_counter() - start)
    value, error = outcomes[0]
    return Measured(
        value=value,
        error=error,
        seconds=statistics.median(seconds),
        peak_mib=peak_memory(call),
    )


def _cpu_name() -> str:
    """Name the CPU model, falling back to its architecture."""
    try:
        if sys.platform == "darwin":
            return subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except (OSError, subprocess.CalledProcessError):
        pass
    return platform.processor() or platform.machine()


def _memory_gib() -> float | None:
    """Total physical memory, in GiB, if the platform reports it."""
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30
    except (AttributeError, ValueError, OSError):
        return None


def _usable_cpus() -> int | None:
    """CPUs this process may run on, which a container can set below the total."""
    if hasattr(os, "sched_getaffinity"):
        return len(os.sched_getaffinity(0))
    return os.cpu_count()


def _opencv_threads() -> int | None:
    try:
        import cv2
    except ImportError:
        return None
    return cv2.getNumThreads()


def _version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def process_peak_rss_mib() -> float | None:
    """Peak resident memory of this process so far, in MiB, native code included.

    Returns:
        The high-water mark of the whole process, ``None`` where the platform
        has no ``resource`` module.
    """
    try:
        import resource
    except ImportError:
        return None
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # macOS reports bytes, Linux kibibytes.
    return peak / MIB if sys.platform == "darwin" else peak / 1024


def environment() -> dict[str, object]:
    """Describe the machine and software the costs are measured with.

    Returns:
        A JSON-ready mapping: hardware, thread settings, Python and library
        versions (``None`` for a library not installed), and the time it was
        taken, so that runs on different machines can be told apart.
    """
    return {
        "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "machine": {
            "system": platform.platform(),
            "architecture": platform.machine(),
            "cpu": _cpu_name(),
            "memory_gib": _memory_gib(),
        },
        "threads": {
            "cpu_count": os.cpu_count(),
            "usable_cpus": _usable_cpus(),
            "opencv": _opencv_threads(),
            **{name: os.environ.get(name) for name in THREAD_VARIABLES},
        },
        "python": platform.python_version(),
        "libraries": {name: _version(name) for name in LIBRARIES},
    }


def describe(context: dict[str, object]) -> str:
    """Summarise an ``environment()`` mapping on one line, for the results table.

    Args:
        context: As returned by ``environment()``.

    Returns:
        CPU, memory, thread count and system, e.g. ``Apple M1, 8 GiB, 8 CPUs,
        macOS-15.6-arm64-arm-64bit``.
    """
    machine, threads = context["machine"], context["threads"]
    memory = machine["memory_gib"]
    parts = [
        machine["cpu"],
        f"{memory:.0f} GiB" if memory is not None else None,
        f"{threads['usable_cpus']} CPUs",
        machine["system"],
    ]
    return ", ".join(part for part in parts if part)

"""Measure what a method call costs, and record the machine it was measured on.

Time is wall-clock, the median over repeated calls on the same pair. Memory is
the peak measured during one more call, made apart from the timed ones because
measuring it slows the call down. How time and memory are read is the method's
``Meter``. By default memory is the peak traced by ``tracemalloc``, which sees
allocations made through Python's allocators, NumPy's array buffers included, but
not memory that native code (OpenCV, GDAL, FFT or BLAS scratch) allocates for
itself. ``docs/decisions.md`` measures how much that misses. PyTorch methods
use a ``TorchMeter`` instead, since ``tracemalloc`` does not see tensors either.
"""

import contextlib
import gc
import importlib.metadata
import itertools
import math
import os
import platform
import statistics
import subprocess
import sys
import tracemalloc
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter
from typing import Protocol

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
    "torch",
    "torchvision",
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
        peak_mib: Peak memory the meter measured during the memory call, in MiB,
            above what was allocated before it, NaN if the meter has no figure.
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


# What each meter's memory figure is, by meter name, as the results table says it.
MEMORY_READINGS = {
    "tracemalloc": "the peak traced by tracemalloc, which misses native allocations",
    "torch-cpu": "the peak held by CPU tensors, from PyTorch's profiler",
    "cuda": "the peak held by CUDA tensors",
    "none": "not measured, as no counter is available on the device",
}


class Meter(Protocol):
    """How the cost of a method's calls is read.

    Attributes:
        name: What the memory figure is, a key of ``MEMORY_READINGS``, recorded
            with the results so that figures read differently are not compared.
    """

    name: str

    def synchronize(self) -> None:
        """Wait until the work the call started is done, before a clock read."""

    def peak_mib(self, call: Callable[[], object]) -> float:
        """Run a call once and return its peak memory, in MiB, or NaN if unknown."""


@dataclass(frozen=True)
class Tracemalloc:
    """The default meter: work ends when the call returns, memory is traced."""

    name: str = "tracemalloc"

    def synchronize(self) -> None:
        """Nothing to wait for: the call's work is done when it returns."""

    def peak_mib(self, call: Callable[[], object]) -> float:
        """Peak memory traced by ``tracemalloc``, see ``peak_memory``."""
        return peak_memory(call)


TRACEMALLOC = Tracemalloc()


@contextlib.contextmanager
def _native_stderr_silenced() -> Iterator[None]:
    """Send what native code writes to stderr to the null device, meanwhile."""
    sys.stderr.flush()
    saved = os.dup(2)
    try:
        with open(os.devnull, "w") as null:
            os.dup2(null.fileno(), 2)
            yield
    finally:
        os.dup2(saved, 2)
        os.close(saved)


def torch_cpu_peak(call: Callable[[], object]) -> float:
    """Run a call once and return the peak memory held by CPU tensors, in MiB.

    PyTorch's profiler reports every tensor allocation and release with its
    size. Summed in time order they give the bytes held at each moment; the
    peak is taken above what was held before the call. The allocator's own
    cache, the model's weights and NumPy arrays are not counted.

    Args:
        call: Call to measure. What it returns or raises is discarded.

    Returns:
        Peak tensor memory during the call, in MiB.
    """
    import torch
    from torch.profiler import ProfilerActivity, profile

    profiler = profile(activities=[ProfilerActivity.CPU], profile_memory=True)
    # Kineto announces each start and stop on stderr, which would print two
    # lines per pair. The call itself keeps its stderr.
    with _native_stderr_silenced():
        profiler.start()
    try:
        _attempt(call)
    finally:
        with _native_stderr_silenced():
            profiler.stop()
    # The profiler's own event list, rebuilt from these, loses allocations made
    # on worker threads; the raw events keep them. Pinned by a test.
    events = sorted(
        (event.start_ns(), event.nbytes())
        for event in profiler.profiler.kineto_results.events()
        if event.name() == "[memory]"
        and event.device_type() == torch.autograd.DeviceType.CPU
    )
    held = itertools.accumulate(nbytes for _, nbytes in events)
    peak = max(itertools.chain([0], held)) / MIB
    # The profiler sits in a reference cycle that keeps its trace, about 1 GB
    # for one RoMa call, and Python's collector reaches it only now and then:
    # over a run the process grew until macOS killed it. Collected here.
    del profiler, events
    gc.collect()
    return peak


def cuda_peak(call: Callable[[], object], device: str = "cuda") -> float:
    """Run a call once and return the peak memory CUDA tensors took, in MiB.

    Args:
        call: Call to measure. What it returns or raises is discarded.
        device: CUDA device the call runs on.

    Returns:
        Peak of ``torch.cuda.max_memory_allocated`` during the call, above what
        was allocated before it.
    """
    import torch

    torch.cuda.synchronize(device)
    torch.cuda.reset_peak_memory_stats(device)
    before = torch.cuda.memory_allocated(device)
    _attempt(call)
    torch.cuda.synchronize(device)
    return (torch.cuda.max_memory_allocated(device) - before) / MIB


@dataclass(frozen=True)
class TorchMeter:
    """Cost of a PyTorch method's calls on one device.

    Attributes:
        device: ``"cpu"``, ``"mps"`` or ``"cuda"``.
    """

    device: str

    @property
    def name(self) -> str:
        """``torch-cpu``, ``cuda``, or ``none`` on MPS, which has no peak counter."""
        return {"cpu": "torch-cpu", "cuda": "cuda"}.get(self.device, "none")

    def synchronize(self) -> None:
        """Wait for the kernels queued on the device, which run asynchronously."""
        import torch

        if self.device == "cuda":
            torch.cuda.synchronize()
        elif self.device == "mps":
            torch.mps.synchronize()

    def peak_mib(self, call: Callable[[], object]) -> float:
        """Peak tensor memory on the device, or NaN on MPS.

        MPS allocations reach neither the profiler nor a peak counter, and the
        process's resident memory does not tell one call from the next (see
        docs/decisions.md), so no figure is better than a wrong one.
        """
        if self.device == "cuda":
            return cuda_peak(call)
        if self.device == "cpu":
            return torch_cpu_peak(call)
        _attempt(call)
        return math.nan


def measure(
    call: Callable[[], object],
    repeats: int,
    warmup: int = 0,
    meter: Meter = TRACEMALLOC,
) -> Measured:
    """Time a call, then measure its peak memory.

    The call is made ``warmup`` times untimed, ``repeats`` times timed, and once
    more for its memory. Only the call is measured: whatever prepares its inputs
    happens before this function is entered.

    Args:
        call: Call to measure, with its inputs bound.
        repeats: Timed calls, at least one.
        warmup: Untimed calls made first, to pay one-off costs such as lazy
            imports and library initialisation.
        meter: How time and memory are read. The meter synchronises before each
            clock read, so work left running on a device is counted.

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
        meter.synchronize()
        start = perf_counter()
        outcomes.append(_attempt(call))
        meter.synchronize()
        seconds.append(perf_counter() - start)
    value, error = outcomes[0]
    return Measured(
        value=value,
        error=error,
        seconds=statistics.median(seconds),
        peak_mib=meter.peak_mib(call),
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


def _torch_threads() -> int | None:
    # Only if a method has loaded torch: importing it to read one number would
    # cost over a second.
    torch = sys.modules.get("torch")
    return None if torch is None else torch.get_num_threads()


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
            "torch": _torch_threads(),
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

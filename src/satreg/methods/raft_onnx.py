"""RAFT run by ONNX Runtime, from a file ``satreg export`` wrote.

The file holds a RAFT network with its weights and a fixed number of
refinements: which model it is, fine-tuned or not, refined how many times, is
the file's business and not a parameter here. It takes the images ``raft``
prepares and returns the flow on the CPU, without PyTorch: the same as
``raft`` to a fraction of a thousandth of a pixel wherever the model works,
and up to a pixel apart on pairs both fail. Needs the ``onnx`` extra.
"""

import functools
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

import numpy as np

from ..compute import ONNXRUNTIME, OnnxRuntimeMeter
from ..displacement import Dense
from ..weights import fetch as fetch_released
from ..weights import released_onnx
from .raft import network_input

# Modules the method needs. PyTorch is not one of them.
REQUIRED_MODULES = ("onnxruntime",)

# Names of the graph's inputs and output, written by the export: the two
# images as (1, 3, rows, cols) arrays, and the flow as (1, 2, rows, cols).
INPUTS = ("image1", "image2")
OUTPUT = "flow"

# The one device ONNX Runtime runs on here.
PROVIDERS = ("CPUExecutionProvider",)


def missing_modules() -> list[str]:
    """Name the modules the method needs that are not installed."""
    return [name for name in REQUIRED_MODULES if importlib.util.find_spec(name) is None]


@functools.cache
def _released_file(name: str) -> str:
    """Fetch a published file and check its hash once per process."""
    return str(fetch_released(name))


@functools.cache
def _session(path: str, threads: int) -> Any:
    """Open a file with ONNX Runtime once per process."""
    import onnxruntime

    if not Path(path).is_file():
        raise FileNotFoundError(f"no ONNX file at {path}: write it with satreg export")
    options = onnxruntime.SessionOptions()
    options.intra_op_num_threads = threads
    return onnxruntime.InferenceSession(path, options, providers=list(PROVIDERS))


@dataclass(frozen=True)
class RaftOnnx:
    """RAFT exported to ONNX, run by ONNX Runtime on the CPU.

    Attributes:
        file: Path of an ONNX file written by ``satreg export``.
        release: Name of a published ONNX file, a key of
            ``weights.RELEASED_ONNX``, downloaded on first use. One of the two
            is given.
        threads: Threads a call may use, 0 to let ONNX Runtime choose.
    """

    file: str = ""
    release: str = ""
    threads: int = 0

    # Modules the method runs on, imported before its memory footprint is read.
    runtime: ClassVar[tuple[str, ...]] = REQUIRED_MODULES

    def __post_init__(self) -> None:
        if bool(self.file) == bool(self.release):
            raise ValueError(
                "a method takes its ONNX file from a path or from a release, one "
                f"of the two: got {self.file!r} and {self.release!r}"
            )
        if self.release:
            released_onnx(self.release)
        if self.threads < 0:
            raise ValueError(f"threads must not be negative, got {self.threads}")

    @property
    def meter(self) -> OnnxRuntimeMeter:
        """Time the calls; no counter reads their memory."""
        return ONNXRUNTIME

    def session(self) -> Any:
        """The file opened by ONNX Runtime, once per process.

        Raises:
            FileNotFoundError: If the method's file is not there.
            WeightsUnavailable: If the released file is not cached and cannot
                be downloaded.
            WeightsRefused: If the downloaded file is not the pinned one.
        """
        return _session(self.file or _released_file(self.release), self.threads)

    def described(self) -> dict[str, str]:
        """What the file says of itself, as ``satreg export`` wrote it: its
        model, refinements, weights and whether they are fine-tuned."""
        return dict(self.session().get_modelmeta().custom_metadata_map)

    def __call__(self, reference: np.ndarray, moving: np.ndarray) -> Dense:
        """Estimate the displacement at every pixel.

        Args:
            reference: Reference image.
            moving: Moving image, same shape as ``reference``.

        Returns:
            The flow of the file's last refinement, on the reference grid.
        """
        rows, cols = reference.shape
        feeds = {
            name: network_input(image)[np.newaxis]
            for name, image in zip(INPUTS, (reference, moving), strict=True)
        }
        (flow,) = self.session().run([OUTPUT], feeds)
        # As for raft: the flow goes from the reference to the moving image,
        # in (x, y) order, on the padded grid.
        return Dense(flow[0, :, :rows, :cols][::-1])

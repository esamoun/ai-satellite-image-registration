"""Export RAFT to ONNX: one file per model, weights and refinement count.

RAFT refines its flow in a loop. The exporter traces the network once on an
example pair and writes what it saw, so the loop is unrolled: a file holds a
fixed number of refinements, and three counts are three files. The image size
stays free. Each file says where it comes from, in its metadata, and is checked
against PyTorch on one pair before it is kept. Needs the ``dl`` and ``onnx``
extras. See docs/decisions.md.
"""

import dataclasses
import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .compute import file_sha256
from .methods import deep
from .methods.raft import MIN_SIDE, Raft
from .methods.raft_onnx import INPUTS, OUTPUT, RaftOnnx
from .simulate import margin_for, simulate_translation
from .texture import fractal_texture
from .weights import onnx_name, released

# Modules an export needs besides PyTorch: one writes the file's metadata, the
# other runs the file for the parity check.
REQUIRED_MODULES = ("onnx", "onnxruntime")

# ONNX operator set the files are written in, the one the N2 spike exported
# RAFT with. RAFT's correlation lookup needs GridSample, which came with 16.
OPSET = 17

# Refinement counts exported by default: the one RAFT was trained with, and
# two cheaper ones.
REFINEMENTS = (4, 8, 12)

# Side of the blank pair the network is traced on, in px: the smallest RAFT
# takes. Nothing of the size is written to the file, whose axes stay free.
TRACE_SIDE = MIN_SIDE

# Largest difference accepted between the flow ONNX Runtime and PyTorch give on
# the parity pair, at any pixel, in px. A hundredth of the 0.1 px the project
# aims at; the N2 spike measured under 4e-4.
PARITY_TOLERANCE_PX = 1e-3

# The parity pair: a synthetic texture shifted by a fraction of a pixel, of a
# side the network was not traced on.
PARITY_SIDE = 256
PARITY_SHIFT = (1.37, -2.61)
PARITY_SEED = 0


class ParityError(Exception):
    """An exported file does not give PyTorch's flow."""


@dataclass(frozen=True)
class Exported:
    """One ONNX file and what was checked of it.

    Attributes:
        name: The file's name without its suffix.
        model: ``"large"`` or ``"small"``.
        weights: File name of the weights it holds, or their path for a
            checkpoint.
        refinements: Refinements of the flow it holds.
        megabytes: Size of the file, in MB.
        sha256: SHA-256 of the file.
        parity_px: Largest difference with PyTorch's flow on the parity pair,
            at any pixel, in px.
    """

    name: str
    model: str
    weights: str
    refinements: int
    megabytes: float
    sha256: str
    parity_px: float


def missing_modules() -> list[str]:
    """Name the modules an export needs that are not installed."""
    return deep.missing_modules(*REQUIRED_MODULES)


def weights_name(method: Raft, name: str) -> str:
    """What the weights of a method are called in the name of its exports.

    Args:
        method: A RAFT method.
        name: The method's name in the configuration, which names the weights
            of a checkpoint.

    Returns:
        The name of the released weights, ``raft_large`` or ``raft_small`` for
        the pretrained ones, the method's own name for a checkpoint.
    """
    if method.release:
        return method.release
    return name if method.checkpoint else f"raft_{method.model}"


def origin(method: Raft) -> dict[str, str]:
    """Name the weights a method runs, by file and hash.

    Returns:
        ``weights``, the file's name, or its path for a checkpoint, and
        ``weights_sha256``.
    """
    if method.release:
        weights = released(method.release)
        return {"weights": weights.asset, "weights_sha256": weights.sha256}
    if method.checkpoint:
        return {
            "weights": method.checkpoint,
            "weights_sha256": file_sha256(Path(method.checkpoint)),
        }
    cached = deep.weights_file(method.weights())
    return {"weights": cached.name, "weights_sha256": file_sha256(cached)}


def described(method: Raft, refinements: int) -> dict[str, str]:
    """What an exported file says of itself, in its metadata.

    Args:
        method: The method exported.
        refinements: Refinements written to the file.

    Returns:
        ``model``, ``iterations``, ``fine_tuned`` (``"true"`` or ``"false"``)
        and the weights' file and hash, all as text.
    """
    return {
        "model": method.model,
        # The refinements, under the key the published files were written
        # with: renaming it would change their bytes and their pinned hashes.
        "iterations": str(refinements),
        "fine_tuned": str(bool(method.checkpoint or method.release)).lower(),
        **origin(method),
    }


def _final_flow(network: Any, refinements: int) -> Any:
    """Wrap a RAFT network into a module that returns its last flow only."""
    import torch

    class FinalFlow(torch.nn.Module):
        """The network, refined a fixed number of times, as the exporter traces it."""

        def __init__(self) -> None:
            super().__init__()
            self.network = network

        def forward(self, image1: torch.Tensor, image2: torch.Tensor) -> torch.Tensor:
            """Return the flow of the last refinement, where RAFT returns them all."""
            return self.network(image1, image2, num_flow_updates=refinements)[-1]

    return FinalFlow().eval()


def export(method: Raft, refinements: int, path: Path) -> None:
    """Write a RAFT method to an ONNX file, with a fixed number of refinements.

    The file is written by PyTorch's TorchScript-based exporter, the one the N2
    spike found faster under ONNX Runtime, from the network on the CPU. Its
    metadata names the model, the refinements and the weights (``described``).

    Args:
        method: The method whose network and weights are exported.
        refinements: Refinements of the flow written to the file, whatever the
            method's own count.
        path: The file to write; parent directories are created.

    Raises:
        ValueError: If ``refinements`` is below one.
    """
    import onnx
    import torch

    if refinements < 1:
        raise ValueError(f"refinements must be positive, got {refinements}")
    network = dataclasses.replace(method, device="cpu").network()
    blank = torch.zeros(1, 3, TRACE_SIDE, TRACE_SIDE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with torch.no_grad(), warnings.catch_warnings():
        # The tracer warns of every value it writes as a constant, the size of
        # the correlation pyramid among them, and PyTorch of the exporter's age.
        warnings.simplefilter("ignore")
        torch.onnx.export(
            _final_flow(network, refinements),
            (blank, blank),
            str(path),
            dynamo=False,
            opset_version=OPSET,
            input_names=list(INPUTS),
            output_names=[OUTPUT],
            dynamic_axes={name: {2: "rows", 3: "cols"} for name in INPUTS},
        )
    graph = onnx.load(str(path))
    onnx.helper.set_model_props(graph, described(method, refinements))
    onnx.save(graph, str(path))


def parity_pair() -> tuple[np.ndarray, np.ndarray]:
    """The pair an export is compared with PyTorch on: reference and moving."""
    margin = margin_for(max(map(abs, PARITY_SHIFT)))
    source = fractal_texture(PARITY_SIDE + 2 * margin, seed=PARITY_SEED)
    dx, dy = PARITY_SHIFT
    pair = simulate_translation(source, dx=dx, dy=dy, margin=margin)
    return pair.reference, pair.moving


def parity(method: Raft, refinements: int, path: Path) -> float:
    """Compare an exported file with the PyTorch method it was exported from.

    Args:
        method: The PyTorch method.
        refinements: Refinements the file holds.
        path: The ONNX file.

    Returns:
        Largest difference between the two flows on the parity pair, at any
        pixel and along either axis, in px.
    """
    reference, moving = parity_pair()
    torch_method = dataclasses.replace(method, iterations=refinements, device="cpu")
    expected = torch_method(reference, moving).values
    found = RaftOnnx(file=str(path))(reference, moving).values
    return float(np.abs(found - expected).max())


def export_checked(method: Raft, name: str, refinements: int, out: Path) -> Exported:
    """Export a method with one refinement count and check the file.

    Args:
        method: The PyTorch method.
        name: The method's name in the configuration.
        refinements: Refinements written to the file.
        out: Directory the file is written to, named after its weights and
            refinements.

    Returns:
        The file and its parity with PyTorch.

    Raises:
        ParityError: If the file's flow is further than
            ``PARITY_TOLERANCE_PX`` from PyTorch's. The file is left there.
    """
    stem = onnx_name(weights_name(method, name), refinements)
    path = out / f"{stem}.onnx"
    export(method, refinements, path)
    difference = parity(method, refinements, path)
    if not difference <= PARITY_TOLERANCE_PX:
        raise ParityError(
            f"{path} is {difference:.2e} px from PyTorch on the parity pair, over "
            f"the {PARITY_TOLERANCE_PX:g} px accepted"
        )
    return Exported(
        name=stem,
        model=method.model,
        weights=origin(method)["weights"],
        refinements=refinements,
        megabytes=path.stat().st_size / 1e6,
        sha256=file_sha256(path),
        parity_px=difference,
    )


def to_markdown(rows: Sequence[Exported]) -> str:
    """Render the exported files as a table.

    Args:
        rows: The files.

    Returns:
        Markdown: one line per file, with its size, parity and hash.
    """
    lines = [
        "| file | model | weights | refinements | MB | parity with PyTorch (px) "
        "| SHA-256 |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    lines += [
        f"| `{row.name}.onnx` | RAFT {row.model} | `{row.weights}` | "
        f"{row.refinements} | {row.megabytes:.1f} | {row.parity_px:.1e} | "
        f"`{row.sha256}` |"
        for row in rows
    ]
    return "\n".join(lines) + "\n"

"""Spike (N2 ticket 02): does torchvision's RAFT export to ONNX?

Throwaway: exports RAFT with the TorchScript-based and the dynamo-based
exporters, runs the result under ONNX Runtime on the CPU, compares its flow with
PyTorch's on one simulated Beauce pair, and checks that dynamic int8
quantization runs. Findings are in docs/decisions.md. Needs the ``dl`` extra
plus ``onnx``, ``onnxruntime`` and ``onnxscript``.

Kept as the record of what N2 measured. The files the project runs are written
by ``satreg export`` (``src/satreg/onnxexport.py``) since N3 ticket 10.

    python scripts/raft_onnx_spike.py --model large --exporter legacy
"""

import argparse
import sys
import tempfile
import time
import traceback
from pathlib import Path

import numpy as np
import torch

from satreg.ingest import read_chip
from satreg.methods.raft import Raft, network_input
from satreg.simulate import margin_for, simulate_translation

CHIP_DIR = Path(__file__).resolve().parents[1] / "data" / "chips" / "beauce"


class FinalFlow(torch.nn.Module):
    """RAFT with a fixed number of refinements, returning the last flow only."""

    def __init__(self, network: torch.nn.Module, iterations: int) -> None:
        super().__init__()
        self.network = network
        self.iterations = iterations

    def forward(self, image1: torch.Tensor, image2: torch.Tensor) -> torch.Tensor:
        return self.network(image1, image2, num_flow_updates=self.iterations)[-1]


def pair(size: int) -> tuple[np.ndarray, np.ndarray]:
    """One simulated Beauce translation pair, as RAFT's inputs."""
    chip = read_chip(next(CHIP_DIR.glob("*.tif")))
    margin = margin_for(3.0)
    source = chip[: size + 2 * margin, : size + 2 * margin]
    simulated = simulate_translation(source, dx=1.37, dy=-2.61, margin=margin)
    return (
        network_input(simulated.reference)[None],
        network_input(simulated.moving)[None],
    )


def median_ms(call, repeats: int = 5) -> float:
    call()
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        call()
        times.append(time.perf_counter() - start)
    return 1000 * float(np.median(times))


def export(module, inputs, path: Path, exporter: str, dynamic: bool, opset: int):
    names = {"input_names": ["image1", "image2"], "output_names": ["flow"]}
    if exporter == "legacy":
        axes = {"image1": {2: "rows", 3: "cols"}, "image2": {2: "rows", 3: "cols"}}
        torch.onnx.export(
            module,
            inputs,
            str(path),
            dynamo=False,
            opset_version=opset,
            dynamic_axes=axes if dynamic else None,
            **names,
        )
    else:
        shapes = None
        if dynamic:
            rows, cols = torch.export.Dim("rows"), torch.export.Dim("cols")
            shapes = {"image1": {2: rows, 3: cols}, "image2": {2: rows, 3: cols}}
        program = torch.onnx.export(
            module,
            inputs,
            dynamo=True,
            opset_version=opset,
            dynamic_shapes=shapes,
            **names,
        )
        program.save(str(path))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="large", choices=("large", "small"))
    parser.add_argument("--exporter", default="legacy", choices=("legacy", "dynamo"))
    parser.add_argument("--iterations", type=int, default=12)
    parser.add_argument("--opset", type=int, default=17)
    parser.add_argument("--dynamic", action="store_true")
    parser.add_argument("--size", type=int, default=256)
    parser.add_argument("--also-size", type=int, default=512)
    parser.add_argument("--quantize", action="store_true")
    args = parser.parse_args()

    import onnxruntime as ort

    torch.set_num_threads(4)
    network = Raft(model=args.model).network()
    module = FinalFlow(network, args.iterations).eval()
    image1, image2 = pair(args.size)
    inputs = (torch.from_numpy(image1), torch.from_numpy(image2))

    with torch.inference_mode():
        reference = module(*inputs).numpy()

    def torch_call() -> None:
        with torch.inference_mode():
            module(*inputs)

    torch_ms = median_ms(torch_call)

    out = Path(tempfile.mkdtemp()) / f"raft_{args.model}.onnx"
    print(f"torch {torch.__version__}, ort {ort.__version__}, opset {args.opset}")
    print(f"exporting {args.model} ({args.exporter}, dynamic={args.dynamic})")
    start = time.perf_counter()
    try:
        with torch.no_grad():
            export(module, inputs, out, args.exporter, args.dynamic, args.opset)
    except Exception:  # noqa: BLE001 - a spike: report whatever breaks
        traceback.print_exc(limit=6)
        print("EXPORT FAILED")
        return 1
    print(
        f"exported in {time.perf_counter() - start:.1f} s, "
        f"{out.stat().st_size / 2**20:.1f} MiB -> {out}"
    )

    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    session = ort.InferenceSession(
        str(out), options, providers=["CPUExecutionProvider"]
    )
    feed = {"image1": image1, "image2": image2}
    flow = session.run(None, feed)[0]
    diff = np.hypot(*(flow - reference)[0])
    ort_ms = median_ms(lambda: session.run(None, feed))
    print(f"max |flow diff| {diff.max():.2e} px, mean {diff.mean():.2e} px")
    print(
        f"time per pair at {args.size} px: torch {torch_ms:.0f} ms, ort {ort_ms:.0f} ms"
    )

    if args.dynamic:
        big1, big2 = pair(args.also_size)
        try:
            flow = session.run(None, {"image1": big1, "image2": big2})[0]
            with torch.inference_mode():
                ref = module(torch.from_numpy(big1), torch.from_numpy(big2)).numpy()
            print(
                f"at {args.also_size} px: max |flow diff| "
                f"{np.hypot(*(flow - ref)[0]).max():.2e} px"
            )
        except Exception as error:  # noqa: BLE001
            print(f"at {args.also_size} px: FAILED: {str(error)[:300]}")

    if args.quantize:
        from onnxruntime.quantization import QuantType, quantize_dynamic

        quantized = out.with_name(out.stem + "_int8.onnx")
        try:
            quantize_dynamic(str(out), str(quantized), weight_type=QuantType.QInt8)
            q_session = ort.InferenceSession(
                str(quantized), options, providers=["CPUExecutionProvider"]
            )
            q_flow = q_session.run(None, feed)[0]
            q_ms = median_ms(lambda: q_session.run(None, feed))
            q_diff = np.hypot(*(q_flow - reference)[0])
            print(
                f"int8: {quantized.stat().st_size / 2**20:.1f} MiB, {q_ms:.0f} ms, "
                f"max |flow diff| vs torch {q_diff.max():.2e} px "
                f"(mean {q_diff.mean():.2e})"
            )
        except Exception:  # noqa: BLE001
            traceback.print_exc(limit=6)
            print("QUANTIZATION FAILED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

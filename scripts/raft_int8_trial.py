"""Trial (N3 ticket 11): does static int8 quantization of RAFT pay under ONNX Runtime?

Throwaway: quantizes one exported RAFT file in several ways, static on a handful
of calibration pairs and dynamic beside it, and says of each what the ticket
asks before going further: does it run, which operators end up int8, how many
quantize/dequantize hops surround the float ``GridSample`` nodes, size, speed,
and how far the flow moves from the float file's. Findings are in
docs/decisions.md. Needs the ``dl`` and ``onnx`` extras.

Calibration and evaluation pairs both come from the validation chips, and from
different pair indices: the evaluation pairs are the first of every cell of the
light validation set, the calibration pairs are drawn past its end.

A variant is a selection of nodes, then options joined by ``+``: ``conv`` is every
convolution, ``guarded+perchannel+entropy`` the guarded selection with one scale
per output channel and ranges calibrated by entropy.

    python scripts/raft_int8_trial.py --file outputs/onnx/raft_large_r12.onnx
"""

import argparse
import collections
import dataclasses
import sys
import tempfile
import time
import traceback
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
from onnxruntime.quantization import (
    CalibrationDataReader,
    CalibrationMethod,
    QuantFormat,
    QuantType,
    quantize_dynamic,
    quantize_static,
)
from onnxruntime.quantization.shape_inference import quant_pre_process

from satreg import cli, validation
from satreg.benchmark import simulated_pairs
from satreg.displacement import Dense
from satreg.methods.raft import network_input
from satreg.metrics import is_failure, score
from satreg.simulate import SimulatedPair

VALIDATION_CONFIG = Path("configs/validation.toml")
THREADS = 4
ENCODERS = ("/network/feature_encoder/", "/network/context_encoder/")
UPDATE = ("/network/update_block/", "/network/mask_predictor/")
# Convolutions that read the flow, or write the flow update and the upsampling
# mask: eight bits over a range of tens of pixels is a coarse ruler for those.
FLOW_EDGES = ("/motion_encoder/convflow1/", "/flow_head/conv2", "/mask_predictor/conv/")
RECURRENT = ("/recurrent_block/",)
METHODS = {
    "minmax": CalibrationMethod.MinMax,
    "entropy": CalibrationMethod.Entropy,
    "percentile": CalibrationMethod.Percentile,
}
# Operators that compute on integers, in a graph ONNX Runtime has optimized.
INT8_OPS = (
    "QLinearConv",
    "QLinearMatMul",
    "QLinearAdd",
    "QLinearMul",
    "QLinearConcat",
    "QLinearSigmoid",
    "QLinearAveragePool",
    "QLinearLeakyRelu",
    "QLinearSoftmax",
    "ConvInteger",
    "MatMulInteger",
)


def validation_pairs(first: int, last: int) -> list[tuple[dict, SimulatedPair]]:
    """The validation pairs of indices ``first`` to ``last - 1`` of every cell."""
    table = cli.load_run_config(VALIDATION_CONFIG, "validate")
    options = cli._parser(table, "validate").parse_args(["validate"])
    training, series = cli._training(options)
    config = dataclasses.replace(cli._benchmark_config(options), n_pairs=last)
    anchors = validation.load_validation_chips(
        training, series, options.data_dir, options.chips
    )
    images = {name: anchor.image for name, anchor in anchors.items()}
    presets = cli.degradation_presets(options)
    return [
        (labels, pair)
        for labels, pair in simulated_pairs(images, config, presets)
        if labels["pair"] >= first
    ]


def feed(pair: SimulatedPair) -> dict[str, np.ndarray]:
    return {
        "image1": network_input(pair.reference)[np.newaxis],
        "image2": network_input(pair.moving)[np.newaxis],
    }


class Reader(CalibrationDataReader):
    """Hands the calibration pairs to ONNX Runtime, one at a time."""

    def __init__(self, pairs: list[SimulatedPair]) -> None:
        self.feeds = iter([feed(pair) for pair in pairs])

    def get_next(self) -> dict[str, np.ndarray] | None:
        return next(self.feeds, None)


def session(path: Path, optimized: Path | None = None) -> ort.InferenceSession:
    options = ort.SessionOptions()
    options.intra_op_num_threads = THREADS
    if optimized is not None:
        options.optimized_model_filepath = str(optimized)
    return ort.InferenceSession(str(path), options, providers=["CPUExecutionProvider"])


def median_ms(call, repeats: int = 5) -> float:
    call()
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        call()
        times.append(time.perf_counter() - start)
    return 1000 * float(np.median(times))


def conv_names(
    path: Path, prefixes: tuple[str, ...] = ("",), without: tuple[str, ...] = ()
) -> list[str]:
    graph = onnx.load(str(path)).graph
    return [
        node.name
        for node in graph.node
        if node.op_type == "Conv"
        and node.name.startswith(prefixes)
        and not any(part in node.name for part in without)
    ]


def interleaved_ms(
    files: dict[str, Path], one: dict[str, np.ndarray], rounds: int
) -> dict[str, float]:
    """Median time of each file, the files taking turns so heat is shared."""
    sessions = {name: session(path) for name, path in files.items()}
    times = collections.defaultdict(list)
    for turn in range(rounds + 1):
        for name, run in sessions.items():
            start = time.perf_counter()
            run.run(["flow"], one)
            if turn:
                times[name].append(time.perf_counter() - start)
    return {name: 1000 * float(np.median(spent)) for name, spent in times.items()}


def describe_graph(path: Path) -> str:
    """Count the operators ONNX Runtime runs, and the hops around GridSample."""
    graph = onnx.load(str(path)).graph
    counts = collections.Counter(node.op_type for node in graph.node)
    producer = {out: node.op_type for node in graph.node for out in node.output}
    consumers = collections.defaultdict(list)
    for node in graph.node:
        for name in node.input:
            consumers[name].append(node.op_type)
    samples = [node for node in graph.node if node.op_type == "GridSample"]
    hops_in = sum(
        producer.get(name) == "DequantizeLinear"
        for node in samples
        for name in node.input
    )
    hops_out = sum(
        "QuantizeLinear" in consumers[name] for node in samples for name in node.output
    )
    integer = {op: counts[op] for op in INT8_OPS if counts[op]}
    float_convs = counts["Conv"]
    hops = {
        op: counts[op]
        for op in ("QuantizeLinear", "DequantizeLinear", "DynamicQuantizeLinear")
        if counts[op]
    }
    return (
        f"{len(graph.node)} nodes; int8 {integer or 'none'}; float Conv "
        f"{float_convs}; hops {hops or 'none'}; GridSample {len(samples)} "
        f"(dequantized inputs {hops_in}, quantized outputs {hops_out})"
    )


def evaluate(
    path: Path, pairs: list[tuple[dict, SimulatedPair]], float_flows: list | None
) -> tuple[list[np.ndarray], str]:
    """Run a file on the evaluation pairs: its flows, and a line about them."""
    run = session(path)
    flows, epes, failed, moved = [], [], 0, []
    by_preset = collections.defaultdict(list)
    for index, (labels, pair) in enumerate(pairs):
        (flow,) = run.run(["flow"], feed(pair))
        flows.append(flow)
        rows, cols = pair.reference.shape
        scored = score(
            pair.truth,
            Dense(flow[0, :, :rows, :cols][::-1]),
            pair.reference.shape,
            pair.valid,
        )
        if is_failure(scored):
            failed += 1
        else:
            epes.append(scored.mean_epe)
        if float_flows is not None:
            moved.append(float(np.hypot(*(flow - float_flows[index])[0]).mean()))
            by_preset[labels["degradation"]].append(moved[-1])
    one = feed(pairs[0][1])
    ms = median_ms(lambda: run.run(["flow"], one))
    line = (
        f"{path.stat().st_size / 1e6:.1f} MB, {ms:.0f} ms, EPE "
        f"{np.mean(epes) if epes else float('nan'):.4f} px over "
        f"{len(epes)}/{len(pairs)} pairs, {failed} failed"
    )
    if moved:
        line += (
            f", flow moved from float by {np.mean(moved):.4f} px on average "
            f"(worst pair {np.max(moved):.4f}; "
            + ", ".join(f"{k} {np.mean(v):.4f}" for k, v in by_preset.items())
            + ")"
        )
    return flows, line


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--calibration", type=int, default=12)
    parser.add_argument("--method", default="minmax", choices=tuple(METHODS))
    parser.add_argument("--evaluation", type=int, default=1)
    parser.add_argument(
        "--variants",
        nargs="+",
        default=["all", "conv", "encoders", "update", "dynamic"],
    )
    parser.add_argument("--rounds", type=int, default=7)
    parser.add_argument("--clean-only", action="store_true")
    parser.add_argument("--keep", type=Path, default=None)
    args = parser.parse_args()

    work = args.keep or Path(tempfile.mkdtemp())
    work.mkdir(parents=True, exist_ok=True)
    print(f"onnxruntime {ort.__version__}, {args.file}, {THREADS} threads")

    evaluation = validation_pairs(0, args.evaluation)
    pool = validation_pairs(10, 11)
    # The cells come scenario by scenario, three degradation presets each: a plain
    # one-in-three would calibrate on clean pairs only, and the ranges it finds
    # are too narrow for the hard ones. Step along a diagonal instead.
    step = max(1, len(pool) // args.calibration)
    picks = [turn * step + turn % step for turn in range(len(pool) // step)]
    if args.clean_only:
        picks = list(range(0, len(pool), step))
    calibration = [pool[pick][1] for pick in picks][: args.calibration]
    print(
        "calibration presets:",
        dict(collections.Counter(pool[pick][0]["degradation"] for pick in picks)),
    )
    print(
        f"{len(evaluation)} evaluation pairs, {len(calibration)} calibration pairs "
        f"of {len(pool)}, {args.method} unless a variant says otherwise, images "
        f"{feed(evaluation[0][1])['image1'].shape}"
    )

    optimized = work / "float.optimized.onnx"
    session(args.file, optimized)
    print(f"float: {describe_graph(optimized)}")
    float_flows, line = evaluate(args.file, evaluation, None)
    print(f"float: {line}")

    # Symbolic shape inference does not get through this graph ("Incomplete
    # symbolic shape inference"), so the preparation runs without it.
    prepared = work / "prepared.onnx"
    quant_pre_process(str(args.file), str(prepared), skip_symbolic_shape=True)

    selections = {
        "all": {},
        "conv": {"op_types_to_quantize": ["Conv"]},
        "encoders": {"nodes_to_quantize": conv_names(prepared, ENCODERS)},
        "update": {"nodes_to_quantize": conv_names(prepared, UPDATE)},
        "guarded": {"nodes_to_quantize": conv_names(prepared, without=FLOW_EDGES)},
        "noflowin": {"nodes_to_quantize": conv_names(prepared, without=FLOW_EDGES[:1])},
        "noflowout": {
            "nodes_to_quantize": conv_names(prepared, without=FLOW_EDGES[1:2])
        },
        "nomask": {"nodes_to_quantize": conv_names(prepared, without=FLOW_EDGES[2:])},
        "feedforward": {
            "nodes_to_quantize": conv_names(prepared, without=FLOW_EDGES + RECURRENT)
        },
    }
    # Ranges are folded in every few pairs to hold memory down. ONNX Runtime
    # raises "No data is collected" when the last chunk comes out empty, so the
    # chunk must not divide the number of pairs.
    chunk = next(size for size in range(8, 1, -1) if len(calibration) % size)
    built = {"float": args.file}
    for variant in args.variants:
        selection, *flags = variant.split("+")
        method = next((flag for flag in flags if flag in METHODS), args.method)
        path = work / f"{variant}.onnx"
        start = time.perf_counter()
        try:
            if selection == "dynamic":
                quantize_dynamic(str(args.file), str(path), weight_type=QuantType.QInt8)
            else:
                quantize_static(
                    str(prepared),
                    str(path),
                    Reader(calibration),
                    quant_format=QuantFormat.QDQ,
                    per_channel="perchannel" in flags,
                    activation_type=QuantType.QUInt8
                    if "uint8" in flags
                    else QuantType.QInt8,
                    weight_type=QuantType.QInt8,
                    calibrate_method=METHODS[method],
                    extra_options={"CalibMaxIntermediateOutputs": chunk},
                    **selections[selection],
                )
            seconds = time.perf_counter() - start
            optimized = work / f"{variant}.optimized.onnx"
            session(path, optimized)
            print(
                f"{variant}: quantized in {seconds:.0f} s; {describe_graph(optimized)}"
            )
            _, line = evaluate(path, evaluation, float_flows)
            print(f"{variant}: {line}")
            built[variant] = path
        except Exception:  # noqa: BLE001 - a trial: report whatever breaks
            traceback.print_exc(limit=4)
            print(f"{variant}: FAILED")
        sys.stdout.flush()

    timed = interleaved_ms(built, feed(evaluation[0][1]), args.rounds)
    print(f"interleaved, median of {args.rounds} rounds, one pair:")
    for name, ms in timed.items():
        print(f"  {name}: {ms:.0f} ms ({ms / timed['float']:.2f} of float)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

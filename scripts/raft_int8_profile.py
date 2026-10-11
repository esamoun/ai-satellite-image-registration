"""Profile (N3 ticket 11): where does the time of an exported RAFT file go?

Throwaway: runs exported files under ONNX Runtime with its profiler on, on one
validation pair, and gives the time of a call by kind of operator. It is what
says what the float ``GridSample`` costs an int8 copy. Findings are in
docs/decisions.md. Needs the ``dl`` and ``onnx`` extras.

    python scripts/raft_int8_profile.py outputs/onnx/raft_large_ft_r12.onnx \
        outputs/onnx/raft_large_ft_r12_int8.onnx
"""

import argparse
import collections
import json
import sys
import tempfile
from pathlib import Path

import onnxruntime as ort
from raft_int8_trial import THREADS, feed, validation_pairs

# Operators given a line of their own; the others are summed.
SHOWN = 6


def profile(path: Path, inputs: dict, calls: int) -> dict[str, float]:
    """Time of a call by kind of operator, in ms: the mean of ``calls`` calls
    made after a first one, which is not counted."""
    with tempfile.TemporaryDirectory() as scratch:
        options = ort.SessionOptions()
        options.intra_op_num_threads = THREADS
        options.enable_profiling = True
        options.profile_file_prefix = str(Path(scratch) / "profile")
        session = ort.InferenceSession(
            str(path), options, providers=["CPUExecutionProvider"]
        )
        for _ in range(1 + calls):
            session.run(None, inputs)
        events = json.loads(Path(session.end_profiling()).read_text())
    runs = sorted(event["ts"] for event in events if event["name"] == "model_run")
    spent: dict[str, float] = collections.defaultdict(float)
    for event in events:
        counted = event["cat"] == "Node" and event["name"].endswith("_kernel_time")
        if counted and event["ts"] >= runs[1]:
            spent[event["args"]["op_name"]] += event["dur"] / 1000 / calls
    return dict(sorted(spent.items(), key=lambda item: -item[1]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", type=Path, nargs="+")
    parser.add_argument("--calls", type=int, default=10)
    args = parser.parse_args()
    _, pair = validation_pairs(0, 1)[0]
    for path in args.files:
        spent = profile(path, feed(pair), args.calls)
        total = sum(spent.values())
        shown = list(spent.items())[:SHOWN]
        other = total - sum(ms for _, ms in shown)
        cells = [f"{name} {ms:.0f}" for name, ms in (*shown, ("others", other))]
        print(f"{path.stem}: {total:.0f} ms in operators: " + ", ".join(cells))
    return 0


if __name__ == "__main__":
    sys.exit(main())

# syntax=docker/dockerfile:1

# The container image of `satreg`: the package, ONNX Runtime, the classic
# methods and the nine fine-tuned RAFT files, with no PyTorch. It registers a
# supplied pair and runs a small benchmark with no network.
#
#   docker build --secret id=github_token,env=GITHUB_TOKEN --tag satreg:local .
#   docker run --rm --network none satreg:local register
#
# What is in it, what is left out and why: docs/decisions.md, entries of
# 2026-10-13. The rationale lives there and is not repeated here.

# The Python the development machine runs. Built for amd64 and arm64: every
# dependency has a wheel for both, so nothing is compiled.
FROM python:3.13-slim

# Where the fine-tuned files are cached and read: `satreg` works out PyTorch's
# cache directory from TORCH_HOME without importing PyTorch. matplotlib wants a
# directory it can write to, whichever user the container image runs as.
# ONNX Runtime 1.31 carries telemetry, which is on unless this variable is set.
ENV TORCH_HOME=/opt/satreg/cache \
    MPLCONFIGDIR=/tmp/matplotlib \
    ORT_DISABLE_TELEMETRY=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Paths in the configs are relative to the working directory, as they are to
# the repository root on a laptop.
WORKDIR /app

# The one system library a wheel asks for and does not carry: rasterio's wheel
# loads libexpat.so.1, which the slim base does not have.
RUN apt-get update \
    && apt-get install --yes --no-install-recommends libexpat1 \
    && rm -rf /var/lib/apt/lists/*

# The package, then ONNX Runtime alone: the `onnx` extra also brings `onnx`,
# which only `satreg export` needs, with PyTorch. The install leaves a copy of
# the package behind in `build/`, which nothing reads.
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/
RUN pip install . onnxruntime && rm -rf build

# The nine ONNX files of the release, each checked against the SHA-256 pinned
# in src/satreg/weights.py: a file with another hash fails the build. While the
# repository is private the download needs a token, mounted for this step only
# and written to no layer. Without one the files are read from the release's
# public address.
RUN --mount=type=secret,id=github_token,env=GITHUB_TOKEN \
    python -c "from satreg import weights; [print(weights.fetch(name)) for name in weights.RELEASED_ONNX]"

# The method parameters and run configs, the demo pairs, and the Beauce
# benchmark chip where `satreg benchmark` looks for it.
COPY configs/ configs/
COPY examples/ examples/
COPY docker/data/ data/

ENTRYPOINT ["satreg"]
CMD ["--help"]

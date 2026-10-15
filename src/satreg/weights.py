"""The fine-tuned weights, published as assets of a GitHub release.

A training's kept checkpoint leaves the machine that trained it as a release
asset, and so do its exports to ONNX, one per refinement count. This module
names each published file with its SHA-256, downloads it once to PyTorch's
cache, next to the pretrained weights torchvision puts there, and refuses a
file whose hash is not the one written here. The repository is public and
the download needs no token; one is still taken from the environment, as when
the repository was private, and sent to GitHub's API only. See
docs/decisions.md.
"""

import json
import os
import shutil
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .compute import file_sha256

# The repository whose releases hold the weights, as owner/name.
REPOSITORY = "esamoun/ai-satellite-image-registration"

# The environment variable a token is read from, for a repository that is not
# public; this one is, and needs none. The token is never an option of a
# command: options are written to context.json.
TOKEN_VARIABLE = "GITHUB_TOKEN"

# Seconds without an answer before a request to GitHub is given up.
TIMEOUT = 30.0

# Bytes read at a time from a download.
BLOCK = 1 << 20

# Keys of a checkpoint that only resuming its training needs: a file with one
# of them is a run's checkpoint, not its kept weights, and is not published.
RESUME_KEYS = ("optimizer", "schedule")

# What a published file says of its training, copied to the JSON beside it.
DESCRIBED_KEYS = (
    "step",
    "validation",
    "train",
    "pairs",
    "ranges",
    "chips",
    "commit",
    "dirty",
)

# On what terms the weights are published, from what was read of their sources
# (docs/decisions.md, entry of 2026-10-15). The release's notes end with it, and
# the README carries it word for word: the container image holds the README.
WEIGHTS_TERMS = (
    "**The fine-tuned weights.** The MIT licence covers the code. It does not "
    "settle the terms of the fine-tuned RAFT weights, or of the ONNX files made "
    "from them. They start from torchvision's pretrained weights, "
    "`Raft_Large_Weights.C_T_SKHT_V2` and `Raft_Small_Weights.C_T_V2`, which carry "
    "no licence of their own. torchvision warns that a pretrained model may carry "
    "the terms of its training data, and leaves them to the user. Both models were "
    "trained on FlyingChairs and FlyingThings3D. The large one was then trained on "
    "Sintel, KITTI and HD1K. FlyingChairs and FlyingThings3D are for research only, "
    "and forbid any commercial use. KITTI is under CC BY-NC-SA 3.0. Sintel's pages "
    "state no licence, and nor does HD1K's page as archived in 2024. Whether a "
    "dataset's terms reach the weights trained on it is not settled here. The "
    "fine-tuned weights are published for research and for reproducing this "
    "project's results. No commercial right is granted. The sources, as read on "
    "2026-10-15, are in [`docs/decisions.md`]"
    f"(https://github.com/{REPOSITORY}/blob/main/docs/decisions.md)."
)


class WeightsUnavailable(Exception):
    """Published weights are not cached and could not be downloaded."""


class WeightsRefused(Exception):
    """A file is not the published weights: its SHA-256 is not the pinned one."""


@dataclass(frozen=True)
class ReleasedWeights:
    """The kept weights of a training, as published.

    Attributes:
        name: What the weights are called in ``configs/methods.toml``.
        model: ``"large"`` or ``"small"``, the RAFT model they are for.
        run: The training they come from, a directory of ``outputs/train/``.
        tag: Tag of the release that holds them.
        sha256: SHA-256 of the file, the one its scored tables recorded.
    """

    name: str
    model: str
    run: str
    tag: str
    sha256: str

    @property
    def asset(self) -> str:
        """File name in the release and in the cache, as torchvision names its
        own: the name, then the first eight digits of the hash."""
        return f"{self.name}-{self.sha256[:8]}.pth"

    @property
    def card(self) -> str:
        """File name of the JSON that describes the training, beside the asset."""
        return Path(self.asset).with_suffix(".json").name


# The published weights, by name. Each is the best.pt of its training, byte for
# byte, so its hash is the one in the context.json of the tables that scored it
# (docs/results/n3/).
RELEASED = {
    weights.name: weights
    for weights in (
        ReleasedWeights(
            name="raft_large_ft",
            model="large",
            run="large-cross-date",
            tag="weights-n3",
            sha256="44bcc668d20a633410259e43de2c56a4712c4e23860fb8f456cc5bb6a8589d13",
        ),
        ReleasedWeights(
            name="raft_small_ft",
            model="small",
            run="small-cross-date",
            tag="weights-n3",
            sha256="b666aaadf41886411bc53665aa6c3e30ab699d211cbe4ae97025c41e0a10e137",
        ),
    )
}


@dataclass(frozen=True)
class ReleasedOnnx:
    """Published weights exported to ONNX with one refinement count.

    Attributes:
        weights: Name of the published weights the file was exported from, a
            key of ``RELEASED``.
        refinements: Refinements of the flow the file holds, unrolled.
        tag: Tag of the release that holds it.
        sha256: SHA-256 of the file ``satreg export`` wrote, or of the int8
            copy ``satreg quantize`` made of it.
        int8: Whether the file is that copy, quantized to 8-bit integers.
    """

    weights: str
    refinements: int
    tag: str
    sha256: str
    int8: bool = False

    @property
    def name(self) -> str:
        """What the file is called in ``configs/methods.toml``, and by
        ``satreg export`` or ``satreg quantize`` without the suffix."""
        return onnx_name(self.weights, self.refinements) + (
            INT8_SUFFIX if self.int8 else ""
        )

    @property
    def asset(self) -> str:
        """File name in the release and in the cache, as for the weights."""
        return f"{self.name}-{self.sha256[:8]}.onnx"


Released = ReleasedWeights | ReleasedOnnx


# What the name of an ONNX export takes when the file is its int8 copy, the one
# calibrated on validation pairs (see satreg.quantize).
INT8_SUFFIX = "_int8"


def onnx_name(weights: str, refinements: int) -> str:
    """Name of an ONNX export: its weights, then ``r`` and its refinements."""
    return f"{weights}_r{refinements}"


# The published ONNX files, by name: each of the published weights with 4, 8
# and 12 refinements, as `satreg export` wrote them on the machine of
# docs/results/n3/context-onnx.json. An export is byte for byte the same there
# from one run to the next, and nothing says it is on another machine or
# version of PyTorch: these files are downloaded, not rebuilt. Then the int8
# copies kept for the cost curve, as `satreg quantize` wrote them there
# (docs/results/n3/int8-files.md): the static ones of RAFT large.
RELEASED_ONNX = {
    exported.name: exported
    for exported in (
        ReleasedOnnx(
            weights="raft_large_ft",
            refinements=4,
            tag="weights-n3",
            sha256="c8ee13ca706020957af22b3f0b1a686e6bc562e010cfbc83c8ebbb6fa39b1ede",
        ),
        ReleasedOnnx(
            weights="raft_large_ft",
            refinements=8,
            tag="weights-n3",
            sha256="813662803b0cca223bcde6a9c1be0f7d6c1e7e515301961624c2ebf8213afe2c",
        ),
        ReleasedOnnx(
            weights="raft_large_ft",
            refinements=12,
            tag="weights-n3",
            sha256="da410478e79cb32343b6f8c2c0f88e53d0b93d192a1152d8b3e088aef242fcfe",
        ),
        ReleasedOnnx(
            weights="raft_small_ft",
            refinements=4,
            tag="weights-n3",
            sha256="72fa35ab2a2c537a6f3dda9aacc057498cbd69a7ac676c6eee0352b189f17361",
        ),
        ReleasedOnnx(
            weights="raft_small_ft",
            refinements=8,
            tag="weights-n3",
            sha256="7cac15615efd9ec3771421f6eab8daa3b19da78f21e86b2aba6a238fcbec6359",
        ),
        ReleasedOnnx(
            weights="raft_small_ft",
            refinements=12,
            tag="weights-n3",
            sha256="c7671f015621fa28434bd9f39b61632ebec45650791fd6611ce2cecbddf4ed76",
        ),
        ReleasedOnnx(
            weights="raft_large_ft",
            refinements=4,
            tag="weights-n3",
            sha256="51b27700729010b0d2ecd67f8ebdb22619c8bcb3de1fbfd3ef81ecca63e05dd0",
            int8=True,
        ),
        ReleasedOnnx(
            weights="raft_large_ft",
            refinements=8,
            tag="weights-n3",
            sha256="3d91f7b91ca04418de0f119c2d7738ed2272ace7b5548b290aa367dbb72e4dd3",
            int8=True,
        ),
        ReleasedOnnx(
            weights="raft_large_ft",
            refinements=12,
            tag="weights-n3",
            sha256="97b6a8c7e0e66f008de4ffcc61030c03bc18a9587e236af8ef5173b12ccff609",
            int8=True,
        ),
    )
}


def released(name: str) -> ReleasedWeights:
    """The published weights of a name.

    Raises:
        ValueError: If no weights are published under ``name``.
    """
    if name not in RELEASED:
        raise ValueError(
            f"no released weights named {name!r} (released: {', '.join(RELEASED)})"
        )
    return RELEASED[name]


def released_onnx(name: str) -> ReleasedOnnx:
    """The published ONNX file of a name.

    Raises:
        ValueError: If no ONNX file is published under ``name``.
    """
    if name not in RELEASED_ONNX:
        raise ValueError(
            f"no released ONNX file named {name!r} "
            f"(released: {', '.join(RELEASED_ONNX)})"
        )
    return RELEASED_ONNX[name]


def lookup(name: str) -> Released:
    """The published file of a name, weights or ONNX export.

    Raises:
        ValueError: If nothing is published under ``name``.
    """
    if name in RELEASED:
        return RELEASED[name]
    if name in RELEASED_ONNX:
        return RELEASED_ONNX[name]
    raise ValueError(
        f"no released file named {name!r} "
        f"(released: {', '.join((*RELEASED, *RELEASED_ONNX))})"
    )


def cache_directory() -> Path:
    """Where the files are cached: PyTorch's own cache of checkpoints.

    PyTorch is asked where that is if a method has loaded it. It is not
    imported to answer: an ONNX file runs without it, and the default place is
    worked out as PyTorch does, from ``TORCH_HOME`` then ``XDG_CACHE_HOME``.
    """
    if (torch := sys.modules.get("torch")) is not None:
        return Path(torch.hub.get_dir()) / "checkpoints"
    cache = os.environ.get("XDG_CACHE_HOME") or "~/.cache"
    home = os.environ.get("TORCH_HOME") or os.path.join(cache, "torch")
    return Path(home).expanduser() / "hub" / "checkpoints"


def check(path: Path, weights: Released, called: str = "") -> None:
    """Refuse a file that is not the published one.

    Args:
        path: The file.
        weights: The published file it should be.
        called: What the message calls the file (default: its name).

    Raises:
        WeightsRefused: If the file's SHA-256 is not the pinned one.
    """
    found = file_sha256(path)
    if found != weights.sha256:
        raise WeightsRefused(
            f"{called or path.name} is not the published {weights.name}: its "
            f"SHA-256 starts with {found[:16]}, the code pins {weights.sha256[:16]}"
        )


def _request(url: str, accept: str, token: str | None) -> Request:
    """A request to GitHub, with the token where GitHub's API asks for one."""
    request = Request(url, headers={"Accept": accept, "User-Agent": "satreg"})
    if token:
        # Not sent on to where a redirection leads: an asset is served by
        # another host, through an address that is already signed.
        request.add_unredirected_header("Authorization", f"Bearer {token}")
    return request


def _open(url: str, accept: str, token: str | None, weights: Released) -> Any:
    """Open an address of GitHub, with an error that says what to do about it."""
    where = f"release {weights.tag} of {REPOSITORY}"
    try:
        return urlopen(_request(url, accept, token), timeout=TIMEOUT)
    except HTTPError as exc:
        if token and exc.code in (401, 403):
            reason = f"GitHub refused the token of {TOKEN_VARIABLE} (HTTP {exc.code})"
        elif token:
            reason = (
                f"{where} has no such file for the token of {TOKEN_VARIABLE} "
                f"(HTTP {exc.code})"
            )
        elif exc.code == 404:
            reason = (
                f"{where} is not public: set {TOKEN_VARIABLE} to a token that can "
                "read the repository (see docs/running.md)"
            )
        else:
            reason = f"GitHub answered HTTP {exc.code} for {where}"
    except (URLError, TimeoutError) as exc:
        reason = f"GitHub could not be reached ({getattr(exc, 'reason', exc)})"
    raise WeightsUnavailable(f"{weights.asset} is not cached, and {reason}")


def download(weights: Released, destination: Path, token: str | None) -> None:
    """Download a published file from its release, unchecked.

    Without a token the file is asked at the address anyone can read, the
    repository being public. With one it goes through GitHub's API, the only way
    into a private repository: the release is read first, to find the asset.

    Args:
        weights: The published file.
        destination: The file to write.
        token: A token that can read the repository, or ``None``.

    Raises:
        WeightsUnavailable: If GitHub cannot be reached, refuses the token, or
            has no such release or asset for it.
    """
    if token:
        api = f"https://api.github.com/repos/{REPOSITORY}/releases"
        listing = f"{api}/tags/{weights.tag}"
        with _open(listing, "application/vnd.github+json", token, weights) as response:
            assets = json.load(response).get("assets", [])
        found = [asset["id"] for asset in assets if asset["name"] == weights.asset]
        if not found:
            raise WeightsUnavailable(
                f"release {weights.tag} of {REPOSITORY} has no asset {weights.asset}"
            )
        url = f"{api}/assets/{int(found[0])}"
    else:
        url = (
            f"https://github.com/{REPOSITORY}/releases/download/"
            f"{weights.tag}/{weights.asset}"
        )
    with (
        _open(url, "application/octet-stream", token, weights) as response,
        destination.open("wb") as f,
    ):
        shutil.copyfileobj(response, f, BLOCK)


def fetch(name: str, source: Path | None = None, directory: Path | None = None) -> Path:
    """A published file in the cache, downloaded if it is not there.

    A cached file is hashed again each time: one that is no longer the
    published file is dropped and fetched anew. A fetched file is written
    beside its place and moved there only once its hash is the pinned one, so
    the cache never holds anything else under that name.

    Args:
        name: Name of the file, a key of ``RELEASED`` or ``RELEASED_ONNX``.
        source: A directory holding the asset, read in place of the release.
        directory: The cache (default: PyTorch's).

    Returns:
        The file's path.

    Raises:
        ValueError: If nothing is published under ``name``.
        WeightsUnavailable: If the file is not cached and cannot be fetched.
        WeightsRefused: If the fetched file's hash is not the pinned one.
    """
    weights = lookup(name)
    path = (directory or cache_directory()) / weights.asset
    if path.is_file():
        if file_sha256(path) == weights.sha256:
            return path
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(".partial")
    try:
        if source is None:
            download(weights, partial, os.environ.get(TOKEN_VARIABLE) or None)
        elif (source / weights.asset).is_file():
            shutil.copyfile(source / weights.asset, partial)
        else:
            raise WeightsUnavailable(f"no {weights.asset} in {source}")
        check(partial, weights, called=weights.asset)
        os.replace(partial, path)
    finally:
        partial.unlink(missing_ok=True)
    return path


def card(weights: ReleasedWeights, state: Mapping[str, Any], size: int) -> dict:
    """Describe published weights and their training, as plain data.

    Args:
        weights: The weights.
        state: The content of their file, as ``raft.read_checkpoint`` reads it.
        size: Size of the file, in bytes.

    Returns:
        What the JSON beside the asset says: the file, its hash, and the
        training's configuration, commit and kept validation.
    """
    return {
        "asset": weights.asset,
        "sha256": weights.sha256,
        "bytes": size,
        "model": weights.model,
        "run": weights.run,
        "release": weights.tag,
        "repository": REPOSITORY,
        **{key: state.get(key) for key in DESCRIBED_KEYS},
    }


def export(name: str, runs: Path, out: Path) -> dict:
    """Copy a training's kept weights to the file its release publishes.

    The copy is the kept file itself, unchanged: it already holds the network's
    weights and the description of its training, without what resuming needs,
    and its hash stays the one the scored tables recorded. A JSON beside it
    repeats that description for a reader without PyTorch.

    Args:
        name: Name of the weights, a key of ``RELEASED``.
        runs: Directory of the trainings, ``outputs/train``.
        out: Directory the asset and its JSON are written to.

    Returns:
        The description written beside the asset.

    Raises:
        ValueError: If no weights are published under ``name``, or the file
            holds another model or what resuming a training needs.
        FileNotFoundError: If the training's kept weights are not there.
        WeightsRefused: If they are not the file the code pins.
    """
    from .methods.raft import read_checkpoint
    from .train import BEST

    weights = released(name)
    kept = runs / weights.run / BEST
    state = read_checkpoint(str(kept))
    check(kept, weights)
    if extra := [key for key in RESUME_KEYS if key in state]:
        raise ValueError(
            f"{kept} holds {', '.join(extra)}: it is a checkpoint to resume from, "
            "not a run's kept weights"
        )
    if (trained := state["train"]["model"]) != weights.model:
        raise ValueError(f"{kept} holds a {trained} model, {name} is {weights.model}")
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(kept, out / weights.asset)
    described = card(weights, state, kept.stat().st_size)
    (out / weights.card).write_text(json.dumps(described, indent=2) + "\n")
    return described


def export_onnx(name: str, exports: Path, out: Path) -> dict:
    """Copy an ONNX export to the file its release publishes.

    Args:
        name: Name of the file, a key of ``RELEASED_ONNX``.
        exports: Directory ``satreg export`` wrote to, and ``satreg quantize``
            the int8 copies, ``outputs/onnx``.
        out: Directory the asset is written to.

    Returns:
        What the release says of the asset: the file, its hash and size, the
        weights it was exported from, its refinements and whether it is an
        int8 copy.

    Raises:
        ValueError: If no ONNX file is published under ``name``.
        FileNotFoundError: If the export is not there.
        WeightsRefused: If it is not the file the code pins.
    """
    exported = released_onnx(name)
    source = exports / f"{name}.onnx"
    if not source.is_file():
        writer = "quantize" if exported.int8 else "export"
        raise FileNotFoundError(f"no export at {source}: write it with satreg {writer}")
    check(source, exported)
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, out / exported.asset)
    return {
        "asset": exported.asset,
        "sha256": exported.sha256,
        "bytes": source.stat().st_size,
        "weights": released(exported.weights).asset,
        "refinements": exported.refinements,
        "int8": exported.int8,
        "release": exported.tag,
        "repository": REPOSITORY,
    }


def notes(cards: list[dict], onnx_cards: list[dict] | None = None) -> str:
    """The text of the release: what each asset is, how it is checked, on what terms.

    It ends with ``WEIGHTS_TERMS``, the note on what the weights may be used for.

    Args:
        cards: The description of each asset, as ``export`` returns it.
        onnx_cards: The description of each ONNX asset, as ``export_onnx``
            returns it, if the release holds any.

    Returns:
        Markdown.
    """
    lines = [
        "Fine-tuned RAFT weights of level N3: the kept checkpoint of each "
        "training, as `satreg train` wrote it (weights, training configuration "
        "and commit, no optimiser state). `satreg` downloads them by itself and "
        "refuses a file whose SHA-256 is not the one below, pinned in "
        "`src/satreg/weights.py`.",
        "",
        "| asset | model | training | commit | kept step | light validation "
        "score (px) | MB | SHA-256 |",
        "|---|---|---|---|---:|---:|---:|---|",
    ]
    for described in cards:
        validation = described["validation"] or {}
        lines.append(
            f"| `{described['asset']}` | RAFT {described['model']} | "
            f"`{described['run']}` | `{str(described['commit'])[:7]}` | "
            f"{described['step']} | {validation.get('score', float('nan')):.4f} | "
            f"{described['bytes'] / 1e6:.1f} | `{described['sha256']}` |"
        )
    lines += [
        "",
        "Each `.json` repeats what its `.pth` says of the training. Both models "
        "start from torchvision's pretrained RAFT weights and were trained on "
        "pairs simulated from Sentinel-2 chips (contains modified Copernicus "
        "Sentinel data 2025-2026).",
    ]
    if onnx_cards:
        lines += [
            "",
            "Each `.onnx` is one of these weights exported with a fixed number "
            "of refinements, for ONNX Runtime: `satreg export` wrote it, image "
            "size left free, and `satreg` checks it against its SHA-256 like "
            "the weights. It runs without PyTorch.",
        ]
        if any(described["int8"] for described in onnx_cards):
            lines[-1] += (
                " An int8 file is the copy `satreg quantize` made of the float "
                "one with the same refinements: its convolutions compute on "
                "8-bit integers, with scales set on pairs of the validation "
                "set."
            )
        lines += [
            "",
            "| asset | exported from | refinements | computes in | MB | SHA-256 |",
            "|---|---|---:|---|---:|---|",
        ]
        lines += [
            f"| `{described['asset']}` | `{described['weights']}` | "
            f"{described['refinements']} | "
            f"{'int8' if described['int8'] else 'float'} | "
            f"{described['bytes'] / 1e6:.1f} | `{described['sha256']}` |"
            for described in onnx_cards
        ]
    lines += ["", WEIGHTS_TERMS]
    return "\n".join(lines) + "\n"

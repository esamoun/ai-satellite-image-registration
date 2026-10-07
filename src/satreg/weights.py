"""The fine-tuned weights, published as assets of a GitHub release.

A training's kept checkpoint leaves the machine that trained it as a release
asset. This module names each published file with its SHA-256, downloads it
once to PyTorch's cache, next to the pretrained weights torchvision puts there,
and refuses a file whose hash is not the one written here. While the
repository is private the download needs a token, read from the environment
and sent to GitHub's API only. See docs/decisions.md.
"""

import json
import os
import shutil
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .compute import file_sha256

# The repository whose releases hold the weights, as owner/name.
REPOSITORY = "esamoun/ai-satellite-image-registration"

# The environment variable a token for a private repository is read from. The
# token is never an option of a command: options are written to context.json.
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


def cache_directory() -> Path:
    """Where the weights are cached: PyTorch's own cache of checkpoints."""
    import torch

    return Path(torch.hub.get_dir()) / "checkpoints"


def check(path: Path, weights: ReleasedWeights, called: str = "") -> None:
    """Refuse a file that is not the published weights.

    Args:
        path: The file.
        weights: The weights it should be.
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


def _open(url: str, accept: str, token: str | None, weights: ReleasedWeights) -> Any:
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
                "read the repository (see the README)"
            )
        else:
            reason = f"GitHub answered HTTP {exc.code} for {where}"
    except (URLError, TimeoutError) as exc:
        reason = f"GitHub could not be reached ({getattr(exc, 'reason', exc)})"
    raise WeightsUnavailable(f"{weights.asset} is not cached, and {reason}")


def download(weights: ReleasedWeights, destination: Path, token: str | None) -> None:
    """Download published weights from their release, unchecked.

    Without a token the file is asked at the address anyone can read once the
    repository is public. With one it goes through GitHub's API, the only way
    into a private repository: the release is read first, to find the asset.

    Args:
        weights: The weights.
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
    """The file of published weights in the cache, downloaded if not there.

    A cached file is hashed again each time: one that is no longer the
    published file is dropped and fetched anew. A fetched file is written
    beside its place and moved there only once its hash is the pinned one, so
    the cache never holds anything else under that name.

    Args:
        name: Name of the weights, a key of ``RELEASED``.
        source: A directory holding the asset, read in place of the release.
        directory: The cache (default: PyTorch's).

    Returns:
        The file's path.

    Raises:
        ValueError: If no weights are published under ``name``.
        WeightsUnavailable: If the file is not cached and cannot be fetched.
        WeightsRefused: If the fetched file's hash is not the pinned one.
    """
    weights = released(name)
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


def notes(cards: list[dict]) -> str:
    """The text of the release: what each asset is and how it is checked.

    Args:
        cards: The description of each asset, as ``export`` returns it.

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
    return "\n".join(lines) + "\n"

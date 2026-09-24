"""What the pretrained deep-learning methods share.

PyTorch and torchvision are an optional extra (``pip install -e ".[dl]"``, or
``make install-dl``), imported only when a method runs, so the rest of the
package and its tests work without them. A method runs on the device its
configuration names, never on one picked for it. Pretrained weights are
downloaded once, by torchvision, to PyTorch's cache (``~/.cache/torch`` unless
``TORCH_HOME`` says otherwise), outside the repository. See docs/decisions.md.
"""

import functools
import importlib.util
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

# Modules every deep-learning method needs.
REQUIRED_MODULES = ("torch", "torchvision")

# Devices a method can be configured to run on.
DEVICES = ("cpu", "mps", "cuda")


def missing_modules(*extra: str) -> list[str]:
    """Name the modules a deep-learning method needs that are not installed.

    Args:
        extra: Modules the method needs besides ``REQUIRED_MODULES``.

    Returns:
        Missing module names, empty if the method can run.
    """
    return [
        name
        for name in (*REQUIRED_MODULES, *extra)
        if importlib.util.find_spec(name) is None
    ]


def check_device(device: str) -> None:
    """Refuse a device name that is not one of ``DEVICES``.

    Raises:
        ValueError: If ``device`` is unknown.
    """
    if device not in DEVICES:
        raise ValueError(f"device must be one of {', '.join(DEVICES)}, got {device!r}")


def check_available(device: str) -> None:
    """Refuse a device this machine does not have.

    Raises:
        RuntimeError: If ``device`` is not available on this machine.
    """
    import torch

    available = {
        "cpu": True,
        "mps": torch.backends.mps.is_available(),
        "cuda": torch.cuda.is_available(),
    }
    if not available[device]:
        raise RuntimeError(f"device {device} is not available on this machine")


def cached_file(name: str) -> Path:
    """Where PyTorch's hub caches a downloaded checkpoint file.

    Args:
        name: File name of the checkpoint in the cache.

    Returns:
        The file's path, whether or not it is there yet.
    """
    import torch

    return Path(torch.hub.get_dir()) / "checkpoints" / name


def pad(image: np.ndarray, multiple: int, min_side: int = 0) -> np.ndarray:
    """Extend an image down and right, by edge replication, to a side a network takes.

    Padding only after the last row and column leaves every pixel where it was,
    so what the network finds on the padded image is on the image's own grid.

    Args:
        image: 2-D image.
        multiple: Each side is rounded up to a multiple of this.
        min_side: Each side is then raised to at least this.

    Returns:
        The padded image, the image itself if no padding is needed.
    """
    rows, cols = image.shape
    target = [max(min_side, -(-side // multiple) * multiple) for side in (rows, cols)]
    extra = (target[0] - rows, target[1] - cols)
    if extra == (0, 0):
        return image
    return np.pad(image, ((0, extra[0]), (0, extra[1])), mode="edge")


def weights_file(weights: Any) -> Path:
    """Where torchvision caches a set of pretrained weights.

    Args:
        weights: A torchvision weights enum member, e.g.
            ``Raft_Large_Weights.C_T_SKHT_V2``.

    Returns:
        The checkpoint's path in PyTorch's cache, whether or not it is there yet.
    """
    return cached_file(Path(weights.url).name)


@functools.cache
def load_network(builder: Callable[..., Any], weights: Any, device: str) -> Any:
    """Build a pretrained network once per process, in evaluation mode.

    The first call downloads the weights if they are not cached, which is why
    the benchmark's warm-up call is not timed.

    Args:
        builder: torchvision model builder, e.g. ``raft_large``.
        weights: Weights enum member to load into it.
        device: One of ``DEVICES``.

    Returns:
        The network, on ``device``, with gradients off.

    Raises:
        RuntimeError: If ``device`` is not available on this machine.
    """
    check_available(device)
    network = builder(weights=weights, progress=False).eval().to(device)
    network.requires_grad_(False)
    return network

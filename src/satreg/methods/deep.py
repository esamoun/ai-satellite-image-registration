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

# Modules the deep-learning methods need.
REQUIRED_MODULES = ("torch", "torchvision")

# Devices a method can be configured to run on.
DEVICES = ("cpu", "mps", "cuda")


def missing_modules() -> list[str]:
    """Name the modules the deep-learning methods need that are not installed.

    Returns:
        Missing module names, empty if the methods can run.
    """
    return [name for name in REQUIRED_MODULES if importlib.util.find_spec(name) is None]


def check_device(device: str) -> None:
    """Refuse a device name that is not one of ``DEVICES``.

    Raises:
        ValueError: If ``device`` is unknown.
    """
    if device not in DEVICES:
        raise ValueError(f"device must be one of {', '.join(DEVICES)}, got {device!r}")


def weights_file(weights: Any) -> Path:
    """Where torchvision caches a set of pretrained weights.

    Args:
        weights: A torchvision weights enum member, e.g.
            ``Raft_Large_Weights.C_T_SKHT_V2``.

    Returns:
        The checkpoint's path in PyTorch's cache, whether or not it is there yet.
    """
    import torch

    return Path(torch.hub.get_dir()) / "checkpoints" / Path(weights.url).name


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
    import torch

    available = {
        "cpu": True,
        "mps": torch.backends.mps.is_available(),
        "cuda": torch.cuda.is_available(),
    }
    if not available[device]:
        raise RuntimeError(f"device {device} is not available on this machine")
    network = builder(weights=weights, progress=False).eval().to(device)
    network.requires_grad_(False)
    return network

"""RAFT optical flow, with torchvision's pretrained weights, as a dense field.

RAFT was trained on RGB video frames, not on satellite bands, and is used here
as shipped: no fine-tuning. Its flow, one vector per pixel, is returned as a
``Dense`` displacement and scored like any other. Needs the ``dl`` extra.
"""

from dataclasses import dataclass

import numpy as np

from ..compute import TorchMeter
from ..displacement import Dense
from . import deep

# Model name to torchvision builder, weights enum and weights, pinned by name so
# that a torchvision release changing its defaults does not change the results.
# Both are the defaults of torchvision 0.29. The large weights were fine-tuned on
# Sintel, KITTI and HD1K after FlyingChairs and FlyingThings; the small ones saw
# the two synthetic datasets only, the only small weights torchvision ships.
MODELS = {
    "large": ("raft_large", "Raft_Large_Weights", "C_T_SKHT_V2"),
    "small": ("raft_small", "Raft_Small_Weights", "C_T_V2"),
}

# Each image is stretched linearly between these percentiles of its own values.
# The same rule as SIFT's 8-bit conversion, for the same reasons, without the
# rounding to 8 bits. See docs/decisions.md.
STRETCH_PERCENTILES = (1.0, 99.0)

# RAFT's features are computed at 1/8 resolution, so it takes images whose sides
# are multiples of 8. Its correlation pyramid halves them three more times, so a
# side must also be at least 128 px.
SIDE_MULTIPLE = 8
MIN_SIDE = 128


def stretch(image: np.ndarray) -> np.ndarray:
    """Map an image to the [-1, 1] range RAFT's weights were trained on.

    Values are stretched linearly so that the ``STRETCH_PERCENTILES`` of the
    image map to -1 and 1, then clipped. The mapping depends on the image alone,
    so a gain or offset applied to it leaves the result unchanged, whatever
    degradation the pair went through.

    Args:
        image: 2-D image, any real dtype, e.g. uint16 digital numbers.

    Returns:
        The stretched image, float32. A flat image maps to zeros.
    """
    lo, hi = np.percentile(image, STRETCH_PERCENTILES)
    if hi <= lo:
        return np.zeros(image.shape, dtype=np.float32)
    scaled = (image.astype(float) - lo) * (2 / (hi - lo)) - 1
    return np.clip(scaled, -1, 1).astype(np.float32)


def pad(image: np.ndarray) -> np.ndarray:
    """Extend an image down and right, by edge replication, to a side RAFT takes.

    An image under 128 px a side runs, but padding it that far costs accuracy:
    0.1 to 0.3 px of mean error on 64 px synthetic pairs, against 0.02 to 0.07
    at 256 px (see docs/decisions.md).

    Args:
        image: 2-D image.

    Returns:
        The padded image, the image itself if no padding is needed.
    """
    return deep.pad(image, SIDE_MULTIPLE, MIN_SIDE)


def network_input(image: np.ndarray) -> np.ndarray:
    """Turn a single-band image into RAFT's input: three equal channels.

    Args:
        image: 2-D image.

    Returns:
        Float32 array of shape ``(3, rows, cols)``, rows and cols padded by
        ``pad``, values in [-1, 1].
    """
    band = pad(stretch(image))
    return np.repeat(band[np.newaxis], 3, axis=0)


@dataclass(frozen=True)
class Raft:
    """RAFT, torchvision's pretrained optical-flow network.

    Attributes:
        model: ``"large"`` (5.3 M parameters) or ``"small"`` (1.0 M).
        iterations: Recurrent refinements of the flow, at least one.
        device: ``"cpu"``, ``"mps"`` or ``"cuda"``.
    """

    model: str = "large"
    iterations: int = 12
    device: str = "cpu"

    def __post_init__(self) -> None:
        if self.model not in MODELS:
            raise ValueError(
                f"model must be one of {', '.join(MODELS)}, got {self.model!r}"
            )
        if self.iterations < 1:
            raise ValueError(f"iterations must be positive, got {self.iterations}")
        deep.check_device(self.device)

    @property
    def meter(self) -> TorchMeter:
        """Read time and memory on the method's device."""
        return TorchMeter(self.device)

    def weights(self) -> object:
        """The torchvision weights of the model, an enum member."""
        from torchvision.models import optical_flow

        _, enum, name = MODELS[self.model]
        return getattr(optical_flow, enum)[name]

    def network(self) -> object:
        """The pretrained network on the method's device, built once per process."""
        from torchvision.models import optical_flow

        builder = getattr(optical_flow, MODELS[self.model][0])
        return deep.load_network(builder, self.weights(), self.device)

    def __call__(self, reference: np.ndarray, moving: np.ndarray) -> Dense:
        """Estimate the displacement at every pixel.

        Args:
            reference: Reference image.
            moving: Moving image, same shape as ``reference``.

        Returns:
            The flow of the last refinement, on the reference grid.
        """
        import torch

        network = self.network()
        rows, cols = reference.shape
        image1, image2 = (
            torch.from_numpy(network_input(image))[None].to(self.device)
            for image in (reference, moving)
        )
        with torch.inference_mode():
            flows = network(image1, image2, num_flow_updates=self.iterations)
        flow = flows[-1][0, :, :rows, :cols].cpu().numpy()
        # torchvision's flow goes from image1 to image2, in (x, y) order:
        # image2(p + flow) = image1(p). With the reference as image1, it is the
        # displacement, once put in (row, col) order.
        return Dense(flow[::-1])


def fetch_weights() -> list[str]:
    """Download the weights of every model to PyTorch's cache, if not there.

    Returns:
        Path of each model's weights file.
    """
    paths = []
    for model in MODELS:
        method = Raft(model=model)
        method.network()
        paths.append(str(deep.weights_file(method.weights())))
    return paths

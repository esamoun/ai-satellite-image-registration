"""LightGlue matching learned keypoints, an affine transform fitted by RANSAC.

The keypoints are ALIKED's (or DISK's, in the ``lightglue_disk`` variant), and
LightGlue, a transformer, matches them. The same RANSAC affine fit as SIFT's then
turns the matches into a displacement, so the comparison with ``sift_ransac``
isolates what learned features and matching add. kornia's implementation and
weights are used as shipped, without fine-tuning. Needs the ``dl`` extra.
"""

import contextlib
import functools
import sys
from dataclasses import dataclass
from typing import Any

import numpy as np

from ..compute import TorchMeter
from . import deep, ransac
from .base import Estimate
from .raft import stretch

# Feature extractor to the checkpoint files kornia 0.8 caches for it and for
# the LightGlue weights trained on its keypoints, in PyTorch's cache. ALIKED is
# its "n16" model, the one LightGlue was trained with. DISK is its "depth"
# model, the one LightGlue's DISK weights use.
FEATURES = {
    "aliked": ("aliked-n16.pth", "aliked_lightglue_v0-1_arxiv-pth"),
    "disk": ("depth-save.pth", "disk_lightglue_v0-1_arxiv-pth"),
}

# ALIKED keeps a keypoint whose detection score is above this, its default and
# the value LightGlue's own ALIKED wrapper uses.
ALIKED_THRESHOLD = 0.2

# DISK's U-Net halves its input four times, so a side must be a multiple of 16.
# ALIKED pads its input itself, by edge replication.
DISK_SIDE_MULTIPLE = 16


def missing_modules() -> list[str]:
    """Name the modules LightGlue needs that are not installed."""
    return deep.missing_modules("kornia")


def network_input(image: np.ndarray) -> np.ndarray:
    """Turn a single-band image into the extractors' input: three equal channels.

    Both extractors were trained on RGB photographs scaled to [0, 1]. The band is
    stretched linearly so that the image's own 1st and 99th percentiles land on
    0 and 1, then clipped: RAFT's stretch, moved to [0, 1]. The mapping depends
    on the image alone, so a gain or offset applied to it leaves the result
    unchanged, whatever degradation the pair went through.

    Args:
        image: 2-D image, any real dtype, e.g. uint16 digital numbers.

    Returns:
        Float32 array of shape ``(3, rows, cols)``, values in [0, 1].
    """
    band = (stretch(image) + 1) / 2
    return np.repeat(band[np.newaxis], 3, axis=0)


@functools.cache
def _networks(
    features: str, max_keypoints: int, match_threshold: float, device: str
) -> tuple[Any, Any]:
    """Build the extractor and the matcher once per process, in evaluation mode.

    The first call downloads the weights if they are not cached, which is why
    the benchmark's warm-up call is not timed.

    Raises:
        RuntimeError: If ``device`` is not available on this machine.
    """
    import torch
    from kornia import feature

    deep.check_available(device)
    if features == "aliked":
        extractor = feature.ALIKED.from_pretrained(
            "aliked-n16",
            max_num_keypoints=max_keypoints,
            detection_threshold=ALIKED_THRESHOLD,
            device=torch.device(device),
        )
    else:
        extractor = feature.DISK.from_pretrained("depth", device=torch.device(device))
    # kornia prints a line on stdout when it loads LightGlue's weights, and
    # stdout carries the benchmark's summary table.
    with contextlib.redirect_stdout(sys.stderr):
        matcher = feature.LightGlue(features, filter_threshold=match_threshold)
    networks = extractor.eval().to(device), matcher.eval().to(device)
    for network in networks:
        network.requires_grad_(False)
    return networks


@dataclass(frozen=True)
class LightGlue:
    """Learned sparse matching: ALIKED or DISK keypoints, LightGlue, RANSAC affine.

    Attributes:
        features: Keypoint extractor, ``"aliked"`` or ``"disk"``.
        max_keypoints: Most keypoints kept per image, the strongest ones.
        match_threshold: LightGlue keeps a match whose confidence is above
            this, in [0, 1).
        ransac_threshold: Largest reprojection error of an inlier, in pixels.
        min_inliers: Fewest inliers for the fit to be trusted, at least 3.
            Below it the method reports a failure rather than a guess.
        device: ``"cpu"``, ``"mps"`` or ``"cuda"``.
    """

    features: str = "aliked"
    max_keypoints: int = 2048
    match_threshold: float = 0.1
    ransac_threshold: float = 1.0
    min_inliers: int = 10
    device: str = "cpu"

    def __post_init__(self) -> None:
        if self.features not in FEATURES:
            raise ValueError(
                f"features must be one of {', '.join(FEATURES)}, got {self.features!r}"
            )
        if self.max_keypoints < 1:
            raise ValueError(
                f"max_keypoints must be positive, got {self.max_keypoints}"
            )
        if not 0 <= self.match_threshold < 1:
            raise ValueError(
                f"match_threshold must be in [0, 1), got {self.match_threshold}"
            )
        ransac.check_parameters(self.ransac_threshold, self.min_inliers)
        deep.check_device(self.device)

    @property
    def meter(self) -> TorchMeter:
        """Read time and memory on the method's device."""
        return TorchMeter(self.device)

    def weights_files(self) -> list[str]:
        """Where the extractor's and the matcher's weights sit in PyTorch's cache."""
        return [str(deep.cached_file(name)) for name in FEATURES[self.features]]

    def keypoints(self, image: np.ndarray) -> tuple[Any, Any]:
        """Detect and describe the keypoints of an image.

        Returns:
            The keypoints ``(n, 2)``, in ``(x, y) = (col, row)`` order with
            pixel centres on integers, and their descriptors ``(n, d)``, as
            tensors on the method's device.
        """
        import torch

        extractor, _ = _networks(
            self.features, self.max_keypoints, self.match_threshold, self.device
        )
        rows, cols = image.shape
        channels = network_input(image)
        if self.features == "aliked":
            found = extractor(torch.from_numpy(channels)[None].to(self.device))[0]
            return found.keypoints, found.descriptors

        # kornia's own padding adds zeros, whose edge would draw keypoints.
        padded = np.stack([deep.pad(c, DISK_SIDE_MULTIPLE) for c in channels])
        found = extractor(
            torch.from_numpy(padded)[None].to(self.device), n=self.max_keypoints
        )[0]
        # Keypoints on the padding are not on the image.
        inside = (found.keypoints[:, 0] < cols) & (found.keypoints[:, 1] < rows)
        return found.keypoints[inside], found.descriptors[inside]

    def __call__(self, reference: np.ndarray, moving: np.ndarray) -> Estimate:
        """Estimate an affine displacement from matched learned keypoints.

        Args:
            reference: Reference image.
            moving: Moving image, same shape as ``reference``.

        Returns:
            The affine estimate, with the keypoint, match and inlier counts as
            diagnostics.

        Raises:
            RegistrationFailure: If there are fewer than ``min_inliers`` matches
                or inliers, or RANSAC finds no model.
        """
        import torch

        _, matcher = _networks(
            self.features, self.max_keypoints, self.match_threshold, self.device
        )
        with torch.inference_mode():
            ref_keys, ref_desc = self.keypoints(reference)
            mov_keys, mov_desc = self.keypoints(moving)
            diagnostics = {"keypoints": min(len(ref_keys), len(mov_keys))}
            matches = np.zeros((0, 2), dtype=int)
            if diagnostics["keypoints"] > 0:
                # LightGlue normalises keypoints by the image size, (width, height).
                found = matcher(
                    {
                        "image0": {
                            "keypoints": ref_keys[None],
                            "descriptors": ref_desc[None],
                            "image_size": torch.tensor(
                                [reference.shape[::-1]], device=self.device
                            ),
                        },
                        "image1": {
                            "keypoints": mov_keys[None],
                            "descriptors": mov_desc[None],
                            "image_size": torch.tensor(
                                [moving.shape[::-1]], device=self.device
                            ),
                        },
                    }
                )
                matches = found["matches"][0].cpu().numpy()

        ref_points = ref_keys.cpu().numpy()[matches[:, 0]]
        mov_points = mov_keys.cpu().numpy()[matches[:, 1]]
        return ransac.fit_affine(
            ref_points,
            mov_points,
            self.ransac_threshold,
            self.min_inliers,
            diagnostics,
        )


def fetch_weights() -> list[str]:
    """Download the weights of every extractor and its matcher, if not cached.

    Returns:
        Path of each weights file.
    """
    paths = []
    for features in FEATURES:
        method = LightGlue(features=features)
        _networks(features, method.max_keypoints, method.match_threshold, "cpu")
        paths.extend(method.weights_files())
    return paths

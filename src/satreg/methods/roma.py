"""RoMa, a dense matcher on a DINOv2 backbone, read as a field or fitted by RANSAC.

RoMa matches every pixel of the reference to a position in the moving image and
rates each match with a certainty. It works on a square grid of its own (its
*working resolution*), in normalised coordinates, so its warp is mapped back to
the pixels of the pair here. The warp becomes either matches on a regular
lattice, fitted with the RANSAC affine shared with SIFT (``roma``), or a
``Dense`` displacement (``roma_dense``). The outdoor weights are used as shipped,
without fine-tuning. Needs the ``dl`` extra and ``romatch``, installed without
its own dependencies by ``make install-roma``. See docs/decisions.md.
"""

import functools
import math
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy import ndimage

from ..compute import TorchMeter
from ..displacement import Dense
from . import deep, ransac
from .base import Estimate, RegistrationFailure
from .lightglue import network_input

# Checkpoints of RoMa's outdoor model and of its DINOv2 ViT-L/14 backbone, as
# romatch 0.1.2 names them. PyTorch's hub caches each under the last part of its
# URL. The files are not versioned upstream: docs/decisions.md records the
# SHA-256 of the ones measured.
WEIGHTS_URLS = (
    "https://github.com/Parskatt/storage/releases/download/roma/roma_outdoor.pth",
    "https://dl.fbaipublicfiles.com/dinov2/dinov2_vitl14/dinov2_vitl14_pretrain.pth",
)

# DINOv2 cuts its input into 14 px patches, so RoMa's coarse grid is a multiple
# of 14 on each side.
PATCH = 14

# RoMa normalises its input with ImageNet's per-channel statistics.
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

OUTPUTS = ("dense", "affine")


def missing_modules() -> list[str]:
    """Name the modules RoMa needs that are not installed."""
    return deep.missing_modules("romatch", "einops", "loguru")


def weights_files() -> list[str]:
    """Where RoMa's and DINOv2's weights sit in PyTorch's cache."""
    return [str(deep.cached_file(url.rsplit("/", 1)[1])) for url in WEIGHTS_URLS]


def working_input(image: np.ndarray, side: int) -> np.ndarray:
    """Turn a single-band image into RoMa's input at its working resolution.

    LightGlue's conversion (the image's own 1st and 99th percentiles stretched
    to [0, 1], three equal channels), resized to a square of ``side`` px by
    bicubic interpolation, then normalised with ImageNet's statistics, as RoMa's
    own loader does with a photograph.

    Args:
        image: 2-D image, any real dtype.
        side: Side of RoMa's working grid, in pixels.

    Returns:
        Float32 array of shape ``(3, side, side)``.
    """
    import torch
    import torch.nn.functional as F

    channels = torch.from_numpy(network_input(image))[None]
    resized = F.interpolate(
        channels, size=(side, side), mode="bicubic", align_corners=False
    )[0].numpy()
    return (resized - IMAGENET_MEAN[:, None, None]) / IMAGENET_STD[:, None, None]


def to_pair_grid(maps: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    """Resample maps from RoMa's working grid to the pixel centres of the pair.

    RoMa's grid and the pair's cover the same image edge to edge, and each pixel
    is a cell whose centre is sampled (PyTorch's ``align_corners=False``). Pair
    pixel ``i`` of ``n`` therefore sits at ``(i + 0.5) * m / n - 0.5`` on a
    working side of ``m``. Values are interpolated linearly; a centre beyond the
    outermost working centres takes the nearest one.

    Args:
        maps: ``(c, m_rows, m_cols)`` maps on the working grid.
        shape: ``(rows, cols)`` of the pair.

    Returns:
        ``(c, rows, cols)`` maps on the pair's grid.
    """
    rows, cols = shape
    m_rows, m_cols = maps.shape[1:]
    at = np.meshgrid(
        (np.arange(rows) + 0.5) * m_rows / rows - 0.5,
        (np.arange(cols) + 0.5) * m_cols / cols - 0.5,
        indexing="ij",
    )
    return np.stack(
        [ndimage.map_coordinates(m, at, order=1, mode="nearest") for m in maps]
    )


def to_pixels(normalised: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    """Turn RoMa's normalised ``(x, y)`` positions into ``(row, col)`` pixels.

    RoMa's -1 and 1 are the outer edges of the image, not the centres of its
    outer pixels, so pixel centre ``i`` of ``n`` is at ``(2 i + 1) / n - 1``.
    romatch's own ``to_pixel_coordinates`` leaves out the half pixel, which puts
    the centre of the first pixel at 0.5.

    Args:
        normalised: ``(2, ...)`` positions, ``x`` then ``y``, in [-1, 1].
        shape: ``(rows, cols)`` of the image they are positions in.

    Returns:
        ``(2, ...)`` positions, ``row`` then ``col``, with pixel centres on
        integers as in the displacement convention.
    """
    rows, cols = shape
    x, y = normalised
    return np.stack([(y + 1) * rows / 2 - 0.5, (x + 1) * cols / 2 - 0.5])


def lattice(shape: tuple[int, int], most: int) -> tuple[np.ndarray, np.ndarray]:
    """A regular lattice of at most ``most`` pixels, centred on the image.

    Returns:
        Row and column indices of the lattice's pixels.
    """
    rows, cols = shape
    step = max(1, math.ceil(math.sqrt(rows * cols / most)))
    r = np.arange((rows - 1) % step // 2, rows, step)
    c = np.arange((cols - 1) % step // 2, cols, step)
    return tuple(np.meshgrid(r, c, indexing="ij"))


@functools.cache
def _network(resolution: int, upsample_resolution: int, device: str) -> Any:
    """Build RoMa once per process, in evaluation mode.

    The first call downloads the weights if they are not cached, which is why
    the benchmark's warm-up call is not timed.

    Raises:
        RuntimeError: If ``device`` is not available on this machine.
    """
    import torch
    from loguru import logger
    from romatch.models.model_zoo import roma_model

    deep.check_available(device)
    roma_weights, dinov2_weights = (
        torch.hub.load_state_dict_from_url(
            url, map_location=device, progress=False, weights_only=True
        )
        for url in WEIGHTS_URLS
    )
    # romatch logs its resolutions and warns that its fused correlation kernel
    # is Linux-only, which does not concern the portable kernel used here.
    logger.disable("romatch")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        network = roma_model(
            resolution=(resolution, resolution),
            upsample_preds=upsample_resolution > 0,
            upsample_res=(upsample_resolution,) * 2 if upsample_resolution else None,
            weights=roma_weights,
            dinov2_weights=dinov2_weights,
            device=device,
            # One direction is enough: the symmetric pass adds the moving-to-
            # reference warp, which nothing reads.
            symmetric=False,
            # The same kernel on every platform, so that a Linux GPU and the M1
            # compute the same thing.
            use_custom_corr=False,
        )
    network.eval().requires_grad_(False)
    return network


@dataclass(frozen=True)
class Roma:
    """RoMa's outdoor model, its warp read as a field or fitted by RANSAC.

    Attributes:
        output: ``"affine"``, an affine transform fitted by RANSAC to the warp
            at the certain pixels of a regular lattice, or ``"dense"``, the warp
            at every pixel as a ``Dense`` displacement.
        resolution: Side of RoMa's working grid, in pixels, a multiple of 14.
            Both images are resized to a square of this side.
        upsample_resolution: Side of RoMa's second, refining pass, in pixels,
            above ``resolution``, or 0 for no second pass.
        certainty_threshold: A pixel whose certainty is at least this is
            certain, in (0, 1).
        min_certain_fraction: Smallest fraction of certain pixels for the pair
            to be registered, in [0, 1]. Below it the method reports a failure.
        max_matches: Most lattice pixels the affine fit is given.
        ransac_threshold: Largest reprojection error of an inlier, in pixels
            (affine output).
        min_inliers: Fewest inliers for the affine fit to be trusted, at least 3.
        device: ``"cpu"``, ``"mps"`` or ``"cuda"``.
    """

    output: str = "affine"
    resolution: int = 280
    upsample_resolution: int = 0
    certainty_threshold: float = 0.5
    min_certain_fraction: float = 0.005
    max_matches: int = 5000
    ransac_threshold: float = 1.0
    min_inliers: int = 10
    device: str = "cpu"

    def __post_init__(self) -> None:
        if self.output not in OUTPUTS:
            raise ValueError(
                f"output must be one of {', '.join(OUTPUTS)}, got {self.output!r}"
            )
        if self.resolution < PATCH or self.resolution % PATCH:
            raise ValueError(
                f"resolution must be a positive multiple of {PATCH}, "
                f"got {self.resolution}"
            )
        if self.upsample_resolution and self.upsample_resolution <= self.resolution:
            raise ValueError(
                "upsample_resolution must be 0 or above resolution, "
                f"got {self.upsample_resolution}"
            )
        if not 0 < self.certainty_threshold < 1:
            raise ValueError(
                f"certainty_threshold must be in (0, 1), got {self.certainty_threshold}"
            )
        if not 0 <= self.min_certain_fraction <= 1:
            raise ValueError(
                "min_certain_fraction must be in [0, 1], "
                f"got {self.min_certain_fraction}"
            )
        ransac.check_parameters(self.ransac_threshold, self.min_inliers)
        if self.max_matches < self.min_inliers:
            raise ValueError(
                f"max_matches must be at least min_inliers, got {self.max_matches}"
            )
        deep.check_device(self.device)

    @property
    def meter(self) -> TorchMeter:
        """Read time and memory on the method's device."""
        return TorchMeter(self.device)

    def warp(
        self, reference: np.ndarray, moving: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Run RoMa and bring its warp and certainty to the pair's grid.

        Returns:
            The position in the moving image of every reference pixel,
            ``(2, rows, cols)`` in ``(row, col)`` order, and the certainty of
            each, ``(rows, cols)`` in [0, 1].
        """
        import torch

        network = _network(self.resolution, self.upsample_resolution, self.device)
        images = {}
        for key, side in (("low", self.resolution), ("high", self.upsample_resolution)):
            if side:
                images[key] = [
                    torch.from_numpy(working_input(image, side))[None].to(self.device)
                    for image in (reference, moving)
                ]
        high = {}
        if "high" in images:
            high = {
                "im_A_high_res": images["high"][0],
                "im_B_high_res": images["high"][1],
            }
        warp, certainty = network.match(*images["low"], **high)
        # warp is (1, m, m, 4): the working grid's own (x, y), then the matching
        # (x, y) in the moving image, both normalised.
        maps = np.concatenate(
            [
                warp[0, ..., 2:].permute(2, 0, 1).float().cpu().numpy(),
                certainty.float().cpu().numpy(),
            ]
        )
        on_pair = to_pair_grid(maps, reference.shape)
        return to_pixels(on_pair[:2], moving.shape), on_pair[2]

    def __call__(self, reference: np.ndarray, moving: np.ndarray) -> Estimate:
        """Estimate the displacement from RoMa's warp.

        Args:
            reference: Reference image.
            moving: Moving image, same shape as ``reference``.

        Returns:
            The dense field or the affine fit, with the mean certainty and the
            fraction of certain pixels as diagnostics (and the match and inlier
            counts for the affine fit).

        Raises:
            RegistrationFailure: If fewer than ``min_certain_fraction`` of the
                pixels are certain, or, for the affine fit, there are fewer than
                ``min_inliers`` matches or inliers.
        """
        positions, certainty = self.warp(reference, moving)
        certain = certainty >= self.certainty_threshold
        diagnostics = {
            "mean_certainty": float(certainty.mean()),
            "certain_fraction": float(certain.mean()),
        }
        if diagnostics["certain_fraction"] < self.min_certain_fraction:
            raise RegistrationFailure(
                f"{diagnostics['certain_fraction']:.1%} of the pixels are certain, "
                f"need {self.min_certain_fraction:.1%}",
                diagnostics,
            )

        if self.output == "dense":
            field = positions - np.indices(reference.shape)
            return Estimate(Dense(field), diagnostics)

        r, c = lattice(reference.shape, self.max_matches)
        keep = certain[r, c]
        r, c = r[keep], c[keep]
        # The RANSAC fit takes OpenCV's (x, y) order.
        ref_points = np.stack([c, r], axis=1).astype(float)
        mov_points = positions[::-1, r, c].T
        return ransac.fit_affine(
            ref_points,
            mov_points,
            self.ransac_threshold,
            self.min_inliers,
            diagnostics,
        )


def fetch_weights() -> list[str]:
    """Download RoMa's and DINOv2's weights to PyTorch's cache, if not there.

    Returns:
        Path of each weights file.
    """
    import torch

    paths = weights_files()
    for url, path in zip(WEIGHTS_URLS, paths, strict=True):
        if not Path(path).exists():
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            torch.hub.download_url_to_file(url, path, progress=False)
    return paths

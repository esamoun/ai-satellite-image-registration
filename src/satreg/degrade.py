"""Degradations that make a simulated pair harder without touching its geometry.

Each degradation is a small parameterised callable ``(pair, rng) -> pair``. It
changes pixel values only: the ground truth of the pair it returns is the one it
was given, and all its randomness comes from ``rng``. A ``Preset`` combines them
in a fixed physical order, and named presets are read from a TOML file. See
docs/decisions.md.
"""

import dataclasses
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import ndimage

from .simulate import SimulatedPair
from .texture import power_law_field

Degradation = Callable[[SimulatedPair, np.random.Generator], SimulatedPair]
"""Turns a clean pair into a degraded one, without touching its ground truth."""

# Spectral slope of the field clouds are cut from. Steeper than the 1/f of the
# ground, so a 256 px window holds a few large, smooth-edged banks rather than
# scattered speckle.
CLOUD_SPECTRAL_EXPONENT = 2.0


@dataclass(frozen=True)
class Radiometry:
    """A radiometric difference of the moving image: tone curve, contrast, level.

    Gamma bends the moving image's own range: values are mapped to [0, 1] by its
    minimum and maximum, raised to ``gamma``, and mapped back. Gain then scales
    the deviations from the image mean, and the offset shifts the level by a
    number of reference standard deviations. Both act relative to the image's
    own statistics, so the same preset means the same thing on a zero-mean
    texture and on Sentinel-2 digital numbers, whose mean is far above their
    spread.

    Attributes:
        gain: Contrast gain, positive.
        offset: Level shift, in reference standard deviations.
        gamma: Exponent of the tone curve, positive. 1 leaves it linear.
    """

    gain: float = 1.0
    offset: float = 0.0
    gamma: float = 1.0

    def __post_init__(self) -> None:
        if self.gain <= 0 or self.gamma <= 0:
            raise ValueError(
                f"gain and gamma must be positive, got {self.gain}, {self.gamma}"
            )

    def __call__(self, pair: SimulatedPair, rng: np.random.Generator) -> SimulatedPair:
        """Apply the radiometric change to the moving image."""
        moving = pair.moving
        lo, hi = moving.min(), moving.max()
        if self.gamma != 1 and hi > lo:
            moving = lo + (hi - lo) * ((moving - lo) / (hi - lo)) ** self.gamma
        mean = moving.mean()
        moving = mean + self.gain * (moving - mean) + self.offset * pair.reference.std()
        return dataclasses.replace(pair, moving=moving)


@dataclass(frozen=True)
class Clouds:
    """Procedural clouds laid over the moving image.

    A smooth random field is thresholded so that a share ``cover`` of the pixels
    lies above the threshold. Opacity ramps linearly from 0 to 1 across a band of
    ``softness`` field standard deviations centred on the threshold, so banks
    have opaque cores and thin edges, and exactly ``cover`` of the pixels are at
    least half covered.

    Attributes:
        cover: Target share of pixels at least half covered, in [0, 1].
        softness: Width of the edge ramp, in standard deviations of the field.
        brightness: Cloud level above the reference mean, in reference standard
            deviations. Clouds are far brighter than the ground in visible bands.
    """

    cover: float
    softness: float = 0.5
    brightness: float = 4.0

    def __post_init__(self) -> None:
        if not 0 <= self.cover <= 1:
            raise ValueError(f"cover must be in [0, 1], got {self.cover}")
        if self.softness <= 0:
            raise ValueError(f"softness must be positive, got {self.softness}")

    def opacity(self, shape: tuple[int, int], rng: np.random.Generator) -> np.ndarray:
        """Draw a cloud opacity map.

        Args:
            shape: ``(rows, cols)`` of the map.
            rng: Generator for the cloud field.

        Returns:
            Opacity in [0, 1], of ``shape``.
        """
        field = power_law_field(shape, CLOUD_SPECTRAL_EXPONENT, rng)
        threshold = np.quantile(field, 1 - self.cover)
        return np.clip(0.5 + (field - threshold) / self.softness, 0.0, 1.0)

    def __call__(self, pair: SimulatedPair, rng: np.random.Generator) -> SimulatedPair:
        """Blend clouds into the moving image and record their opacity."""
        if self.cover == 0:
            return pair
        alpha = self.opacity(pair.moving.shape, rng)
        level = pair.reference.mean() + self.brightness * pair.reference.std()
        moving = (1 - alpha) * pair.moving + alpha * level
        if pair.cloud is not None:
            alpha = 1 - (1 - pair.cloud) * (1 - alpha)
        return dataclasses.replace(pair, moving=moving, cloud=alpha)


@dataclass(frozen=True)
class Blur:
    """A Gaussian blur of the moving image, for a sharpness difference.

    The kernel is symmetric, so it moves no content: the blurred image has the
    same geometry as the sharp one.

    Attributes:
        sigma: Standard deviation of the kernel, in pixels, non-negative.
    """

    sigma: float

    def __post_init__(self) -> None:
        if self.sigma < 0:
            raise ValueError(f"sigma must be non-negative, got {self.sigma}")

    def __call__(self, pair: SimulatedPair, rng: np.random.Generator) -> SimulatedPair:
        """Blur the moving image."""
        if self.sigma == 0:
            return pair
        moving = ndimage.gaussian_filter(pair.moving, self.sigma, mode="reflect")
        return dataclasses.replace(pair, moving=moving)


@dataclass(frozen=True)
class Noise:
    """Independent white Gaussian noise on both images, at a given SNR.

    Both images are acquisitions from the same sensor, so both get noise, drawn
    independently at the same level. The SNR is the reference's standard
    deviation over the noise's, in decibels: it measures how much scene contrast
    stands above the noise, which is what registration works from.

    Attributes:
        snr_db: ``20 * log10(std(reference) / std(noise))``.
    """

    snr_db: float

    def sigma(self, pair: SimulatedPair) -> float:
        """Standard deviation of the noise this SNR gives on ``pair``."""
        return float(pair.reference.std() / 10 ** (self.snr_db / 20))

    def __call__(self, pair: SimulatedPair, rng: np.random.Generator) -> SimulatedPair:
        """Add noise to both images."""
        sigma = self.sigma(pair)
        return dataclasses.replace(
            pair,
            reference=pair.reference + rng.normal(0, sigma, pair.reference.shape),
            moving=pair.moving + rng.normal(0, sigma, pair.moving.shape),
        )


@dataclass(frozen=True)
class Preset:
    """A combination of degradations, applied in a fixed physical order.

    The ground changes appearance (radiometry), clouds cover it, the sensor of
    the moving acquisition blurs everything it sees (blur), and both detectors
    add noise last. The order does not depend on how the preset is written.

    Attributes:
        radiometry: Radiometric difference, or ``None``.
        clouds: Clouds, or ``None``.
        blur: Blur, or ``None``.
        noise: Noise, or ``None``.
    """

    radiometry: Radiometry | None = None
    clouds: Clouds | None = None
    blur: Blur | None = None
    noise: Noise | None = None

    def __call__(self, pair: SimulatedPair, rng: np.random.Generator) -> SimulatedPair:
        """Apply every degradation of the preset, in order."""
        for step in (self.radiometry, self.clouds, self.blur, self.noise):
            if step is not None:
                pair = step(pair, rng)
        return pair


_STEPS: dict[str, type] = {
    "radiometry": Radiometry,
    "clouds": Clouds,
    "blur": Blur,
    "noise": Noise,
}


def load_presets(path: Path) -> dict[str, Preset]:
    """Read named degradation presets.

    Args:
        path: TOML file with one ``[presets.<name>]`` table per preset, holding
            an inline table of parameters per degradation, e.g.
            ``noise = { snr_db = 30 }``. An empty table is the clean preset.

    Returns:
        Preset name to preset, in file order.

    Raises:
        ValueError: If the ``presets`` table is missing, or a preset names an
            unknown degradation or gives it missing, unknown or invalid
            parameters.
    """
    with path.open("rb") as f:
        raw = tomllib.load(f)
    if not raw.get("presets"):
        raise ValueError(f"{path} needs [presets.<name>] tables")

    presets = {}
    for name, steps in raw["presets"].items():
        unknown = sorted(set(steps) - set(_STEPS))
        if unknown:
            raise ValueError(
                f"{path}: preset {name}: unknown degradation {', '.join(unknown)} "
                f"(known: {', '.join(_STEPS)})"
            )
        try:
            presets[name] = Preset(
                **{key: _STEPS[key](**params) for key, params in steps.items()}
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{path}: preset {name}: {exc}") from exc
    return presets

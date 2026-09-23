"""Run methods on simulated pairs and score them against the ground truth."""

import logging
import math
import zlib
from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np

from .degrade import Degradation, Preset
from .displacement import Affine
from .methods import Method
from .metrics import FAILURE_EPE_PX, is_failure, score
from .simulate import (
    SimulatedPair,
    margin_for,
    simulate_affine,
    simulate_translation,
)

logger = logging.getLogger(__name__)

DEGRADATIONS: dict[str, Degradation] = {"clean": Preset()}

# Geometric models a pair can be simulated with. An affine pair is its
# translation twin, same window and same shift of the centre, plus a rotation, a
# scale and a shear about the centre.
SCENARIOS = ("translation", "affine")


@dataclass(frozen=True)
class BenchmarkConfig:
    """Parameters of a benchmark run.

    Attributes:
        n_pairs: Simulated pairs per site.
        size: Side of each image in a pair, in pixels.
        max_shift: Shift components are drawn uniformly in ``[-max_shift,
            max_shift]`` px.
        max_rotation_deg: Affine rotations are drawn in ``[-max, max]`` degrees.
        max_scale_change: Affine scales are drawn in ``[1 - max, 1 + max]``.
        max_shear: Affine shears are drawn in ``[-max, max]``.
        scenarios: Geometric models to simulate, among ``SCENARIOS``.
        seed: Seed for pair geometry and degradations.
        failure_threshold: Mean end-point error above which a pair failed, in px.
    """

    n_pairs: int = 20
    size: int = 256
    max_shift: float = 4.0
    max_rotation_deg: float = 0.2
    max_scale_change: float = 0.002
    max_shear: float = 0.002
    scenarios: tuple[str, ...] = SCENARIOS
    seed: int = 0
    failure_threshold: float = FAILURE_EPE_PX

    def __post_init__(self) -> None:
        ranges = (self.max_shift, self.max_rotation_deg, self.max_shear)
        if min(ranges) < 0:
            raise ValueError(f"displacement ranges must be non-negative, got {ranges}")
        unknown = [s for s in self.scenarios if s not in SCENARIOS]
        if unknown or not self.scenarios:
            raise ValueError(
                f"scenarios must be among {', '.join(SCENARIOS)}, got {self.scenarios}"
            )
        if not 0 <= self.max_scale_change < 1:
            raise ValueError(
                f"max_scale_change must be in [0, 1), got {self.max_scale_change}"
            )


@dataclass(frozen=True)
class PairResult:
    """Outcome of one method on one pair: one row of the per-pair table.

    Attributes:
        site: Site the pair was cut from.
        scenario: Geometric model the pair was simulated with.
        degradation: Name of the degradation applied to the pair.
        method: Name of the method.
        pair: Index of the pair within its site.
        cloud_fraction: Share of the moving image at least half covered by cloud.
        truth: Ground-truth displacement, as text.
        estimate: Estimated displacement as text, empty if the method raised.
        mean_epe: Mean end-point error in pixels, NaN if the method raised.
        share_below_0_1: Share of pixels with an error under 0.1 px.
        share_below_0_5: Share of pixels with an error under 0.5 px.
        failed: Whether the pair counts as a failure.
        error: Exception raised by the method, empty otherwise.
    """

    site: str
    scenario: str
    degradation: str
    method: str
    pair: int
    cloud_fraction: float
    truth: str
    estimate: str
    mean_epe: float
    share_below_0_1: float
    share_below_0_5: float
    failed: bool
    error: str


def _rng(seed: int, *keys: str | int) -> np.random.Generator:
    """Derive a generator from the run seed and names, stable under reordering."""
    ints = [zlib.crc32(k.encode()) if isinstance(k, str) else k for k in keys]
    return np.random.default_rng([seed, *ints])


def max_reach(config: BenchmarkConfig) -> float:
    """Bound how far any pair of a run moves content, per component.

    The linear part ``A = R S H`` of an affine pair satisfies ``A - I = (R - I) +
    R (S - I) + R S (H - I)``, so its norm is at most ``e = 2 sin(theta / 2) +
    |s - 1| + s |h|``. The displacement of a point ``r`` from the centre is at most
    ``e |r| + |t|``, and that of the inverse map, which the warp samples, at most
    ``(e |r| + |t|) / (1 - e)``. Over a pair, ``|r|`` is at most half a diagonal.

    Args:
        config: Run parameters.

    Returns:
        An upper bound on the absolute row or column displacement, in pixels, of
        every pair of the run and of the inverse of its warp.
    """
    theta = math.radians(config.max_rotation_deg)
    scale = 1 + config.max_scale_change
    e = 2 * math.sin(theta / 2) + config.max_scale_change + scale * config.max_shear
    half_diagonal = (config.size - 1) / math.sqrt(2)
    shift = math.sqrt(2) * config.max_shift
    if e >= 1:
        raise ValueError("affine ranges too large: the warp could fold the image")
    return (e * half_diagonal + shift) / (1 - e)


def draw_pair(
    image: np.ndarray,
    config: BenchmarkConfig,
    rng: np.random.Generator,
    scenario: str = "translation",
) -> SimulatedPair:
    """Cut a random window from a site image and simulate a random displacement.

    The window, the shift and the affine parameters are drawn in the same order
    whatever the scenario, so a generator seeded the same way gives an affine
    pair and a translation pair with the same reference image and the same
    displacement at the centre. The margin covers every scenario of the run, for
    the same reason.

    Args:
        image: 2-D site image.
        config: Run parameters.
        rng: Generator for the window position and the displacement.
        scenario: One of ``SCENARIOS``.

    Returns:
        A clean simulated pair of ``config.size`` px.

    Raises:
        ValueError: If the image is too small for the window and its margin, or
            the scenario is unknown.
    """
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario!r}")
    margin = margin_for(max_reach(config))
    window = config.size + 2 * margin
    rows, cols = image.shape
    if rows < window or cols < window:
        raise ValueError(
            f"site image {image.shape} is smaller than the {window} px window needed "
            f"for {config.size} px pairs with shifts up to {config.max_shift} px"
        )
    top = int(rng.integers(0, rows - window + 1))
    left = int(rng.integers(0, cols - window + 1))
    dy, dx = rng.uniform(-config.max_shift, config.max_shift, size=2)
    rotation = rng.uniform(-config.max_rotation_deg, config.max_rotation_deg)
    scale = 1 + rng.uniform(-config.max_scale_change, config.max_scale_change)
    shear = rng.uniform(-config.max_shear, config.max_shear)
    source = image[top : top + window, left : left + window]
    if scenario == "translation":
        return simulate_translation(source, dx=float(dx), dy=float(dy), margin=margin)
    centre = (config.size - 1) / 2
    truth = Affine.about(
        (centre, centre),
        rotation_deg=float(rotation),
        scale=float(scale),
        shear=float(shear),
        dx=float(dx),
        dy=float(dy),
    )
    return simulate_affine(source, truth, margin)


def _run_method(
    method: Method,
    pair: SimulatedPair,
    failure_threshold: float,
    labels: dict[str, str | int],
) -> PairResult:
    """Run and score one method on one pair, turning any exception into a failure.

    Args:
        method: Method to run.
        pair: Simulated pair.
        failure_threshold: Mean end-point error above which the pair failed, in px.
        labels: ``site``, ``scenario``, ``degradation``, ``method`` and ``pair``
            of the row.

    Returns:
        The pair's result row.
    """
    try:
        estimate = method(pair.reference, pair.moving)
        pair_score = score(pair.truth, estimate, pair.reference.shape, pair.valid)
    # A method that crashes is a result, not a reason to stop the run.
    except Exception as exc:
        logger.warning("%s failed: %s: %s", labels["method"], type(exc).__name__, exc)
        return PairResult(
            **labels,
            cloud_fraction=pair.cloud_fraction,
            truth=repr(pair.truth),
            estimate="",
            mean_epe=math.nan,
            share_below_0_1=0.0,
            share_below_0_5=0.0,
            failed=True,
            error=f"{type(exc).__name__}: {exc}",
        )
    return PairResult(
        **labels,
        cloud_fraction=pair.cloud_fraction,
        truth=repr(pair.truth),
        estimate=repr(estimate),
        mean_epe=pair_score.mean_epe,
        share_below_0_1=pair_score.share_below_0_1,
        share_below_0_5=pair_score.share_below_0_5,
        failed=is_failure(pair_score, failure_threshold),
        error="",
    )


def run_benchmark(
    sites: Mapping[str, np.ndarray],
    methods: Mapping[str, Method],
    config: BenchmarkConfig,
    degradations: Mapping[str, Degradation] = DEGRADATIONS,
) -> list[PairResult]:
    """Score every method on every simulated pair.

    Pair geometry depends only on the seed, the site name and the pair index, so
    every scenario, degradation and method sees the same window and the same
    displacement at the centre. Errors are averaged over the pair's valid pixels.

    Args:
        sites: Site name to 2-D image to cut pairs from.
        methods: Method name to method.
        config: Run parameters.
        degradations: Degradation name to degradation.

    Returns:
        One result per site, scenario, degradation, method and pair.

    Raises:
        ValueError: If ``config.n_pairs`` is not positive.
    """
    if config.n_pairs < 1:
        raise ValueError(f"n_pairs must be positive, got {config.n_pairs}")

    results = []
    for site, image in sites.items():
        for index in range(config.n_pairs):
            for scenario in config.scenarios:
                geometry = _rng(config.seed, site, index)
                clean = draw_pair(image, config, geometry, scenario)
                for degradation_name, degrade in degradations.items():
                    rng = _rng(config.seed, site, index, degradation_name)
                    pair = degrade(clean, rng)
                    for method_name, method in methods.items():
                        labels = {
                            "site": site,
                            "scenario": scenario,
                            "degradation": degradation_name,
                            "method": method_name,
                            "pair": index,
                        }
                        results.append(
                            _run_method(method, pair, config.failure_threshold, labels)
                        )
    return results

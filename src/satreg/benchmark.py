"""Run methods on simulated pairs and score them against the ground truth."""

import dataclasses
import json
import logging
import math
import zlib
from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from .compute import measure
from .degrade import Degradation, Preset
from .displacement import Affine
from .georef import Georef
from .methods import (
    Estimate,
    GeoreferencedMethod,
    Method,
    RegistrationFailure,
    cost_meter,
)
from .metrics import FAILURE_EPE_PX, is_failure, score
from .simulate import (
    SimulatedPair,
    SmoothField,
    margin_for,
    simulate_affine,
    simulate_dense,
    simulate_translation,
)

logger = logging.getLogger(__name__)

DEGRADATIONS: dict[str, Degradation] = {"clean": Preset()}

# Geometric models a pair can be simulated with. An affine pair is its
# translation twin, same window and same shift of the centre, plus a rotation, a
# scale and a shear about the centre. A dense pair is its affine twin plus a
# smooth local field.
SCENARIOS = ("translation", "affine", "dense")


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
        max_local_shift: The local field of a dense pair has its largest
            magnitude over the pair drawn in ``[0, max]`` px. It stands for the
            residuals orthorectification leaves locally, mostly relief seen
            through an elevation model error from two viewing angles.
        local_length: Correlation length of that field, in px: the distance
            over which the residuals of one elevation model error stay alike.
        scenarios: Geometric models to simulate, among ``SCENARIOS``.
        band_pairs: Inter-band pairs to simulate, as ``(reference band, moving
            band)``: the reference image is cut from the first band and the
            moving image from the second, over the same window. Empty for
            single-band pairs, cut from each site's one image.
        seed: Seed for pair geometry and degradations.
        failure_threshold: Mean end-point error above which a pair failed, in px.
        warmup: Untimed calls of each method before its first timed one.
        repeats: Timed calls of a method on each pair; its time is their median.
    """

    n_pairs: int = 20
    size: int = 256
    max_shift: float = 4.0
    max_rotation_deg: float = 0.2
    max_scale_change: float = 0.002
    max_shear: float = 0.002
    max_local_shift: float = 0.8
    local_length: float = 64.0
    scenarios: tuple[str, ...] = SCENARIOS
    band_pairs: tuple[tuple[str, str], ...] = ()
    seed: int = 0
    failure_threshold: float = FAILURE_EPE_PX
    warmup: int = 1
    repeats: int = 3

    def __post_init__(self) -> None:
        if self.warmup < 0 or self.repeats < 1:
            raise ValueError(
                f"need warmup >= 0 and repeats >= 1, got {self.warmup} and "
                f"{self.repeats}"
            )
        ranges = (
            self.max_shift,
            self.max_rotation_deg,
            self.max_shear,
            self.max_local_shift,
        )
        if min(ranges) < 0:
            raise ValueError(f"displacement ranges must be non-negative, got {ranges}")
        unknown = [s for s in self.scenarios if s not in SCENARIOS]
        if unknown or not self.scenarios:
            raise ValueError(
                f"scenarios must be among {', '.join(SCENARIOS)}, got {self.scenarios}"
            )
        if any(len(pair) != 2 for pair in self.band_pairs):
            raise ValueError(
                f"band pairs must be (reference, moving), got {self.band_pairs}"
            )
        if self.local_length <= 0:
            raise ValueError(f"local_length must be positive, got {self.local_length}")
        if not 0 <= self.max_scale_change < 1:
            raise ValueError(
                f"max_scale_change must be in [0, 1), got {self.max_scale_change}"
            )


@dataclass(frozen=True)
class PairResult:
    """Outcome of one method on one pair: one row of the per-pair table.

    Attributes:
        site: Site the pair was cut from.
        bands: Band pair the pair was cut from, as ``reference/moving``, e.g.
            ``B04/B08``; empty for a single-band pair.
        scenario: Geometric model the pair was simulated with.
        degradation: Name of the degradation applied to the pair.
        method: Name of the method.
        device: Device the method ran on, ``"cpu"``, ``"mps"`` or ``"cuda"``.
        pair: Index of the pair within its site.
        cloud_fraction: Share of the moving image at least half covered by cloud.
        truth: Ground-truth displacement, as text.
        estimate: Estimated displacement as text, empty if the method raised.
        mean_epe: Mean end-point error in pixels, NaN if the method raised.
        share_below_0_1: Share of pixels with an error under 0.1 px.
        share_below_0_5: Share of pixels with an error under 0.5 px.
        failed: Whether the pair counts as a failure.
        error: Why the method gave up or crashed, empty otherwise.
        diagnostics: The method's own diagnostics as a JSON object, e.g.
            ``{"inliers": 153}``, empty if it reports none.
        time_ms: Median wall-clock time of the method call over the repeats, in
            milliseconds, whether it returned or raised.
        peak_mib: Peak memory the method call allocated, in MiB, as its meter
            reads it: traced by ``tracemalloc`` unless the method has its own
            (see ``satreg.compute``). NaN if the meter has no figure.
    """

    site: str
    bands: str
    scenario: str
    degradation: str
    method: str
    device: str
    pair: int
    cloud_fraction: float
    truth: str
    estimate: str
    mean_epe: float
    share_below_0_1: float
    share_below_0_5: float
    failed: bool
    error: str
    diagnostics: str
    # Cost changes from one run to the next on the same seed, so it is left out
    # of equality: two runs agree when their outcomes do.
    time_ms: float = field(compare=False)
    peak_mib: float = field(compare=False)


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
    The local field of a dense pair adds at most its peak ``l`` to the first
    bound, hence ``(e |r| + |t| + l) / (1 - e)`` for the inverse map.

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
    return (e * half_diagonal + shift + config.max_local_shift) / (1 - e)


def draw_pair(
    image: np.ndarray,
    config: BenchmarkConfig,
    rng: np.random.Generator,
    scenario: str = "translation",
    georef: Georef | None = None,
    reference: np.ndarray | None = None,
) -> SimulatedPair:
    """Cut a random window from a site image and simulate a random displacement.

    The window, the shift and the affine parameters are drawn in the same order
    whatever the scenario, so a generator seeded the same way gives an affine
    pair and a translation pair with the same reference image and the same
    displacement at the centre. A dense pair draws its local field after them,
    so it adds that field to its affine twin's truth. The margin covers every
    scenario, whether the run has it or not, for the same reason.

    An inter-band pair warps the window of ``image``, one band, into the moving
    image, and takes the reference image from the same window of ``reference``,
    another band of the same scene and grid. It is the single-band pair of
    ``image`` drawn with the same generator, with the reference swapped.

    Args:
        image: 2-D site image, the moving band of an inter-band pair.
        config: Run parameters.
        rng: Generator for the window position and the displacement.
        scenario: One of ``SCENARIOS``.
        georef: Map grid of the site image, if it has one.
        reference: Reference band of an inter-band pair, same shape and grid
            as ``image``; ``None`` for a single-band pair.

    Returns:
        A clean simulated pair of ``config.size`` px, on the grid of the window
        it covers when the site image has one.

    Raises:
        ValueError: If the image is too small for the window and its margin,
            the scenario is unknown, or the reference band is not the image's
            shape.
    """
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario!r}")
    if reference is not None and reference.shape != image.shape:
        raise ValueError(
            f"reference band {reference.shape} is not the shape of {image.shape}"
        )
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
    centre = (config.size - 1) / 2
    affine = Affine.about(
        (centre, centre),
        rotation_deg=float(rotation),
        scale=float(scale),
        shear=float(shear),
        dx=float(dx),
        dy=float(dy),
    )
    if scenario == "translation":
        pair = simulate_translation(source, dx=float(dx), dy=float(dy), margin=margin)
    elif scenario == "affine":
        pair = simulate_affine(source, affine, margin)
    else:
        peak = rng.uniform(0, config.max_local_shift)
        shape = (config.size, config.size)
        local = SmoothField.draw(rng, config.local_length, float(peak), shape)
        pair = simulate_dense(source, affine, local, margin)
    if reference is not None:
        # The window of the reference band, cropped by the margin like the pair.
        rows = slice(top + margin, top + margin + config.size)
        cols = slice(left + margin, left + margin + config.size)
        pair = dataclasses.replace(pair, reference=reference[rows, cols].astype(float))
    if georef is None:
        return pair
    # The pair is the window cropped by the margin on each side.
    return dataclasses.replace(pair, georef=georef.window(top + margin, left + margin))


def in_units_of(image: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Map a band linearly onto the mean and standard deviation of another.

    The degradations measure their levels in the reference image's statistics
    (cloud brightness, level offset, noise). Mapped this way, a moving band keeps
    every contrast it has, inversions included, but a cloud laid over it is as
    bright in its own units as over the reference, and the noise has the same
    SNR on both images. Every method stretches each image by its own statistics,
    so none sees the change. See docs/decisions.md.

    Args:
        image: 2-D band, the moving band of an inter-band pair.
        reference: 2-D band it is paired with.

    Returns:
        ``image`` as floats, with the mean and standard deviation of
        ``reference`` over the whole array.

    Raises:
        ValueError: If ``image`` is constant.
    """
    spread = float(image.std())
    if spread == 0:
        raise ValueError("a constant band cannot be mapped onto another")
    scaled = (image - image.mean()) * (reference.std() / spread)
    return reference.mean() + scaled


def _pair_sources(
    site: str,
    image: np.ndarray,
    config: BenchmarkConfig,
    bands: Mapping[str, Mapping[str, np.ndarray]],
) -> list[tuple[str, np.ndarray, np.ndarray | None]]:
    """List what a site's pairs are cut from: ``(bands label, moving, reference)``.

    A single-band run cuts both images from ``image``. An inter-band run cuts
    each band pair from the site's bands, the moving band in the reference
    band's units, except when both are the same band, which is left as stored
    so the pair is its single-band twin exactly.
    """
    if not config.band_pairs:
        return [("", image, None)]
    if site not in bands:
        raise ValueError(f"band pairs need the bands of site {site!r}")
    sources = []
    for reference_band, moving_band in config.band_pairs:
        missing = {reference_band, moving_band} - set(bands[site])
        if missing:
            raise ValueError(f"site {site!r} has no band {sorted(missing)[0]}")
        reference = bands[site][reference_band]
        moving = bands[site][moving_band]
        if moving_band != reference_band:
            moving = in_units_of(moving, reference)
        label = f"{reference_band}/{moving_band}"
        sources.append((label, moving, reference))
    return sources


def method_device(method: Method) -> str:
    """Name the device a method runs on.

    Args:
        method: A method, built-in or variant.

    Returns:
        The device its configuration names, for the deep-learning methods, and
        ``"cpu"`` for the others, which run on no other.
    """
    return getattr(method, "device", "cpu")


def _as_json(diagnostics: dict[str, float]) -> str:
    """Render diagnostics for a CSV cell: a JSON object, or empty if none."""
    return json.dumps(diagnostics, sort_keys=True) if diagnostics else ""


def _run_method(
    method: Method,
    pair: SimulatedPair,
    config: BenchmarkConfig,
    labels: dict[str, str | int],
    warmup: int = 0,
) -> PairResult:
    """Run, time and score one method on one pair; any exception is a failure.

    A ``RegistrationFailure`` is the method declining the pair, an expected
    outcome; any other exception is a crash. Both are failed rows. Only the
    method call is timed and traced: the pair is simulated and degraded before,
    and scored after.

    Args:
        method: Method to run.
        pair: Simulated pair.
        config: Run parameters: failure threshold and repeat count.
        labels: ``site``, ``bands``, ``scenario``, ``degradation``, ``method``,
            ``device`` and ``pair`` of the row.
        warmup: Untimed calls to make first.

    Returns:
        The pair's result row.
    """

    def call() -> object:
        if isinstance(method, GeoreferencedMethod):
            return method(pair.reference, pair.moving, pair.georef)
        return method(pair.reference, pair.moving)

    measured = measure(call, config.repeats, warmup, cost_meter(method))
    cost = {"time_ms": 1000 * measured.seconds, "peak_mib": measured.peak_mib}
    diagnostics = {}
    try:
        estimate = measured.result()
        if isinstance(estimate, Estimate):
            diagnostics = dict(estimate.diagnostics)
            estimate = estimate.displacement
        pair_score = score(pair.truth, estimate, pair.reference.shape, pair.valid)
    # A method that crashes is a result, not a reason to stop the run.
    except Exception as exc:
        if isinstance(exc, RegistrationFailure):
            diagnostics = exc.diagnostics
            logger.debug("%s gave up: %s", labels["method"], exc)
        else:
            logger.warning(
                "%s failed: %s: %s", labels["method"], type(exc).__name__, exc
            )
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
            diagnostics=_as_json(diagnostics),
            **cost,
        )
    return PairResult(
        **labels,
        cloud_fraction=pair.cloud_fraction,
        truth=repr(pair.truth),
        estimate=repr(estimate),
        mean_epe=pair_score.mean_epe,
        share_below_0_1=pair_score.share_below_0_1,
        share_below_0_5=pair_score.share_below_0_5,
        failed=is_failure(pair_score, config.failure_threshold),
        error="",
        diagnostics=_as_json(diagnostics),
        **cost,
    )


def run_benchmark(
    sites: Mapping[str, np.ndarray],
    methods: Mapping[str, Method],
    config: BenchmarkConfig,
    degradations: Mapping[str, Degradation] = DEGRADATIONS,
    georefs: Mapping[str, Georef] | None = None,
    bands: Mapping[str, Mapping[str, np.ndarray]] | None = None,
) -> list[PairResult]:
    """Score every method on every simulated pair.

    Pair geometry depends only on the seed, the site name and the pair index, so
    every band pair, scenario, degradation and method sees the same window and
    the same displacement at the centre. Errors are averaged over the pair's
    valid pixels. Each method is warmed up on the first pair it gets, then timed
    on every pair.

    Args:
        sites: Site name to 2-D image to cut pairs from.
        methods: Method name to method.
        config: Run parameters.
        degradations: Degradation name to degradation.
        georefs: Site name to the map grid of its image, for the sites that
            have one. Georeferenced methods get the grid of each pair.
        bands: Site name to band name to 2-D band, all on the grid of the
            site's image, for a run with ``config.band_pairs``. The pairs of
            such a run are cut from the bands instead of the site's image.

    Returns:
        One result per site, band pair, scenario, degradation, method and pair.

    Raises:
        ValueError: If ``config.n_pairs`` is not positive, or a band pair names
            a band a site does not have.
    """
    if config.n_pairs < 1:
        raise ValueError(f"n_pairs must be positive, got {config.n_pairs}")

    georefs = georefs or {}
    warmed: set[str] = set()
    results = []
    for site, image in sites.items():
        sources = _pair_sources(site, image, config, bands or {})
        for band_label, moving, reference in sources:
            for index in range(config.n_pairs):
                for scenario in config.scenarios:
                    geometry = _rng(config.seed, site, index)
                    clean = draw_pair(
                        moving, config, geometry, scenario, georefs.get(site), reference
                    )
                    for degradation_name, degrade in degradations.items():
                        rng = _rng(config.seed, site, index, degradation_name)
                        pair = degrade(clean, rng)
                        for method_name, method in methods.items():
                            labels = {
                                "site": site,
                                "bands": band_label,
                                "scenario": scenario,
                                "degradation": degradation_name,
                                "method": method_name,
                                "device": method_device(method),
                                "pair": index,
                            }
                            warmup = 0 if method_name in warmed else config.warmup
                            warmed.add(method_name)
                            results.append(
                                _run_method(method, pair, config, labels, warmup)
                            )
    return results

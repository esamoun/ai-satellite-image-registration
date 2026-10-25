"""Cycle consistency: accuracy on real pairs, which have no ground truth.

Three dates A < B < C of a site share one grid. A method registers A to B, B to C
and A to C, the earlier date as reference each time, as for every real pair.
Chained, the first two legs should give the third: the closure residual
``compose(d_AB, d_BC)(p) - d_AC(p)`` on A's grid is zero for exact estimates.
Its size, per method and site, is the real-pair counterpart of the simulated
end-point error. It is not the same quantity: errors that the three legs share
in the right proportions cancel out of it. Simulated triplets, whose legs have a
known truth, report both, to show how far one stands for the other. See
docs/decisions.md.

Real pairs are registered on the same 256 px windows ``check-presets`` measures,
the benchmark's pair size, and each pair of a window once, whichever triplets
share it.
"""

import dataclasses
import itertools
import logging
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np
from scipy import ndimage

from .appearance import windows
from .benchmark import BenchmarkConfig, _as_json, _rng, max_reach, method_device
from .compute import measure
from .degrade import Preset
from .displacement import Affine, Dense, Displacement, Translation, compose
from .georef import Georef
from .methods import (
    Estimate,
    GeoreferencedMethod,
    Method,
    RegistrationFailure,
    cost_meter,
)
from .metrics import endpoint_error
from .presetcheck import MAX_WINDOW_CLOUD, WINDOW_PX
from .real import Acquisition, triplets
from .simulate import (
    OPAQUE_CLOUD,
    SimulatedPair,
    SmoothField,
    invert,
    margin_for,
    simulate_affine,
    simulate_dense,
    simulate_translation,
)

logger = logging.getLogger(__name__)

# Scenario label of real triplets, next to the simulated scenarios.
REAL = "real"

# Percentile of the non-translation part of a displacement reported for it: the
# confidence level of the Sentinel-2 multi-temporal registration requirement
# (0.3 px at 95 %). For an affine displacement it sits a little inside the
# worst corner.
NON_TRANSLATION_PERCENTILE = 95


@dataclass(frozen=True)
class Leg:
    """One registration of a triplet: a method on one pair of dates.

    Attributes:
        displacement: What the method returned, ``None`` if it declined or
            crashed.
        error: Why it declined or crashed, empty otherwise.
        diagnostics: The method's diagnostics, as a JSON object or empty.
        time_ms: Median wall-clock time of the call, in milliseconds.
        peak_mib: Peak memory of the call, in MiB, as its meter reads it.
    """

    displacement: Displacement | None
    error: str
    diagnostics: str
    time_ms: float
    peak_mib: float


def register(
    method: Method,
    reference: np.ndarray,
    moving: np.ndarray,
    georef: Georef | None,
    repeats: int,
    warmup: int = 0,
) -> Leg:
    """Run and time one method on one pair; any exception is a failed leg.

    Args:
        method: Method to run.
        reference: Reference image.
        moving: Moving image, same shape.
        georef: Map grid of both images, for georeferenced methods.
        repeats: Timed calls.
        warmup: Untimed calls made first.

    Returns:
        The leg.
    """

    def call() -> object:
        if isinstance(method, GeoreferencedMethod):
            return method(reference, moving, georef)
        return method(reference, moving)

    measured = measure(call, repeats, warmup, cost_meter(method))
    cost = {"time_ms": 1000 * measured.seconds, "peak_mib": measured.peak_mib}
    try:
        estimate = measured.result()
    # A method that crashes is a result, not a reason to stop the run.
    except Exception as exc:
        diagnostics = {}
        if isinstance(exc, RegistrationFailure):
            diagnostics = exc.diagnostics
            logger.debug("%s gave up: %s", method, exc)
        else:
            logger.warning("%s failed: %s: %s", method, type(exc).__name__, exc)
        return Leg(None, f"{type(exc).__name__}: {exc}", _as_json(diagnostics), **cost)
    diagnostics = {}
    if isinstance(estimate, Estimate):
        diagnostics = dict(estimate.diagnostics)
        estimate = estimate.displacement
    return Leg(estimate, "", _as_json(diagnostics), **cost)


def translation_part(displacement: Displacement, shape: tuple[int, int]) -> np.ndarray:
    """The translation a displacement makes over a window: its median.

    For an affine displacement on a window, each component is linear over a grid
    symmetric about its centre, so the median is the displacement at the centre.
    A dense one's median is not pulled by a few wild pixels.

    Args:
        displacement: Any displacement.
        shape: ``(rows, cols)`` of the window.

    Returns:
        ``(dy, dx)``, in pixels.
    """
    return np.median(displacement.field(shape).reshape(2, -1), axis=1)


def displacement_summary(
    displacement: Displacement, shape: tuple[int, int]
) -> tuple[float, float]:
    """Size a displacement: its translation, and the part that is not one.

    Args:
        displacement: Any displacement.
        shape: ``(rows, cols)`` of the window it applies to.

    Returns:
        The magnitude of ``translation_part``, and the
        ``NON_TRANSLATION_PERCENTILE`` percentile over the window of the distance
        between the displacement and that translation, both in pixels.
    """
    t = translation_part(displacement, shape)
    rest = displacement.field(shape) - t[:, None, None]
    return (
        float(np.hypot(*t)),
        float(np.percentile(np.hypot(*rest), NON_TRANSLATION_PERCENTILE)),
    )


def lands_inside(displacement: Displacement, shape: tuple[int, int]) -> np.ndarray:
    """Pixels whose displaced position lies within the grid's pixel centres.

    Args:
        displacement: Any displacement, on a ``shape`` grid.
        shape: ``(rows, cols)`` of the grid.

    Returns:
        Boolean array of ``shape``. Non-finite displacements land nowhere.
    """
    target = np.indices(shape, dtype=float) + displacement.field(shape)
    rows, cols = shape
    with np.errstate(invalid="ignore"):
        return (
            (target[0] >= 0)
            & (target[0] <= rows - 1)
            & (target[1] >= 0)
            & (target[1] <= cols - 1)
        )


def closure_error(
    ab: Displacement,
    bc: Displacement,
    ac: Displacement,
    shape: tuple[int, int],
    mask: np.ndarray,
) -> np.ndarray:
    """Per-pixel closure residual of a triplet: A to B to C against A to C.

    Args:
        ab: Displacement from A to B, on A's grid.
        bc: Displacement from B to C, on B's grid.
        ac: Displacement from A to C, on A's grid.
        shape: ``(rows, cols)`` of the grid.
        mask: Pixels of A to keep. Only pixels whose position in B and in C, by
            ``ab`` and ``ac``, lies inside the grid are a closure, so the rest
            are dropped too.

    Returns:
        1-D array of the residual's magnitude, in pixels, one per kept pixel.

    Raises:
        ValueError: If no pixel is kept.
    """
    keep = mask & lands_inside(ab, shape) & lands_inside(ac, shape)
    return endpoint_error(ac, compose(ab, bc), shape, keep)


@dataclass(frozen=True)
class LegRow:
    """One registration of a cycle run: one row of ``legs.csv``.

    Attributes:
        site: Site the windows are cut from.
        scenario: ``REAL``, or the geometric model of a simulated triplet.
        condition: For a simulated triplet, its degradation preset; empty for a
            real pair.
        pair: ``"<role>-<role>"`` of a real pair, reference first, or ``"A-B"``,
            ``"B-C"`` or ``"A-C"`` in a simulated triplet.
        gap_days: Days between the two dates, 0 for a simulated pair.
        window: Window of the chip for a real pair, triplet index for a
            simulated one.
        method: Method name.
        device: Device the method ran on.
        estimate: The displacement returned, as text, empty if none.
        translation_px: Magnitude of its translation part, ``translation_part``.
        non_translation_px: Size of the rest, by ``displacement_summary``.
        truth: The true displacement, as text, empty for a real pair.
        true_translation_px: Magnitude of the truth's translation part.
        true_non_translation_px: Size of the rest of the truth.
        failed: Whether the method declined or crashed.
        error: Why, empty otherwise.
        diagnostics: The method's diagnostics, as a JSON object or empty.
        time_ms: Median wall-clock time of the call, in ms.
        peak_mib: Peak memory of the call, in MiB.
    """

    site: str
    scenario: str
    condition: str
    pair: str
    gap_days: int
    window: int
    method: str
    device: str
    estimate: str
    translation_px: float
    non_translation_px: float
    truth: str
    true_translation_px: float
    true_non_translation_px: float
    failed: bool
    error: str
    diagnostics: str
    time_ms: float = field(compare=False)
    peak_mib: float = field(compare=False)


@dataclass(frozen=True)
class TripletRow:
    """Closure of one triplet for one method: one row of ``triplets.csv``.

    Attributes:
        site: Site the windows are cut from.
        scenario: ``REAL``, or the geometric model of a simulated triplet.
        triplet: Roles of the three dates in chronological order, e.g.
            ``"anchor-days-season"``, or the degradation preset of a simulated
            triplet.
        window: Window of the chip for a real triplet, triplet index for a
            simulated one.
        method: Method name.
        device: Device the method ran on.
        cloud_fraction: Share of the window hidden on one of the three dates, or
            under opaque cloud in B or C for a simulated triplet.
        mean_closure: Mean closure residual over the kept pixels, in pixels, NaN
            if a leg failed.
        share_below_0_1: Share of kept pixels with a residual under 0.1 px.
        share_below_0_5: Share of kept pixels with a residual under 0.5 px.
        true_epe: Mean over the three legs of their mean end-point error on the
            same pixels, NaN for a real triplet or a failed leg.
        truth_closure: Mean closure residual of the true legs on the same
            pixels, what composing alone leaves; NaN for a real triplet.
        failed: Whether a leg declined or crashed, or the mean closure exceeds
            the failure threshold.
        error: Which leg failed and why, empty otherwise.
        time_ms: Mean over the three legs of their call time, in ms: the cost of
            one registration.
        peak_mib: Largest peak memory of the three calls, in MiB.
    """

    site: str
    scenario: str
    triplet: str
    window: int
    method: str
    device: str
    cloud_fraction: float
    mean_closure: float
    share_below_0_1: float
    share_below_0_5: float
    true_epe: float
    truth_closure: float
    failed: bool
    error: str
    time_ms: float = field(compare=False)
    peak_mib: float = field(compare=False)


LEGS = ("A-B", "B-C", "A-C")


def triplet_row(
    labels: Mapping[str, str | int],
    legs: Sequence[Leg],
    names: Sequence[str],
    shape: tuple[int, int],
    hidden: np.ndarray,
    threshold: float,
    truths: Sequence[Displacement] | None = None,
) -> TripletRow:
    """Score the closure of one triplet.

    Args:
        labels: ``site``, ``scenario``, ``triplet``, ``window``, ``method`` and
            ``device`` of the row.
        legs: The legs A to B, B to C and A to C.
        names: Names of the legs, for the error message.
        shape: ``(rows, cols)`` of the window.
        hidden: Pixels of A left out: hidden on a date, or under opaque cloud.
        threshold: Mean closure above which the triplet failed, in px.
        truths: The true legs, in the same order, for a simulated triplet.

    Returns:
        The row. A failed leg fails the triplet.
    """
    cost = {
        "time_ms": float(np.mean([leg.time_ms for leg in legs])),
        "peak_mib": float(max(leg.peak_mib for leg in legs)),
    }
    base = {**labels, "cloud_fraction": float(hidden.mean()), **cost}
    failed_legs = [
        f"{name}: {leg.error}"
        for name, leg in zip(names, legs, strict=True)
        if leg.displacement is None
    ]
    mask = ~hidden
    if truths is not None:
        # Only pixels whose true position in B and C is observable are scored,
        # like the valid pixels of a simulated pair.
        mask = mask & lands_inside(truths[0], shape) & lands_inside(truths[2], shape)
    if not failed_legs:
        ab, bc, ac = (leg.displacement for leg in legs)
        try:
            residual = closure_error(ab, bc, ac, shape, mask)
        except ValueError as exc:
            failed_legs = [f"closure: {exc}"]
    if failed_legs:
        return TripletRow(
            **base,
            mean_closure=math.nan,
            share_below_0_1=0.0,
            share_below_0_5=0.0,
            true_epe=math.nan,
            truth_closure=math.nan,
            failed=True,
            error="; ".join(failed_legs),
        )

    mean = float(residual.mean())
    true_epe = truth_closure = math.nan
    if truths is not None:
        keep = mask & lands_inside(ab, shape) & lands_inside(ac, shape)
        true_epe = float(
            np.mean(
                [
                    endpoint_error(t, leg.displacement, shape, keep).mean()
                    for t, leg in zip(truths, legs, strict=True)
                ]
            )
        )
        truth_closure = float(closure_error(*truths, shape, keep).mean())
    return TripletRow(
        **base,
        mean_closure=mean,
        share_below_0_1=float(np.mean(residual < 0.1)),
        share_below_0_5=float(np.mean(residual < 0.5)),
        true_epe=true_epe,
        truth_closure=truth_closure,
        failed=not np.isfinite(mean) or mean > threshold,
        error="",
    )


def _leg_row(
    labels: Mapping[str, str | int],
    leg: Leg,
    shape: tuple[int, int],
    truth: Displacement | None = None,
) -> LegRow:
    estimate = leg.displacement
    size = (math.nan, math.nan)
    if estimate is not None and np.all(np.isfinite(estimate.field(shape))):
        size = displacement_summary(estimate, shape)
    true_size = (math.nan, math.nan)
    if truth is not None:
        true_size = displacement_summary(truth, shape)
    return LegRow(
        **labels,
        estimate=repr(estimate) if estimate is not None else "",
        translation_px=size[0],
        non_translation_px=size[1],
        truth=repr(truth) if truth is not None else "",
        true_translation_px=true_size[0],
        true_non_translation_px=true_size[1],
        failed=estimate is None,
        error=leg.error,
        diagnostics=leg.diagnostics,
        time_ms=leg.time_ms,
        peak_mib=leg.peak_mib,
    )


def run_real(
    site: str,
    series: Sequence[Acquisition],
    methods: Mapping[str, Method],
    config: BenchmarkConfig,
    warmed: set[str] | None = None,
) -> tuple[list[LegRow], list[TripletRow]]:
    """Register every pair a site's triplets need, and score their closure.

    Each triplet is scored on each 256 px window of the chip whose share hidden
    on one of its three dates is at most ``MAX_WINDOW_CLOUD``. A pair of dates is
    registered once per window, whichever triplets share it.

    Args:
        site: Site name.
        series: The site's acquisitions, on one grid.
        methods: Method name to method.
        config: Run parameters: failure threshold, warm-up and repeats.
        warmed: Methods already warmed up, updated in place.

    Returns:
        One leg row per registration, and one triplet row per triplet, window
        and method.
    """
    warmed = set() if warmed is None else warmed
    cut = windows(WINDOW_PX, series[0].image.shape)
    shape = (WINDOW_PX, WINDOW_PX)
    legs: dict[tuple[str, str, int, str], Leg] = {}
    leg_rows, rows = [], []
    for a, b, c in triplets(list(series)):
        label = "-".join(x.role for x in (a, b, c))
        for index, (window_rows, window_cols) in enumerate(cut):
            hidden = (a.hidden | b.hidden | c.hidden)[window_rows, window_cols]
            if hidden.mean() > MAX_WINDOW_CLOUD:
                continue
            for name, method in methods.items():
                device = method_device(method)
                triplet_legs = []
                for reference, moving in ((a, b), (b, c), (a, c)):
                    key = (reference.role, moving.role, index, name)
                    if key not in legs:
                        warmup = 0 if name in warmed else config.warmup
                        warmed.add(name)
                        georef = reference.georef.window(
                            window_rows.start, window_cols.start
                        )
                        legs[key] = register(
                            method,
                            reference.image[window_rows, window_cols].astype(float),
                            moving.image[window_rows, window_cols].astype(float),
                            georef,
                            config.repeats,
                            warmup,
                        )
                        gap = (moving.datetime.date() - reference.datetime.date()).days
                        labels = {
                            "site": site,
                            "scenario": REAL,
                            "condition": "",
                            "pair": f"{reference.role}-{moving.role}",
                            "gap_days": gap,
                            "window": index,
                            "method": name,
                            "device": device,
                        }
                        leg_rows.append(_leg_row(labels, legs[key], shape))
                    triplet_legs.append(legs[key])
                labels = {
                    "site": site,
                    "scenario": REAL,
                    "triplet": label,
                    "window": index,
                    "method": name,
                    "device": device,
                }
                rows.append(
                    triplet_row(
                        labels,
                        triplet_legs,
                        [f"{x.role}-{y.role}" for x, y in ((a, b), (b, c), (a, c))],
                        shape,
                        hidden,
                        config.failure_threshold,
                    )
                )
    return leg_rows, rows


@dataclass(frozen=True)
class SimulatedTriplet:
    """Three images of one window with known displacements between them.

    B and C are A under two displacements drawn independently, so the truth of
    B to C is the second after the inverse of the first.

    Attributes:
        images: A, B and C.
        truths: True displacements A to B, B to C and A to C.
        clouds: Cloud opacity over B and over C, or ``None`` where there is none.
        georef: Map grid of the window, if the site image has one.
    """

    images: tuple[np.ndarray, np.ndarray, np.ndarray]
    truths: tuple[Displacement, Displacement, Displacement]
    clouds: tuple[np.ndarray | None, np.ndarray | None] = (None, None)
    georef: Georef | None = None


def _invert_affine(transform: Affine) -> Affine:
    inverse = np.linalg.inv(np.asarray(transform.matrix))
    offset = -inverse @ np.asarray(transform.offset)
    return Affine(
        matrix=(
            (float(inverse[0, 0]), float(inverse[0, 1])),
            (float(inverse[1, 0]), float(inverse[1, 1])),
        ),
        offset=(float(offset[0]), float(offset[1])),
    )


def draw_triplet(
    image: np.ndarray,
    config: BenchmarkConfig,
    rng: np.random.Generator,
    scenario: str,
    georef: Georef | None = None,
) -> SimulatedTriplet:
    """Cut a random window from a site image and simulate a clean triplet.

    Each of the two displacements is drawn as ``draw_pair`` draws a pair's, from
    the same ranges, so each leg from A is a benchmark pair and B to C spans up
    to twice the ranges.

    Args:
        image: 2-D site image.
        config: Run parameters: window size and displacement ranges.
        rng: Generator for the window and the displacements.
        scenario: ``"translation"``, ``"affine"`` or ``"dense"``.
        georef: Map grid of the site image, if it has one.

    Returns:
        The triplet, on the grid of the window when the image has one.

    Raises:
        ValueError: If the image is too small for the window and its margin.
    """
    margin = margin_for(max_reach(config))
    window = config.size + 2 * margin
    rows, cols = image.shape
    if rows < window or cols < window:
        raise ValueError(f"site image {image.shape} is smaller than {window} px")
    top = int(rng.integers(0, rows - window + 1))
    left = int(rng.integers(0, cols - window + 1))
    source = image[top : top + window, left : left + window].astype(float)
    centre = (config.size - 1) / 2
    shape = (config.size, config.size)
    grid = np.indices(shape, dtype=float)

    legs = []
    for _ in range(2):
        dy, dx = rng.uniform(-config.max_shift, config.max_shift, size=2)
        rotation = rng.uniform(-config.max_rotation_deg, config.max_rotation_deg)
        scale = 1 + rng.uniform(-config.max_scale_change, config.max_scale_change)
        shear = rng.uniform(-config.max_shear, config.max_shear)
        affine = Affine.about(
            (centre, centre),
            rotation_deg=float(rotation),
            scale=float(scale),
            shear=float(shear),
            dx=float(dx),
            dy=float(dy),
        )
        # Drawn for every scenario, so that the second leg's draws are the same
        # whatever the scenario.
        peak = rng.uniform(0, config.max_local_shift)
        local = SmoothField.draw(rng, config.local_length, float(peak), shape)
        if scenario == "translation":
            pair = simulate_translation(source, float(dx), float(dy), margin)
            legs.append((pair, None))
        elif scenario == "affine":
            legs.append((simulate_affine(source, affine, margin), None))
        else:

            def forward(points, affine=affine, local=local):
                return affine.apply(points) + local(points)

            legs.append((simulate_dense(source, affine, local, margin), forward))

    (first, forward1), (second, forward2) = legs
    if scenario == "translation":
        t1, t2 = first.truth, second.truth
        between = Translation(dx=t2.dx - t1.dx, dy=t2.dy - t1.dy)
    elif scenario == "affine":
        between = compose(_invert_affine(first.truth), second.truth)
    else:
        # Content at q in B came from invert(forward1, q) in A, and is found at
        # forward2 of that in C.
        between = Dense(forward2(invert(forward1, grid)) - grid)
    return SimulatedTriplet(
        images=(first.reference, first.moving, second.moving),
        truths=(first.truth, between, second.truth),
        georef=georef.window(top + margin, left + margin) if georef else None,
    )


def degrade_triplet(
    triplet: SimulatedTriplet, degrade: Preset, rng: np.random.Generator
) -> SimulatedTriplet:
    """Degrade each image of a triplet once, whichever legs it takes part in.

    B and C each get the preset as the moving image of a pair with A: their own
    radiometry, clouds and blur. A gets the noise of the first of these pairs, as
    a reference does. Each image is then the same in every leg, as a real date
    is.

    Args:
        triplet: A clean triplet.
        degrade: The degradation, as for a pair.
        rng: Generator for its randomness.

    Returns:
        The degraded triplet, same truths.
    """
    a, b, c = triplet.images
    ab = degrade(SimulatedPair(a, b, triplet.truths[0]), rng)
    ac = degrade(SimulatedPair(a, c, triplet.truths[2]), rng)
    return dataclasses.replace(
        triplet,
        images=(ab.reference, ab.moving, ac.moving),
        clouds=(ab.cloud, ac.cloud),
    )


def _opaque(
    cloud: np.ndarray | None, truth: Displacement, shape: tuple[int, int]
) -> np.ndarray:
    """Pixels of A whose true position in B or C lies under opaque cloud."""
    if cloud is None:
        return np.zeros(shape, bool)
    target = np.indices(shape, dtype=float) + truth.field(shape)
    opacity = ndimage.map_coordinates(cloud, target, order=1, mode="nearest")
    return opacity >= OPAQUE_CLOUD


def run_simulated(
    site: str,
    image: np.ndarray,
    methods: Mapping[str, Method],
    config: BenchmarkConfig,
    degradations: Mapping[str, Preset],
    georef: Georef | None = None,
    warmed: set[str] | None = None,
) -> tuple[list[LegRow], list[TripletRow]]:
    """Score the closure of simulated triplets, next to their true error.

    Triplet geometry depends only on the seed, the site and the triplet index,
    so every degradation and method sees the same windows and displacements.
    Every scenario draws the same window and centre shifts.

    Args:
        site: Site name.
        image: 2-D site image to cut windows from.
        methods: Method name to method.
        config: Run parameters; ``n_pairs`` is the number of triplets per
            scenario and degradation, ``size`` the window side.
        degradations: Degradation name to degradation.
        georef: Map grid of the site image, if it has one.
        warmed: Methods already warmed up, updated in place.

    Returns:
        One leg row per registration, and one triplet row per triplet and
        method.
    """
    warmed = set() if warmed is None else warmed
    shape = (config.size, config.size)
    leg_rows, rows = [], []
    for index, scenario, (condition, degrade) in itertools.product(
        range(config.n_pairs), config.scenarios, degradations.items()
    ):
        clean = draw_triplet(
            image, config, _rng(config.seed, site, "cycle", index), scenario, georef
        )
        triplet = degrade_triplet(
            clean, degrade, _rng(config.seed, site, "cycle", index, condition)
        )
        a, b, c = triplet.images
        ab, bc, ac = triplet.truths
        hidden = _opaque(triplet.clouds[0], ab, shape) | _opaque(
            triplet.clouds[1], ac, shape
        )
        for name, method in methods.items():
            device = method_device(method)
            legs = []
            for leg_name, reference, moving, truth in zip(
                LEGS, (a, b, a), (b, c, c), triplet.truths, strict=True
            ):
                warmup = 0 if name in warmed else config.warmup
                warmed.add(name)
                leg = register(
                    method, reference, moving, triplet.georef, config.repeats, warmup
                )
                labels = {
                    "site": site,
                    "scenario": scenario,
                    "condition": condition,
                    "pair": leg_name,
                    "gap_days": 0,
                    "window": index,
                    "method": name,
                    "device": device,
                }
                leg_rows.append(_leg_row(labels, leg, shape, truth))
                legs.append(leg)
            labels = {
                "site": site,
                "scenario": scenario,
                "triplet": condition,
                "window": index,
                "method": name,
                "device": device,
            }
            rows.append(
                triplet_row(
                    labels,
                    legs,
                    LEGS,
                    shape,
                    hidden,
                    config.failure_threshold,
                    (ab, bc, ac),
                )
            )
    return leg_rows, rows


@dataclass(frozen=True)
class CycleSummaryRow:
    """One row of the closure table: a method on a site, scenario and triplet.

    As in the benchmark, accuracy columns average the triplets that did not
    fail, which ``failure_rate`` counts, and cost columns take the median over
    every triplet.

    Attributes:
        site: Site name.
        scenario: ``REAL`` or a simulated scenario.
        triplet: Roles of a real triplet, or the degradation of simulated ones.
        method: Method name.
        device: Device the method ran on.
        n_triplets: Triplets attempted (windows, for a real triplet).
        cloud_fraction: Mean share of the window left out as hidden.
        failure_rate: Share of triplets that failed.
        mean_closure: Mean closure residual over non-failed triplets, in px.
        share_below_0_1: Share of pixels under 0.1 px, over non-failed ones.
        share_below_0_5: Share of pixels under 0.5 px, over non-failed ones.
        true_epe: Mean true end-point error of the legs, over non-failed
            triplets, NaN for real ones.
        truth_closure: Mean closure of the true legs, over non-failed triplets,
            NaN for real ones.
        time_ms: Median over triplets of the mean call time, in ms.
        peak_mib: Median over triplets of the largest peak memory, in MiB.
    """

    site: str
    scenario: str
    triplet: str
    method: str
    device: str
    n_triplets: int
    cloud_fraction: float
    failure_rate: float
    mean_closure: float
    share_below_0_1: float
    share_below_0_5: float
    true_epe: float
    truth_closure: float
    time_ms: float
    peak_mib: float


def _mean(values: Sequence[float]) -> float:
    return float(np.mean(values)) if values else math.nan


def _median(values: Sequence[float]) -> float:
    return float(np.median(values)) if values else math.nan


def summarize(rows: Sequence[TripletRow]) -> list[CycleSummaryRow]:
    """Group triplet rows by site, scenario, triplet, method and device.

    Args:
        rows: Triplet rows, in any order.

    Returns:
        One row per group, in order of first appearance.
    """
    groups: dict[tuple[str, str, str, str, str], list[TripletRow]] = {}
    for r in rows:
        key = (r.site, r.scenario, r.triplet, r.method, r.device)
        groups.setdefault(key, []).append(r)
    summary = []
    for (site, scenario, triplet, method, device), group in groups.items():
        kept = [r for r in group if not r.failed]
        summary.append(
            CycleSummaryRow(
                site=site,
                scenario=scenario,
                triplet=triplet,
                method=method,
                device=device,
                n_triplets=len(group),
                cloud_fraction=_mean([r.cloud_fraction for r in group]),
                failure_rate=(len(group) - len(kept)) / len(group),
                mean_closure=_mean([r.mean_closure for r in kept]),
                share_below_0_1=_mean([r.share_below_0_1 for r in kept]),
                share_below_0_5=_mean([r.share_below_0_5 for r in kept]),
                true_epe=_mean([r.true_epe for r in kept]),
                truth_closure=_mean([r.truth_closure for r in kept]),
                time_ms=_median([r.time_ms for r in group]),
                peak_mib=_median([r.peak_mib for r in group]),
            )
        )
    return summary


def _percent(x: float) -> str:
    return "n/a" if math.isnan(x) else f"{100 * x:.1f} %"


def _pixels(x: float) -> str:
    return "n/a" if math.isnan(x) else f"{x:.4f}"


def _cost(x: float) -> str:
    return "n/a" if math.isnan(x) else f"{x:.1f}"


def to_markdown(rows: Sequence[CycleSummaryRow]) -> str:
    """Render the closure table as markdown, real triplets and simulated apart.

    Args:
        rows: Summary rows.

    Returns:
        One table for real triplets, then one for simulated ones with their true
        error next to the closure, each ending with a newline; a table is left
        out if it has no row.
    """
    columns = (
        "| site | {what} | method | device | triplets | clouds | closure (px) "
        "| < 0.1 px | < 0.5 px |{extra} failures | time (ms) | memory (MiB) |\n"
    )
    out = []
    real = [r for r in rows if r.scenario == REAL]
    if real:
        out.append(
            columns.format(what="triplet", extra="")
            + "|---" * 4
            + "|---:" * 8
            + "|\n"
            + "".join(
                f"| {r.site} | {r.triplet} | {r.method} | {r.device} "
                f"| {r.n_triplets} | {_percent(r.cloud_fraction)} "
                f"| {_pixels(r.mean_closure)} | {_percent(r.share_below_0_1)} "
                f"| {_percent(r.share_below_0_5)} | {_percent(r.failure_rate)} "
                f"| {_cost(r.time_ms)} | {_cost(r.peak_mib)} |\n"
                for r in real
            )
        )
    simulated = [r for r in rows if r.scenario != REAL]
    if simulated:
        out.append(
            columns.format(
                what="scenario | degradation",
                extra=" true EPE (px) | truth closure (px) |",
            )
            + "|---" * 5
            + "|---:" * 10
            + "|\n"
            + "".join(
                f"| {r.site} | {r.scenario} | {r.triplet} | {r.method} | {r.device} "
                f"| {r.n_triplets} | {_percent(r.cloud_fraction)} "
                f"| {_pixels(r.mean_closure)} | {_percent(r.share_below_0_1)} "
                f"| {_percent(r.share_below_0_5)} | {_pixels(r.true_epe)} "
                f"| {_pixels(r.truth_closure)} | {_percent(r.failure_rate)} "
                f"| {_cost(r.time_ms)} | {_cost(r.peak_mib)} |\n"
                for r in simulated
            )
        )
    return "\n".join(out)


@dataclass(frozen=True)
class MotionRow:
    """How far a method finds real dates apart, next to the simulated ranges.

    Attributes:
        pair: Role pair of real dates, roles in series order, or the simulated
            scenario whose truths the row sizes.
        method: Method name, or ``"truth"`` for a simulated row.
        n: Registrations sized (non-failed legs).
        translation_px: ``(median, max)`` of the translation magnitude.
        non_translation_px: ``(median, max)`` of the non-translation part.
        translation_only: Whether every sized displacement is a translation,
            whose non-translation part is zero by construction.
    """

    pair: str
    method: str
    n: int
    translation_px: tuple[float, float]
    non_translation_px: tuple[float, float]
    translation_only: bool


def motion_summary(
    legs: Sequence[LegRow], role_order: Sequence[str]
) -> list[MotionRow]:
    """Size the displacements found between real dates, and the simulated truths.

    Real legs are grouped by pair of roles and method, across sites and windows;
    simulated legs from A (A-B and A-C, one benchmark pair each) by scenario,
    from their truths, once per triplet whatever the method and degradation.

    Args:
        legs: Leg rows of a run.
        role_order: Roles in series order, to order and name real pairs.

    Returns:
        Simulated rows first, then real ones by pair and method.
    """
    rank = {role: i for i, role in enumerate(role_order)}
    groups: dict[tuple[str, str], list[tuple[float, float, bool]]] = {}
    seen: set[tuple] = set()
    for leg in legs:
        if leg.scenario == REAL:
            if leg.failed or math.isnan(leg.translation_px):
                continue
            roles = sorted(leg.pair.split("-"), key=rank.__getitem__)
            key = ("-".join(roles), leg.method)
            is_translation = leg.estimate.startswith("Translation(")
            groups.setdefault(key, []).append(
                (leg.translation_px, leg.non_translation_px, is_translation)
            )
        elif leg.pair != "B-C":
            truth_key = (leg.site, leg.scenario, leg.window, leg.pair)
            if truth_key in seen:
                continue
            seen.add(truth_key)
            groups.setdefault((leg.scenario, "truth"), []).append(
                (leg.true_translation_px, leg.true_non_translation_px, False)
            )

    def order(key: tuple[str, str]) -> tuple:
        pair, method = key
        if method == "truth":
            return (0, pair, "")
        first, second = pair.split("-")
        return (1, rank[first], rank[second], method)

    rows = []
    for key in sorted(groups, key=order):
        values = np.array([v[:2] for v in groups[key]])
        rows.append(
            MotionRow(
                pair=key[0],
                method=key[1],
                n=len(values),
                translation_px=(
                    float(np.median(values[:, 0])),
                    float(values[:, 0].max()),
                ),
                non_translation_px=(
                    float(np.median(values[:, 1])),
                    float(values[:, 1].max()),
                ),
                translation_only=all(v[2] for v in groups[key]),
            )
        )
    return rows


def motion_markdown(rows: Sequence[MotionRow]) -> str:
    """Render ``motion_summary`` as a markdown table.

    Args:
        rows: Rows of ``motion_summary``.

    Returns:
        The table, ending with a newline.
    """
    header = (
        "| pair | method | registrations | translation (px) | "
        f"non-translation, p{NON_TRANSLATION_PERCENTILE} (px) |\n"
        "|---|---|---:|---:|---:|\n"
    )

    def cell(value: tuple[float, float]) -> str:
        return f"{value[0]:.3f} (max {value[1]:.3f})"

    body = ""
    for r in rows:
        pair = f"simulated {r.pair}" if r.method == "truth" else r.pair
        rest = "translation only" if r.translation_only else cell(r.non_translation_px)
        body += f"| {pair} | {r.method} | {r.n} | {cell(r.translation_px)} | {rest} |\n"
    return header + body

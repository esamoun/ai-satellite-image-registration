"""False changes: what residual misregistration costs change detection.

Change detection here is the plainest detector there is, so that it does not
decide the result. The moving image's level is matched to the reference (a gain
and an offset, from the uncorrected pair), it is resampled onto the reference
grid with a method's displacement, and a pixel has changed where the two images
differ by more than ``K_SIGMA`` times the noise of their difference. Resampling
uses the simulator's interpolation, and "no correction" goes through it too, as
the identity. Level, threshold and interpolation are then the same for every
method, and only the displacement differs.

Where the ground has not changed, every detected change is false. On simulated
pairs that is every pixel. On real pairs it is the stable ground of
``landcover``. See docs/decisions.md.
"""

import dataclasses
import functools
import itertools
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import ndimage, signal

from .appearance import noise_sigma, windows
from .benchmark import BenchmarkConfig, _rng, draw_pair, max_reach, method_device
from .cycle import displacement_summary, lands_inside, register
from .degrade import Preset
from .displacement import Affine, Dense, Displacement, Translation
from .georef import Georef
from .methods import Method
from .metrics import endpoint_error
from .presetcheck import MAX_WINDOW_CLOUD, WINDOW_PX
from .real import Acquisition, pairs
from .simulate import OVERSAMPLING, SimulatedPair, margin_for

# A pixel has changed where the level-matched images differ by more than this
# many standard deviations of the noise of their difference. For Gaussian noise,
# 0.27 % of unchanged pixels exceed it.
K_SIGMA = 3.0

# Pixels of each window edge left out of every count, so a pixel is read from the
# moving image's content and not from its mirrored border.
BORDER_PX = 8

# Cloud opacity from which a simulated moving pixel is left out: clouds change
# the image, not the ground's position, and the detector would see them.
CLEAR_OPACITY = 0.01

# Pixels a real pair's cloud and shadow mask is grown by: the scene
# classification is 20 m, and a cloud's edge is soft.
CLOUD_DILATION_PX = 2

# Residual shifts of the reference curve, in px.
RESIDUALS_PX = tuple(round(0.05 * i, 2) for i in range(21))

# Share of a chip that must be stable ground for its site to enter the tables
# pooled over sites. Below it, stable ground is a few roads and villages among
# fields or forest, which the window's level match, fitted on the fields, does
# not level. See docs/decisions.md.
MIN_STABLE_SHARE = 0.05

# Name of the row that corrects nothing: the identity, resampled like the others.
NONE = "none"

# Scenarios the simulated experiment runs by default: a translation, and the
# affine twin a translation-only method cannot follow.
SCENARIOS = ("translation", "affine")


class Resampler:
    """Reads one image at arbitrary positions, by the simulator's interpolation.

    As ``simulate.oversampled_sample`` does: the image is mirrored, oversampled
    ``factor`` times by Fourier zero-padding, and read by a cubic spline. The
    oversampling and the spline's coefficients are computed once, so an image
    can be read under many displacements at the cost of the reads only. At the
    image's own pixel centres it returns the image itself.

    Attributes:
        shape: ``(rows, cols)`` of the image.
    """

    def __init__(
        self, image: np.ndarray, reach: float, factor: int = OVERSAMPLING
    ) -> None:
        """Set up the reads.

        Args:
            image: 2-D image.
            reach: How far past the image a position may fall, in px, and still
                read its mirror image rather than the oversampled grid's.
            factor: Oversampling factor, at least 1.
        """
        self.shape = image.shape
        self._factor = factor
        self._pad = margin_for(reach)
        fine = np.pad(image.astype(float), self._pad, mode="symmetric")
        for axis in (0, 1):
            fine = signal.resample(fine, fine.shape[axis] * factor, axis=axis)
        self._coefficients = ndimage.spline_filter(fine, order=3, mode="mirror")

    def __call__(self, positions: np.ndarray) -> np.ndarray:
        """Read the image at ``(2, ...)`` positions, rows then columns."""
        return ndimage.map_coordinates(
            self._coefficients,
            self._factor * (positions + self._pad),
            order=3,
            mode="mirror",
            prefilter=False,
        )

    def correct(self, displacement: Displacement) -> np.ndarray:
        """Resample the image onto the reference grid of a displacement.

        Reference pixel ``p`` takes the value at ``p + d(p)``: where the
        displacement says its content went.

        Args:
            displacement: Displacement from the reference to this image.

        Returns:
            The corrected image, on the reference grid.
        """
        grid = np.indices(self.shape, dtype=float)
        return self(grid + displacement.field(self.shape))


def correct(moving: np.ndarray, displacement: Displacement) -> np.ndarray:
    """Resample a moving image onto the reference grid, whatever the displacement.

    Args:
        moving: Moving image.
        displacement: Displacement from the reference to ``moving``, on a grid
            of the same shape.

    Returns:
        The corrected image: ``moving(p + d(p))`` at each reference pixel ``p``.
        Positions off the image read its mirror image.
    """
    field = displacement.field(moving.shape)
    reach = float(np.nanmax(np.abs(field))) if np.isfinite(field).all() else 0.0
    return Resampler(moving, reach).correct(displacement)


def match_level(
    reference: np.ndarray,
    moving: np.ndarray,
    reference_mask: np.ndarray,
    moving_mask: np.ndarray,
) -> tuple[float, float]:
    """The gain and offset that give the moving image the reference's level.

    The mean and the standard deviation of each image are matched. Neither
    depends on how well the images are aligned, so the same gain and offset
    serve every method's correction, and "no correction".

    Args:
        reference: Reference image.
        moving: Moving image.
        reference_mask: Reference pixels the moments are taken over.
        moving_mask: Moving pixels the moments are taken over.

    Returns:
        ``(gain, offset)``: ``gain * moving + offset`` has the reference's mean
        and standard deviation over the masks.
    """
    ref, mov = reference[reference_mask], moving[moving_mask]
    spread = float(mov.std())
    gain = float(ref.std()) / spread if spread > 0 else 1.0
    return gain, float(ref.mean()) - gain * float(mov.mean())


def threshold(reference: np.ndarray, moving: np.ndarray, k: float = K_SIGMA) -> float:
    """The difference above which a pixel has changed.

    Args:
        reference: Reference image.
        moving: Moving image, level-matched.
        k: Standard deviations of the noise of the difference.

    Returns:
        ``k * sqrt(sigma_ref^2 + sigma_mov^2)``, with each image's noise by
        Immerkær's estimator. It reads fine texture as noise too, so on a sharp
        image it is an upper bound.
    """
    return k * math.hypot(noise_sigma(reference), noise_sigma(moving))


def changed(reference: np.ndarray, corrected: np.ndarray, limit: float) -> np.ndarray:
    """Pixels the detector flags: where the two images differ by more than ``limit``.

    Args:
        reference: Reference image.
        corrected: Moving image, level-matched and on the reference grid.
        limit: Threshold on the absolute difference.

    Returns:
        Boolean array, same shape.
    """
    return np.abs(corrected - reference) > limit


def false_change_rate(
    reference: np.ndarray, corrected: np.ndarray, mask: np.ndarray, limit: float
) -> float:
    """Share of unchanged pixels the detector flags as changed.

    Args:
        reference: Reference image.
        corrected: Moving image, level-matched and on the reference grid.
        mask: Pixels whose ground did not change.
        limit: Threshold on the absolute difference.

    Returns:
        The share, NaN if ``mask`` keeps no pixel.
    """
    if not mask.any():
        return math.nan
    return float(changed(reference, corrected, limit)[mask].mean())


def interior(shape: tuple[int, int], border: int = BORDER_PX) -> np.ndarray:
    """Pixels at least ``border`` px from every edge."""
    mask = np.zeros(shape, bool)
    mask[border:-border, border:-border] = True
    return mask


def shifted(displacement: Displacement, dy: float, dx: float) -> Displacement:
    """A displacement plus a constant shift, of the same model.

    Args:
        displacement: Any displacement.
        dy: Shift added along rows, in px.
        dx: Shift added along columns, in px.

    Returns:
        ``displacement(p) + (dy, dx)`` at every pixel.
    """
    if isinstance(displacement, Translation):
        return Translation(dx=displacement.dx + dx, dy=displacement.dy + dy)
    if isinstance(displacement, Affine):
        ty, tx = displacement.offset
        return dataclasses.replace(displacement, offset=(ty + dy, tx + dx))
    if isinstance(displacement, Dense):
        return Dense(displacement.values + np.reshape((dy, dx), (2, 1, 1)))
    raise TypeError(f"unknown displacement {type(displacement).__name__}")


@dataclass(frozen=True)
class CurveRow:
    """False changes of one simulated pair corrected with its truth plus a shift.

    Attributes:
        site: Site name.
        degradation: Preset applied to the pair.
        pair: Index of the pair within its site.
        residual_px: Size of the shift added to the truth, in px.
        direction_deg: Its direction, counter-clockwise from the columns' axis
            as displayed.
        false_change: Share of the pair's clear pixels flagged as changed.
        n_pixels: Clear pixels counted.
        threshold: Threshold on the absolute difference, in the image's units.
    """

    site: str
    degradation: str
    pair: int
    residual_px: float
    direction_deg: float
    false_change: float
    n_pixels: int
    threshold: float


@dataclass(frozen=True)
class SimulatedRow:
    """False changes of one simulated pair corrected with one method's estimate.

    Attributes:
        site: Site name.
        scenario: Geometric model of the pair.
        degradation: Preset applied to the pair.
        method: Method name, or ``NONE``.
        device: Device the method ran on, empty for ``NONE``.
        pair: Index of the pair within its site.
        estimate: The displacement, as text; empty if the method raised.
        residual_px: Mean end-point error of the estimate over the clear
            pixels, in px: the misregistration the correction leaves.
        false_change: Share of clear pixels flagged as changed, NaN if the
            method raised.
        n_pixels: Clear pixels counted.
        threshold: Threshold on the absolute difference.
        failed: Whether the method raised, or left more than the failure
            threshold of residual.
        error: Why the method gave up or crashed, empty otherwise.
        time_ms: Median wall-clock time of the method call, in milliseconds.
    """

    site: str
    scenario: str
    degradation: str
    method: str
    device: str
    pair: int
    estimate: str
    residual_px: float
    false_change: float
    n_pixels: int
    threshold: float
    failed: bool
    error: str
    time_ms: float = dataclasses.field(compare=False)


@dataclass(frozen=True)
class RealRow:
    """Changes detected on one real window after one method's correction.

    Attributes:
        site: Site name.
        pair: ``"<role>-<role>"``, reference first.
        gap_days: Days between the two dates.
        window: Index of the window in the chip.
        method: Method name, or ``NONE``.
        device: Device the method ran on, empty for ``NONE``.
        estimate: The displacement, as text; empty if the method raised.
        translation_px: Size of the displacement's translation part, in px.
        non_translation_px: Size of the rest, as ``cycle.displacement_summary``.
        stable_px: Stable, clear pixels counted.
        stable_changed_px: Those flagged as changed: false changes.
        other_px: Clear pixels that are not stable ground.
        other_changed_px: Those flagged as changed, true or false.
        threshold: Threshold on the absolute difference, in digital numbers.
        gain: Gain of the level match.
        offset: Offset of the level match.
        failed: Whether the method raised or returned a non-finite field.
        error: Why, empty otherwise.
        time_ms: Median wall-clock time of the method call, in milliseconds.
    """

    site: str
    pair: str
    gap_days: int
    window: int
    method: str
    device: str
    estimate: str
    translation_px: float
    non_translation_px: float
    stable_px: int
    stable_changed_px: int
    other_px: int
    other_changed_px: int
    threshold: float
    gain: float
    offset: float
    failed: bool
    error: str
    time_ms: float = dataclasses.field(compare=False)


def _clear_of_cloud(pair: SimulatedPair) -> tuple[np.ndarray, np.ndarray]:
    """Reference and moving pixels no cloud touches, the reference by its truth."""
    shape = pair.reference.shape
    if pair.cloud is None:
        return np.ones(shape, bool), np.ones(shape, bool)
    target = np.indices(shape, dtype=float) + pair.truth.field(shape)
    seen = ndimage.map_coordinates(pair.cloud, target, order=1, mode="nearest")
    return seen < CLEAR_OPACITY, pair.cloud < CLEAR_OPACITY


def _finite(displacement: Displacement, shape: tuple[int, int]) -> bool:
    return bool(np.isfinite(displacement.field(shape)).all())


def _rate(
    reference: np.ndarray,
    resampler: Resampler,
    mask: np.ndarray,
    limit: float,
    displacement: Displacement,
) -> float:
    """False-change rate of one correction of a simulated pair.

    Pixels the displacement reads from off the image are left out, as in
    ``SimulatedPair.valid``.
    """
    ok = mask & lands_inside(displacement, reference.shape)
    corrected = resampler.correct(displacement)
    return false_change_rate(reference, corrected, ok, limit)


def run_simulated(
    site: str,
    image: np.ndarray,
    methods: Mapping[str, Method],
    config: BenchmarkConfig,
    degradations: Mapping[str, Preset],
    georef: Georef | None = None,
    residuals: Sequence[float] = RESIDUALS_PX,
    warmed: set[str] | None = None,
) -> tuple[list[CurveRow], list[SimulatedRow]]:
    """Count false changes on simulated pairs, for known residuals and methods.

    Each pair is drawn as the benchmark draws it, degraded, level-matched, and
    corrected two ways. Its truth plus a shift of each size in ``residuals``, in
    one random direction per pair, gives the reference curve: false changes
    against a residual that is known exactly. It is drawn on translation pairs
    only, where the residual is the shift itself. Each method's estimate, and
    the identity, give its own residual and false changes, which place it on
    that curve.

    Args:
        site: Site name.
        image: 2-D site image to cut windows from.
        methods: Method name to method.
        config: Run parameters: pairs per site, size, ranges, scenarios, seed,
            failure threshold, warm-up and repeats.
        degradations: Preset name to preset.
        georef: Map grid of the site image, if it has one.
        residuals: Sizes of the shifts of the reference curve, in px.
        warmed: Methods already warmed up, updated in place.

    Returns:
        The curve rows, and one row per pair, scenario, preset and method.
    """
    warmed = set() if warmed is None else warmed
    shape = (config.size, config.size)
    reach = max_reach(config) + max(residuals, default=0.0)
    curve, rows = [], []
    for index, scenario, (condition, degrade) in itertools.product(
        range(config.n_pairs), config.scenarios, degradations.items()
    ):
        clean = draw_pair(
            image,
            config,
            _rng(config.seed, site, "false-change", index),
            scenario,
            georef,
        )
        pair = degrade(clean, _rng(config.seed, site, "false-change", index, condition))
        reference_clear, moving_clear = _clear_of_cloud(pair)
        mask = pair.valid & interior(shape) & reference_clear
        gain, offset = match_level(
            pair.reference, pair.moving, mask, interior(shape) & moving_clear
        )
        moving = gain * pair.moving + offset
        limit = threshold(pair.reference, moving)
        resampler = Resampler(moving, reach)
        n_pixels = int(mask.sum())

        rate = functools.partial(_rate, pair.reference, resampler, mask, limit)

        if scenario == "translation":
            angle = _rng(config.seed, site, "false-change", index, "direction").uniform(
                0, 2 * math.pi
            )
            for residual in residuals:
                # Counter-clockwise as displayed: rows point down.
                dy, dx = -residual * math.sin(angle), residual * math.cos(angle)
                curve.append(
                    CurveRow(
                        site=site,
                        degradation=condition,
                        pair=index,
                        residual_px=residual,
                        direction_deg=math.degrees(angle),
                        false_change=rate(shifted(pair.truth, dy, dx)),
                        n_pixels=n_pixels,
                        threshold=limit,
                    )
                )

        labels = {
            "site": site,
            "scenario": scenario,
            "degradation": condition,
            "pair": index,
            "n_pixels": n_pixels,
            "threshold": limit,
        }
        identity = Translation(0.0, 0.0)
        rows.append(
            SimulatedRow(
                **labels,
                method=NONE,
                device="",
                estimate=repr(identity),
                residual_px=float(
                    endpoint_error(pair.truth, identity, shape, mask).mean()
                ),
                false_change=rate(identity),
                failed=False,
                error="",
                time_ms=0.0,
            )
        )
        for name, method in methods.items():
            warmup = 0 if name in warmed else config.warmup
            warmed.add(name)
            leg = register(
                method, pair.reference, pair.moving, pair.georef, config.repeats, warmup
            )
            estimate = leg.displacement
            if estimate is None or not _finite(estimate, shape):
                residual, false_change = math.nan, math.nan
                error = leg.error or "non-finite displacement"
            else:
                residual = float(
                    endpoint_error(pair.truth, estimate, shape, mask).mean()
                )
                false_change, error = rate(estimate), ""
            rows.append(
                SimulatedRow(
                    **labels,
                    method=name,
                    device=method_device(method),
                    estimate="" if estimate is None else repr(estimate),
                    residual_px=residual,
                    false_change=false_change,
                    failed=bool(error) or not residual <= config.failure_threshold,
                    error=error,
                    time_ms=leg.time_ms,
                )
            )
    return curve, rows


def run_real(
    site: str,
    series: Sequence[Acquisition],
    stable: np.ndarray,
    methods: Mapping[str, Method],
    config: BenchmarkConfig,
    warmed: set[str] | None = None,
) -> list[RealRow]:
    """Count the changes each method's correction leaves on a site's real pairs.

    Every pair of dates is cut into the 256 px windows ``cycle`` registers, and a
    window is kept if at most ``MAX_WINDOW_CLOUD`` of it is hidden on either
    date. Its hidden pixels, grown by ``CLOUD_DILATION_PX``, and its border are
    left out. The level match and the threshold are taken once per window, on
    the uncorrected pair, and serve every method.

    Args:
        site: Site name.
        series: The site's acquisitions, on one grid.
        stable: Stable ground on the chip grid, from ``landcover``.
        methods: Method name to method.
        config: Run parameters: warm-up and repeats.
        warmed: Methods already warmed up, updated in place.

    Returns:
        One row per pair, window and method, ``NONE`` first.
    """
    warmed = set() if warmed is None else warmed
    shape = (WINDOW_PX, WINDOW_PX)
    rows = []
    for pair in pairs(list(series)):
        for index, (window_rows, window_cols) in enumerate(
            windows(WINDOW_PX, pair.reference.shape)
        ):
            hidden = pair.cloud[window_rows, window_cols]
            if hidden.mean() > MAX_WINDOW_CLOUD:
                continue
            reference = pair.reference[window_rows, window_cols].astype(float)
            raw = pair.moving[window_rows, window_cols].astype(float)
            clear = interior(shape) & ~ndimage.binary_dilation(
                hidden, iterations=CLOUD_DILATION_PX
            )
            on_stable = clear & stable[window_rows, window_cols]
            gain, offset = match_level(reference, raw, clear, clear)
            moving = gain * raw + offset
            limit = threshold(reference, moving)
            resampler = Resampler(moving, BORDER_PX)
            georef = pair.georef.window(window_rows.start, window_cols.start)
            labels = {
                "site": site,
                "pair": f"{pair.roles[0]}-{pair.roles[1]}",
                "gap_days": pair.gap_days,
                "window": index,
                "threshold": limit,
                "gain": gain,
                "offset": offset,
            }
            candidates: list[tuple[str, Method | None]] = [(NONE, None)]
            candidates += list(methods.items())
            for name, method in candidates:
                if method is None:
                    estimate, error, time_ms = Translation(0.0, 0.0), "", 0.0
                else:
                    warmup = 0 if name in warmed else config.warmup
                    warmed.add(name)
                    leg = register(
                        method, reference, raw, georef, config.repeats, warmup
                    )
                    estimate, error, time_ms = leg.displacement, leg.error, leg.time_ms
                    if estimate is not None and not _finite(estimate, shape):
                        error = "non-finite displacement"
                if estimate is None or error:
                    counts = dict.fromkeys(
                        (
                            "stable_px",
                            "stable_changed_px",
                            "other_px",
                            "other_changed_px",
                        ),
                        0,
                    )
                    sizes = (math.nan, math.nan)
                else:
                    flagged = changed(reference, resampler.correct(estimate), limit)
                    inside = lands_inside(estimate, shape)
                    stable_here = on_stable & inside
                    other_here = clear & ~on_stable & inside
                    counts = {
                        "stable_px": int(stable_here.sum()),
                        "stable_changed_px": int((flagged & stable_here).sum()),
                        "other_px": int(other_here.sum()),
                        "other_changed_px": int((flagged & other_here).sum()),
                    }
                    sizes = displacement_summary(estimate, shape)
                rows.append(
                    RealRow(
                        **labels,
                        method=name,
                        device="" if method is None else method_device(method),
                        estimate="" if estimate is None else repr(estimate),
                        translation_px=sizes[0],
                        non_translation_px=sizes[1],
                        **counts,
                        failed=bool(error),
                        error=error,
                        time_ms=time_ms,
                    )
                )
    return rows


@dataclass(frozen=True)
class CurvePoint:
    """The reference curve at one residual, over a site's pairs.

    Attributes:
        site: Site name.
        degradation: Preset applied to the pairs.
        residual_px: Shift added to the truth, in px.
        n_pairs: Pairs averaged.
        mean: Mean false-change rate.
        p10: Its 10th percentile over pairs.
        p90: Its 90th percentile over pairs.
    """

    site: str
    degradation: str
    residual_px: float
    n_pairs: int
    mean: float
    p10: float
    p90: float


def curve_summary(rows: Sequence[CurveRow]) -> list[CurvePoint]:
    """Average the reference curve over pairs, per site, preset and residual.

    Args:
        rows: Curve rows, in any order.

    Returns:
        One point per group, in order of first appearance.
    """
    groups: dict[tuple[str, str, float], list[float]] = {}
    for r in rows:
        key = (r.site, r.degradation, r.residual_px)
        groups.setdefault(key, []).append(r.false_change)
    return [
        CurvePoint(
            site=site,
            degradation=degradation,
            residual_px=residual,
            n_pairs=len(values),
            mean=float(np.nanmean(values)),
            p10=float(np.nanpercentile(values, 10)),
            p90=float(np.nanpercentile(values, 90)),
        )
        for (site, degradation, residual), values in groups.items()
    ]


def on_curve(
    points: Sequence[CurvePoint], site: str, degradation: str, residual: float
) -> float:
    """What the reference curve predicts at a residual, by linear interpolation.

    Args:
        points: Curve points.
        site: Site name.
        degradation: Preset.
        residual: Residual in px.

    Returns:
        The mean false-change rate the curve gives there, NaN past its end or if
        it has no point for the site and preset.
    """
    kept = sorted(
        (p.residual_px, p.mean)
        for p in points
        if p.site == site and p.degradation == degradation
    )
    if not kept or math.isnan(residual) or residual > kept[-1][0]:
        return math.nan
    x, y = zip(*kept, strict=True)
    return float(np.interp(residual, x, y))


@dataclass(frozen=True)
class SimulatedSummary:
    """One method's false changes on one site's simulated pairs.

    Attributes:
        site: Site name.
        scenario: Geometric model of the pairs.
        degradation: Preset.
        method: Method name, or ``NONE``.
        n_pairs: Pairs attempted.
        failure_rate: Share of pairs that failed.
        residual_px: Mean residual over non-failed pairs, in px.
        false_change: Mean false-change rate over non-failed pairs.
        curve_at_residual: What the reference curve gives at that residual.
        at_zero: What it gives at zero residual: the floor that blur, noise and
            radiometry leave with a perfect registration.
    """

    site: str
    scenario: str
    degradation: str
    method: str
    n_pairs: int
    failure_rate: float
    residual_px: float
    false_change: float
    curve_at_residual: float
    at_zero: float


def _mean(values: Sequence[float]) -> float:
    return float(np.mean(values)) if values else math.nan


def simulated_summary(
    rows: Sequence[SimulatedRow], points: Sequence[CurvePoint]
) -> list[SimulatedSummary]:
    """Group simulated rows by site, scenario, preset and method.

    Args:
        rows: Simulated rows, in any order.
        points: The reference curve, for the prediction at each residual.

    Returns:
        One row per group, in order of first appearance.
    """
    groups: dict[tuple[str, str, str, str], list[SimulatedRow]] = {}
    for r in rows:
        groups.setdefault((r.site, r.scenario, r.degradation, r.method), []).append(r)
    out = []
    for (site, scenario, degradation, method), group in groups.items():
        # "No correction" is never a failure: it is the baseline.
        kept = [r for r in group if method == NONE or not r.failed]
        residual = _mean([r.residual_px for r in kept])
        out.append(
            SimulatedSummary(
                site=site,
                scenario=scenario,
                degradation=degradation,
                method=method,
                n_pairs=len(group),
                failure_rate=(len(group) - len(kept)) / len(group),
                residual_px=residual,
                false_change=_mean([r.false_change for r in kept]),
                curve_at_residual=on_curve(points, site, degradation, residual),
                at_zero=on_curve(points, site, degradation, 0.0),
            )
        )
    return out


@dataclass(frozen=True)
class RealSummary:
    """Changes one method's correction leaves on real pairs, pooled over windows.

    Attributes:
        site: Site name, or ``"all"``.
        pair: Role pair, or ``"all"``.
        method: Method name, or ``NONE``.
        n_windows: Windows registered.
        failures: Windows the method failed on, left out of the counts.
        stable_px: Stable, clear pixels counted.
        stable_changed: Share of them flagged as changed: the false-change rate.
        other_changed: Share of the other clear pixels flagged, true changes
            and false ones together.
    """

    site: str
    pair: str
    method: str
    n_windows: int
    failures: int
    stable_px: int
    stable_changed: float
    other_changed: float


def _share(part: int, whole: int) -> float:
    return part / whole if whole else math.nan


def real_summary(
    rows: Sequence[RealRow], by: str, role_order: Sequence[str] = ()
) -> list[RealSummary]:
    """Pool real rows by site or by pair, and method.

    Counts are summed before they are divided, so a window with more stable
    ground weighs more. A pair is named by its roles in series order, whichever
    date is the reference, so a site whose "days" date comes before its anchor
    pools with the others.

    Args:
        rows: Real rows, in any order.
        by: ``"site"`` or ``"pair"``: the grouping; the other is ``"all"``.
        role_order: Roles in series order, to name and order pairs.

    Returns:
        One row per group, sites in order of first appearance, pairs in series
        order.
    """
    rank = {role: i for i, role in enumerate(role_order)}

    def key(r: RealRow) -> str:
        if by == "site":
            return r.site
        roles = sorted(r.pair.split("-"), key=lambda role: rank.get(role, len(rank)))
        return "-".join(roles)

    groups: dict[tuple[str, str], list[RealRow]] = {}
    for r in rows:
        groups.setdefault((key(r), r.method), []).append(r)
    if by == "pair":
        pair_rank = {
            name: tuple(rank.get(role, len(rank)) for role in name.split("-"))
            for name, _ in groups
        }
        groups = dict(sorted(groups.items(), key=lambda item: pair_rank[item[0][0]]))
    out = []
    for (name, method), group in groups.items():
        kept = [r for r in group if not r.failed]
        stable = sum(r.stable_px for r in kept)
        other = sum(r.other_px for r in kept)
        out.append(
            RealSummary(
                site=name if by == "site" else "all",
                pair=name if by == "pair" else "all",
                method=method,
                n_windows=len(group),
                failures=len(group) - len(kept),
                stable_px=stable,
                stable_changed=_share(sum(r.stable_changed_px for r in kept), stable),
                other_changed=_share(sum(r.other_changed_px for r in kept), other),
            )
        )
    return out


def _percent(x: float, digits: int = 2) -> str:
    return "n/a" if math.isnan(x) else f"{100 * x:.{digits}f} %"


def _pixels(x: float) -> str:
    return "n/a" if math.isnan(x) else f"{x:.3f}"


def simulated_markdown(rows: Sequence[SimulatedSummary]) -> str:
    """Render the simulated summary as a markdown table.

    Args:
        rows: Simulated summary rows.

    Returns:
        The table, ending with a newline.
    """
    return (
        "| site | scenario | degradation | method | pairs | residual (px) "
        "| false change | curve at residual | curve at 0 | failures |\n"
        + "|---" * 4
        + "|---:" * 6
        + "|\n"
        + "".join(
            f"| {r.site} | {r.scenario} | {r.degradation} | {r.method} "
            f"| {r.n_pairs} | {_pixels(r.residual_px)} "
            f"| {_percent(r.false_change)} | {_percent(r.curve_at_residual)} "
            f"| {_percent(r.at_zero)} | {_percent(r.failure_rate, 0)} |\n"
            for r in rows
        )
    )


def real_markdown(rows: Sequence[RealSummary]) -> str:
    """Render a real summary as a markdown table.

    Args:
        rows: Real summary rows, grouped by site or by pair.

    Returns:
        The table, ending with a newline.
    """
    by = "pair" if rows and rows[0].site == "all" else "site"
    return (
        f"| {by} | method | windows | failures | stable px "
        "| false change (stable) | changed (other ground) |\n"
        + "|---" * 2
        + "|---:" * 5
        + "|\n"
        + "".join(
            f"| {getattr(r, by)} | {r.method} | {r.n_windows} | {r.failures} "
            f"| {r.stable_px} | {_percent(r.stable_changed)} "
            f"| {_percent(r.other_changed)} |\n"
            for r in rows
        )
    )


# Largest residual the figure shows, in px: a method past it has failed.
FIGURE_MAX_RESIDUAL_PX = 1.2

# Marker of each scenario's method points.
MARKERS = {"translation": "o", "affine": "^"}


def plot(
    points: Sequence[CurvePoint], summary: Sequence[SimulatedSummary], path: Path
) -> None:
    """Draw the reference curve and each method's point on it, per preset and site.

    Args:
        points: Reference curve.
        summary: Simulated summary; ``NONE`` rows are left out, as their
            residual is the whole displacement.
        path: Output PNG.
    """
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    sites = list(dict.fromkeys(p.site for p in points))
    presets = list(dict.fromkeys(p.degradation for p in points))
    methods = list(dict.fromkeys(r.method for r in summary if r.method != NONE))
    colours = dict(zip(methods, plt.get_cmap("tab10").colors, strict=False))
    fig, axes = plt.subplots(
        len(presets),
        len(sites),
        figsize=(3.2 * len(sites), 2.8 * len(presets)),
        sharex=True,
        squeeze=False,
    )
    for (i, preset), (j, site) in itertools.product(
        enumerate(presets), enumerate(sites)
    ):
        ax = axes[i][j]
        curve = sorted(
            (p for p in points if p.site == site and p.degradation == preset),
            key=lambda p: p.residual_px,
        )
        x = [p.residual_px for p in curve]
        ax.fill_between(
            x,
            [100 * p.p10 for p in curve],
            [100 * p.p90 for p in curve],
            color="0.85",
            label="shifted truth, p10-p90",
        )
        ax.plot(x, [100 * p.mean for p in curve], color="0.3", label="shifted truth")
        for r in summary:
            if (r.site, r.degradation) != (site, preset) or r.method == NONE:
                continue
            if not r.residual_px <= FIGURE_MAX_RESIDUAL_PX:
                continue
            ax.plot(
                r.residual_px,
                100 * r.false_change,
                MARKERS.get(r.scenario, "s"),
                color=colours[r.method],
                markeredgecolor="black",
                markeredgewidth=0.5,
                label=f"{r.method} ({r.scenario})",
            )
        ax.set_xlim(0, FIGURE_MAX_RESIDUAL_PX)
        ax.set_ylim(bottom=0)
        ax.grid(alpha=0.3)
        if i == 0:
            ax.set_title(site)
        if j == 0:
            ax.set_ylabel(f"{preset}\nfalse change (%)")
        if i == len(presets) - 1:
            ax.set_xlabel("residual misregistration (px)")
    handles, labels = axes[0][0].get_legend_handles_labels()
    unique = dict(zip(labels, handles, strict=True))
    for ax in axes.flat:
        h, lab = ax.get_legend_handles_labels()
        unique.update(zip(lab, h, strict=True))
    fig.legend(
        unique.values(),
        unique.keys(),
        loc="lower center",
        ncol=4,
        fontsize="small",
        frameon=False,
    )
    fig.tight_layout(rect=(0, 0.04 + 0.025 * math.ceil(len(unique) / 4), 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)

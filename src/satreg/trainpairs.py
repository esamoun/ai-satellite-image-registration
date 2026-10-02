"""Training pairs (N3): simulated pairs under randomly drawn degradations.

A training pair is cut from a training chip by the benchmark's own simulator
(``benchmark.draw_pair``) and degraded by the benchmark's own degradations
(``degrade.Preset``). What differs from a test pair is how the degradation is
chosen: its parameters are drawn in continuous ranges instead of taken from one
of three presets, and clouds may also fall on the reference image.

A pair is same-date, both images from one date of the chip and an exact truth,
or cross-date, the reference from one date and the moving image from another,
whose truth carries the residual misregistration between the two dates.

Pair ``i`` of a generator depends on the seed, on ``i`` and on the configuration
only, not on which pairs were asked for before it. See docs/decisions.md.
"""

import dataclasses
import math
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import numpy as np

from .benchmark import SCENARIOS, BenchmarkConfig, _rng, draw_pair, in_units_of
from .degrade import Blur, Clouds, Noise, Preset, Radiometry
from .displacement import Translation
from .ingest import stac_scenes
from .methods import raft
from .real import Acquisition, Candidates, SeriesConfig, load_series
from .simulate import OPAQUE_CLOUD, SimulatedPair
from .trainchips import TRAIN, TrainingConfig

SAME_DATE, CROSS_DATE = "same-date", "cross-date"

# Motion ranges of the benchmark simulator, which training pairs take unless
# their configuration sets its own.
_BENCHMARK = BenchmarkConfig()

Range = tuple[float, float]


def _range(name: str, value: object, lowest: float | None = None) -> Range:
    """Check a ``[low, high]`` range read from a configuration file."""
    try:
        low, high = (float(bound) for bound in value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be [low, high], got {value!r}") from None
    if low > high or (lowest is not None and low < lowest):
        at_least = "" if lowest is None else f" and low >= {lowest:g}"
        raise ValueError(f"{name} needs low <= high{at_least}, got {value!r}")
    return low, high


def _probability(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{name} must be a number in [0, 1], got {value!r}")
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be in [0, 1], got {value!r}")
    return float(value)


@dataclass(frozen=True)
class DrawnDegradation:
    """The degradation of one training pair: one value per parameter.

    Attributes:
        gain: Contrast gain of the moving image.
        offset: Level shift of the moving image, in reference standard
            deviations.
        gamma: Exponent of the moving image's tone curve.
        cover: Cloud cover of the moving image, 0 if it has no clouds.
        sigma: Blur of the moving image, in pixels.
        snr_db: Signal-to-noise ratio of both images, in decibels.
        reference_cover: Cloud cover of the reference image, 0 if it has no
            clouds.
    """

    gain: float
    offset: float
    gamma: float
    cover: float
    sigma: float
    snr_db: float
    reference_cover: float

    @property
    def preset(self) -> Preset:
        """The benchmark degradation with these parameters.

        It covers everything but the clouds of the reference image, which no
        benchmark preset has.
        """
        return Preset(
            radiometry=Radiometry(self.gain, self.offset, self.gamma),
            clouds=Clouds(self.cover),
            blur=Blur(self.sigma),
            noise=Noise(self.snr_db),
        )


@dataclass(frozen=True)
class DegradationRanges:
    """Ranges the degradation of a training pair is drawn in.

    Each parameter is drawn on its own. Gain and gamma multiply, so they are
    drawn uniformly on a log scale: a gain of 0.5 is as likely as a gain of 2.
    The others are drawn uniformly.

    Attributes:
        gain: Range of the contrast gain, positive.
        offset: Range of the level shift, in reference standard deviations.
        gamma: Range of the tone-curve exponent, positive.
        cover: Range of the cloud cover of an image that has clouds, in [0, 1].
        sigma: Range of the blur, in pixels, non-negative.
        snr_db: Range of the signal-to-noise ratio, in decibels.
        cloudy_moving: Probability that the moving image has clouds.
        cloudy_reference: Probability that the reference image has clouds,
            drawn independently.
    """

    gain: Range
    offset: Range
    gamma: Range
    cover: Range
    sigma: Range
    snr_db: Range
    cloudy_moving: float
    cloudy_reference: float

    def __post_init__(self) -> None:
        _range("gain", self.gain, lowest=0)
        _range("gamma", self.gamma, lowest=0)
        if min(self.gain[0], self.gamma[0]) == 0:
            raise ValueError("gain and gamma must be positive")
        _range("offset", self.offset)
        _range("sigma", self.sigma, lowest=0)
        _range("snr_db", self.snr_db)
        _range("cover", self.cover, lowest=0)
        if self.cover[1] > 1:
            raise ValueError(f"cover must stay in [0, 1], got {self.cover}")
        _probability("cloudy_moving", self.cloudy_moving)
        _probability("cloudy_reference", self.cloudy_reference)

    def draw(self, rng: np.random.Generator) -> DrawnDegradation:
        """Draw the degradation of one pair.

        Every value is drawn whether it is used or not, so the generator ends in
        the same state whatever the pair gets.

        Args:
            rng: Generator for the parameters.

        Returns:
            The drawn parameters.
        """

        def uniform(bounds: Range) -> float:
            return float(rng.uniform(*bounds))

        def log_uniform(bounds: Range) -> float:
            # Exact at both ends: a range of one value gives that value.
            low, high = bounds
            return float(low * (high / low) ** rng.uniform())

        gain, offset, gamma = (
            log_uniform(self.gain),
            uniform(self.offset),
            log_uniform(self.gamma),
        )
        cloudy_moving, cover = rng.uniform() < self.cloudy_moving, uniform(self.cover)
        sigma, snr_db = uniform(self.sigma), uniform(self.snr_db)
        cloudy_reference = rng.uniform() < self.cloudy_reference
        reference_cover = uniform(self.cover)
        return DrawnDegradation(
            gain=gain,
            offset=offset,
            gamma=gamma,
            cover=cover if cloudy_moving else 0.0,
            sigma=sigma,
            snr_db=snr_db,
            reference_cover=reference_cover if cloudy_reference else 0.0,
        )


def load_ranges(path: Path) -> DegradationRanges:
    """Read the training ranges, declared next to the test presets.

    Args:
        path: TOML file with a ``[training]`` table: ``[training.radiometry]``
            (``gain``, ``offset``, ``gamma``), ``[training.clouds]`` (``cover``,
            ``moving``, ``reference``), ``[training.blur]`` (``sigma``) and
            ``[training.noise]`` (``snr_db``). Ranges are ``[low, high]``;
            ``moving`` and ``reference`` are probabilities.

    Returns:
        The ranges.

    Raises:
        ValueError: If the table is missing, or a key is missing, unknown or
            invalid.
    """
    with path.open("rb") as f:
        raw = tomllib.load(f)
    if "training" not in raw:
        raise ValueError(f"{path} needs a [training] table")
    keys = {
        "radiometry": {"gain": "gain", "offset": "offset", "gamma": "gamma"},
        "clouds": {
            "cover": "cover",
            "moving": "cloudy_moving",
            "reference": "cloudy_reference",
        },
        "blur": {"sigma": "sigma"},
        "noise": {"snr_db": "snr_db"},
    }
    training = raw["training"]
    if unknown := sorted(set(training) - set(keys)):
        raise ValueError(f"{path}: [training]: unknown degradation {unknown[0]!r}")
    fields = {}
    for step, names in keys.items():
        table = training.get(step, {})
        if unknown := sorted(set(table) - set(names)):
            raise ValueError(f"{path}: [training.{step}]: unknown key {unknown[0]!r}")
        for key, name in names.items():
            if key not in table:
                raise ValueError(f"{path}: [training.{step}] needs {key}")
            value = table[key]
            fields[name] = tuple(value) if isinstance(value, list) else value
    try:
        return DegradationRanges(**fields)
    except ValueError as exc:
        raise ValueError(f"{path}: [training]: {exc}") from exc


@dataclass(frozen=True)
class PairsConfig:
    """What training pairs are made of, besides their degradation.

    Attributes:
        size: Side of each image, in pixels: one the network takes without
            padding, so the flow and the mask stay on the grid of its input.
        scenarios: Geometric models pairs are drawn among, each as likely.
        cross_date: Share of cross-date pairs, in [0, 1]; the others are
            same-date.
        seed: Seed of the pairs.
        max_shift: As in ``BenchmarkConfig``, like the other motion ranges.
        max_rotation_deg: Largest rotation of an affine pair, in degrees.
        max_scale_change: Largest scale change of an affine pair.
        max_shear: Largest shear of an affine pair.
        max_local_shift: Largest peak of a dense pair's local field, in pixels.
        local_length: Correlation length of that field, in pixels.
    """

    size: int = _BENCHMARK.size
    scenarios: tuple[str, ...] = SCENARIOS
    cross_date: float = 0.0
    seed: int = 0
    max_shift: float = _BENCHMARK.max_shift
    max_rotation_deg: float = _BENCHMARK.max_rotation_deg
    max_scale_change: float = _BENCHMARK.max_scale_change
    max_shear: float = _BENCHMARK.max_shear
    max_local_shift: float = _BENCHMARK.max_local_shift
    local_length: float = _BENCHMARK.local_length

    def __post_init__(self) -> None:
        _probability("cross_date", self.cross_date)
        if self.size < raft.MIN_SIDE or self.size % raft.SIDE_MULTIPLE:
            raise ValueError(
                f"size must be a multiple of {raft.SIDE_MULTIPLE} and at least "
                f"{raft.MIN_SIDE}, got {self.size}"
            )
        # Checks the scenarios and the motion ranges.
        _ = self.simulation

    @property
    def simulation(self) -> BenchmarkConfig:
        """The benchmark simulator's parameters for these pairs."""
        motion = dataclasses.asdict(self)
        del motion["cross_date"]
        return BenchmarkConfig(**motion)


def load_pairs_config(path: Path) -> PairsConfig:
    """Read what training pairs are made of.

    Args:
        path: TOML file with a ``[pairs]`` table whose keys are the attributes
            of ``PairsConfig``; a key left out takes its default.

    Returns:
        The configuration.

    Raises:
        ValueError: If the table is missing or has unknown or invalid keys.
    """
    with path.open("rb") as f:
        raw = tomllib.load(f)
    if "pairs" not in raw:
        raise ValueError(f"{path} needs a [pairs] table")
    table = dict(raw["pairs"])
    known = [f.name for f in dataclasses.fields(PairsConfig)]
    if unknown := sorted(set(table) - set(known)):
        raise ValueError(
            f"{path}: [pairs]: unknown key {unknown[0]!r} (keys: {', '.join(known)})"
        )
    if "scenarios" in table:
        table["scenarios"] = tuple(table["scenarios"])
    try:
        return PairsConfig(**table)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{path}: [pairs]: {exc}") from exc


def loss_mask(
    pair: SimulatedPair,
    reference_cloud: np.ndarray | None = None,
    hidden: np.ndarray | None = None,
) -> np.ndarray:
    """Reference pixels a training loss may use.

    A pixel is left out if its content falls out of the moving image after the
    displacement, if it lands under opaque cloud there, if it is itself under
    opaque cloud on the reference image, or if it is ``hidden``. Unlike the
    benchmark's valid pixels, cloud is left out whatever the truth: under an
    opaque cloud there is nothing to match, and a loss there would teach the
    network to guess.

    Args:
        pair: The pair, with the opacity of the clouds of its moving image.
        reference_cloud: Opacity of the clouds laid over the reference image,
            in [0, 1], or ``None``.
        hidden: Reference pixels to leave out for another reason, or ``None``.

    Returns:
        Boolean array, the shape of the reference image.
    """
    mask = pair.in_frame & ~pair.under_cloud
    if reference_cloud is not None:
        mask &= reference_cloud < OPAQUE_CLOUD
    if hidden is not None:
        mask &= ~hidden
    return mask


@dataclass(frozen=True)
class PairDraw:
    """What one training pair is, before any pixel is read.

    Attributes:
        index: Index of the pair in its generator.
        chip: Training chip it is cut from.
        kind: ``SAME_DATE`` or ``CROSS_DATE``.
        dates: Roles of the dates the reference and the moving image come from;
            twice the same for a same-date pair.
        scenario: Geometric model of its displacement.
        degradation: Its degradation.
    """

    index: int
    chip: str
    kind: str
    dates: tuple[str, str]
    scenario: str
    degradation: DrawnDegradation


@dataclass(frozen=True)
class TrainingPair:
    """A training pair: two images, the flow between them and a loss mask.

    Attributes:
        draw: What the pair is.
        pair: The degraded pair, with its truth and the opacity of the clouds
            of its moving image.
        reference_cloud: Opacity of the clouds laid over the reference image,
            ``None`` if it has none.
        hidden: Reference pixels where either date of a cross-date pair shows
            cloud or cloud shadow in its scene classification; ``None`` for a
            same-date pair.
    """

    draw: PairDraw
    pair: SimulatedPair
    reference_cloud: np.ndarray | None = None
    hidden: np.ndarray | None = None

    @property
    def reference(self) -> np.ndarray:
        """Reference image."""
        return self.pair.reference

    @property
    def moving(self) -> np.ndarray:
        """Moving image."""
        return self.pair.moving

    @property
    def flow(self) -> np.ndarray:
        """Ground-truth flow on the reference grid, ``(2, rows, cols)``.

        ``dy`` then ``dx``, as everywhere in the package: ``moving(p + flow(p))
        = reference(p)``. torchvision's RAFT gives ``dx`` then ``dy``.
        """
        return self.pair.truth.field(self.pair.reference.shape)

    @property
    def mask(self) -> np.ndarray:
        """Reference pixels the loss may use, see ``loss_mask``."""
        return loss_mask(self.pair, self.reference_cloud, self.hidden)

    def network_inputs(self) -> tuple[np.ndarray, np.ndarray]:
        """Reference and moving image as the network takes them.

        The conversion is the one the ``raft`` method applies to a benchmark
        pair, each image stretched by its own percentiles.

        Returns:
            Two float32 arrays of shape ``(3, rows, cols)``, values in [-1, 1].
        """
        return raft.network_input(self.reference), raft.network_input(self.moving)


def pair_rng(seed: int, index: int, purpose: str) -> np.random.Generator:
    """The generator of one random part of a training pair.

    Args:
        seed: Seed of the pairs.
        index: Index of the pair.
        purpose: ``"draw"`` for what the pair is, ``"geometry"`` for its window
            and displacement, ``"pixels"`` for its cloud fields and noise.

    Returns:
        A generator that depends on these three only.
    """
    return _rng(seed, "train-pairs", index, purpose)


def _pick(rng: np.random.Generator, n: int) -> int:
    """Draw an index below ``n`` from exactly one uniform number."""
    return min(int(rng.uniform() * n), n - 1)


class PairGenerator:
    """Training pairs by index, from the dates of training chips.

    Attributes:
        chips: Chip name to the dates of its series.
        config: What pairs are made of.
        ranges: Ranges their degradations are drawn in.
    """

    def __init__(
        self,
        chips: Mapping[str, Sequence[Acquisition]],
        config: PairsConfig,
        ranges: DegradationRanges,
    ) -> None:
        """Check that the chips can give the pairs asked for.

        Raises:
            ValueError: If there is no chip, a chip has no date, or cross-date
                pairs are asked of a chip with a single date.
        """
        if not chips:
            raise ValueError("training pairs need at least one chip")
        needed = 2 if config.cross_date > 0 else 1
        for name, dates in chips.items():
            if len(dates) < needed:
                raise ValueError(
                    f"{name} has {len(dates)} date(s), pairs need at least {needed}"
                )
        self.chips = {name: tuple(dates) for name, dates in chips.items()}
        self.config = config
        self.ranges = ranges

    def draw(self, index: int) -> PairDraw:
        """Say what pair ``index`` is, without reading a pixel.

        The chip, the kind, the dates, the scenario and the degradation each
        take their own draws, in that order, whatever the others come out as.
        Two configurations that differ by their share of cross-date pairs only
        therefore give pair ``index`` the same chip, reference date, scenario,
        degradation, window and displacement.

        Args:
            index: Index of the pair, non-negative.

        Returns:
            The pair's description.
        """
        rng = pair_rng(self.config.seed, index, "draw")
        names = list(self.chips)
        chip = names[_pick(rng, len(names))]
        dates = self.chips[chip]
        cross = rng.uniform() < self.config.cross_date
        first = _pick(rng, len(dates))
        # Any other date of the chip, each as likely.
        step = 1 + _pick(rng, max(len(dates) - 1, 1))
        second = (first + step) % len(dates) if cross else first
        scenario = self.config.scenarios[_pick(rng, len(self.config.scenarios))]
        return PairDraw(
            index=index,
            chip=chip,
            kind=CROSS_DATE if cross else SAME_DATE,
            dates=(dates[first].role, dates[second].role),
            scenario=scenario,
            degradation=self.ranges.draw(rng),
        )

    def __call__(self, index: int) -> TrainingPair:
        """Make pair ``index``.

        Args:
            index: Index of the pair, non-negative.

        Returns:
            The pair, the same at every call.
        """
        draw = self.draw(index)
        by_role = {date.role: date for date in self.chips[draw.chip]}
        reference, moving = (by_role[role] for role in draw.dates)
        simulation = self.config.simulation
        geometry = pair_rng(self.config.seed, index, "geometry")
        if draw.kind == SAME_DATE:
            clean = draw_pair(
                reference.image,
                simulation,
                geometry,
                draw.scenario,
                georef=reference.georef,
            )
            hidden = None
        else:
            # As for an inter-band pair: the moving date is put in the units of
            # the reference date, which the degradations measure their levels
            # in, and warped; the reference is the same window of its own date.
            clean = draw_pair(
                in_units_of(moving.image, reference.image),
                simulation,
                geometry,
                draw.scenario,
                georef=reference.georef,
                reference=reference.image,
            )
            hidden = _window(reference.hidden | moving.hidden, reference, clean)

        pixels = pair_rng(self.config.seed, index, "pixels")
        pair = draw.degradation.preset(clean, pixels)
        reference_cloud = None
        if draw.degradation.reference_cover > 0:
            # The benchmark's clouds, laid over the clean reference at the
            # level they have on the moving image; the noise the preset gave
            # the reference goes on top, as a detector adds it last.
            clouded = Clouds(draw.degradation.reference_cover)(
                SimulatedPair(clean.reference, clean.reference, Translation(0.0, 0.0)),
                pixels,
            )
            noise = pair.reference - clean.reference
            pair = dataclasses.replace(pair, reference=clouded.moving + noise)
            reference_cloud = clouded.cloud
        return TrainingPair(draw, pair, reference_cloud, hidden)


def _window(
    chip_array: np.ndarray, chip: Acquisition, pair: SimulatedPair
) -> np.ndarray:
    """Cut the window of a pair out of an array given on its chip's grid."""
    # The pair's grid is the chip's, moved by whole pixels to its window.
    offset = ~chip.georef.transform @ pair.georef.transform
    top, left = round(offset.f), round(offset.c)
    rows, cols = pair.reference.shape
    return chip_array[top : top + rows, left : left + cols]


def load_training_series(
    training: TrainingConfig,
    series: SeriesConfig,
    data_dir: Path,
    names: Sequence[str] | None = None,
    candidates: Candidates = stac_scenes,
) -> dict[str, list[Acquisition]]:
    """Load the dates of the chips training pairs are cut from.

    The chips are asked for by role, so a validation chip, a benchmark chip or
    a held-out site raises instead of being drawn from.

    Args:
        training: The training chips configuration.
        series: Series configuration, which says which dates a chip has.
        data_dir: Root of downloaded data.
        names: Training chips to load, all of them if ``None``.
        candidates: Scene search, replaced by a fake in tests.

    Returns:
        Chip name to its acquisitions, earliest first.

    Raises:
        ValueError: If a name is not a training chip.
    """
    catalogue = training.benchmark.catalogue
    return {
        chip.name: load_series(chip.site, catalogue, series, data_dir, candidates)
        for chip in training.select(TRAIN, names)
    }


@dataclass(frozen=True)
class PairRow:
    """One training pair as a table row: what it is and what it cost to make.

    Attributes:
        index: Index of the pair.
        chip: Training chip it is cut from.
        kind: ``SAME_DATE`` or ``CROSS_DATE``.
        reference_date: Role of the date of the reference image.
        moving_date: Role of the date of the moving image.
        scenario: Geometric model of its displacement.
        gain: Contrast gain of the moving image.
        offset: Level shift of the moving image, in reference standard
            deviations.
        gamma: Exponent of the moving image's tone curve.
        cover: Cloud cover of the moving image.
        sigma: Blur of the moving image, in pixels.
        snr_db: Signal-to-noise ratio of both images, in decibels.
        reference_cover: Cloud cover of the reference image.
        usable: Share of the pixels the loss may use.
        time_ms: Time to make the pair, its flow, its mask and the network's
            inputs, in milliseconds.
    """

    index: int
    chip: str
    kind: str
    reference_date: str
    moving_date: str
    scenario: str
    gain: float
    offset: float
    gamma: float
    cover: float
    sigma: float
    snr_db: float
    reference_cover: float
    usable: float
    time_ms: float


def timed_pairs(
    generator: PairGenerator, indices: Sequence[int]
) -> tuple[list[TrainingPair], list[PairRow]]:
    """Make pairs and time each one, as a training loop would ask for them.

    The time of a pair covers all a training step reads from it: the two
    images converted for the network, the flow and the mask.

    Args:
        generator: The generator.
        indices: Indices of the pairs to make.

    Returns:
        The pairs, and one row per pair.
    """
    pairs, rows = [], []
    for index in indices:
        start = perf_counter()
        pair = generator(index)
        _ = pair.network_inputs(), pair.flow
        usable = float(pair.mask.mean())
        seconds = perf_counter() - start
        draw = pair.draw
        rows.append(
            PairRow(
                index=index,
                chip=draw.chip,
                kind=draw.kind,
                reference_date=draw.dates[0],
                moving_date=draw.dates[1],
                scenario=draw.scenario,
                **dataclasses.asdict(draw.degradation),
                usable=usable,
                time_ms=1000 * seconds,
            )
        )
        pairs.append(pair)
    return pairs, rows


def to_markdown(rows: Sequence[PairRow]) -> str:
    """Summarise drawn pairs: how many of each kind, and how fast they are made.

    Args:
        rows: One row per pair, non-empty.

    Returns:
        A table per kind and scenario, then the throughput over all the pairs.
    """
    lines = [
        "| kind | scenario | pairs | cloud on both | usable pixels | time per pair |",
        "|---|---|---:|---:|---:|---:|",
    ]
    groups = sorted({(row.kind, row.scenario) for row in rows}, reverse=True)
    for kind, scenario in groups:
        group = [row for row in rows if (row.kind, row.scenario) == (kind, scenario)]
        both = sum(row.cover > 0 and row.reference_cover > 0 for row in group)
        lines.append(
            f"| {kind} | {scenario} | {len(group)} | {both} "
            f"| {100 * np.mean([row.usable for row in group]):.1f} % "
            f"| {np.mean([row.time_ms for row in group]):.0f} ms |"
        )
    seconds = sum(row.time_ms for row in rows) / 1000
    lines += [
        "",
        f"Throughput: {len(rows) / seconds:.1f} pairs per second in one process "
        f"({len(rows)} pairs in {seconds:.1f} s), from the chips in memory to the "
        "network's inputs, the flow and the mask.",
    ]
    return "\n".join(lines) + "\n"


def contact_sheet(pairs: Sequence[TrainingPair], path: Path, per_row: int = 4) -> None:
    """Save training pairs side by side, as the network sees them.

    Each pair takes three panels: the reference image, the moving image, and
    the reference again with the pixels the loss leaves out in red. Images are
    shown through the network's stretch.

    Args:
        pairs: Pairs to show, non-empty.
        path: Output PNG; parent directories are created.
        per_row: Pairs per row of the sheet.
    """
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    n_rows = math.ceil(len(pairs) / per_row)
    fig, axes = plt.subplots(
        n_rows, 3 * per_row, figsize=(6.0 * per_row, 2.45 * n_rows), squeeze=False
    )
    for ax in axes.flat:
        ax.axis("off")
    for i, pair in enumerate(pairs):
        left, middle, right = axes[i // per_row][3 * (i % per_row) :][:3]
        reference, moving = (
            (raft.stretch(image) + 1) / 2 for image in (pair.reference, pair.moving)
        )
        mask = pair.mask
        excluded = np.repeat(reference[..., np.newaxis], 3, axis=2)
        excluded[~mask] = 0.5 * excluded[~mask] + 0.5 * np.array([1.0, 0.0, 0.0])
        left.imshow(reference, cmap="gray", vmin=0, vmax=1)
        middle.imshow(moving, cmap="gray", vmin=0, vmax=1)
        right.imshow(excluded)

        draw, d = pair.draw, pair.draw.degradation
        dates = draw.dates[0]
        if draw.kind == CROSS_DATE:
            dates += f" -> {draw.dates[1]}"
        left.set_title(f"#{draw.index} {draw.chip}, {draw.kind}\n{dates}", fontsize=7)
        middle.set_title(
            f"{draw.scenario}, gain {d.gain:.2f}, offset {d.offset:+.2f}\n"
            f"gamma {d.gamma:.2f}, blur {d.sigma:.1f} px, {d.snr_db:.0f} dB",
            fontsize=7,
        )
        right.set_title(
            f"cloud: ref {d.reference_cover:.2f}, moving {d.cover:.2f}\n"
            f"{100 * mask.mean():.0f} % usable",
            fontsize=7,
        )
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=110)
    plt.close(fig)

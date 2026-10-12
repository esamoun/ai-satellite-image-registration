"""The data of the demo page: the demo pairs and what five methods make of them.

``satreg demo`` computes once what the static page shows, so the page computes
nothing. For each site it picks one pair of the benchmark by a rule on the ground
truth (``pick``), draws it as the benchmark does under two presets, as a
translation (the slider) and as a dense field (the arrows), runs the methods on
both, and writes:

- to the demo directory, per site and preset: the images of the slider as PNG, the
  changed pixels of the false-change detector before and after each correction,
  ``pair.json`` (truth, estimates, errors, failures) and ``arrows.json`` (the true
  field, each estimate and their difference on a coarse grid);
- to the examples directory: the same pairs as GeoTIFF on their map grid, with a
  manifest, for ``satreg register``.

Showing a pair measures nothing: no figure written here enters a table. Nothing
written here holds a time or a memory figure, and nothing depends on the date
or the machine's clock, so a second run writes the same files.
"""

import json
import math
import shutil
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import rasterio

from . import register as supplied
from .benchmark import BenchmarkConfig, _rng, draw_pair, max_reach
from .cycle import lands_inside, register
from .degrade import Preset
from .displacement import Displacement, Translation
from .falsechange import (
    BORDER_PX,
    K_SIGMA,
    NONE,
    Resampler,
    _clear_of_cloud,
    changed,
    interior,
    match_level,
    threshold,
)
from .georef import Georef
from .methods import Method
from .metrics import score
from .simulate import SimulatedPair

# What Copernicus asks of anyone who redistributes Sentinel data they modified.
NOTICE = "Contains modified Copernicus Sentinel data 2025"

# The rule: a site's demo pair is the first pair of the benchmark whose true
# shift is over this. Under it a slider shows nothing. Set on 2026-10-12 from
# the true shifts of pairs 0 to 3 alone: see docs/decisions.md.
MIN_SHIFT_PX = 2.0

# The presets a demo pair is shown under: no degradation, and the hardest.
PRESETS = ("clean", "hard")

# The methods run on a demo pair, after "no registration" (``NONE``).
METHODS = ("phase_correlation_hann", "sift_ransac", "raft", "raft_ft")

# The scenario of the slider and that of the arrows.
SLIDER = "translation"
ARROWS = "dense"

# One arrow every so many pixels, each way.
ARROW_STEP_PX = 16

# Images are shown between these percentiles of the pair's reference image.
DISPLAY_PERCENTILES = (2.0, 98.0)

# Changed pixels are opaque, pixels the detector does not count are veiled, and
# the rest is transparent, so the picture lies over the image it is about.
CHANGED_RGBA = (230, 0, 126, 255)
NOT_COUNTED_RGBA = (0, 0, 0, 96)

# The published files of the cost curve, copied as they are.
CURVE_FILES = ("curve-points.csv", "curve-references.csv", "curve-refinements.csv")

MANIFEST_FILE = "manifest.json"
SLIDER_FILE = "pair.json"
ARROWS_FILE = "arrows.json"
TRUTH_FILE = "truth_dense.tif"

# Decimals kept in the JSON files: a ten-thousandth of a pixel.
DECIMALS = 4


@dataclass(frozen=True)
class Source:
    """A site image demo pairs are cut from.

    Attributes:
        name: Site name.
        image: 2-D site image.
        georef: Its map grid.
        scene: Identifier of the scene it was cut from, ``None`` if it has none.
        acquired: When that scene was acquired, ISO 8601, ``None`` likewise.
    """

    name: str
    image: np.ndarray
    georef: Georef
    scene: str | None = None
    acquired: str | None = None


@dataclass(frozen=True)
class Outcome:
    """What a method made of a pair.

    Attributes:
        displacement: Its estimate, ``None`` if it gave none that can be used.
        error_px: Mean end-point error over the pair's valid pixels, NaN without
            an estimate.
        failure: Whether the pair counts as a failure, as the benchmark counts.
        reason: Why, empty otherwise.
    """

    displacement: Displacement | None
    error_px: float
    failure: bool
    reason: str


def true_shift(
    site: str, image: np.ndarray, config: BenchmarkConfig, index: int
) -> float:
    """Length of the shift at the centre of a pair of the benchmark, in pixels.

    Read from the simulator's own draw of the pair: no method is run.

    Args:
        site: Site name.
        image: 2-D site image.
        config: The benchmark's parameters.
        index: Index of the pair.

    Returns:
        The length of its true shift.
    """
    pair = draw_pair(image, config, _rng(config.seed, site, index), SLIDER)
    return math.hypot(pair.truth.dx, pair.truth.dy)


def pick(site: str, image: np.ndarray, config: BenchmarkConfig) -> int:
    """Pick a site's demo pair: the first whose true shift is over ``MIN_SHIFT_PX``.

    The rule reads the ground truth only, never what a method made of a pair.

    Args:
        site: Site name.
        image: 2-D site image.
        config: The benchmark's parameters.

    Returns:
        Index of the pair.

    Raises:
        ValueError: If none of the site's ``config.n_pairs`` pairs moves that far.
    """
    for index in range(config.n_pairs):
        if true_shift(site, image, config, index) > MIN_SHIFT_PX:
            return index
    raise ValueError(
        f"none of the {config.n_pairs} pairs of {site} moves by more than "
        f"{MIN_SHIFT_PX:g} px"
    )


def draw(
    source: Source,
    config: BenchmarkConfig,
    index: int,
    preset: str,
    degrade: Preset,
) -> dict[str, SimulatedPair]:
    """Draw a demo pair as the benchmark draws it, for the slider and the arrows.

    Both are the benchmark's own pairs of that site, index and preset. They share
    the window, hence the reference image, and the shift drawn for the centre;
    the dense one adds its small rotation, scale, shear and local field.

    Args:
        source: The site.
        config: The benchmark's parameters.
        index: Index of the pair.
        preset: Name of the preset, which seeds the degradation.
        degrade: The preset.

    Returns:
        ``SLIDER`` and ``ARROWS`` to their pair.
    """
    pairs = {}
    for scenario in (SLIDER, ARROWS):
        geometry = _rng(config.seed, source.name, index)
        clean = draw_pair(source.image, config, geometry, scenario, source.georef)
        pairs[scenario] = degrade(clean, _rng(config.seed, source.name, index, preset))
    return pairs


def window_of(source: Source, pair: SimulatedPair) -> dict[str, int]:
    """Where a pair lies in its site image: top-left pixel and side."""
    origin = pair.georef.transform
    col, row = ~source.georef.transform @ (origin.c, origin.f)
    return {"row": round(row), "col": round(col), "size": pair.reference.shape[0]}


def run(method: Method | None, pair: SimulatedPair, config: BenchmarkConfig) -> Outcome:
    """Run one method on one pair and score it as the benchmark does.

    Args:
        method: The method, ``None`` for no registration.
        pair: The pair.
        config: The benchmark's parameters, for the failure threshold.

    Returns:
        The outcome. No registration is scored and is not a method's failure.
    """
    shape = pair.reference.shape
    if method is None:
        identity = Translation(0.0, 0.0)
        error = score(pair.truth, identity, shape, pair.valid).mean_epe
        return Outcome(identity, error, False, "")
    leg = register(method, pair.reference, pair.moving, pair.georef, repeats=1)
    estimate = leg.displacement
    if estimate is None:
        return Outcome(None, math.nan, True, leg.error)
    if not np.isfinite(estimate.field(shape)).all():
        return Outcome(None, math.nan, True, "non-finite displacement")
    error = score(pair.truth, estimate, shape, pair.valid).mean_epe
    if not error <= config.failure_threshold:
        reason = (
            f"mean error over the failure threshold of {config.failure_threshold:g} px"
        )
        return Outcome(estimate, error, True, reason)
    return Outcome(estimate, error, False, "")


@dataclass(frozen=True)
class Detector:
    """The fixed change detector of the false-change experiment, on one pair.

    Set up as ``falsechange.run_simulated`` sets it up: the moving image is given
    the reference's level, the threshold is ``K_SIGMA`` times the noise of the
    difference, and the pixels counted are those in the frame, off the border
    and clear of cloud.

    Attributes:
        reference: Reference image.
        moving: Moving image, level-matched.
        gain: Gain of the level matching.
        offset: Its offset.
        mask: Pixels the detector counts, before a correction's own frame.
        limit: Difference above which a pixel has changed.
        resampler: Reads ``moving`` under a displacement.
    """

    reference: np.ndarray
    moving: np.ndarray
    gain: float
    offset: float
    mask: np.ndarray
    limit: float
    resampler: Resampler

    @classmethod
    def of(cls, pair: SimulatedPair, config: BenchmarkConfig) -> "Detector":
        """Set the detector up on a pair."""
        shape = pair.reference.shape
        reference_clear, moving_clear = _clear_of_cloud(pair)
        mask = pair.valid & interior(shape) & reference_clear
        gain, offset = match_level(
            pair.reference, pair.moving, mask, interior(shape) & moving_clear
        )
        moving = gain * pair.moving + offset
        return cls(
            reference=pair.reference,
            moving=moving,
            gain=gain,
            offset=offset,
            mask=mask,
            limit=threshold(pair.reference, moving),
            resampler=Resampler(moving, max_reach(config)),
        )

    def look(
        self, displacement: Displacement
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Correct the moving image by a displacement and flag what changed.

        Args:
            displacement: Displacement from the reference to the moving image.

        Returns:
            The corrected image, the pixels counted (those of ``mask`` the
            displacement reads from inside the moving image) and, among them,
            the pixels flagged as changed.
        """
        inside = lands_inside(displacement, self.reference.shape)
        corrected = self.resampler.correct(displacement)
        counted = self.mask & inside
        flagged = changed(self.reference, corrected, self.limit) & counted
        # Read from off the image, a pixel shows its mirror image: no data.
        return np.where(inside, corrected, np.nan), counted, flagged


def display_range(reference: np.ndarray) -> tuple[float, float]:
    """The values shown as black and as white: percentiles of the reference."""
    low, high = np.percentile(reference, DISPLAY_PERCENTILES)
    return float(low), float(high)


def as_bytes(image: np.ndarray, low: float, high: float) -> np.ndarray:
    """An image as 8-bit grey levels, linear between ``low`` and ``high``.

    Args:
        image: 2-D image; NaN where it holds no data.
        low: Value shown as black.
        high: Value shown as white.

    Returns:
        The image as ``uint8``, clipped, black where it holds no data.
    """
    if high <= low:
        return np.zeros(image.shape, np.uint8)
    scaled = np.clip((np.nan_to_num(image, nan=low) - low) / (high - low), 0, 1)
    return np.round(255 * scaled).astype(np.uint8)


def changed_picture(counted: np.ndarray, flagged: np.ndarray) -> np.ndarray:
    """The detector's answer as an RGBA picture to lay over the image."""
    picture = np.zeros((*counted.shape, 4), np.uint8)
    picture[~counted] = NOT_COUNTED_RGBA
    picture[flagged] = CHANGED_RGBA
    return picture


def _write_png(path: Path, picture: np.ndarray) -> None:
    """Write a grey or RGBA picture as PNG, which holds no date."""
    if picture.ndim == 3:
        picture = cv2.cvtColor(picture, cv2.COLOR_RGBA2BGRA)
    if not cv2.imwrite(str(path), picture, [cv2.IMWRITE_PNG_COMPRESSION, 9]):
        raise OSError(f"could not write {path}")


def _plain(value: object) -> object:
    """A value as JSON holds it: rounded, and ``None`` where it is not finite."""
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_plain(item) for item in value]
    if isinstance(value, np.ndarray):
        return _plain(value.tolist())
    if isinstance(value, bool | np.bool_):
        return bool(value)
    if isinstance(value, float | np.floating):
        # Adding zero turns the -0.0 of a rounding into 0.0.
        return round(float(value), DECIMALS) + 0.0 if math.isfinite(value) else None
    if isinstance(value, np.integer):
        return int(value)
    return value


def _write_json(path: Path, payload: Mapping, indent: int | None = None) -> None:
    separators = None if indent else (",", ":")
    text = json.dumps(
        _plain(payload),
        indent=indent,
        separators=separators,
        sort_keys=True,
        allow_nan=False,
    )
    path.write_text(text + "\n")


def described(displacement: Displacement | None, shape: tuple[int, int]) -> dict | None:
    """A displacement's model and parameters, a dense one summed up."""
    if displacement is None:
        return None
    summary = supplied.described(displacement, shape)
    # Where `satreg register` writes a dense field; nothing is written here.
    summary.pop("file", None)
    return summary


def _emptied(directory: Path, patterns: Sequence[str]) -> Path:
    """Make a directory, and remove from it what an earlier run wrote there."""
    directory.mkdir(parents=True, exist_ok=True)
    for pattern in patterns:
        for path in directory.glob(pattern):
            path.unlink()
    return directory


def write_slider(
    directory: Path,
    pair: SimulatedPair,
    outcomes: Mapping[str, Outcome],
    config: BenchmarkConfig,
) -> dict:
    """Write the slider's images and ``SLIDER_FILE`` for a translation pair.

    The images are the detector's: the moving image at the reference's level,
    and that image resampled by each estimate. All are shown in the display
    range of the reference. A method without an estimate has no image.

    Args:
        directory: Directory to write to.
        pair: The translation pair.
        outcomes: Method name to its outcome, ``NONE`` included.
        config: The benchmark's parameters.

    Returns:
        What ``SLIDER_FILE`` holds.
    """
    shape = pair.reference.shape
    detector = Detector.of(pair, config)
    low, high = display_range(pair.reference)
    _write_png(directory / "reference.png", as_bytes(pair.reference, low, high))
    _write_png(directory / "moving.png", as_bytes(detector.moving, low, high))
    methods = {}
    for name, outcome in outcomes.items():
        entry = {
            "estimate": described(outcome.displacement, shape),
            "error_px": outcome.error_px,
            "failure": outcome.failure,
            "reason": outcome.reason,
            "corrected": None,
            "changed": None,
            "changed_px": None,
            "counted_px": None,
            "changed_share": None,
        }
        if outcome.displacement is not None:
            corrected, counted, flagged = detector.look(outcome.displacement)
            # Without registration the corrected image is the moving image.
            entry["corrected"] = "moving.png"
            if name != NONE:
                entry["corrected"] = f"corrected-{name}.png"
                picture = as_bytes(corrected, low, high)
                _write_png(directory / entry["corrected"], picture)
            entry["changed"] = f"changed-{name}.png"
            _write_png(directory / entry["changed"], changed_picture(counted, flagged))
            entry["changed_px"] = int(flagged.sum())
            entry["counted_px"] = int(counted.sum())
            entry["changed_share"] = (
                float(flagged.sum() / counted.sum()) if counted.any() else math.nan
            )
        methods[name] = entry
    truth = described(pair.truth, shape)
    truth["shift_px"] = math.hypot(pair.truth.dx, pair.truth.dy)
    payload = {
        "scenario": SLIDER,
        "truth": truth,
        "images": {"reference": "reference.png", "moving": "moving.png"},
        "display": {"black": low, "white": high},
        "detector": {
            "k_sigma": K_SIGMA,
            "limit": detector.limit,
            "border_px": BORDER_PX,
            "gain": detector.gain,
            "offset": detector.offset,
        },
        "cloud_fraction": pair.cloud_fraction,
        "methods": methods,
    }
    _write_json(directory / SLIDER_FILE, payload, indent=1)
    return payload


def write_arrows(
    directory: Path, pair: SimulatedPair, outcomes: Mapping[str, Outcome]
) -> dict:
    """Write ``ARROWS_FILE`` for a dense pair.

    The true field, each estimate and their difference (estimate minus truth)
    are given at one pixel every ``ARROW_STEP_PX``, as ``dy`` and ``dx`` in
    pixels. ``observed`` tells where the truth can be seen in the moving image:
    elsewhere a pixel has no error to speak of.

    Args:
        directory: Directory to write to.
        pair: The dense pair.
        outcomes: Method name to its outcome, ``NONE`` included.

    Returns:
        What ``ARROWS_FILE`` holds.
    """
    shape = pair.reference.shape
    rows = list(range(ARROW_STEP_PX // 2, shape[0], ARROW_STEP_PX))
    cols = list(range(ARROW_STEP_PX // 2, shape[1], ARROW_STEP_PX))
    at = np.ix_(rows, cols)
    truth = pair.truth.field(shape)
    methods = {}
    for name, outcome in outcomes.items():
        entry = {
            "estimate": described(outcome.displacement, shape),
            "error_px": outcome.error_px,
            "failure": outcome.failure,
            "reason": outcome.reason,
            "dy": None,
            "dx": None,
            "error_dy": None,
            "error_dx": None,
        }
        if outcome.displacement is not None:
            field = outcome.displacement.field(shape)
            entry.update(
                dy=field[0][at],
                dx=field[1][at],
                error_dy=(field[0] - truth[0])[at],
                error_dx=(field[1] - truth[1])[at],
            )
        methods[name] = entry
    payload = {
        "scenario": ARROWS,
        "grid": {"step_px": ARROW_STEP_PX, "rows": rows, "cols": cols},
        "truth": {
            **described(pair.truth, shape),
            "dy": truth[0][at],
            "dx": truth[1][at],
        },
        "observed": pair.valid[at],
        "image": "reference.png",
        "cloud_fraction": pair.cloud_fraction,
        "methods": methods,
    }
    _write_json(directory / ARROWS_FILE, payload)
    return payload


def _tif(path: Path, layers: np.ndarray, pair: SimulatedPair, names, tags) -> None:
    kept = {key: value for key, value in tags.items() if value is not None}
    supplied.write_tif(path, layers, pair.georef, names, kept)


def write_examples(
    directory: Path,
    source: Source,
    preset: str,
    pairs: Mapping[str, SimulatedPair],
) -> list[dict]:
    """Write a demo pair's images as GeoTIFF, as ``satreg register`` reads them.

    ``<site>/<preset>/reference.tif`` is the reference image of both pairs,
    ``moving_translation.tif`` and ``moving_dense.tif`` their moving images, and
    ``<site>/truth_dense.tif`` the true field of the dense pair, ``dy`` then
    ``dx``, which no preset changes. All are on the map grid of the window.

    Args:
        directory: The examples directory.
        source: The site.
        preset: Name of the preset.
        pairs: ``SLIDER`` and ``ARROWS`` to their pair.

    Returns:
        The two entries of the manifest, paths relative to ``directory``.

    Raises:
        ValueError: If the two pairs do not share their reference image.
    """
    slider, arrows = pairs[SLIDER], pairs[ARROWS]
    if not np.array_equal(slider.reference, arrows.reference):
        raise ValueError(f"the pairs of {source.name} do not share their reference")
    shape = slider.reference.shape
    tags = {
        "notice": NOTICE if source.scene else None,
        "site": source.name,
        "scene": source.scene,
        "acquired": source.acquired,
        "preset": preset,
    }
    where = _emptied(directory / source.name / preset, ["*.tif"])
    reference = where / "reference.tif"
    _tif(reference, slider.reference[None], slider, ["reference"], tags)
    entries = []
    for scenario, pair in pairs.items():
        moving = where / f"moving_{scenario}.tif"
        _tif(moving, pair.moving[None], pair, ["moving"], tags | {"scenario": scenario})
        truth = described(pair.truth, shape)
        if scenario == ARROWS:
            field = directory / source.name / TRUTH_FILE
            flow = pair.truth.field(shape)
            _tif(field, flow, pair, ["dy", "dx"], tags | {"preset": None})
            truth["file"] = field.relative_to(directory).as_posix()
        entries.append(
            {
                "site": source.name,
                "scene": source.scene,
                "acquired": source.acquired,
                "window": window_of(source, pair),
                "preset": preset,
                "scenario": scenario,
                "reference": reference.relative_to(directory).as_posix(),
                "moving": moving.relative_to(directory).as_posix(),
                "truth": truth,
            }
        )
    return entries


def copy_curve(source: Path, directory: Path) -> list[str]:
    """Copy the published files of the cost curve, byte for byte.

    Args:
        source: Directory that holds ``CURVE_FILES``.
        directory: Directory to copy them to, created if needed.

    Returns:
        The names of the copies.

    Raises:
        FileNotFoundError: If one of the files is not in ``source``.
    """
    missing = [name for name in CURVE_FILES if not (source / name).is_file()]
    if missing:
        raise FileNotFoundError(f"no {missing[0]} in {source}")
    directory.mkdir(parents=True, exist_ok=True)
    for name in CURVE_FILES:
        shutil.copyfile(source / name, directory / name)
    return list(CURVE_FILES)


def scene_of(chip: Path) -> tuple[str, str]:
    """The scene a chip was cut from and when it was acquired, from its tags."""
    with rasterio.open(chip) as src:
        tags = src.tags()
    return tags["item_id"], tags["datetime"]


def size_of(directory: Path) -> tuple[int, int]:
    """Number of files under a directory, and their total size in bytes."""
    files = [path for path in directory.rglob("*") if path.is_file()]
    return len(files), sum(path.stat().st_size for path in files)


EXAMPLES_README = """\
# Demo pairs

{notice}

These are the demo pairs of the project's page: for each site, one pair of the
benchmark, picked by a rule on its ground truth (the first pair of the site
whose true shift is over {min_shift:g} px), under the `clean` and `hard` presets.
`satreg demo` wrote them; `manifest.json` gives each pair's site, scene, window
in the site image and true displacement.

Each `<site>/<preset>/` holds `reference.tif` and two moving images of it:
`moving_translation.tif`, shifted as a whole, and `moving_dense.tif`, moved by
a field that varies from pixel to pixel, given in `<site>/truth_dense.tif`
(`dy` then `dx`, in pixels).

```bash
satreg register examples/{site}/clean/reference.tif \\
    examples/{site}/clean/moving_translation.tif \\
    --method phase_correlation --out out/
```

{convention}
"""


def build(
    sources: Sequence[Source],
    methods: Mapping[str, Method],
    presets: Mapping[str, Preset],
    config: BenchmarkConfig,
    out: Path,
    examples: Path,
    curve: Path,
) -> list[dict]:
    """Write the demo's data, and the demo pairs as files.

    Args:
        sources: The sites, none of them held out.
        methods: Method name to method, run after no registration.
        presets: Preset name to preset.
        config: The benchmark's parameters.
        out: The demo directory.
        examples: The examples directory.
        curve: Directory of the published files of the cost curve.

    Returns:
        One row per site, preset, scenario and method: the pair picked for the
        site, the method's error on it and its failure.

    Raises:
        FileNotFoundError: If a file of the cost curve is missing.
        ValueError: If a site has no pair that moves far enough.
    """
    copied = copy_curve(curve, out / "curve")
    runners: dict[str, Method | None] = {NONE: None, **methods}
    sites, entries, rows = [], [], []
    for source in sources:
        index = pick(source.name, source.image, config)
        for preset, degrade in presets.items():
            pairs = draw(source, config, index, preset, degrade)
            where = _emptied(out / source.name / preset, ["*.png", "*.json"])
            for scenario, pair in pairs.items():
                outcomes = {
                    name: run(method, pair, config) for name, method in runners.items()
                }
                if scenario == SLIDER:
                    write_slider(where, pair, outcomes, config)
                else:
                    write_arrows(where, pair, outcomes)
                rows += [
                    {
                        "site": source.name,
                        "pair": index,
                        "preset": preset,
                        "scenario": scenario,
                        "method": name,
                        "error_px": outcome.error_px,
                        "failure": outcome.failure,
                        "reason": outcome.reason,
                    }
                    for name, outcome in outcomes.items()
                ]
            entries += write_examples(examples, source, preset, pairs)
        truth = pairs[SLIDER].truth
        sites.append(
            {
                "name": source.name,
                "pair": index,
                "scene": source.scene,
                "acquired": source.acquired,
                "window": window_of(source, pairs[SLIDER]),
                "shift": {
                    "dx": truth.dx,
                    "dy": truth.dy,
                    "px": math.hypot(truth.dx, truth.dy),
                },
            }
        )
    notice = NOTICE if any(source.scene for source in sources) else None
    rule = {
        "seed": config.seed,
        "min_shift_px": MIN_SHIFT_PX,
        "text": "For each site, the first pair of the benchmark whose true shift "
        f"is over {MIN_SHIFT_PX:g} px. The rule reads the ground truth only.",
    }
    _write_json(
        out / MANIFEST_FILE,
        {
            "notice": notice,
            "convention": supplied.CONVENTION,
            "rule": rule,
            "size_px": config.size,
            "failure_threshold_px": config.failure_threshold,
            "presets": list(presets),
            "methods": list(runners),
            "sites": sites,
            "files": {"slider": SLIDER_FILE, "arrows": ARROWS_FILE},
            "curve": [f"curve/{name}" for name in copied],
        },
        indent=1,
    )
    _write_json(
        examples / MANIFEST_FILE,
        {
            "notice": notice,
            "convention": supplied.CONVENTION,
            "rule": rule,
            "pairs": entries,
        },
        indent=1,
    )
    (examples / "README.md").write_text(
        EXAMPLES_README.format(
            notice=f"{notice}." if notice else "Synthetic images.",
            min_shift=MIN_SHIFT_PX,
            site=sources[0].name,
            convention=supplied.CONVENTION,
        )
    )
    return rows

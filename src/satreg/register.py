"""Register a supplied pair: two images someone gives, one method, its result.

A supplied pair belongs to no site and has no ground truth (CONTEXT.md), so
nothing here is scored: a method estimates the displacement, the moving image
is corrected with it, and both are written. The images are taken whole, or
through one window cut from both. A pair the command does not take is refused
with what to do instead, never resampled, tiled or cropped on its behalf. See
docs/decisions.md.
"""

import json
import math
import warnings
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter

import numpy as np
import rasterio
from rasterio.errors import NotGeoreferencedWarning, RasterioIOError
from rasterio.windows import Window

from . import falsechange, weights
from .displacement import Affine, Displacement, Translation
from .georef import Georef
from .methods import Method, missing_dependencies
from .methods.base import Estimate, GeoreferencedMethod
from .methods.raft import MIN_SIDE, Raft
from .methods.raft_onnx import RaftOnnx

# Largest side of a pair the command registers, in px. Set from what a pair
# cost on the M1 at 256, 512 and 1,024 px: fine-tuned RAFT under ONNX Runtime
# holds in 0.7 GiB at 512 px and takes 5.2 to 5.5 GiB at 1,024 px
# (docs/decisions.md). A larger image is refused, not tiled.
MAX_SIDE_PX = 512

# How far two grids may sit apart and still be one grid, in pixels.
GRID_TOLERANCE_PX = 1e-6

DISPLACEMENT_FILE = "displacement.json"
CORRECTED_FILE = "corrected.tif"
FLOW_FILE = "flow.tif"

CONVENTION = (
    "moving(p + d) = reference(p): the content at pixel p of the reference is "
    "found at p + d in the moving image; d = (dy, dx) in pixels, rows down"
)


class Refused(Exception):
    """A pair or a request the command does not take, with what to do instead."""


@dataclass(frozen=True)
class SuppliedPair:
    """Two images given to be registered, as the methods take them.

    Attributes:
        reference: Reference image.
        moving: Moving image, same shape as ``reference``.
        georef: Map grid of both images, ``None`` if neither file carries one.
        described: Where the pair comes from, JSON-ready: the files, the band
            read from each, the window and the shape.
    """

    reference: np.ndarray
    moving: np.ndarray
    georef: Georef | None
    described: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Registration:
    """What one method answered on a supplied pair.

    Attributes:
        method: The method's name.
        displacement: Estimated displacement.
        diagnostics: The method's own diagnostics.
        duration_s: Duration of the call, in seconds. It is the first call of
            its process, so a model's loading is in it.
    """

    method: str
    displacement: Displacement
    diagnostics: Mapping[str, float]
    duration_s: float


def _open(path: Path) -> rasterio.DatasetReader:
    """Open a supplied image, refused if it is not a raster file."""
    if not path.is_file():
        raise Refused(f"no file at {path}")
    try:
        with warnings.catch_warnings():
            # A PNG has no map grid, and that is not worth a warning here.
            warnings.simplefilter("ignore", NotGeoreferencedWarning)
            return rasterio.open(path)
    except RasterioIOError:
        raise Refused(
            f"{path} is not an image this command reads: give a GeoTIFF or a PNG"
        ) from None


def _band(src: rasterio.DatasetReader, band: int | None) -> int:
    """Index of the band to read from a file, its only one if it has one."""
    if src.count == 1:
        return 1
    if band is None:
        raise Refused(
            f"{src.name} has {src.count} bands and one is registered: name it "
            f"with --band N (1 to {src.count})"
        )
    if not 1 <= band <= src.count:
        raise Refused(
            f"{src.name} has no band {band}: pass --band between 1 and {src.count}"
        )
    return band


def _cut(height: int, width: int, window: tuple[int, int, int] | None) -> Window:
    """The part of the images that is read: all of them, or the window."""
    if window is None:
        return Window(0, 0, width, height)
    row, col, size = window
    if size < 1 or row < 0 or col < 0 or row + size > height or col + size > width:
        raise Refused(
            f"--window {row} {col} {size} does not fit in the images, {height} x "
            f"{width} px: ROW and COL are its top-left pixel, SIZE its side"
        )
    return Window(col, row, size, size)


def _grid(src: rasterio.DatasetReader) -> Georef | None:
    """The map grid of a file, ``None`` if it has no reference system."""
    return Georef(src.crs, src.transform) if src.crs is not None else None


def same_grid(one: Georef, other: Georef) -> bool:
    """Whether two map grids are one: same reference system, same transform."""
    pixel = math.hypot(one.transform.a, one.transform.d)
    return one.crs == other.crs and one.transform.almost_equals(
        other.transform, precision=GRID_TOLERANCE_PX * pixel
    )


def read_pair(
    reference: Path,
    moving: Path,
    band: int | None = None,
    window: tuple[int, int, int] | None = None,
) -> SuppliedPair:
    """Read a supplied pair, whole or through one window cut from both images.

    Args:
        reference: File of the reference image, GeoTIFF or PNG.
        moving: File of the moving image, of the same shape.
        band: Band to read from a file that has several, counted from 1. A
            file with a single band gives that one.
        window: ``(row, col, size)`` of a square window to cut from both, by
            its top-left pixel and its side.

    Returns:
        The pair, on the grid of the files when they carry one.

    Raises:
        Refused: If a file cannot be read, the images differ in shape, a file
            has several bands and none is named, the window does not fit, the
            pair is above ``MAX_SIDE_PX`` a side, the two files carry
            different map grids, or a pixel is not a number.
    """
    with _open(reference) as ref, _open(moving) as mov:
        if (ref.height, ref.width) != (mov.height, mov.width):
            raise Refused(
                f"the images differ in shape: {reference} is {ref.height} x "
                f"{ref.width} px and {moving} is {mov.height} x {mov.width} px. "
                "Put them on one grid first (gdalwarp does it): this command "
                "does not resample what it is given"
            )
        bands = (_band(ref, band), _band(mov, band))
        cut = _cut(ref.height, ref.width, window)
        if max(cut.height, cut.width) > MAX_SIDE_PX:
            raise Refused(
                f"the pair is {cut.height} x {cut.width} px, above the "
                f"{MAX_SIDE_PX} px a side this command registers: cut a window "
                f"with --window ROW COL SIZE, SIZE up to {MAX_SIDE_PX}. Nothing "
                "is tiled"
            )
        grids = (_grid(ref), _grid(mov))
        if None not in grids and not same_grid(*grids):
            raise Refused(
                f"{reference} and {moving} carry different map grids, so their "
                "pixels do not cover the same ground. Put them on one grid "
                "first (gdalwarp does it): this command does not resample "
                "what it is given"
            )
        images = [
            src.read(index, window=cut).astype(float)
            for src, index in zip((ref, mov), bands, strict=True)
        ]
    for path, image in zip((reference, moving), images, strict=True):
        if not np.isfinite(image).all():
            raise Refused(
                f"{path} has pixels that are not numbers in the area read: cut "
                "a window clear of them with --window ROW COL SIZE"
            )
    georef = grids[0] or grids[1]
    if georef is not None:
        georef = georef.window(cut.row_off, cut.col_off)
    return SuppliedPair(
        reference=images[0],
        moving=images[1],
        georef=georef,
        described={
            "reference": str(reference),
            "moving": str(moving),
            "bands": list(bands),
            "window": None if window is None else list(window),
            "shape": list(images[0].shape),
            "georeferenced": georef is not None,
        },
    )


def available(methods: Mapping[str, Method]) -> tuple[list[str], list[str]]:
    """Sort out the methods that can run in this environment.

    Args:
        methods: Method name to method, as the configuration builds them.

    Returns:
        The names of those that can run as things are, then of those that
        would first download their published file. A method whose optional
        packages are not installed, or whose own file is not there, is in
        neither.
    """
    here, after_download = [], []
    for name, method in methods.items():
        if missing_dependencies(method):
            continue
        local = getattr(method, "checkpoint", "") or getattr(method, "file", "")
        if local and not Path(local).is_file():
            continue
        release = getattr(method, "release", "")
        if release and not _cached(release):
            after_download.append(name)
        else:
            here.append(name)
    return here, after_download


def _cached(release: str) -> bool:
    """Whether a published file is in the cache. Its hash is checked on use."""
    return (weights.cache_directory() / weights.lookup(release).asset).is_file()


def padding_note(method: Method, shape: tuple[int, int]) -> str | None:
    """What to tell someone whose pair RAFT has to pad, ``None`` otherwise.

    Args:
        method: The method the pair is registered with.
        shape: ``(rows, cols)`` of the pair.

    Returns:
        The note, for a RAFT method and a pair under ``MIN_SIDE`` a side.
    """
    if not isinstance(method, Raft | RaftOnnx) or min(shape) >= MIN_SIDE:
        return None
    return (
        f"the pair is {shape[0]} x {shape[1]} px and RAFT pads it up to "
        f"{MIN_SIDE} px a side, which costs accuracy: 0.14 to 0.30 px of mean "
        "error on 64 px synthetic pairs, against 0.02 to 0.07 px at 256 px"
    )


def register(name: str, method: Method, pair: SuppliedPair) -> Registration:
    """Run one method on a supplied pair.

    Args:
        name: The method's name.
        method: The method.
        pair: The pair.

    Returns:
        The displacement, the method's diagnostics and the duration of the call.

    Raises:
        Refused: If the method works in map coordinates and the pair has no
            map grid.
        RegistrationFailure: If the method judges it cannot register the pair.
    """
    images = (pair.reference, pair.moving)
    if isinstance(method, GeoreferencedMethod):
        if pair.georef is None:
            raise Refused(
                f"method {name} works in map coordinates and neither image "
                "carries a map grid: give GeoTIFFs with their reference system, "
                "or name another method"
            )
        images = (*images, pair.georef)
    started = perf_counter()
    answer = method(*images)
    duration = perf_counter() - started
    estimate = answer if isinstance(answer, Estimate) else Estimate(answer)
    return Registration(
        method=name,
        displacement=estimate.displacement,
        diagnostics=dict(estimate.diagnostics),
        duration_s=duration,
    )


def correct(pair: SuppliedPair, displacement: Displacement) -> np.ndarray:
    """Resample the moving image of a pair onto the reference grid.

    The interpolation is ``falsechange.correct``, the simulator's. That one
    reads the mirror of the image past its edges; here a pixel whose content
    lies outside the moving image is left without data instead.

    Args:
        pair: The pair.
        displacement: Displacement from the reference to the moving image.

    Returns:
        The corrected image, NaN where the moving image does not reach.
    """
    corrected = falsechange.correct(pair.moving, displacement)
    rows, cols = pair.moving.shape
    row, col = np.indices(pair.moving.shape) + displacement.field(pair.moving.shape)
    inside = (row >= 0) & (row <= rows - 1) & (col >= 0) & (col <= cols - 1)
    corrected[~inside] = np.nan
    return corrected


def described(displacement: Displacement, shape: tuple[int, int]) -> dict:
    """A displacement as ``displacement.json`` gives it.

    Args:
        displacement: The displacement.
        shape: ``(rows, cols)`` of the pair.

    Returns:
        Its model and parameters. A dense one is summed up here and given
        pixel by pixel in ``FLOW_FILE``.
    """
    if isinstance(displacement, Translation):
        return {
            "model": "translation",
            "dx": float(displacement.dx),
            "dy": float(displacement.dy),
        }
    if isinstance(displacement, Affine):
        return {
            "model": "affine",
            "matrix": [list(map(float, row)) for row in displacement.matrix],
            "offset": list(map(float, displacement.offset)),
        }
    dy, dx = displacement.field(shape)
    return {
        "model": "dense",
        "file": FLOW_FILE,
        "mean_dx": float(dx.mean()),
        "mean_dy": float(dy.mean()),
        "max_px": float(np.hypot(dy, dx).max()),
    }


def clear(out: Path) -> None:
    """Remove the files of an earlier call from ``out``.

    Called before the method runs, so that the directory never shows the
    result of another call as that of this one, whether this one fails or
    answers with a displacement of another model.
    """
    for name in (DISPLACEMENT_FILE, CORRECTED_FILE, FLOW_FILE):
        (out / name).unlink(missing_ok=True)


def write(
    out: Path,
    pair: SuppliedPair,
    registration: Registration,
    notes: list[str] | None = None,
) -> dict:
    """Write the result of a registration.

    ``DISPLACEMENT_FILE`` holds the displacement, the method, the duration of
    the call and the method's diagnostics. ``CORRECTED_FILE`` is the moving
    image resampled onto the reference grid, with the pair's map grid if it
    has one. ``FLOW_FILE`` is written for a dense displacement: ``dy`` then
    ``dx``, in pixels.

    Args:
        out: Directory to write to, created if needed.
        pair: The pair.
        registration: What the method answered.
        notes: What the person was told about this call.

    Returns:
        What ``DISPLACEMENT_FILE`` holds.
    """
    shape = pair.reference.shape
    result = {
        "method": registration.method,
        "pair": dict(pair.described),
        "convention": CONVENTION,
        "displacement": described(registration.displacement, shape),
        "duration_s": registration.duration_s,
        "diagnostics": {
            key: float(value) if np.isfinite(value) else None
            for key, value in registration.diagnostics.items()
        },
    }
    corrected = correct(pair, registration.displacement)
    result["corrected"] = {
        "file": CORRECTED_FILE,
        "no_data_px": int(np.isnan(corrected).sum()),
    }
    result["notes"] = list(notes or [])
    out.mkdir(parents=True, exist_ok=True)
    _write_tif(out / CORRECTED_FILE, corrected[None], pair.georef, ["corrected"])
    if result["displacement"]["model"] == "dense":
        flow = registration.displacement.field(shape)
        _write_tif(out / FLOW_FILE, flow, pair.georef, ["dy", "dx"])
    (out / DISPLACEMENT_FILE).write_text(json.dumps(result, indent=2) + "\n")
    return result


def _write_tif(
    path: Path, layers: np.ndarray, georef: Georef | None, names: list[str]
) -> None:
    """Write ``(bands, rows, cols)`` as a float GeoTIFF, NaN for no data."""
    profile = {
        "driver": "GTiff",
        "count": layers.shape[0],
        "height": layers.shape[1],
        "width": layers.shape[2],
        "dtype": "float32",
        "nodata": float("nan"),
        "compress": "deflate",
    }
    if georef is not None:
        profile.update(crs=georef.crs, transform=georef.transform)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", NotGeoreferencedWarning)
        with rasterio.open(path, "w", **profile) as dst:
            dst.write(layers.astype("float32"))
            for index, name in enumerate(names, 1):
                dst.set_band_description(index, name)

"""AROSICS global co-registration (``COREG``), on the pair's map grid.

AROSICS and the GDAL bindings it needs are an optional extra (``pip install -e
".[arosics]"``, see docs/running.md). This module imports them only when the
method runs, so the rest of the package works without them.
"""

import importlib.util
from dataclasses import dataclass
from typing import ClassVar

import numpy as np

from ..displacement import Translation
from ..georef import Georef
from .base import Estimate, GeoreferencedMethod, RegistrationFailure

# Modules AROSICS needs: itself, and GDAL's Python bindings, which pip cannot
# install without a system GDAL.
REQUIRED_MODULES = ("arosics", "osgeo")

# Marks no pixel as no-data. Simulated pairs have none, and AROSICS would
# otherwise guess a no-data value from the image corners.
NO_DATA = np.nan


def missing_modules() -> list[str]:
    """Name the modules AROSICS needs that are not installed.

    Returns:
        Missing module names, empty if AROSICS can run.
    """
    return [name for name in REQUIRED_MODULES if importlib.util.find_spec(name) is None]


@dataclass(frozen=True)
class Arosics(GeoreferencedMethod):
    """AROSICS ``COREG``: phase correlation in a matching window, in map units.

    AROSICS estimates one global translation. It matches a square window at the
    centre of the overlap, checks the integer peak and retries around it, then
    refines to sub-pixel precision and rates the result's reliability.

    Attributes:
        window: Side of the matching window, in pixels. AROSICS shrinks it to
            fit the pair, then to a power of two.
        max_shift: Largest shift component accepted, in pixels. Larger ones are
            reported by AROSICS as invalid, and here as a failure.
        max_iter: Attempts at finding a valid integer peak.
        min_reliability: Lowest reliability AROSICS may give the shift, in
            percent. Below it the method reports a failure.
    """

    window: int = 256
    max_shift: float = 5.0
    max_iter: int = 5
    min_reliability: float = 40.0

    # Modules the method runs on, imported before its memory footprint is read.
    runtime: ClassVar[tuple[str, ...]] = REQUIRED_MODULES

    def __post_init__(self) -> None:
        if self.window < 1:
            raise ValueError(f"window must be positive, got {self.window}")
        if self.max_shift <= 0:
            raise ValueError(f"max_shift must be positive, got {self.max_shift}")
        if self.max_iter < 1:
            raise ValueError(f"max_iter must be positive, got {self.max_iter}")
        if not 0 <= self.min_reliability <= 100:
            raise ValueError(
                f"min_reliability must be in [0, 100], got {self.min_reliability}"
            )

    def __call__(
        self, reference: np.ndarray, moving: np.ndarray, georef: Georef | None
    ) -> Estimate:
        """Estimate the translation of a georeferenced pair.

        Args:
            reference: Reference image.
            moving: Moving image, same shape as ``reference``.
            georef: Map grid of both images.

        Returns:
            The translation, with AROSICS' reliability (percent) and the side of
            the matching window it used as diagnostics.

        Raises:
            ValueError: If the pair has no map grid.
            RegistrationFailure: If AROSICS finds no valid match, or rates the
                one it finds below ``min_reliability``.
        """
        if georef is None:
            raise ValueError("AROSICS needs a georeferenced pair")
        from arosics import COREG
        from geoarray import GeoArray

        wkt = georef.crs.to_wkt()
        images = [
            GeoArray(image, georef.geotransform, wkt, nodata=NO_DATA)
            for image in (reference, moving)
        ]
        coreg = COREG(
            *images,
            ws=(self.window, self.window),
            max_shift=self.max_shift,
            max_iter=self.max_iter,
            nodata=(NO_DATA, NO_DATA),
            CPUs=1,
            progress=False,
            q=True,
            # Errors are collected in coreg.tracked_errors instead of raised.
            ignore_errors=True,
        )
        coreg.calculate_spatial_shifts()

        diagnostics = {}
        if coreg.matchWin is not None:
            # AROSICS correlates the largest power-of-two square that fits in the
            # matching window it cut, so that is the window it actually used.
            fft_window = COREG._shrink_winsize_to_binarySize(coreg.matchWin.shape)
            if fft_window:
                diagnostics["window"] = min(fft_window)
        if not coreg.success:
            reasons = [str(error) for error in coreg.tracked_errors]
            raise RegistrationFailure(
                "; ".join(reasons) or "no valid matching window", diagnostics
            )
        # AROSICS rates a shift only when it is not exactly zero.
        if coreg.shift_reliability is not None:
            diagnostics["reliability"] = float(coreg.shift_reliability)
            if coreg.shift_reliability < self.min_reliability:
                raise RegistrationFailure(
                    f"reliability {coreg.shift_reliability:.2f} %, "
                    f"need {self.min_reliability:g} %",
                    diagnostics,
                )
        return Estimate(
            to_displacement(coreg.x_shift_map, coreg.y_shift_map, georef),
            diagnostics,
        )


def to_displacement(
    x_shift_map: float, y_shift_map: float, georef: Georef
) -> Translation:
    """Convert AROSICS' map shift into a displacement on the reference grid.

    AROSICS reports the correction to apply to the moving image's origin, in
    map units: the moving image lines up with the reference once its grid moves
    by ``(x_shift_map, y_shift_map)``. Content displaced by ``d`` pixels is
    corrected by moving the grid by ``-d`` pixels, so ``d`` is minus the
    correction, brought back to pixels by the inverse of the grid's linear part.
    Going through map units, rather than AROSICS' own pixel shift, keeps the
    conversion right on any grid orientation.

    Args:
        x_shift_map: Correction of the origin's easting, in map units.
        y_shift_map: Correction of the origin's northing, in map units.
        georef: Grid the pair sits on.

    Returns:
        The displacement, in pixels.
    """
    t = georef.transform
    linear = np.array([[t.a, t.b], [t.d, t.e]])
    col, row = np.linalg.solve(linear, [x_shift_map, y_shift_map])
    return Translation(dx=-float(col), dy=-float(row))

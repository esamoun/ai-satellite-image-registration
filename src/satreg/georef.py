"""Where an image's pixels sit on the ground: a CRS and a pixel-to-map transform.

Most methods only see pixels. Some, like AROSICS, work in map coordinates and
need to know the grid. A simulated pair keeps the grid of the chip it was cut
from, offset by whole pixels, and both of its images share it: the displacement
is content moving on one grid, as between two orthorectified acquisitions.
"""

from dataclasses import dataclass

from rasterio import Affine
from rasterio.crs import CRS


@dataclass(frozen=True)
class Georef:
    """A map grid.

    Attributes:
        crs: Coordinate reference system of the map coordinates.
        transform: Maps ``(col, row)`` of a pixel corner to map ``(x, y)``, as in
            rasterio: ``(0, 0)`` is the top-left corner of the top-left pixel.
    """

    crs: CRS
    transform: Affine

    def window(self, row: int, col: int) -> "Georef":
        """The grid of a window whose top-left pixel is ``(row, col)`` here.

        Args:
            row: Row of the window's top-left pixel.
            col: Column of the window's top-left pixel.

        Returns:
            The same grid, with its origin moved to that pixel.
        """
        return Georef(self.crs, self.transform @ Affine.translation(col, row))

    @property
    def geotransform(self) -> tuple[float, float, float, float, float, float]:
        """The transform in GDAL's order: ``(x0, dx/dcol, dx/drow, y0, ...)``."""
        return self.transform.to_gdal()


# Grid given to the synthetic site, which has no place on the ground: 10 m pixels
# in UTM 31N, the zone of the Beauce, like a Sentinel-2 tile.
NOMINAL = Georef(
    CRS.from_epsg(32631), Affine(10.0, 0.0, 400_000.0, 0.0, -10.0, 5_400_000.0)
)

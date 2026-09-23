"""Displacements between a reference image and a moving image.

One convention holds across the package, for ground truth and estimates alike: a
displacement ``d`` at reference pixel ``p = (row, col)`` means the content at ``p``
in the reference is found at ``p + d`` in the moving image, i.e.
``moving(p + d) = reference(p)``. Components are ``(dy, dx)`` in pixels, rows
pointing down and columns pointing right.

Every displacement, whatever its model, can be evaluated as a field on the
reference grid. Metrics only ever see that field, so a translation, an affine
transform and a dense flow are scored the same way. See docs/decisions.md.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


class Displacement(ABC):
    """A displacement model that can be evaluated on a reference pixel grid."""

    @abstractmethod
    def field(self, shape: tuple[int, int]) -> np.ndarray:
        """Evaluate the displacement at every pixel of a reference grid.

        Args:
            shape: ``(rows, cols)`` of the reference image.

        Returns:
            Array of shape ``(2, rows, cols)``: ``dy`` then ``dx``, in pixels.
        """


@dataclass(frozen=True)
class Translation(Displacement):
    """The same shift at every pixel.

    Attributes:
        dx: Shift along columns, in pixels (positive to the right).
        dy: Shift along rows, in pixels (positive downwards).
    """

    dx: float
    dy: float

    def field(self, shape: tuple[int, int]) -> np.ndarray:
        """Evaluate the constant shift on a ``shape`` grid."""
        out = np.empty((2, *shape))
        out[0] = self.dy
        out[1] = self.dx
        return out


@dataclass(frozen=True)
class Affine(Displacement):
    """A displacement that varies linearly across the grid.

    Reference pixel ``p = (row, col)`` is found at ``matrix @ p + offset`` in the
    moving image, so the displacement is ``(matrix - I) @ p + offset``. Pixel
    coordinates are array indices: the centre of the top-left pixel is ``(0, 0)``.

    Attributes:
        matrix: Linear part, in ``(row, col)`` order: ``((yy, yx), (xy, xx))``.
        offset: ``(ty, tx)``, in pixels.
    """

    matrix: tuple[tuple[float, float], tuple[float, float]]
    offset: tuple[float, float]

    @classmethod
    def about(
        cls,
        centre: tuple[float, float],
        rotation_deg: float = 0.0,
        scale: float = 1.0,
        shear: float = 0.0,
        dx: float = 0.0,
        dy: float = 0.0,
    ) -> "Affine":
        """Build an affine displacement from physical parameters.

        The shear is applied first, then the scale, then the rotation, all about
        ``centre``, and the centre itself moves by ``(dx, dy)``.

        Args:
            centre: ``(row, col)`` the linear part is applied about.
            rotation_deg: Rotation in degrees, counter-clockwise as displayed
                (rows pointing down).
            scale: Isotropic scale factor, positive.
            shear: Horizontal shear: a row ``h`` px below the centre moves right by
                ``shear * h`` px.
            dx: Displacement of the centre along columns, in pixels.
            dy: Displacement of the centre along rows, in pixels.

        Returns:
            The affine displacement.

        Raises:
            ValueError: If ``scale`` is not positive.
        """
        if scale <= 0:
            raise ValueError(f"scale must be positive, got {scale}")
        theta = np.radians(rotation_deg)
        cos, sin = np.cos(theta), np.sin(theta)
        # In (x, y) = (col, row) with y down, [[cos, sin], [-sin, cos]] turns
        # counter-clockwise on screen.
        rotation = np.array([[cos, sin], [-sin, cos]])
        linear_xy = rotation @ (scale * np.array([[1.0, shear], [0.0, 1.0]]))
        matrix = linear_xy[::-1, ::-1]  # to (row, col) order
        c = np.asarray(centre, dtype=float)
        offset = c + (dy, dx) - matrix @ c
        return cls(
            matrix=(
                (float(matrix[0, 0]), float(matrix[0, 1])),
                (float(matrix[1, 0]), float(matrix[1, 1])),
            ),
            offset=(float(offset[0]), float(offset[1])),
        )

    def apply(self, points: np.ndarray) -> np.ndarray:
        """Map reference positions to their positions in the moving image.

        Args:
            points: Array of shape ``(2, ...)``: rows then columns.

        Returns:
            Array of the same shape: ``matrix @ p + offset`` for each point.
        """
        m = np.asarray(self.matrix)
        return np.tensordot(m, points, axes=1) + np.reshape(
            self.offset, (2,) + (1,) * (points.ndim - 1)
        )

    def field(self, shape: tuple[int, int]) -> np.ndarray:
        """Evaluate ``(matrix - I) @ p + offset`` on a ``shape`` grid."""
        grid = np.indices(shape, dtype=float)
        return self.apply(grid) - grid


@dataclass(frozen=True, eq=False, repr=False)
class Dense(Displacement):
    """A displacement given pixel by pixel, on one grid only.

    Attributes:
        values: Array of shape ``(2, rows, cols)``: ``dy`` then ``dx``, in pixels.
            A read-only float copy of the array it was built from.
    """

    values: np.ndarray

    def __post_init__(self) -> None:
        values = np.array(self.values, dtype=float)
        if values.ndim != 3 or values.shape[0] != 2:
            raise ValueError(
                f"a dense field has shape (2, rows, cols), got {values.shape}"
            )
        values.flags.writeable = False
        object.__setattr__(self, "values", values)

    @property
    def shape(self) -> tuple[int, int]:
        """``(rows, cols)`` of the grid the field is given on."""
        return self.values.shape[1:]

    def field(self, shape: tuple[int, int]) -> np.ndarray:
        """Return a copy of the field, which exists on its own grid only.

        Raises:
            ValueError: If ``shape`` is not the field's own grid.
        """
        if tuple(shape) != self.shape:
            raise ValueError(f"field is given on {self.shape}, not on {tuple(shape)}")
        return self.values.copy()

    def __repr__(self) -> str:
        # A summary, not the values: the repr goes to one cell of the per-pair
        # table.
        dy, dx = self.values.reshape(2, -1).mean(axis=1)
        return f"Dense(shape={self.shape}, mean_dx={dx:.6g}, mean_dy={dy:.6g})"

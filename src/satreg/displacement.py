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

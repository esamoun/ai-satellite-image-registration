"""What a registration method returns, and how it reports that it failed."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

import numpy as np

from ..displacement import Displacement
from ..georef import Georef


@dataclass(frozen=True)
class Estimate:
    """A displacement with the method's own diagnostics.

    Attributes:
        displacement: Estimated displacement.
        diagnostics: Name to value, e.g. ``{"inliers": 153}``.
    """

    displacement: Displacement
    diagnostics: Mapping[str, float] = field(default_factory=dict)


class RegistrationFailure(Exception):
    """A method's own verdict that it could not register a pair.

    Attributes:
        diagnostics: What the method saw before giving up, e.g. ``{"inliers": 4}``.
    """

    def __init__(
        self, message: str, diagnostics: Mapping[str, float] | None = None
    ) -> None:
        super().__init__(message)
        self.diagnostics = dict(diagnostics or {})


class GeoreferencedMethod(ABC):
    """A method that also needs the map grid the pair sits on."""

    @abstractmethod
    def __call__(
        self, reference: np.ndarray, moving: np.ndarray, georef: Georef | None
    ) -> Displacement | Estimate:
        """Estimate the displacement of a pair whose images share ``georef``.

        Args:
            reference: Reference image.
            moving: Moving image, same shape as ``reference``.
            georef: Map grid of both images, ``None`` if the pair has none.

        Returns:
            The estimated displacement, in pixels of the reference grid.
        """


Method = (
    Callable[[np.ndarray, np.ndarray], Displacement | Estimate] | GeoreferencedMethod
)
"""A method takes ``(reference, moving)``, and ``georef`` if it is a
``GeoreferencedMethod``, and returns the estimated displacement."""

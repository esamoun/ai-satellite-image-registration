"""What a registration method returns, and how it reports that it failed."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

import numpy as np

from ..displacement import Displacement


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


Method = Callable[[np.ndarray, np.ndarray], Displacement | Estimate]
"""A method takes ``(reference, moving)`` and returns the estimated displacement."""

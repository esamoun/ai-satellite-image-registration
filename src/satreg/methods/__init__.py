"""Registration methods, registered under stable names used in results tables."""

from collections.abc import Callable

import numpy as np

from ..displacement import Displacement
from .phase_correlation import phase_correlation

Method = Callable[[np.ndarray, np.ndarray], Displacement]
"""A method takes ``(reference, moving)`` and returns the estimated displacement."""

METHODS: dict[str, Method] = {
    "phase_correlation": phase_correlation,
}

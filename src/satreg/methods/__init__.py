"""Registration methods, registered under stable names used in results tables.

A method takes ``(reference, moving)`` and returns the estimated displacement,
bare or wrapped in an ``Estimate`` with diagnostics. A method that judges it
cannot register a pair raises ``RegistrationFailure``: the benchmark counts the
pair as failed and moves on. Method parameters are read from a TOML file.
"""

import tomllib
from pathlib import Path

from .base import Estimate, Method, RegistrationFailure
from .phase_correlation import phase_correlation
from .sift_ransac import SiftRansac

__all__ = ["METHODS", "Estimate", "Method", "RegistrationFailure", "load_methods"]

METHODS: dict[str, Method] = {
    "phase_correlation": phase_correlation,
    "sift_ransac": SiftRansac(),
}

# Methods whose parameters a configuration file can set, by the class that
# builds them from those parameters.
_CONFIGURABLE: dict[str, type] = {"sift_ransac": SiftRansac}


def load_methods(path: Path) -> dict[str, Method]:
    """Build every method with the parameters set in a configuration file.

    Args:
        path: TOML file with one ``[methods.<name>]`` table per configurable
            method. A method without a table keeps its default parameters.

    Returns:
        Method name to method, for every method of ``METHODS``.

    Raises:
        ValueError: If the file names an unknown or non-configurable method, or
            gives a method missing, unknown or invalid parameters.
    """
    with path.open("rb") as f:
        raw = tomllib.load(f).get("methods", {})
    unknown = sorted(set(raw) - set(_CONFIGURABLE))
    if unknown:
        raise ValueError(
            f"{path}: no configurable method {', '.join(unknown)} "
            f"(configurable: {', '.join(_CONFIGURABLE)})"
        )

    methods = dict(METHODS)
    for name, params in raw.items():
        try:
            methods[name] = _CONFIGURABLE[name](**params)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{path}: method {name}: {exc}") from exc
    return methods

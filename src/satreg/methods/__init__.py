"""Registration methods, registered under stable names used in results tables.

A method takes ``(reference, moving)`` and returns the estimated displacement,
bare or wrapped in an ``Estimate`` with diagnostics. A ``GeoreferencedMethod``
also takes the pair's map grid. A method that judges it cannot register a pair
raises ``RegistrationFailure``: the benchmark counts the pair as failed and
moves on. Method parameters are read from a TOML file, which can also declare
variants: a configurable method under a new name, with other parameters.
"""

import tomllib
from pathlib import Path

from . import arosics
from .arosics import Arosics
from .base import Estimate, GeoreferencedMethod, Method, RegistrationFailure
from .phase_correlation import PhaseCorrelation, phase_correlation
from .sift_ransac import SiftRansac

__all__ = [
    "METHODS",
    "Estimate",
    "GeoreferencedMethod",
    "Method",
    "RegistrationFailure",
    "load_methods",
    "missing_dependencies",
]

METHODS: dict[str, Method] = {
    "arosics": Arosics(),
    "phase_correlation": phase_correlation,
    "sift_ransac": SiftRansac(),
}

# Methods whose parameters a configuration file can set, by the class that
# builds them from those parameters.
_CONFIGURABLE: dict[str, type] = {
    "arosics": Arosics,
    "phase_correlation": PhaseCorrelation,
    "sift_ransac": SiftRansac,
}

# Key of a configuration table that makes it a variant of the method it names.
VARIANT_KEY = "method"

# Methods that need optional packages, by their class and the function naming
# the missing ones. Keyed by class so that variants inherit the requirement.
_OPTIONAL = {Arosics: arosics.missing_modules}


def missing_dependencies(method: Method) -> list[str]:
    """Name the optional packages a method needs that are not installed.

    Args:
        method: A method, built-in or variant.

    Returns:
        Missing module names, empty if the method can run.
    """
    for cls, check in _OPTIONAL.items():
        if isinstance(method, cls):
            return check()
    return []


def load_methods(path: Path) -> dict[str, Method]:
    """Build every method with the parameters set in a configuration file.

    Args:
        path: TOML file with one ``[methods.<name>]`` table per configurable
            method. A method without a table keeps its default parameters. A
            table with a ``method`` key declares a variant: a new method
            ``<name>``, built like the configurable method it names, with the
            table's other keys as parameters.

    Returns:
        Method name to method, for every method of ``METHODS`` and every
        variant, in that order.

    Raises:
        ValueError: If the file names an unknown or non-configurable method,
            declares a variant under a built-in name, or gives a method missing,
            unknown or invalid parameters.
    """
    with path.open("rb") as f:
        raw = tomllib.load(f).get("methods", {})

    methods = dict(METHODS)
    for name, table in raw.items():
        params = dict(table)
        base = params.pop(VARIANT_KEY, name)
        if base not in _CONFIGURABLE:
            raise ValueError(
                f"{path}: no configurable method {base} "
                f"(configurable: {', '.join(_CONFIGURABLE)})"
            )
        if base != name and name in METHODS:
            raise ValueError(f"{path}: variant {name} would replace a built-in method")
        try:
            methods[name] = _CONFIGURABLE[base](**params)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{path}: method {name}: {exc}") from exc
    return methods

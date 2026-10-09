"""Registration methods, registered under stable names used in results tables.

A method takes ``(reference, moving)`` and returns the estimated displacement,
bare or wrapped in an ``Estimate`` with diagnostics. A ``GeoreferencedMethod``
also takes the pair's map grid. A method that judges it cannot register a pair
raises ``RegistrationFailure``: the benchmark counts the pair as failed and
moves on. A method whose cost is not read the default way, such as one that
runs on a GPU, has a ``meter`` attribute (see ``satreg.compute``). Method
parameters are read from a TOML file, which can also declare variants: a
configurable method under a new name, with other parameters.
"""

import tomllib
from pathlib import Path

from ..compute import TRACEMALLOC, Meter
from . import arosics, deep, lightglue, raft_onnx, roma
from .arosics import Arosics
from .base import Estimate, GeoreferencedMethod, Method, RegistrationFailure
from .lightglue import LightGlue
from .phase_correlation import PhaseCorrelation, phase_correlation
from .raft import Raft
from .raft_onnx import RaftOnnx
from .roma import Roma
from .sift_ransac import SiftRansac

__all__ = [
    "METHODS",
    "Estimate",
    "GeoreferencedMethod",
    "Method",
    "RegistrationFailure",
    "cost_meter",
    "default_methods",
    "load_methods",
    "missing_dependencies",
]

METHODS: dict[str, Method] = {
    "arosics": Arosics(),
    "lightglue": LightGlue(),
    "phase_correlation": phase_correlation,
    "raft": Raft(),
    "roma": Roma(),
    "sift_ransac": SiftRansac(),
}

# Methods whose parameters a configuration file can set, by the class that
# builds them from those parameters. `raft_onnx` is not one of `METHODS`: it
# runs a file, and has none until a configuration names one.
_CONFIGURABLE: dict[str, type] = {
    "arosics": Arosics,
    "lightglue": LightGlue,
    "phase_correlation": PhaseCorrelation,
    "raft": Raft,
    "raft_onnx": RaftOnnx,
    "roma": Roma,
    "sift_ransac": SiftRansac,
}

# Built-in methods a benchmark runs only when they are named: RoMa takes about
# 3 s a call on the M1's CPU, over half an hour more in the default run.
OPT_IN = frozenset({"roma"})

# Key of a configuration table that makes it a variant of the method it names.
VARIANT_KEY = "method"

# Methods that need optional packages, by their class and the function naming
# the missing ones. Keyed by class so that variants inherit the requirement.
_OPTIONAL = {
    Arosics: arosics.missing_modules,
    LightGlue: lightglue.missing_modules,
    Raft: deep.missing_modules,
    RaftOnnx: raft_onnx.missing_modules,
    Roma: roma.missing_modules,
}


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


def default_methods() -> list[str]:
    """Name the methods a benchmark runs when none are named.

    Returns:
        The built-in methods whose dependencies are installed, less the opt-in
        ones, sorted.
    """
    return [
        name
        for name in sorted(METHODS)
        if name not in OPT_IN and not missing_dependencies(METHODS[name])
    ]


def cost_meter(method: Method) -> Meter:
    """The meter that reads a method's time and memory.

    Args:
        method: A method, built-in or variant.

    Returns:
        The method's own ``meter`` if it has one, ``tracemalloc`` otherwise.
    """
    return getattr(method, "meter", TRACEMALLOC)


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

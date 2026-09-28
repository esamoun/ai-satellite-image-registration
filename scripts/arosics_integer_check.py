"""Check (2026-09-28): is AROSICS off by ~0.2 px when the true shift is an integer?

Throwaway: on real triplets AROSICS reports shifts of 0.15-0.2 px per component
between dates that phase correlation puts within 0.03 px of each other. This
registers `mild` Beauce translation pairs whose true shift runs from 0 to 2.5 px
along both axes, and prints each method's mean end-point error per shift.
Findings are in docs/decisions.md. Needs the ``arosics`` extra and the Beauce chip.

    python scripts/arosics_integer_check.py
"""

import glob
from pathlib import Path

import numpy as np

from satreg.degrade import load_presets
from satreg.ingest import read_chip, read_georef
from satreg.methods import load_methods
from satreg.simulate import margin_for, simulate_translation

SHIFTS = [0.0, 0.1, 0.25, 0.5, 1.0, 1.25, 2.0, 2.5]
CORNERS = [(0, 0), (100, 150), (200, 60), (150, 200)]
METHODS = ["arosics", "phase_correlation"]


def main() -> None:
    """Print the mean end-point error of each method per true shift."""
    methods = load_methods(Path("configs/methods.toml"))
    mild = load_presets(Path("configs/degradations.toml"))["mild"]
    chip = Path(sorted(glob.glob("data/chips/beauce/B04_*.tif"))[0])
    image = read_chip(chip).astype(float)
    georef = read_georef(chip)
    margin = margin_for(5)
    rng = np.random.default_rng(1)
    print("true shift (px, both axes) | " + " | ".join(METHODS))
    for shift in SHIFTS:
        errors = {name: [] for name in METHODS}
        for top, left in CORNERS:
            size = 256 + 2 * margin
            source = image[top : top + size, left : left + size]
            pair = mild(simulate_translation(source, shift, shift, margin), rng)
            window = georef.window(top + margin, left + margin)
            for name in METHODS:
                method = methods[name]
                if name == "arosics":
                    estimate = method(pair.reference, pair.moving, window)
                else:
                    estimate = method(pair.reference, pair.moving)
                d = getattr(estimate, "displacement", estimate)
                errors[name].append(np.hypot(d.dx - shift, d.dy - shift))
        cells = " | ".join(f"{np.mean(errors[name]):.3f}" for name in METHODS)
        print(f"{shift} | {cells}")


if __name__ == "__main__":
    main()

"""Set the degradation presets next to real pairs.

Each real pair of a series is measured with ``appearance``, window by window, and
so is each preset applied to zero-shift windows of the same sites' anchor chips.
The rows are then grouped: one per pair of roles across sites, one per preset.
See docs/decisions.md.
"""

import dataclasses
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from .appearance import Appearance, appearance, windows
from .benchmark import _rng
from .degrade import Preset
from .displacement import Translation
from .real import ANCHOR, RealPair
from .simulate import SimulatedPair

# Side of the windows a pair is measured on, the benchmark's default pair size.
WINDOW_PX = 256

# Largest share of a window hidden on either date for it to be measured: the
# chip cloud limit, so a window is as clear as a chip.
MAX_WINDOW_CLOUD = 0.01


@dataclass(frozen=True)
class AppearanceRow:
    """How the moving image of one pair differs from its reference.

    Measurements are the medians over the pair's measured windows.

    Attributes:
        site: Site name.
        source: ``"real"`` or ``"preset"``.
        pair: ``"<role>-<role>"`` for a real pair, reference first, or the
            preset name.
        reference_date: Date of the reference, empty for a preset.
        moving_date: Date of the moving image, empty for a preset.
        gap_days: Days between the two dates, 0 for a preset.
        platforms: Satellites of the reference and moving dates, empty for a
            preset.
        cloud_fraction: Share of the chip hidden on either date; for a preset,
            the share of pixels its clouds cover at least half.
        n_windows: Windows measured.
        snr_reference_db: See ``Appearance``.
        snr_moving_db: See ``Appearance``.
        blur_px: See ``Appearance``.
        gain: See ``Appearance``.
        offset: See ``Appearance``.
        tone_bend: See ``Appearance``.
        correlation: See ``Appearance``.
    """

    site: str
    source: str
    pair: str
    reference_date: str
    moving_date: str
    gap_days: int
    platforms: str
    cloud_fraction: float
    n_windows: int
    snr_reference_db: float
    snr_moving_db: float
    blur_px: float
    gain: float
    offset: float
    tone_bend: float
    correlation: float


def measure(
    reference: np.ndarray, moving: np.ndarray, cloud: np.ndarray | None = None
) -> tuple[dict[str, float], int]:
    """Measure a pair on each clear window and take the median.

    Args:
        reference: 2-D reference image.
        moving: 2-D moving image, same shape.
        cloud: Pixels hidden on either image, or ``None`` if none are.

    Returns:
        The median of each ``Appearance`` field over the windows whose hidden
        share is at most ``MAX_WINDOW_CLOUD``, NaN if none is, and the number of
        such windows.
    """
    measured: list[Appearance] = []
    for rows, cols in windows(WINDOW_PX, reference.shape):
        if cloud is not None and cloud[rows, cols].mean() > MAX_WINDOW_CLOUD:
            continue
        measured.append(appearance(reference[rows, cols], moving[rows, cols]))
    names = [f.name for f in dataclasses.fields(Appearance)]
    medians = {
        name: float(np.median([getattr(a, name) for a in measured]))
        if measured
        else math.nan
        for name in names
    }
    return medians, len(measured)


def pair_label(roles: tuple[str, str]) -> str:
    """Name a pair by its roles, reference first."""
    return "-".join(roles)


def real_row(site: str, pair: RealPair) -> AppearanceRow:
    """Measure a real pair.

    Args:
        site: Site of the pair.
        pair: The pair; its hidden pixels are left out.

    Returns:
        The row.
    """
    medians, n = measure(
        pair.reference.astype(float), pair.moving.astype(float), pair.cloud
    )
    return AppearanceRow(
        site=site,
        source="real",
        pair=pair_label(pair.roles),
        reference_date=pair.dates[0].date().isoformat(),
        moving_date=pair.dates[1].date().isoformat(),
        gap_days=pair.gap_days,
        platforms="/".join(pair.platforms),
        cloud_fraction=pair.cloud_fraction,
        n_windows=n,
        **medians,
    )


def preset_row(
    site: str, image: np.ndarray, name: str, preset: Preset, seed: int = 0
) -> AppearanceRow:
    """Measure a preset applied to zero-shift windows of a site image.

    Each window is its own reference; the preset's radiometry, blur and noise
    make the moving image. Its clouds are left out, since windows under cloud
    are not measured on real pairs either: the row reports their nominal cover.

    Args:
        site: Site the image is from.
        image: 2-D chip, the anchor of the site's series.
        name: Preset name.
        preset: The preset.
        seed: Seed of the noise.

    Returns:
        The row.
    """
    clear = dataclasses.replace(preset, clouds=None)
    references, movings = [], []
    for i, (rows, cols) in enumerate(windows(WINDOW_PX, image.shape)):
        window = image[rows, cols].astype(float)
        pair = SimulatedPair(window, window.copy(), Translation(0.0, 0.0))
        pair = clear(pair, _rng(seed, site, name, i))
        references.append(pair.reference)
        movings.append(pair.moving)
    # Windows are laid back on the chip grid so ``measure`` cuts the same ones.
    reference = _tile(references, image.shape)
    moving = _tile(movings, image.shape)
    medians, n = measure(reference, moving)
    return AppearanceRow(
        site=site,
        source="preset",
        pair=name,
        reference_date="",
        moving_date="",
        gap_days=0,
        platforms="",
        cloud_fraction=preset.clouds.cover if preset.clouds else 0.0,
        n_windows=n,
        **medians,
    )


def _tile(parts: list[np.ndarray], shape: tuple[int, int]) -> np.ndarray:
    out = np.zeros(shape)
    for part, (rows, cols) in zip(parts, windows(WINDOW_PX, shape), strict=True):
        out[rows, cols] = part
    return out


@dataclass(frozen=True)
class SummaryRow:
    """Median and range across sites of one kind of pair.

    Each measurement is its distance from an identical pair, so a change and its
    reverse count the same: ``|blur|``, the contrast factor ``max(gain,
    1/gain)``, ``|offset|`` and the tone bend, 0 when unchanged. The SNR
    is the lower of the two images'.

    Attributes:
        source: ``"real"`` or ``"preset"``.
        pair: Role pair, roles in series order, or preset name.
        n_sites: Sites with a measured row.
        gap_days: Median days between the dates.
        values: Measurement name to ``(median, min, max)`` across sites.
    """

    source: str
    pair: str
    n_sites: int
    gap_days: float
    values: dict[str, tuple[float, float, float]]


SUMMARY_COLUMNS = {
    "snr_db": "SNR (dB)",
    "blur_px": "blur (px)",
    "contrast": "contrast ×",
    "offset": "offset (std)",
    "tone_bend": "tone bend",
    "correlation": "correlation",
    "cloud_fraction": "clouds",
}


def _distances(row: AppearanceRow) -> dict[str, float]:
    return {
        "snr_db": min(row.snr_reference_db, row.snr_moving_db),
        "blur_px": abs(row.blur_px),
        "contrast": max(row.gain, 1 / row.gain),
        "offset": abs(row.offset),
        "tone_bend": row.tone_bend,
        "correlation": row.correlation,
        "cloud_fraction": row.cloud_fraction,
    }


def summarize(
    rows: Sequence[AppearanceRow], role_order: Sequence[str]
) -> list[SummaryRow]:
    """Group rows by kind of pair across sites.

    Real pairs are grouped by their two roles whichever came first, since the
    earlier date is the reference and a role's date may fall before the anchor.

    Args:
        rows: Rows of ``real_row`` and ``preset_row``, of any sites.
        role_order: Roles in series order, ``ANCHOR`` first, to name groups.

    Returns:
        One row per preset, in order of appearance, then one per role pair, in
        series order.
    """
    rank = {role: i for i, role in enumerate(role_order)}
    groups: dict[tuple[str, str], list[AppearanceRow]] = {}
    for row in rows:
        key = row.pair
        if row.source == "real":
            key = pair_label(tuple(sorted(row.pair.split("-"), key=rank.__getitem__)))
        groups.setdefault((row.source, key), []).append(row)

    def order(item: tuple[tuple[str, str], list[AppearanceRow]]) -> tuple:
        (source, key), _ = item
        if source == "preset":
            return (0, 0, 0)
        first, second = key.split("-")
        return (1, rank[first], rank[second])

    summary = []
    for (source, key), group in sorted(groups.items(), key=order):
        measured = [_distances(r) for r in group if r.n_windows]
        values = {
            name: (
                (
                    float(np.median([m[name] for m in measured])),
                    float(min(m[name] for m in measured)),
                    float(max(m[name] for m in measured)),
                )
                if measured
                else (math.nan, math.nan, math.nan)
            )
            for name in SUMMARY_COLUMNS
        }
        summary.append(
            SummaryRow(
                source=source,
                pair=key,
                n_sites=len(measured),
                gap_days=float(np.median([r.gap_days for r in group])),
                values=values,
            )
        )
    return summary


def to_markdown(summary: Sequence[SummaryRow], nominal: Mapping[str, Preset]) -> str:
    """Render the summary as a markdown table.

    Args:
        summary: Rows of ``summarize``.
        nominal: Presets by name, whose nominal values are shown under their
            measured ones.

    Returns:
        The table, ending with a newline.
    """

    def cell(name: str, value: tuple[float, float, float]) -> str:
        median, lo, hi = value
        if math.isnan(median):
            return "n/a"
        if name == "cloud_fraction":
            return f"{100 * median:.1f} % [{100 * lo:.1f}, {100 * hi:.1f}]"
        digits = {"snr_db": 1, "tone_bend": 3}.get(name, 2)
        return f"{median:.{digits}f} [{lo:.{digits}f}, {hi:.{digits}f}]"

    header = (
        "| pairs | sites | gap (days) | "
        + " | ".join(SUMMARY_COLUMNS.values())
        + " |\n|---|---:|---:|"
        + "---:|" * len(SUMMARY_COLUMNS)
        + "\n"
    )
    body = ""
    for row in summary:
        label = f"preset `{row.pair}`" if row.source == "preset" else row.pair
        cells = " | ".join(cell(n, row.values[n]) for n in SUMMARY_COLUMNS)
        body += f"| {label} | {row.n_sites} | {row.gap_days:.0f} | {cells} |\n"
        if row.source == "preset" and row.pair in nominal:
            body += f"| ↳ nominal | | | {_nominal(nominal[row.pair])} |\n"
    return header + body


def _nominal(preset: Preset) -> str:
    r, c, b, n = preset.radiometry, preset.clouds, preset.blur, preset.noise
    values = {
        "snr_db": f"{n.snr_db:g} (added)" if n else "",
        "blur_px": f"{b.sigma:g}" if b else "0",
        "contrast": f"{max(r.gain, 1 / r.gain):.2f}" if r else "1",
        "offset": f"{abs(r.offset):g}" if r else "0",
        "tone_bend": f"gamma {r.gamma:g}" if r else "0",
        "correlation": "",
        "cloud_fraction": f"{100 * c.cover:g} %" if c else "0 %",
    }
    return " | ".join(values[name] for name in SUMMARY_COLUMNS)


def role_order(dates: Sequence[str]) -> list[str]:
    """Roles of a series in order, the anchor first."""
    return [ANCHOR, *dates]

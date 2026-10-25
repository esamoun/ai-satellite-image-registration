"""The README's flicker GIF (2026-10-25): one demo pair, before and after.

Two panels side by side, each switching between the reference and a second
image. On the left the second image is the moving image as it is: the pair
jumps, which is the misalignment a change detector would flag. On the right it
is the moving image corrected by phase correlation with a Hann window: the pair
holds still. Every pixel and figure is read from the files `satreg demo` wrote
to `docs/demo/` for Beauce, `clean`; nothing is computed here.

    python scripts/readme_flicker.py
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DEMO = Path("docs/demo/beauce/clean")
OUT = Path("docs/readme/flicker-beauce.gif")
METHOD = "phase_correlation_hann"
SCALE = 2
GAP = 16
STRIP = 56
FRAME_MS = 700


def panel(image: Image.Image, title: str, subtitle: str) -> Image.Image:
    """One image enlarged, with two lines of text above it.

    Args:
        image: A grayscale demo image.
        title: The first line.
        subtitle: The second line.

    Returns:
        The panel, in grayscale.
    """
    big = image.resize((image.width * SCALE, image.height * SCALE), Image.NEAREST)
    out = Image.new("L", (big.width, big.height + STRIP), 255)
    out.paste(big, (0, STRIP))
    draw = ImageDraw.Draw(out)
    draw.text((0, 6), title, fill=0, font=ImageFont.load_default(size=20))
    draw.text((0, 32), subtitle, fill=80, font=ImageFont.load_default(size=16))
    return out


def frame(left: Image.Image, right: Image.Image) -> Image.Image:
    """Two panels side by side on white.

    Args:
        left: The panel without registration.
        right: The panel after registration.

    Returns:
        One frame of the GIF.
    """
    out = Image.new("L", (left.width + GAP + right.width, left.height), 255)
    out.paste(left, (0, 0))
    out.paste(right, (left.width + GAP, 0))
    return out


def main() -> None:
    """Write the GIF from the Beauce `clean` demo pair."""
    pair = json.loads((DEMO / "pair.json").read_text())
    none, method = pair["methods"]["none"], pair["methods"][METHOD]
    reference = Image.open(DEMO / "reference.png").convert("L")
    moving = Image.open(DEMO / "moving.png").convert("L")
    corrected = Image.open(DEMO / method["corrected"]).convert("L")

    left = ("Not registered", f"{none['error_px']:.2f} px off")
    right = ("Phase correlation, Hann window", f"{method['error_px']:.4f} px off")
    frames = [
        frame(panel(reference, *left), panel(reference, *right)),
        frame(panel(moving, *left), panel(corrected, *right)),
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        OUT, save_all=True, append_images=frames[1:], duration=FRAME_MS, loop=0
    )
    print(f"written {OUT}: {frames[0].width} x {frames[0].height} px")


if __name__ == "__main__":
    main()

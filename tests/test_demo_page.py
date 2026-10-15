import json
import re
from pathlib import Path

import pytest
import rasterio

ROOT = Path(__file__).parents[1]
PAGE = ROOT / "docs"
SOURCES = ["index.html", "demo.css", "demo.js"]
REPOSITORY = "https://github.com/esamoun/ai-satellite-image-registration"
TYPEFACE = "fonts/SchibstedGrotesk-wght.woff2"
# The one address the page's code holds without ever fetching it: it names the
# SVG format.
NAMESPACE = "http://www.w3.org/2000/svg"
ADDRESS = re.compile(r"""(?:https?:)?//[\w.-]+\.\w+[^\s"'<>)]*""")


def manifest():
    return json.loads((PAGE / "demo" / "manifest.json").read_text())


def test_github_pages_serves_the_folder_as_it_is():
    assert (PAGE / ".nojekyll").is_file()


def test_the_page_s_style_script_and_typeface_are_beside_it():
    page = (PAGE / "index.html").read_text()
    loaded = re.findall(r'<(?:link|script|img)\b[^>]*?(?:href|src)="([^"]+)"', page)
    assert sorted(loaded) == ["data:,", "demo.css", "demo.js", TYPEFACE]
    for name in ("demo.css", "demo.js", TYPEFACE):
        assert (PAGE / name).is_file()


def test_the_typeface_is_read_from_the_page_s_folder_with_its_licence():
    style = (PAGE / "demo.css").read_text()
    assert re.findall(r"url\(([^)]+)\)", style) == [f'"{TYPEFACE}"']
    assert "SIL Open Font License" in (PAGE / "fonts" / "OFL.txt").read_text()


@pytest.mark.parametrize("name", SOURCES)
def test_the_page_asks_nothing_of_another_host(name):
    source = (PAGE / name).read_text()
    addresses = set(ADDRESS.findall(source))
    if name == "index.html":
        links = set(re.findall(r'<a href="([^"]+)"', source))
        elsewhere = {link for link in links if ADDRESS.match(link)}
        assert addresses == elsewhere
        assert all(link.startswith(REPOSITORY) for link in elsewhere)
        # The other links stay in the page's folder.
        for link in links - elsewhere:
            assert (PAGE / link).is_file(), link
    else:
        assert addresses <= {NAMESPACE}
    assert "@import" not in source


@pytest.mark.parametrize("name", ["curve-points.csv", "curve-references.csv"])
def test_the_curve_files_the_page_reads_are_in_the_manifest(name):
    script = (PAGE / "demo.js").read_text()
    assert f"curve/{name}" in manifest()["curve"]
    assert name in script


def test_the_page_names_every_method_site_and_preset_of_the_demo():
    script = (PAGE / "demo.js").read_text()
    shown = manifest()
    names = [*shown["methods"], *shown["presets"]]
    names += [site["name"] for site in shown["sites"]]
    for name in names:
        assert re.search(rf"^\s+{name}: ", script, re.MULTILINE), name


def test_the_page_s_metres_are_the_pixel_size_of_the_demo_windows():
    # The page says each distance in metres too: a pixel is PIXEL_M on the ground.
    script = (PAGE / "demo.js").read_text()
    said = re.search(r"const PIXEL_M = (\d+);", script)
    assert said
    examples = json.loads((ROOT / "examples" / "manifest.json").read_text())
    for site in manifest()["sites"]:
        same = [
            pair
            for pair in examples["pairs"]
            if pair["site"] == site["name"]
            and pair["scene"] == site["scene"]
            and pair["window"] == site["window"]
        ]
        assert same, site["name"]
        for pair in same:
            with rasterio.open(ROOT / "examples" / pair["reference"]) as image:
                assert image.res == (float(said[1]), float(said[1]))

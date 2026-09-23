import datetime as dt
from pathlib import Path

import pytest

from satreg.sites import DEFAULT_BAND, load_sites

CATALOGUE = """
[stac]
url = "https://stac.example"
collection = "sentinel-2-c1-l2a"
"""


def write(tmp_path, text):
    path = tmp_path / "sites.toml"
    path.write_text(CATALOGUE + text)
    return path


def site_table(**overrides):
    fields = {
        "lon": "1.6",
        "lat": "48.2",
        "chip_px": "512",
        "start": "2025-04-01",
        "end": "2025-09-30",
        "max_cloud": "5.0",
        **overrides,
    }
    return "[sites.beauce]\n" + "".join(f"{k} = {v}\n" for k, v in fields.items())


def test_the_committed_configuration_declares_beauce():
    config = load_sites(Path(__file__).parents[1] / "configs" / "sites.toml")

    assert "beauce" in config.sites
    assert config.sites["beauce"].band == "B04"
    assert config.catalogue.collection == "sentinel-2-c1-l2a"


def test_sites_are_read_from_the_file_with_a_default_band(tmp_path):
    config = load_sites(write(tmp_path, site_table()))

    site = config.sites["beauce"]
    assert config.catalogue.url == "https://stac.example"
    assert (site.name, site.lon, site.lat, site.chip_px) == ("beauce", 1.6, 48.2, 512)
    assert site.start == dt.date(2025, 4, 1) and site.end == dt.date(2025, 9, 30)
    assert site.max_cloud == 5.0
    assert site.band == DEFAULT_BAND == "B04"


def test_the_band_is_configurable(tmp_path):
    config = load_sites(write(tmp_path, site_table(band='"B08"')))

    assert config.sites["beauce"].band == "B08"


@pytest.mark.parametrize(
    "overrides",
    [
        {"lat": "148.2"},
        {"chip_px": "0"},
        {"start": "2025-10-01"},
        {"max_cloud": "120.0"},
        {"start": '"2025-04-01"'},
        {"colour": '"red"'},
    ],
)
def test_invalid_sites_are_rejected(tmp_path, overrides):
    with pytest.raises(ValueError, match="beauce"):
        load_sites(write(tmp_path, site_table(**overrides)))


def test_a_file_without_catalogue_is_rejected(tmp_path):
    path = tmp_path / "sites.toml"
    path.write_text(site_table())

    with pytest.raises(ValueError, match=r"\[stac\]"):
        load_sites(path)

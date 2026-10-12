import json
import math
from pathlib import Path

import cv2
import numpy as np
import pytest
import rasterio
from test_ingest import CENTRE, site_at, write_cog

from satreg import cli, demo, falsechange, register
from satreg.benchmark import BenchmarkConfig, max_reach
from satreg.cli import main
from satreg.cycle import lands_inside
from satreg.degrade import load_presets
from satreg.displacement import Dense, Translation
from satreg.georef import NOMINAL
from satreg.ingest import cache_path
from satreg.methods import deep, load_methods
from satreg.methods.base import RegistrationFailure
from satreg.methods.raft import Raft
from satreg.sites import load_sites
from satreg.texture import fractal_texture

ROOT = Path(__file__).parents[1]
CONFIGS = ROOT / "configs"
PUBLISHED_CURVE = ROOT / "docs" / "results" / "n3" / "final"
OPTIONS = [
    "--degradations-config",
    str(CONFIGS / "degradations.toml"),
    "--methods-config",
    str(CONFIGS / "methods.toml"),
    "--curve",
    str(PUBLISHED_CURVE),
]
CONFIG = BenchmarkConfig()
# The benchmark's chips are all of this shape, and a pair's draw reads nothing
# else of its site image.
CHIP_SHAPE = (1024, 1024)
SCENE = "S2B_T31UDP_20250619T105619_L2A"
ACQUIRED = "2025-06-19T10:56:19Z"


def _skip_reason() -> str | None:
    if missing := deep.missing_modules():
        return f"needs the dl extra ({', '.join(missing)} missing): make install-dl"
    pretrained = deep.weights_file(Raft().weights())
    if not pretrained.exists():
        return f"needs RAFT's pretrained weights at {pretrained}: make install-dl"
    if not register._cached("raft_large_ft"):
        return "needs the released weights raft_large_ft in the cache"
    return None


# The test that runs the networks. The conftest refuses network access, so both
# sets of weights must already be in their caches.
needs_raft = pytest.mark.skipif(_skip_reason() is not None, reason=_skip_reason() or "")


def nothing_found(reference, moving):
    return Dense(np.zeros((2, *reference.shape)))


def gives_up(reference, moving):
    raise RegistrationFailure("3 inliers, need 10", {"inliers": 3})


def stand_ins(args):
    """The demo's four methods where PyTorch is absent.

    The classic ones are the configured ones. In place of the two RAFT, one
    stand-in answers that nothing moved and the other gives up.
    """
    configured = load_methods(CONFIGS / "methods.toml")
    return {
        "phase_correlation_hann": configured["phase_correlation_hann"],
        "sift_ransac": configured["sift_ransac"],
        "raft": nothing_found,
        "raft_ft": gives_up,
    }


def show(out, examples, *options):
    main(["demo", *options, "--out", str(out), "--examples", str(examples), *OPTIONS])


def files_of(directory):
    """Every file under a directory, by its path within it."""
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def keys_of(value):
    """Every key of a JSON value, at any depth."""
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from keys_of(item)
    elif isinstance(value, list):
        for item in value:
            yield from keys_of(item)


@pytest.fixture(scope="module")
def shown(tmp_path_factory):
    """The demo of the synthetic site, written once with the stand-ins."""
    root = tmp_path_factory.mktemp("demo")
    with pytest.MonkeyPatch.context() as patched:
        patched.setattr(cli, "configured_methods", stand_ins)
        show(root / "demo", root / "examples", "--sites", "synthetic")
    return root


@pytest.fixture
def synthetic():
    return demo.Source("synthetic", fractal_texture(1024, seed=CONFIG.seed), NOMINAL)


@pytest.fixture
def presets():
    return load_presets(CONFIGS / "degradations.toml")


def _configured(tmp_path, extra=""):
    """Configure a seen site with its chip in the cache, and a held-out one."""
    site = site_at(*CENTRE, chip_px=512)
    config = tmp_path / "sites.toml"
    config.write_text(
        '[stac]\nurl = "https://stac.example"\ncollection = "sentinel-2-c1-l2a"\n'
        f"[sites.beauce]\nlon = {site.lon}\nlat = {site.lat}\nchip_px = 512\n"
        "start = 2025-04-01\nend = 2025-09-30\nmax_cloud = 5.0\n" + extra
    )
    chip = cache_path(site, load_sites(config).catalogue, tmp_path / "data")
    chip.parent.mkdir(parents=True)
    texture = np.round(2000 + 1000 * fractal_texture(512, seed=3)).astype(np.uint16)
    write_cog(chip, texture)
    with rasterio.open(chip, "r+") as dst:
        dst.update_tags(item_id=SCENE, datetime=ACQUIRED)
    return chip, ["--sites-config", str(config), "--data-dir", str(tmp_path / "data")]


# No chip of it is in the cache: reading it would need the network.
HELD_OUT = (
    "[sites.alps]\nlon = 7.0\nlat = 45.9\nchip_px = 512\n"
    "start = 2025-04-01\nend = 2025-09-30\nmax_cloud = 5.0\nheld_out = true\n"
)


@pytest.mark.parametrize(
    ("site", "index", "shift"),
    [("beauce", 0, 4.07), ("toulouse", 0, 3.12), ("vosges", 1, 2.18)]
    + [("marseille", 0, 3.86)],
)
def test_the_rule_picks_each_seen_site_s_pair_on_the_simulator_s_draw(
    site, index, shift
):
    # No method is given: the rule has none to run.
    image = np.zeros(CHIP_SHAPE)

    picked = demo.pick(site, image, CONFIG)

    assert picked == index
    assert demo.true_shift(site, image, CONFIG, picked) == pytest.approx(
        shift, abs=0.005
    )


def test_the_first_pair_of_the_vosges_moves_too_little_to_be_picked():
    moved = demo.true_shift("vosges", np.zeros(CHIP_SHAPE), CONFIG, 0)

    assert moved == pytest.approx(0.08, abs=0.005)
    assert moved < demo.MIN_SHIFT_PX


def test_the_rule_passes_over_every_pair_under_the_threshold():
    image = np.zeros(CHIP_SHAPE)

    for site in ("beauce", "toulouse", "vosges", "marseille", "synthetic"):
        picked = demo.pick(site, image, CONFIG)
        before = [demo.true_shift(site, image, CONFIG, i) for i in range(picked)]
        assert all(moved <= demo.MIN_SHIFT_PX for moved in before)


def test_a_site_none_of_whose_pairs_moves_enough_has_no_demo_pair():
    still = BenchmarkConfig(max_shift=1.0)

    with pytest.raises(ValueError, match="none of the 20 pairs of beauce moves"):
        demo.pick("beauce", np.zeros(CHIP_SHAPE), still)


def test_the_slider_s_pair_and_the_arrows_share_window_and_central_shift(
    synthetic, presets
):
    index = demo.pick(synthetic.name, synthetic.image, CONFIG)

    for preset in demo.PRESETS:
        pairs = demo.draw(synthetic, CONFIG, index, preset, presets[preset])
        slider, arrows = pairs[demo.SLIDER], pairs[demo.ARROWS]

        np.testing.assert_array_equal(slider.reference, arrows.reference)
        assert demo.window_of(synthetic, slider) == demo.window_of(synthetic, arrows)
        # At the centre the dense pair adds its local field only.
        centre = arrows.truth.field(slider.reference.shape)[:, 128, 128]
        gap = math.hypot(centre[0] - slider.truth.dy, centre[1] - slider.truth.dx)
        assert gap < CONFIG.max_local_shift + 0.05


def test_the_window_is_where_the_pair_was_cut_from_its_site_image(synthetic, presets):
    pair = demo.draw(synthetic, CONFIG, 0, "clean", presets["clean"])[demo.SLIDER]

    window = demo.window_of(synthetic, pair)

    rows = slice(window["row"], window["row"] + window["size"])
    cols = slice(window["col"], window["col"] + window["size"])
    np.testing.assert_allclose(pair.reference, synthetic.image[rows, cols])


def test_no_registration_is_scored_and_is_no_method_s_failure(synthetic, presets):
    pair = demo.draw(synthetic, CONFIG, 0, "clean", presets["clean"])[demo.SLIDER]

    outcome = demo.run(None, pair, CONFIG)

    assert outcome.displacement == Translation(0.0, 0.0)
    assert outcome.error_px == pytest.approx(
        math.hypot(pair.truth.dx, pair.truth.dy), abs=1e-9
    )
    assert not outcome.failure
    assert outcome.reason == ""


def test_a_method_that_gives_up_is_kept_as_a_failure_with_its_reason(
    synthetic, presets
):
    pair = demo.draw(synthetic, CONFIG, 0, "clean", presets["clean"])[demo.SLIDER]

    outcome = demo.run(gives_up, pair, CONFIG)

    assert outcome.displacement is None
    assert math.isnan(outcome.error_px)
    assert outcome.failure
    assert outcome.reason == "RegistrationFailure: 3 inliers, need 10"


def test_an_estimate_over_the_failure_threshold_is_kept_as_a_failure(
    synthetic, presets
):
    pair = demo.draw(synthetic, CONFIG, 0, "clean", presets["clean"])[demo.SLIDER]

    outcome = demo.run(nothing_found, pair, CONFIG)

    assert isinstance(outcome.displacement, Dense)
    assert outcome.error_px > CONFIG.failure_threshold
    assert outcome.failure
    assert outcome.reason == "mean error over the failure threshold of 1 px"


def test_an_estimate_that_is_not_finite_is_a_failure_without_an_estimate(
    synthetic, presets
):
    pair = demo.draw(synthetic, CONFIG, 0, "clean", presets["clean"])[demo.SLIDER]

    outcome = demo.run(
        lambda reference, moving: Translation(math.nan, 0.0), pair, CONFIG
    )

    assert outcome.displacement is None
    assert outcome.failure
    assert outcome.reason == "non-finite displacement"


def test_changed_pixels_are_counted_as_the_false_change_experiment_counts_them(
    synthetic, presets
):
    pair = demo.draw(synthetic, CONFIG, 0, "hard", presets["hard"])[demo.SLIDER]
    shape = pair.reference.shape
    # The experiment's own steps, as falsechange.run_simulated takes them.
    reference_clear, moving_clear = falsechange._clear_of_cloud(pair)
    mask = pair.valid & falsechange.interior(shape) & reference_clear
    gain, offset = falsechange.match_level(
        pair.reference, pair.moving, mask, falsechange.interior(shape) & moving_clear
    )
    moving = gain * pair.moving + offset
    limit = falsechange.threshold(pair.reference, moving)
    resampler = falsechange.Resampler(moving, max_reach(CONFIG))

    detector = demo.Detector.of(pair, CONFIG)

    for displacement in (Translation(0.0, 0.0), pair.truth):
        _, counted, flagged = detector.look(displacement)
        expected = falsechange._rate(
            pair.reference, resampler, mask, limit, displacement
        )
        assert flagged.sum() / counted.sum() == pytest.approx(expected, abs=1e-12)
        assert not (flagged & ~counted).any()
    # Clouds hide ground: those pixels are not counted.
    assert counted.sum() < falsechange.interior(shape).sum()


def test_a_correction_shows_no_data_where_it_reads_off_the_moving_image(
    synthetic, presets
):
    pair = demo.draw(synthetic, CONFIG, 0, "clean", presets["clean"])[demo.SLIDER]
    far = Translation(dx=40.0, dy=0.0)

    corrected, counted, _ = demo.Detector.of(pair, CONFIG).look(far)

    inside = lands_inside(far, pair.reference.shape)
    assert np.isnan(corrected[~inside]).all()
    assert np.isfinite(corrected[inside]).all()
    assert not counted[~inside].any()
    low, high = demo.display_range(pair.reference)
    assert (demo.as_bytes(corrected, low, high)[~inside] == 0).all()


def test_the_changed_picture_marks_changed_pixels_and_veils_those_not_counted():
    counted = np.array([[True, True, False]])
    flagged = np.array([[True, False, False]])

    picture = demo.changed_picture(counted, flagged)

    assert tuple(picture[0, 0]) == demo.CHANGED_RGBA
    assert tuple(picture[0, 1]) == (0, 0, 0, 0)
    assert tuple(picture[0, 2]) == demo.NOT_COUNTED_RGBA


def test_the_command_writes_each_preset_s_images_and_figures(shown):
    manifest = json.loads((shown / "demo" / "manifest.json").read_text())

    assert manifest["methods"] == ["none", *demo.METHODS]
    assert manifest["presets"] == ["clean", "hard"]
    assert manifest["rule"]["min_shift_px"] == 2.0
    assert manifest["rule"]["seed"] == 0
    assert [site["name"] for site in manifest["sites"]] == ["synthetic"]
    assert manifest["sites"][0]["pair"] == 0
    assert manifest["sites"][0]["shift"]["px"] == pytest.approx(3.478, abs=0.001)
    for preset in manifest["presets"]:
        where = shown / "demo" / "synthetic" / preset
        slider = json.loads((where / manifest["files"]["slider"]).read_text())
        arrows = json.loads((where / manifest["files"]["arrows"]).read_text())
        assert slider["scenario"] == "translation"
        assert arrows["scenario"] == "dense"
        assert list(slider["methods"]) == sorted(manifest["methods"])
        assert list(arrows["methods"]) == sorted(manifest["methods"])
        for name in ("reference", "moving"):
            image = cv2.imread(str(where / slider["images"][name]), -1)
            assert image.shape == (256, 256)
            assert image.dtype == np.uint8


def test_the_slider_holds_each_method_s_estimate_error_and_changed_pixels(shown):
    where = shown / "demo" / "synthetic" / "clean"
    slider = json.loads((where / "pair.json").read_text())
    truth = slider["truth"]

    assert truth["model"] == "translation"
    # Each figure is rounded to a ten-thousandth of a pixel.
    shift = math.hypot(truth["dx"], truth["dy"])
    assert truth["shift_px"] == pytest.approx(shift, abs=2e-4)
    without = slider["methods"]["none"]
    assert without["estimate"] == {"model": "translation", "dx": 0.0, "dy": 0.0}
    assert without["error_px"] == pytest.approx(truth["shift_px"], abs=1e-3)
    assert without["corrected"] == "moving.png"
    assert not without["failure"]
    found = slider["methods"]["phase_correlation_hann"]
    assert found["estimate"]["dx"] == pytest.approx(truth["dx"], abs=0.05)
    assert found["estimate"]["dy"] == pytest.approx(truth["dy"], abs=0.05)
    assert found["error_px"] < 0.05
    assert not found["failure"]
    # Registered, a pair of one image flags next to nothing: unregistered, a lot.
    assert found["changed_share"] < 0.01 < without["changed_share"]
    for entry in (without, found):
        picture = cv2.imread(str(where / entry["changed"]), cv2.IMREAD_UNCHANGED)
        assert picture.shape == (256, 256, 4)
        assert (picture[..., 3] == 255).sum() == entry["changed_px"]
        share = entry["changed_px"] / entry["counted_px"]
        assert entry["changed_share"] == pytest.approx(share, abs=1e-4)
    assert (where / found["corrected"]).name == "corrected-phase_correlation_hann.png"


def test_a_failure_is_kept_and_shown_as_a_failure(shown):
    where = shown / "demo" / "synthetic" / "clean"
    for name in ("pair.json", "arrows.json"):
        methods = json.loads((where / name).read_text())["methods"]

        over = methods["raft"]
        assert over["failure"]
        assert over["reason"] == "mean error over the failure threshold of 1 px"
        assert over["error_px"] > 1.0
        assert over["estimate"]["model"] == "dense"
        gave_up = methods["raft_ft"]
        assert gave_up["failure"]
        assert gave_up["reason"] == "RegistrationFailure: 3 inliers, need 10"
        assert gave_up["estimate"] is None
        assert gave_up["error_px"] is None
    slider = json.loads((where / "pair.json").read_text())["methods"]
    # A wrong estimate still has its picture: the page shows what it does.
    assert (where / slider["raft"]["corrected"]).exists()
    assert slider["raft_ft"]["corrected"] is None
    assert slider["raft_ft"]["changed"] is None
    assert slider["raft_ft"]["changed_px"] is None
    assert not (where / "corrected-raft_ft.png").exists()
    assert not (where / "changed-raft_ft.png").exists()


def test_the_arrows_hold_the_true_field_each_estimate_and_their_difference(shown):
    where = shown / "demo" / "synthetic" / "hard"
    arrows = json.loads((where / "arrows.json").read_text())
    grid = arrows["grid"]

    assert grid["step_px"] == 16
    assert grid["rows"] == grid["cols"] == list(range(8, 256, 16))
    truth = np.array([arrows["truth"]["dy"], arrows["truth"]["dx"]])
    assert truth.shape == (2, 16, 16)
    assert np.array(arrows["observed"]).shape == (16, 16)
    # A field that varies from pixel to pixel, not one shift.
    assert truth[0].std() > 0.01
    for name in ("none", "phase_correlation_hann", "raft"):
        entry = arrows["methods"][name]
        estimate = np.array([entry["dy"], entry["dx"]])
        difference = np.array([entry["error_dy"], entry["error_dx"]])
        np.testing.assert_allclose(difference, estimate - truth, atol=2e-4)
    assert arrows["methods"]["raft_ft"]["dy"] is None
    assert arrows["methods"]["raft_ft"]["error_dx"] is None
    np.testing.assert_array_equal(arrows["methods"]["none"]["dx"], np.zeros((16, 16)))
    assert (where / arrows["image"]).exists()


def test_no_file_of_the_demo_holds_a_time_or_a_memory(shown):
    written = sorted((shown / "demo").rglob("*.json"))
    written += sorted((shown / "examples").rglob("*.json"))

    assert len(written) == 6
    for path in written:
        for key in keys_of(json.loads(path.read_text())):
            assert not any(
                word in key for word in ("time", "_ms", "mib", "memory", "peak")
            ), f"{key} in {path.name}"


def test_the_json_files_hold_no_number_that_is_not_one(shown):
    for path in (shown / "demo").rglob("*.json"):
        text = path.read_text()
        assert "NaN" not in text
        assert "Infinity" not in text


def test_the_curve_s_files_are_the_published_ones_byte_for_byte(shown):
    manifest = json.loads((shown / "demo" / "manifest.json").read_text())

    assert manifest["curve"] == [f"curve/{name}" for name in demo.CURVE_FILES]
    assert len(demo.CURVE_FILES) == 3
    for name in demo.CURVE_FILES:
        copy = shown / "demo" / "curve" / name
        assert copy.read_bytes() == (PUBLISHED_CURVE / name).read_bytes()


def test_a_missing_file_of_the_curve_stops_the_command(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "configured_methods", stand_ins)
    (tmp_path / "curve").mkdir()

    with pytest.raises(SystemExit, match="no curve-points.csv in"):
        main(
            ["demo", "--sites", "synthetic", "--out", str(tmp_path / "demo")]
            + ["--examples", str(tmp_path / "examples")]
            + OPTIONS[:-1]
            + [str(tmp_path / "curve")]
        )

    assert not (tmp_path / "examples").exists()


def test_the_examples_are_the_pairs_shown_with_their_manifest(shown):
    examples = shown / "examples"
    manifest = json.loads((examples / "manifest.json").read_text())
    pairs = manifest["pairs"]

    assert [(pair["preset"], pair["scenario"]) for pair in pairs] == [
        ("clean", "translation"),
        ("clean", "dense"),
        ("hard", "translation"),
        ("hard", "dense"),
    ]
    shown_site = json.loads((shown / "demo" / "manifest.json").read_text())["sites"][0]
    for pair in pairs:
        assert pair["site"] == "synthetic"
        assert pair["window"] == shown_site["window"]
        read = register.read_pair(
            examples / pair["reference"], examples / pair["moving"]
        )
        assert read.reference.shape == (256, 256)
        assert read.georef is not None
    slider = json.loads(
        (shown / "demo" / "synthetic" / "clean" / "pair.json").read_text()
    )
    assert pairs[0]["truth"]["dx"] == slider["truth"]["dx"]
    assert pairs[0]["truth"]["dy"] == slider["truth"]["dy"]
    # The dense pair's truth is a file: a field has no two numbers to give.
    assert pairs[1]["truth"]["file"] == "synthetic/truth_dense.tif"
    with rasterio.open(examples / pairs[1]["truth"]["file"]) as src:
        assert src.descriptions == ("dy", "dx")
        assert src.read().shape == (2, 256, 256)
    assert sorted(
        path.name for path in (examples / "synthetic" / "hard").iterdir()
    ) == [
        "moving_dense.tif",
        "moving_translation.tif",
        "reference.tif",
    ]


def test_satreg_register_finds_the_true_shift_of_a_demo_pair(shown, tmp_path):
    examples = shown / "examples"
    pair = json.loads((examples / "manifest.json").read_text())["pairs"][0]
    out = tmp_path / "out"

    main(
        ["register", str(examples / pair["reference"]), str(examples / pair["moving"])]
        + ["--method", "phase_correlation", "--out", str(out)]
        + ["--methods-config", str(CONFIGS / "methods.toml")]
    )

    found = json.loads((out / register.DISPLACEMENT_FILE).read_text())["displacement"]
    assert found["dx"] == pytest.approx(pair["truth"]["dx"], abs=0.05)
    assert found["dy"] == pytest.approx(pair["truth"]["dy"], abs=0.05)


def test_a_synthetic_demo_carries_no_copernicus_notice(shown):
    manifest = json.loads((shown / "examples" / "manifest.json").read_text())

    assert manifest["notice"] is None
    assert "Copernicus" not in (shown / "examples" / "README.md").read_text()
    with rasterio.open(
        shown / "examples" / "synthetic" / "clean" / "reference.tif"
    ) as src:
        assert "notice" not in src.tags()


def test_running_the_command_twice_writes_the_same_files(shown, tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "configured_methods", stand_ins)

    show(tmp_path / "demo", tmp_path / "examples", "--sites", "synthetic")

    first, second = files_of(shown / "demo"), files_of(tmp_path / "demo")
    assert list(first) == list(second)
    assert [name for name in first if first[name] != second[name]] == []
    first, second = files_of(shown / "examples"), files_of(tmp_path / "examples")
    assert list(first) == list(second)
    assert [name for name in first if first[name] != second[name]] == []


def test_a_run_leaves_nothing_of_an_earlier_one_beside_its_files(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "configured_methods", stand_ins)
    stale = [
        tmp_path / "demo" / "synthetic" / "clean" / "corrected-roma.png",
        tmp_path / "examples" / "synthetic" / "clean" / "moving_affine.tif",
    ]
    for path in stale:
        path.parent.mkdir(parents=True)
        path.write_bytes(b"old")

    show(tmp_path / "demo", tmp_path / "examples", "--sites", "synthetic")

    assert not any(path.exists() for path in stale)


def test_the_command_says_which_pair_it_picked_and_what_it_wrote(
    tmp_path, capsys, monkeypatch
):
    monkeypatch.setattr(cli, "configured_methods", stand_ins)

    show(tmp_path / "demo", tmp_path / "examples", "--sites", "synthetic")

    said = capsys.readouterr().out
    assert said.startswith("synthetic: pair 0\n")
    assert "synthetic, clean, translation, none: 3.478\n" in said
    assert (
        "synthetic, hard, dense, raft_ft: none "
        "(failure: RegistrationFailure: 3 inliers, need 10)\n"
    ) in said
    count, size = demo.size_of(tmp_path / "demo")
    assert f"written to {tmp_path / 'demo'}: {count} files, {size / 1e6:.2f} MB" in said


def test_a_seen_site_s_pair_carries_its_scene_its_window_and_the_notice(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(cli, "configured_methods", stand_ins)
    chip, site = _configured(tmp_path, HELD_OUT)
    examples = tmp_path / "examples"

    # No site is named: the seen one is shown, the held-out one is not read.
    show(tmp_path / "demo", examples, *site)

    shown_sites = json.loads((tmp_path / "demo" / "manifest.json").read_text())
    assert [entry["name"] for entry in shown_sites["sites"]] == ["beauce"]
    assert shown_sites["notice"] == "Contains modified Copernicus Sentinel data 2025"
    assert not (tmp_path / "demo" / "alps").exists()
    manifest = json.loads((examples / "manifest.json").read_text())
    assert manifest["notice"] == "Contains modified Copernicus Sentinel data 2025"
    assert manifest["notice"] in (examples / "README.md").read_text()
    pair = manifest["pairs"][0]
    assert (pair["site"], pair["scene"], pair["acquired"]) == (
        "beauce",
        SCENE,
        ACQUIRED,
    )
    window = pair["window"]
    with rasterio.open(chip) as src:
        rows = slice(window["row"], window["row"] + window["size"])
        cols = slice(window["col"], window["col"] + window["size"])
        cut = src.read(1)[rows, cols]
        corner = src.transform @ (window["col"], window["row"])
        crs = src.crs
    with rasterio.open(examples / pair["reference"]) as src:
        # The clean reference is the chip's own pixels, on the chip's map grid.
        np.testing.assert_array_equal(src.read(1), cut)
        assert (src.transform.c, src.transform.f) == pytest.approx(corner)
        assert src.crs == crs
        tags = src.tags()
    assert tags["notice"] == manifest["notice"]
    assert tags["scene"] == SCENE
    assert tags["site"] == "beauce"


def test_a_held_out_site_is_refused_before_anything_is_written(tmp_path):
    _, site = _configured(tmp_path, HELD_OUT)

    with pytest.raises(SystemExit, match="'alps' is held out.*shows seen sites only"):
        show(
            tmp_path / "demo", tmp_path / "examples", "--sites", "beauce", "alps", *site
        )

    assert not (tmp_path / "demo").exists()
    assert not (tmp_path / "examples").exists()


@pytest.mark.parametrize("site", ["alps", "libya4"])
def test_the_repository_s_held_out_sites_are_refused(tmp_path, site):
    with pytest.raises(SystemExit, match=f"'{site}' is held out"):
        show(
            tmp_path / "demo",
            tmp_path / "examples",
            "--sites",
            site,
            "--sites-config",
            str(CONFIGS / "sites.toml"),
            "--data-dir",
            str(tmp_path / "data"),
        )

    assert not (tmp_path / "data").exists()


def test_the_command_has_no_way_to_allow_a_held_out_site(tmp_path, capsys):
    with pytest.raises(SystemExit) as stopped:
        show(tmp_path / "demo", tmp_path / "examples", "--allow-held-out")

    assert stopped.value.code == 2
    assert "unrecognized arguments: --allow-held-out" in capsys.readouterr().err


def test_the_command_has_no_way_to_draw_other_pairs_than_the_benchmark_s(capsys):
    for option in (["--seed", "1"], ["--size", "128"], ["--pairs", "3"]):
        with pytest.raises(SystemExit) as stopped:
            main(["demo", *option])
        assert stopped.value.code == 2
        assert "unrecognized arguments" in capsys.readouterr().err


def test_the_demo_s_methods_and_presets_are_configured_in_the_repository(presets):
    configured = load_methods(CONFIGS / "methods.toml")

    assert set(demo.METHODS) <= set(configured)
    assert set(demo.PRESETS) <= set(presets)


@needs_raft
def test_the_two_raft_run_on_the_synthetic_site_with_their_weights(tmp_path):
    show(tmp_path / "demo", tmp_path / "examples", "--sites", "synthetic")

    where = tmp_path / "demo" / "synthetic" / "clean"
    for name in ("pair.json", "arrows.json"):
        methods = json.loads((where / name).read_text())["methods"]
        for method in ("raft", "raft_ft"):
            assert methods[method]["estimate"]["model"] == "dense"
            assert methods[method]["error_px"] < 0.5
            assert not methods[method]["failure"]
    assert (where / "corrected-raft_ft.png").exists()

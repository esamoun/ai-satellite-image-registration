import json
import logging
import warnings
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.errors import NotGeoreferencedWarning
from rasterio.transform import from_origin
from test_ingest import CRS, TRANSFORM

from satreg import cli, register
from satreg.cli import main
from satreg.displacement import Affine, Dense, Translation
from satreg.methods import load_methods
from satreg.methods.base import Estimate, GeoreferencedMethod, RegistrationFailure
from satreg.methods.raft import Raft
from satreg.methods.raft_onnx import RaftOnnx
from satreg.simulate import margin_for, simulate_translation
from satreg.texture import fractal_texture

CONFIG = Path(__file__).parents[1] / "configs" / "methods.toml"
METHODS = ["--methods-config", str(CONFIG)]

# The known shift of the pairs below: moving(p + d) = reference(p).
DX, DY = 1.5, -0.75


def shifted_pair(size=96, dx=DX, dy=DY, seed=0):
    """A reference and the same texture shifted by ``(dx, dy)``."""
    margin = margin_for(max(abs(dx), abs(dy)))
    # Well above zero, so that a 16-bit PNG holds every value.
    source = 2000 + 300 * fractal_texture(size + 2 * margin, seed=seed)
    pair = simulate_translation(source, dx=dx, dy=dy, margin=margin)
    return pair.reference, pair.moving


def write_tif(path, image, crs=CRS, transform=TRANSFORM):
    """Write ``(rows, cols)`` or ``(bands, rows, cols)`` as a GeoTIFF."""
    layers = np.atleast_3d(image.T).T.astype("float32")
    profile = {"driver": "GTiff", "dtype": "float32", "count": layers.shape[0]}
    profile.update(height=layers.shape[1], width=layers.shape[2])
    if crs is not None:
        profile.update(crs=crs, transform=transform)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(layers)
    return str(path)


def write_png(path, image):
    """Write an image as a 16-bit PNG, which carries no map grid."""
    data = np.round(image).astype("uint16")
    profile = {"driver": "PNG", "dtype": "uint16", "count": 1}
    profile.update(height=data.shape[0], width=data.shape[1])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", NotGeoreferencedWarning)
        with rasterio.open(path, "w", **profile) as dst:
            dst.write(data, 1)
    return str(path)


@pytest.fixture
def pair(tmp_path):
    """The files of a georeferenced pair with a known shift."""
    reference, moving = shifted_pair()
    return [
        write_tif(tmp_path / "reference.tif", reference),
        write_tif(tmp_path / "moving.tif", moving),
    ]


def run(files, out, *options, method="phase_correlation"):
    main(
        ["register", *files, "--method", method, "--out", str(out), *options, *METHODS]
    )
    return json.loads((out / register.DISPLACEMENT_FILE).read_text())


def refusal(arguments):
    """What the command says when it stops with an error code."""
    with pytest.raises(SystemExit) as stopped:
        main(["register", *arguments, *METHODS])
    # A message, not 0: the exit code is non-zero.
    assert isinstance(stopped.value.code, str)
    return stopped.value.code


def use(monkeypatch, method):
    """Have the command run ``method`` under whatever name is asked."""
    monkeypatch.setattr(
        cli, "configured_methods", lambda args: {args.methods[0]: method}
    )


def test_a_known_shift_is_recovered_by_phase_correlation(pair, tmp_path, capsys):
    result = run(pair, tmp_path / "out")

    assert result["method"] == "phase_correlation"
    found = result["displacement"]
    assert found["model"] == "translation"
    assert found["dx"] == pytest.approx(DX, abs=0.05)
    assert found["dy"] == pytest.approx(DY, abs=0.05)
    assert result["duration_s"] > 0
    assert result["pair"]["shape"] == [96, 96]
    assert result["pair"]["georeferenced"] is True
    printed = capsys.readouterr().out
    assert "phase_correlation: translation displacement" in printed
    assert "displacement.json, corrected.tif" in printed


def test_the_corrected_image_is_the_moving_one_back_on_the_reference(pair, tmp_path):
    run(pair, tmp_path / "out")

    with rasterio.open(pair[0]) as src:
        reference = src.read(1)
    with rasterio.open(tmp_path / "out" / register.CORRECTED_FILE) as src:
        corrected = src.read(1)
        # The georeferencing of the input.
        assert src.crs == rasterio.crs.CRS.from_string(CRS)
        assert src.transform == TRANSFORM
    with rasterio.open(pair[1]) as src:
        moving = src.read(1)
    inner = (slice(8, -8), slice(8, -8))
    before = np.abs(moving[inner] - reference[inner]).mean()
    after = np.abs(corrected[inner] - reference[inner]).mean()
    # What is left is the interpolation and the 0.04 px the method is off by.
    assert after < before / 20
    # A translation has no flow file.
    assert not (tmp_path / "out" / register.FLOW_FILE).exists()


def test_pixels_the_moving_image_does_not_reach_hold_no_data(pair, tmp_path, capsys):
    result = run(pair, tmp_path / "out")

    with rasterio.open(tmp_path / "out" / register.CORRECTED_FILE) as src:
        corrected = src.read(1)
    # The content of the last columns lies about 1.5 px past the right edge,
    # that of the first row about 0.75 px above the top one.
    assert np.isnan(corrected[:, -1]).all()
    assert np.isnan(corrected[0]).all()
    assert np.isfinite(corrected[2:, :-3]).all()
    assert result["corrected"]["no_data_px"] == int(np.isnan(corrected).sum())
    assert "hold no data" in capsys.readouterr().out


def test_a_png_pair_is_registered_without_a_map_grid(tmp_path):
    reference, moving = shifted_pair()
    files = [
        write_png(tmp_path / "reference.png", reference),
        write_png(tmp_path / "moving.png", moving),
    ]

    with warnings.catch_warnings():
        # Rasterio warns of a file without a map grid; the command does not.
        warnings.simplefilter("error", NotGeoreferencedWarning)
        result = run(files, tmp_path / "out")

    assert result["displacement"]["dx"] == pytest.approx(DX, abs=0.05)
    assert result["pair"]["georeferenced"] is False
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", NotGeoreferencedWarning)
        with rasterio.open(tmp_path / "out" / register.CORRECTED_FILE) as src:
            assert src.crs is None


def test_without_a_method_the_runnable_ones_are_listed_and_nothing_runs(pair, tmp_path):
    said = refusal([*pair, "--out", str(tmp_path / "out")])

    assert "--method NAME" in said
    assert "no default" in said
    assert "phase_correlation" in said
    assert "sift_ransac" in said
    assert not (tmp_path / "out").exists()


def test_the_methods_are_listed_without_any_file_given():
    assert "phase_correlation" in refusal([])


def test_a_method_needs_its_images_and_its_directory(pair):
    said = refusal([*pair, "--method", "phase_correlation"])

    assert "satreg register REF MOVING --method NAME --out DIR" in said


def test_an_unknown_method_is_refused_with_the_known_ones(pair, tmp_path):
    said = refusal([*pair, "--method", "nope", "--out", str(tmp_path / "out")])

    assert "unknown method 'nope'" in said
    assert "phase_correlation" in said


def test_images_of_different_shapes_are_refused(pair, tmp_path):
    smaller = write_tif(tmp_path / "smaller.tif", shifted_pair(size=64)[1])

    said = refusal(
        [pair[0], smaller, "--method", "phase_correlation", "--out", str(tmp_path)]
    )

    assert "differ in shape" in said
    assert "96 x 96 px" in said and "64 x 64 px" in said
    assert "one grid first" in said


def test_a_file_with_several_bands_needs_its_band_named(pair, tmp_path):
    reference, moving = shifted_pair()
    stack = write_tif(tmp_path / "stack.tif", np.stack([reference, moving]))
    arguments = [pair[0], stack, "--method", "phase_correlation"]

    said = refusal([*arguments, "--out", str(tmp_path / "out")])
    assert "has 2 bands" in said
    assert "--band N (1 to 2)" in said

    said = refusal([*arguments, "--out", str(tmp_path / "out"), "--band", "3"])
    assert "no band 3" in said

    # The second band of the stack is the moving image, the single band of
    # the reference is read whatever --band says.
    result = run([pair[0], stack], tmp_path / "out", "--band", "2")
    assert result["pair"]["bands"] == [1, 2]
    assert result["displacement"]["dx"] == pytest.approx(DX, abs=0.05)


def test_a_window_is_cut_from_both_images_and_keeps_its_place(tmp_path):
    reference, moving = shifted_pair(size=160)
    files = [
        write_tif(tmp_path / "reference.tif", reference),
        write_tif(tmp_path / "moving.tif", moving),
    ]

    result = run(files, tmp_path / "out", "--window", "40", "24", "96")

    assert result["pair"]["window"] == [40, 24, 96]
    assert result["pair"]["shape"] == [96, 96]
    assert result["displacement"]["dx"] == pytest.approx(DX, abs=0.05)
    with rasterio.open(tmp_path / "out" / register.CORRECTED_FILE) as src:
        assert src.shape == (96, 96)
        # 10 m pixels: 24 columns east and 40 rows south of the file's origin.
        assert src.transform == from_origin(390_240, 5_344_600, 10, 10)


@pytest.mark.parametrize("window", [(0, 0, 97), (-1, 0, 32), (90, 0, 32), (0, 0, 0)])
def test_a_window_that_does_not_fit_is_refused(pair, tmp_path, window):
    said = refusal(
        [*pair, "--method", "phase_correlation", "--out", str(tmp_path / "out")]
        + ["--window", *map(str, window)]
    )

    assert "does not fit in the images, 96 x 96 px" in said


def test_an_image_above_the_limit_is_refused_and_a_window_of_it_taken(
    pair, tmp_path, monkeypatch
):
    monkeypatch.setattr(register, "MAX_SIDE_PX", 64)

    said = refusal(
        [*pair, "--method", "phase_correlation", "--out", str(tmp_path / "out")]
    )
    assert "96 x 96 px, above the 64 px a side" in said
    assert "--window ROW COL SIZE" in said
    assert "Nothing is tiled" in said
    assert not (tmp_path / "out").exists()

    result = run(pair, tmp_path / "out", "--window", "16", "16", "64")
    assert result["displacement"]["dx"] == pytest.approx(DX, abs=0.08)


def test_the_limit_is_the_size_the_measurement_settled_on():
    # RAFT takes over 5 GiB at 1,024 px, and nothing was measured above
    # (docs/decisions.md).
    assert register.MAX_SIDE_PX == 512


def test_files_on_different_map_grids_are_refused(tmp_path):
    reference, moving = shifted_pair()
    files = [
        write_tif(tmp_path / "reference.tif", reference),
        write_tif(
            tmp_path / "moving.tif",
            moving,
            transform=from_origin(390_005, 5_345_000, 10, 10),
        ),
    ]

    said = refusal(
        [*files, "--method", "phase_correlation", "--out", str(tmp_path / "out")]
    )

    assert "different map grids" in said
    assert "one grid first" in said
    assert not (tmp_path / "out").exists()


def test_the_grid_of_the_one_georeferenced_file_is_the_pair_s(tmp_path):
    reference, moving = shifted_pair()
    files = [
        write_png(tmp_path / "reference.png", reference),
        write_tif(tmp_path / "moving.tif", moving),
    ]

    result = run(files, tmp_path / "out")

    assert result["pair"]["georeferenced"] is True
    with rasterio.open(tmp_path / "out" / register.CORRECTED_FILE) as src:
        assert src.transform == TRANSFORM


def test_a_missing_file_and_a_file_that_is_no_image_are_refused(pair, tmp_path):
    arguments = ["--method", "phase_correlation", "--out", str(tmp_path / "out")]
    text = tmp_path / "notes.txt"
    text.write_text("not an image")

    assert "no file at" in refusal([pair[0], str(tmp_path / "gone.tif"), *arguments])
    assert "give a GeoTIFF or a PNG" in refusal([pair[0], str(text), *arguments])


def test_pixels_that_are_not_numbers_are_refused(pair, tmp_path):
    holed = shifted_pair()[1]
    holed[5, 5] = np.nan
    files = [pair[0], write_tif(tmp_path / "holed.tif", holed)]

    said = refusal(
        [*files, "--method", "phase_correlation", "--out", str(tmp_path / "out")]
    )

    assert "not numbers" in said
    assert "--window" in said


def test_a_method_that_fails_exits_with_its_reason_and_writes_nothing(
    pair, tmp_path, monkeypatch
):
    out = tmp_path / "out"
    run(pair, out)

    def failing(reference, moving):
        raise RegistrationFailure("too few matches", {"inliers": 3})

    use(monkeypatch, failing)
    said = refusal([*pair, "--method", "sift_ransac", "--out", str(out)])

    assert "sift_ransac could not register this pair: too few matches" in said
    assert "inliers = 3" in said
    assert "Nothing was written" in said
    # Not even the result of the call before.
    assert list(out.iterdir()) == []


def test_a_dense_displacement_is_also_written_as_a_flow(pair, tmp_path, monkeypatch):
    flow = np.empty((2, 96, 96))
    flow[0], flow[1] = DY, DX
    use(monkeypatch, lambda reference, moving: Estimate(Dense(flow), {"score": 0.5}))

    result = run(pair, tmp_path / "out", method="raft_ft_onnx")

    found = result["displacement"]
    assert found["model"] == "dense"
    assert found["file"] == register.FLOW_FILE
    assert found["mean_dx"] == pytest.approx(DX)
    assert found["mean_dy"] == pytest.approx(DY)
    assert result["diagnostics"] == {"score": 0.5}
    with rasterio.open(tmp_path / "out" / register.FLOW_FILE) as src:
        assert src.descriptions == ("dy", "dx")
        assert src.transform == TRANSFORM
        np.testing.assert_allclose(src.read(), flow)


def test_a_flow_of_an_earlier_call_does_not_outlive_it(pair, tmp_path, monkeypatch):
    out = tmp_path / "out"
    with monkeypatch.context() as patched:
        use(patched, lambda reference, moving: Dense(np.zeros((2, 96, 96))))
        run(pair, out, method="raft_ft_onnx")
    assert (out / register.FLOW_FILE).exists()

    run(pair, out)

    assert not (out / register.FLOW_FILE).exists()


def test_an_affine_displacement_is_written_with_its_matrix(pair, tmp_path, monkeypatch):
    affine = Affine.about((48.0, 48.0), rotation_deg=0.5, dx=DX, dy=DY)
    use(monkeypatch, lambda reference, moving: affine)

    result = run(pair, tmp_path / "out", method="sift_ransac")

    assert result["displacement"] == {
        "model": "affine",
        "matrix": [list(row) for row in affine.matrix],
        "offset": list(affine.offset),
    }


class Padded(Raft):
    """A RAFT that answers without its network."""

    def __call__(self, reference, moving):
        return Dense(np.zeros((2, *reference.shape)))


def test_a_pair_raft_has_to_pad_is_registered_with_a_warning(
    tmp_path, monkeypatch, caplog
):
    reference, moving = shifted_pair(size=64)
    files = [
        write_tif(tmp_path / "reference.tif", reference),
        write_tif(tmp_path / "moving.tif", moving),
    ]
    use(monkeypatch, Padded())

    with caplog.at_level(logging.WARNING):
        result = run(files, tmp_path / "out", method="raft_ft")

    note = "RAFT pads it up to 128 px a side, which costs accuracy"
    assert note in caplog.text
    assert "0.14 to 0.30 px" in caplog.text
    assert note in result["notes"][0]


def test_only_raft_under_128_px_is_told_about_padding():
    onnx = RaftOnnx(file="outputs/onnx/raft_large_ft_r12.onnx")

    assert register.padding_note(Raft(), (64, 200)) is not None
    assert register.padding_note(onnx, (127, 127)) is not None
    assert register.padding_note(Raft(), (128, 128)) is None
    assert register.padding_note(load_methods(CONFIG)["sift_ransac"], (64, 64)) is None


class OnTheMap(GeoreferencedMethod):
    """A method that needs the pair's grid, and keeps the one it was given."""

    def __call__(self, reference, moving, georef):
        self.georef = georef
        return Translation(dx=0.0, dy=0.0)


def test_a_method_working_in_map_coordinates_gets_the_grid_of_the_files(
    pair, tmp_path, monkeypatch
):
    method = OnTheMap()
    use(monkeypatch, method)

    run(pair, tmp_path / "whole", method="arosics")
    assert method.georef.crs == rasterio.crs.CRS.from_string(CRS)
    assert method.georef.transform == TRANSFORM

    run(pair, tmp_path / "cut", "--window", "8", "16", "64", method="arosics")
    assert method.georef.transform == from_origin(390_160, 5_344_920, 10, 10)


def test_a_method_working_in_map_coordinates_refuses_a_pair_without_a_grid(
    tmp_path, monkeypatch
):
    reference, moving = shifted_pair()
    files = [
        write_png(tmp_path / "reference.png", reference),
        write_png(tmp_path / "moving.png", moving),
    ]
    use(monkeypatch, OnTheMap())

    said = refusal([*files, "--method", "arosics", "--out", str(tmp_path / "out")])

    assert "method arosics works in map coordinates" in said
    assert "GeoTIFFs with their reference system" in said
    assert not (tmp_path / "out").exists()


def test_methods_without_their_packages_or_their_file_are_not_listed(
    tmp_path, monkeypatch
):
    present = tmp_path / "there.onnx"
    present.write_bytes(b"")
    methods = {
        "classic": load_methods(CONFIG)["phase_correlation"],
        "no_package": Raft(),
        "no_file": RaftOnnx(file=str(tmp_path / "gone.onnx")),
        "file": RaftOnnx(file=str(present)),
        "no_checkpoint": Raft(checkpoint=str(tmp_path / "gone.pt")),
        "released": RaftOnnx(release="raft_large_ft_r12"),
    }
    monkeypatch.setattr(
        register,
        "missing_dependencies",
        lambda method: ["torch"] if method is methods["no_package"] else [],
    )
    monkeypatch.setattr(register.weights, "cache_directory", lambda: tmp_path)

    assert register.available(methods) == (["classic", "file"], ["released"])

    asset = register.weights.lookup("raft_large_ft_r12").asset
    (tmp_path / asset).write_bytes(b"")
    assert register.available(methods) == (["classic", "file", "released"], [])

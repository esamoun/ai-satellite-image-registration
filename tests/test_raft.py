from pathlib import Path

import numpy as np
import pytest

from satreg.displacement import Dense
from satreg.methods import METHODS, cost_meter, deep, load_methods, missing_dependencies
from satreg.methods.raft import MODELS, Raft, network_input, pad, stretch
from satreg.simulate import simulate_translation
from satreg.texture import fractal_texture

REPO_CONFIG = Path(__file__).parents[1] / "configs" / "methods.toml"


def _skip_reason() -> str | None:
    if missing := deep.missing_modules():
        return f"needs the dl extra ({', '.join(missing)} missing): make install-dl"
    for model in MODELS:
        weights = deep.weights_file(Raft(model=model).weights())
        if not weights.exists():
            return f"needs RAFT's {model} weights at {weights}: make install-dl"
    return None


# The tests that run the network. The conftest refuses network access, so the
# weights must already be in PyTorch's cache.
needs_raft = pytest.mark.skipif(_skip_reason() is not None, reason=_skip_reason() or "")


def test_stretch_maps_the_percentiles_to_the_ends_of_the_range():
    image = np.arange(10_000, dtype=np.uint16).reshape(100, 100)

    stretched = stretch(image)

    assert stretched.dtype == np.float32
    assert stretched.min() == -1.0
    assert stretched.max() == 1.0
    assert np.mean(stretched == -1.0) == pytest.approx(0.01, abs=0.001)


def test_stretch_ignores_the_gain_and_offset_of_an_image():
    image = np.random.default_rng(0).integers(1000, 3000, (32, 32)).astype(float)

    np.testing.assert_allclose(stretch(3.0 * image + 500.0), stretch(image), atol=1e-6)


def test_a_flat_image_stretches_to_zeros():
    np.testing.assert_array_equal(stretch(np.full((8, 8), 7, np.uint16)), 0.0)


@pytest.mark.parametrize(
    ("shape", "padded"), [((256, 256), (256, 256)), ((130, 250), (136, 256))]
)
def test_padding_rounds_up_to_a_multiple_of_8(shape, padded):
    assert pad(np.zeros(shape)).shape == padded


def test_padding_reaches_the_smallest_side_raft_takes():
    assert pad(np.zeros((64, 200))).shape == (128, 200)


def test_padding_replicates_the_last_row_and_column_and_moves_nothing():
    image = np.arange(130 * 129, dtype=float).reshape(130, 129)

    padded = pad(image)

    np.testing.assert_array_equal(padded[:130, :129], image)
    np.testing.assert_array_equal(padded[130:, :129], np.tile(image[-1], (6, 1)))
    np.testing.assert_array_equal(padded[:130, 129:].T, np.tile(image[:, -1], (7, 1)))


def test_network_input_is_three_equal_channels():
    image = np.random.default_rng(0).integers(0, 10_000, (130, 130), np.uint16)

    channels = network_input(image)

    assert channels.shape == (3, 136, 136)
    np.testing.assert_array_equal(channels[0], channels[2])
    np.testing.assert_array_equal(channels[0][:130, :130], stretch(image))


@pytest.mark.parametrize(
    ("parameters", "message"),
    [
        ({"model": "huge"}, "model must be one of large, small"),
        ({"iterations": 0}, "iterations must be positive"),
        ({"device": "tpu"}, "device must be one of cpu, mps, cuda"),
    ],
)
def test_bad_parameters_are_rejected(parameters, message):
    with pytest.raises(ValueError, match=message):
        Raft(**parameters)


def test_raft_is_registered_with_its_small_variant():
    methods = load_methods(REPO_CONFIG)

    assert METHODS["raft"] == Raft()
    assert methods["raft"] == Raft(model="large", iterations=12, device="cpu")
    assert methods["raft_small"] == Raft(model="small", iterations=12, device="cpu")


def test_raft_needs_the_dl_extra(monkeypatch):
    monkeypatch.setattr(deep.importlib.util, "find_spec", lambda name: None)

    assert missing_dependencies(Raft(model="small")) == ["torch", "torchvision"]


def test_raft_is_measured_on_its_device():
    assert cost_meter(Raft()).name == "torch-cpu"
    assert cost_meter(Raft(device="cuda")).name == "cuda"
    assert cost_meter(Raft(device="mps")).name == "none"
    assert cost_meter(METHODS["phase_correlation"]).name == "tracemalloc"


def _translated(dx: float, dy: float):
    # A pair of 284 px, which RAFT pads to 288.
    return simulate_translation(fractal_texture(320, seed=3), dx=dx, dy=dy)


@needs_raft
@pytest.mark.parametrize("model", MODELS)
def test_the_flow_follows_the_displacement_convention(model):
    # moving(p + d) = reference(p): content found 3 px right and 2 px up.
    pair = _translated(dx=3.0, dy=-2.0)

    field = Raft(model=model)(pair.reference, pair.moving).field(pair.reference.shape)

    # The sign and the order of the components are what is pinned here, not the
    # accuracy: whole pixels are read 0.02 to 0.08 px short.
    np.testing.assert_allclose(np.median(field, axis=(1, 2)), [-2.0, 3.0], atol=0.25)


@needs_raft
def test_raft_recovers_a_sub_pixel_translation_on_cpu():
    pair = _translated(dx=0.37, dy=-1.62)

    estimate = Raft()(pair.reference, pair.moving)

    field = estimate.field(pair.reference.shape)
    epe = np.hypot(field[0] - pair.truth.dy, field[1] - pair.truth.dx)
    # Measured 0.045 px when this test was written, 0.18 px for the small model.
    assert epe.mean() < 0.1


@needs_raft
def test_the_flow_is_cropped_back_to_the_reference_grid():
    pair = _translated(dx=1.0, dy=1.0)
    reference, moving = pair.reference[:141, :150], pair.moving[:141, :150]

    estimate = Raft(model="small", iterations=4)(reference, moving)

    assert isinstance(estimate, Dense)
    assert estimate.shape == (141, 150)

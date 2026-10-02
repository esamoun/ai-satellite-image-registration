import dataclasses
import json
from pathlib import Path

import numpy as np
import pytest
from test_raft import needs_raft
from test_trainchips import scenes  # noqa: F401
from test_trainpairs import cached, chips, pairs_config, ranges

from satreg import train as training
from satreg.cli import main
from satreg.methods import deep, load_methods
from satreg.methods.raft import Raft
from satreg.train import (
    CHECKPOINT,
    METHOD_NAMES,
    TrainConfig,
    load_train_config,
    log_markdown,
    pair_arrays,
    pair_indices,
)
from satreg.trainpairs import PairGenerator

REPO = Path(__file__).parents[1]
CONFIGS = REPO / "configs"

needs_torch = pytest.mark.skipif(
    bool(deep.missing_modules()), reason="needs the dl extra: make install-dl"
)


def flows(*errors, shape=(2, 2, 8, 8)):
    """A true flow and one prediction per error, each off by it at every pixel."""
    import torch

    flow = torch.arange(float(np.prod(shape))).reshape(shape) / 100
    return [flow + error for error in errors], flow, torch.ones(shape[::3] + (8,)) > 0


@needs_torch
def test_the_loss_of_a_perfect_prediction_is_zero():
    predictions, flow, mask = flows(0.0, 0.0, 0.0)

    assert float(training.sequence_loss(predictions, flow, mask)) == 0.0


@needs_torch
def test_the_loss_weighs_later_refinements_more():
    early, flow, mask = flows(1.0, 0.0, 0.0)
    late, _, _ = flows(0.0, 0.0, 1.0)

    # An error of 1 px on both components: the last refinement weighs 1, the
    # first of three gamma squared.
    assert float(training.sequence_loss(late, flow, mask, gamma=0.5)) == 1.0
    assert float(training.sequence_loss(early, flow, mask, gamma=0.5)) == 0.25


@needs_torch
def test_the_loss_ignores_masked_pixels():
    import torch

    predictions, flow, mask = flows(0.0, 0.0)
    mask[0, :4] = False
    wrong = predictions[-1].clone().requires_grad_(True)
    spoiled = wrong + 5.0 * ~mask[:, None]

    loss = training.sequence_loss([predictions[0], spoiled], flow, mask)
    loss.backward()

    assert float(loss.detach()) == 0.0
    assert torch.all(wrong.grad[0, :, :4] == 0)


@needs_torch
def test_masked_pixels_count_for_zero_in_the_mean_as_in_the_reference():
    predictions, flow, mask = flows(1.0)
    full = float(training.sequence_loss(predictions, flow, mask))
    mask[:, :4] = False

    assert float(training.sequence_loss(predictions, flow, mask)) == full / 2


@needs_torch
def test_the_loss_leaves_out_pixels_whose_true_flow_is_too_long():
    predictions, flow, mask = flows(1.0)
    flow, predictions = flow.clone(), [predictions[0].clone()]
    flow[1] += 500.0
    predictions[0][1] += 500.0

    assert float(training.sequence_loss(predictions, flow, mask)) == 0.5


@needs_torch
def test_the_end_point_error_is_read_on_masked_pixels_pair_by_pair():
    predictions, flow, mask = flows(0.0)
    prediction = predictions[0].clone()
    prediction[0, 0] += 3.0
    prediction[0, 1] += 4.0
    prediction[1, :, :4] += 100.0
    mask[1, :4] = False

    epe = training.masked_epe(prediction, flow, mask)

    np.testing.assert_allclose(epe.numpy(), [5.0, 0.0], atol=1e-5)


@pytest.mark.parametrize(
    ("parameters", "message"),
    [
        ({"model": "huge"}, "model must be one of large, small"),
        ({"steps": 0}, "steps must be positive"),
        ({"learning_rate": 0.0}, "learning_rate must be positive"),
        ({"gamma": 1.5}, "gamma must be in"),
        ({"n_pairs": -1}, "must not be negative"),
        ({"device": "tpu"}, "device must be one of cpu, mps, cuda"),
    ],
)
def test_bad_training_parameters_are_rejected(parameters, message):
    with pytest.raises(ValueError, match=message):
        TrainConfig(**parameters)


def test_the_repository_s_overfit_run_cycles_over_a_few_pairs():
    config = load_train_config(CONFIGS / "train-overfit.toml")

    assert config == TrainConfig(
        model="large", steps=300, n_pairs=8, checkpoint_every=100, device="mps"
    )
    assert (config.gamma, config.iterations, config.freeze_batch_norm) == (
        0.85,
        12,
        True,
    )


def test_a_training_config_with_an_unknown_key_is_refused(tmp_path):
    path = tmp_path / "train.toml"
    path.write_text("[train]\nmixed_precision = true\n")

    with pytest.raises(ValueError, match="unknown key 'mixed_precision'"):
        load_train_config(path)

    path.write_text("[pairs]\nsize = 128\n")
    with pytest.raises(ValueError, match=r"needs a \[train\] table"):
        load_train_config(path)


def test_a_step_takes_the_next_pairs_and_an_overfit_run_cycles_over_its_own():
    config = TrainConfig(batch_size=3)

    assert pair_indices(0, config) == [0, 1, 2]
    assert pair_indices(4, config) == [12, 13, 14]
    assert pair_indices(1, dataclasses.replace(config, n_pairs=4)) == [3, 0, 1]


def test_a_pair_is_handed_to_the_network_with_its_flow_as_dx_then_dy():
    pair = PairGenerator(chips(), pairs_config(), ranges())(0)

    reference, moving, flow, mask = pair_arrays(pair)

    assert reference.shape == moving.shape == (3, 128, 128)
    assert flow.dtype == np.float32
    np.testing.assert_allclose(flow[0], pair.flow[1], rtol=1e-6)
    np.testing.assert_allclose(flow[1], pair.flow[0], rtol=1e-6)
    np.testing.assert_array_equal(mask, pair.mask)


def small(**changes):
    """A run of a few steps of the small model, on the CPU."""
    fields = {"model": "small", "steps": 4, "n_pairs": 2, "checkpoint_every": 2}
    return TrainConfig(**{**fields, **changes})


def generator():
    return PairGenerator(chips(), pairs_config(), ranges())


@needs_raft
def test_training_writes_a_checkpoint_the_method_loads(tmp_path):
    import torch

    result = training.train(generator(), small(), tmp_path, {"commit": "abc"})

    assert result.checkpoint == tmp_path / CHECKPOINT
    assert [row.step for row in result.log] == [1, 2, 3, 4]
    assert training.read_log(tmp_path / training.LOG) == result.log
    assert len(result.epe_before) == len(result.epe_after) == 2
    state = training.load_checkpoint(result.checkpoint)
    assert state["step"] == 4
    assert state["commit"] == "abc"
    assert state["train"] == dataclasses.asdict(small())
    method = Raft(model="small", checkpoint=str(result.checkpoint))
    network = method.network()
    assert not network.training
    for name, value in network.state_dict().items():
        assert torch.equal(value, state["model"][name]), name
    pair = generator()(0)
    assert method(pair.reference, pair.moving).field((128, 128)).shape == (2, 128, 128)


@needs_raft
def test_a_resumed_run_ends_where_an_uninterrupted_one_does(tmp_path):
    import torch

    whole = training.train(generator(), small(), tmp_path / "whole")
    training.train(generator(), small(), tmp_path / "cut", stop_at=2)
    resumed = training.train(generator(), small(), tmp_path / "cut", resume=True)

    assert (resumed.first_step, resumed.last_step) == (2, 4)
    assert resumed.log[:2] == training.read_log(tmp_path / "cut" / training.LOG)[:2]
    assert [row.loss for row in resumed.log] == [row.loss for row in whole.log]
    one, other = (
        training.load_checkpoint(r.checkpoint)["model"] for r in (whole, resumed)
    )
    for name, value in one.items():
        assert torch.equal(value, other[name]), name


@needs_raft
def test_a_run_neither_overwrites_a_checkpoint_nor_resumes_another_run(tmp_path):
    training.train(generator(), small(), tmp_path, stop_at=1)

    with pytest.raises(FileExistsError, match="resume it, or train in another"):
        training.train(generator(), small(), tmp_path)
    with pytest.raises(ValueError, match=r"another run: its \[train\] differs"):
        training.train(generator(), small(learning_rate=1e-3), tmp_path, resume=True)
    with pytest.raises(FileNotFoundError, match="no checkpoint to resume"):
        training.train(generator(), small(), tmp_path / "nowhere", resume=True)


@needs_raft
def test_every_parameter_trains_and_batch_normalisation_is_frozen():
    import torch

    network = training.build_network(TrainConfig(model="large"))

    norms = [m for m in network.modules() if isinstance(m, torch.nn.BatchNorm2d)]
    assert len(norms) == 15
    assert not any(m.training for m in norms)
    assert network.training
    assert all(p.requires_grad for p in network.parameters())
    thawed = training.set_training(network, TrainConfig(freeze_batch_norm=False))
    assert all(m.training for m in thawed.modules())


@needs_raft
def test_a_checkpoint_of_the_other_model_is_refused(tmp_path):
    result = training.train(generator(), small(steps=1), tmp_path)

    with pytest.raises(ValueError, match="holds a small model, the method asks for"):
        Raft(model="large", checkpoint=str(result.checkpoint)).network()


@needs_torch
def test_a_method_without_its_checkpoint_says_where_it_should_be(tmp_path):
    method = Raft(checkpoint=str(tmp_path / "none.pt"))

    with pytest.raises(FileNotFoundError, match=r"no checkpoint at .*none\.pt"):
        method.network()


def test_the_fine_tuned_methods_load_a_checkpoint_from_a_local_path():
    methods = load_methods(CONFIGS / "methods.toml")

    for model, name in METHOD_NAMES.items():
        assert methods[name] == Raft(
            model=model, checkpoint=f"outputs/train/{name}/checkpoint.pt"
        )


@needs_torch
def test_a_benchmark_of_a_method_without_its_checkpoint_is_refused(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    args = ["benchmark", "--pairs", "1", "--methods", "raft_ft", "--out", "out"]
    for option, name in (("--methods", "methods"), ("--degradations", "degradations")):
        args += [f"{option}-config", str(CONFIGS / f"{name}.toml")]

    with pytest.raises(SystemExit, match="raft_ft needs its checkpoint at outputs"):
        main(args)


def _fine_tuned(name):
    """The repository's fine-tuned method, skipping the test without its weights."""
    if deep.missing_modules():
        pytest.skip("needs the dl extra: make install-dl")
    method = load_methods(CONFIGS / "methods.toml")[name]
    checkpoint = REPO / method.checkpoint
    if not checkpoint.is_file():
        pytest.skip(f"needs {name}'s checkpoint at {checkpoint}: satreg train")
    return dataclasses.replace(method, checkpoint=str(checkpoint))


@pytest.mark.parametrize("name", METHOD_NAMES.values())
def test_a_fine_tuned_method_gives_a_dense_displacement(name):
    method = _fine_tuned(name)
    pair = generator()(0)

    field = method(pair.reference, pair.moving).field(pair.reference.shape)

    assert field.shape == (2, 128, 128)
    assert np.isfinite(field).all()


def train_args(tmp_path, scenes):  # noqa: F811
    """The arguments of ``train`` on the cached fixture chip, small and short."""
    args = cached(tmp_path, scenes)
    config = Path(args[args.index("--pairs-config") + 1])
    config.write_text(
        config.read_text()
        + '[train]\nmodel = "small"\nsteps = 3\nn_pairs = 2\ncheckpoint_every = 2\n'
    )
    args[args.index("--pairs-config")] = "--config"
    return ["train"] + args[1:]


@needs_raft
def test_train_writes_the_checkpoint_and_the_run_next_to_it(
    tmp_path,
    capsys,
    scenes,  # noqa: F811
):
    args = train_args(tmp_path, scenes)

    main(args + ["--stop-at", "2"])
    main(args + ["--resume"])

    printed = capsys.readouterr().out
    out = tmp_path / "out"
    assert printed.endswith((out / "summary.md").read_text())
    assert "RAFT small fine-tuned on the first 2 pairs" in printed
    assert "steps 3 to 3 of 3, batches of 2, on cpu" in printed
    assert "- pretrained weights: " in printed
    assert (out / CHECKPOINT).is_file()
    assert len((out / "log.csv").read_text().splitlines()) == 4
    context = json.loads((out / "context.json").read_text())
    assert context["train"]["model"] == "small"
    assert context["pairs"]["size"] == 128
    assert context["chips"] == ["place"]
    assert "commit" in context
    assert [session["steps"] for session in context["sessions"]] == [[0, 2], [2, 3]]


@needs_raft
def test_train_refuses_to_start_over_a_checkpoint(tmp_path, scenes):  # noqa: F811
    args = train_args(tmp_path, scenes)
    main(args + ["--stop-at", "1"])

    with pytest.raises(SystemExit, match="satreg: .*checkpoint.pt exists"):
        main(args)


def test_the_log_is_summed_up_by_stretches_of_steps():
    log = [training.LogRow(i + 1, 1.0 / (i + 1), 0.5, 1e-4, 2.0) for i in range(6)]

    table = log_markdown(log, parts=3)

    assert table.splitlines()[2] == "| 1-2 | 0.7500 | 0.5000 | 1.00e-04 | 2.00 |"
    assert len(table.splitlines()) == 5

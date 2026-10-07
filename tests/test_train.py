import dataclasses
import json
import math
from pathlib import Path

import numpy as np
import pytest
from test_ingest import site_at
from test_raft import needs_raft
from test_real import CONFIG
from test_trainchips import SITES_TOML, scenes  # noqa: F401
from test_trainpairs import cached, chips, pairs_config, ranges

from satreg import cli, compute
from satreg import train as training
from satreg.cli import main
from satreg.methods import deep, load_methods
from satreg.methods.raft import Raft
from satreg.sites import load_sites
from satreg.train import (
    BEST,
    CHECKPOINT,
    LOCAL_METHOD_NAMES,
    METHOD_NAMES,
    Batches,
    LogRow,
    Timing,
    TrainConfig,
    load_train_config,
    log_markdown,
    pair_arrays,
    pair_indices,
)
from satreg.trainchips import TRAIN, VALIDATION, load_training_chips
from satreg.trainpairs import PairGenerator, load_training_series
from satreg.trainval import ALL_PRESETS, ValidationRow, read_validations
from satreg.validation import load_validation_chips

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
        ({"validate_every": -1}, "validate_every and workers must not be negative"),
        ({"workers": -1}, "validate_every and workers must not be negative"),
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


def test_a_training_still_at_work_is_read_from_its_local_path():
    methods = load_methods(CONFIGS / "methods.toml")

    # Where satreg train writes by default, named after the model's method.
    for model, name in METHOD_NAMES.items():
        assert methods[LOCAL_METHOD_NAMES[model]] == Raft(
            model=model, checkpoint=f"outputs/train/{name}/checkpoint.pt"
        )


@needs_torch
def test_a_benchmark_of_a_method_without_its_checkpoint_is_refused(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    args = ["benchmark", "--pairs", "1", "--methods", "raft_ft_local", "--out", "out"]
    for option, name in (("--methods", "methods"), ("--degradations", "degradations")):
        args += [f"{option}-config", str(CONFIGS / f"{name}.toml")]

    with pytest.raises(SystemExit, match="raft_ft_local needs its checkpoint at out"):
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


@pytest.mark.parametrize("name", LOCAL_METHOD_NAMES.values())
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
def test_the_machine_of_a_session_is_described_once_it_has_trained(
    tmp_path,
    monkeypatch,
    scenes,  # noqa: F811
):
    # PyTorch is loaded by the training: described before it, the session has
    # no GPU and no PyTorch threads (seen on Kaggle, "gpu": null on a T4).
    described_after = []

    def environment():
        described_after.append((tmp_path / "out" / CHECKPOINT).is_file())
        return compute.environment()

    monkeypatch.setattr(cli, "environment", environment)

    main(train_args(tmp_path, scenes))

    assert described_after == [True]


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
    log = [LogRow(i + 1, 1.0 / (i + 1), 0.5, 1e-4, 2.0, 0.5) for i in range(6)]

    table = log_markdown(log, parts=3)

    assert table.splitlines()[2] == "| 1-2 | 0.7500 | 0.5000 | 1.00e-04 | 2.00 | 25 % |"
    assert len(table.splitlines()) == 5


def test_a_session_s_speed_leaves_its_first_step_out():
    # The first step pays for starting the device and the workers.
    log = [LogRow(1, 1.0, 0.5, 1e-4, 30.0, 20.0)]
    log += [
        LogRow(i, 1.0, 0.5, 1e-4, seconds, 0.5) for i, seconds in ((2, 1.0), (3, 3.0))
    ]

    assert training.timing(log, batch_size=8) == Timing(
        steps=2, seconds_per_step=2.0, pair_share=0.25, pairs_per_second=4.0
    )
    assert training.timing(log[:1], batch_size=8).seconds_per_step == 30.0
    assert training.timing([], batch_size=8) is None


def test_a_log_written_before_the_pairs_were_timed_is_still_read(tmp_path):
    path = tmp_path / "log.csv"
    path.write_text("step,loss,epe,learning_rate,seconds\n1,0.5,0.25,0.0001,2.0\n")

    (row,) = training.read_log(path)

    assert (row.step, row.loss, row.seconds) == (1, 0.5, 2.0)
    assert math.isnan(row.pair_seconds)


class Scores:
    """A validation set that gives each step a score fixed in advance."""

    def __init__(self, **scores):
        self.scores = {int(step[1:]): score for step, score in scores.items()}
        self.training = []

    def __call__(self, network, step):
        self.training.append(network.training)
        score = self.scores[step]
        return [
            ValidationRow(step, "clean", 2, score, score, 0.0, 0.1),
            ValidationRow(step, ALL_PRESETS, 2, score, score, 0.0, 0.1),
        ]


def weights(path):
    return training.load_checkpoint(path)["model"]


def same_weights(one, other):
    import torch

    return all(torch.equal(value, other[name]) for name, value in one.items())


@needs_raft
def test_a_run_keeps_the_weights_of_its_best_validation(tmp_path):
    config = small(validate_every=2)
    scores = Scores(s0=0.1, s2=0.2, s4=0.3)

    result = training.train(generator(), config, tmp_path / "whole", validate=scores)
    training.train(generator(), small(), tmp_path / "cut", stop_at=2)

    # The pretrained weights score best here, and are a reference only.
    assert [(r.step, r.degradation) for r in result.validations] == [
        (0, "clean"),
        (0, ALL_PRESETS),
        (2, "clean"),
        (2, ALL_PRESETS),
        (4, "clean"),
        (4, ALL_PRESETS),
    ]
    assert result.best.step == 2
    assert scores.training == [False, False, False]
    assert read_validations(tmp_path / "whole" / training.VALIDATIONS) == (
        result.validations
    )
    kept = training.load_checkpoint(tmp_path / "whole" / BEST)
    assert kept["step"] == 2
    assert kept["validation"]["score"] == 0.2
    assert kept["train"] == dataclasses.asdict(config)
    assert same_weights(kept["model"], weights(tmp_path / "cut" / CHECKPOINT))
    assert not same_weights(kept["model"], weights(result.checkpoint))
    method = Raft(model="small", checkpoint=str(tmp_path / "whole" / BEST))
    assert same_weights(method.network().state_dict(), kept["model"])


@needs_raft
def test_validating_does_not_change_what_a_run_learns(tmp_path):
    scores = Scores(s0=0.5, s2=0.4, s4=0.3)

    plain = training.train(generator(), small(), tmp_path / "plain")
    validated = training.train(
        generator(), small(validate_every=2), tmp_path / "validated", validate=scores
    )

    assert [r.loss for r in validated.log] == [r.loss for r in plain.log]
    assert validated.best.step == 4
    assert same_weights(
        weights(tmp_path / "validated" / BEST), weights(validated.checkpoint)
    )


@needs_raft
def test_a_resumed_run_validates_and_keeps_as_an_uninterrupted_one(tmp_path):
    config = small(steps=6, validate_every=2)
    scores = dict(s0=0.5, s2=0.4, s4=0.2, s6=0.3)
    whole, cut = tmp_path / "whole", tmp_path / "cut"

    one = training.train(generator(), config, whole, validate=Scores(**scores))
    training.train(generator(), config, cut, stop_at=3, validate=Scores(**scores))
    resumed = Scores(**scores)
    other = training.train(generator(), config, cut, resume=True, validate=resumed)

    # The pretrained weights and step 2 were validated by the first session.
    assert len(resumed.training) == 2
    assert other.validations == one.validations
    assert other.best.step == 4
    assert same_weights(weights(cut / BEST), weights(whole / BEST))


@needs_raft
def test_a_run_that_validates_needs_a_validation_set(tmp_path):
    with pytest.raises(ValueError, match="needs a validation set"):
        training.train(generator(), small(validate_every=2), tmp_path)


@needs_raft
def test_a_session_out_of_time_stops_with_a_checkpoint_to_resume(tmp_path):
    whole = training.train(generator(), small(), tmp_path / "whole")

    cut = training.train(generator(), small(), tmp_path / "cut", budget_seconds=0.0)
    # The device and the workers are the session's, not the run's.
    resumed = training.train(
        generator(), small(workers=1), tmp_path / "cut", resume=True
    )

    assert (cut.first_step, cut.last_step) == (0, 1)
    assert training.load_checkpoint(cut.checkpoint)["step"] == 4
    assert (resumed.first_step, resumed.last_step) == (1, 4)
    assert [row.loss for row in resumed.log] == [row.loss for row in whole.log]
    assert same_weights(weights(resumed.checkpoint), weights(whole.checkpoint))


@needs_raft
def test_a_checkpoint_older_than_a_setting_resumes_with_its_default(tmp_path):
    import torch

    result = training.train(generator(), small(), tmp_path, stop_at=2)
    state = training.load_checkpoint(result.checkpoint)
    for key in ("validate_every", "workers"):
        del state["train"][key]
    torch.save(state, result.checkpoint)

    resumed = training.train(generator(), small(), tmp_path, resume=True)

    assert resumed.last_step == 4
    with pytest.raises(ValueError, match=r"another run: its \[train\] differs"):
        training.train(
            generator(),
            small(validate_every=2),
            tmp_path,
            resume=True,
            validate=Scores(),
        )


@needs_torch
def test_worker_processes_prepare_the_batches_a_single_process_makes():
    import torch

    config = TrainConfig(steps=3, batch_size=2)
    alone = Batches(generator(), config)
    helped = Batches(generator(), dataclasses.replace(config, workers=2))

    try:
        for step in (0, 1, 2):
            for one, other in zip(alone(step), helped(step), strict=True):
                assert torch.equal(one, other)
    finally:
        helped.close()

    assert helped._pool is None


def validating_args(tmp_path, scenes):  # noqa: F811
    """The arguments of ``train`` for a run that validates, on two cached chips.

    The fixture grid is 300 x 400 px: a training chip in its north-west corner
    and a validation chip in its south-east one, far enough to be told apart.
    """
    chips = {
        "place": (site_at(88, 88, chip_px=176, name="place"), TRAIN, "forest"),
        "town": (site_at(212, 312, chip_px=176, name="town"), VALIDATION, "urban"),
    }
    declared = "[defaults]\nstart = 2025-04-01\nend = 2025-09-30\nmax_cloud = 5.0\n"
    for name, (site, role, landscape) in chips.items():
        declared += (
            f'[chips.{name}]\nlandscape = "{landscape}"\nrole = "{role}"\n'
            f"lon = {site.lon}\nlat = {site.lat}\nchip_px = {site.chip_px}\n"
        )
    (tmp_path / "sites.toml").write_text(SITES_TOML)
    (tmp_path / "train-sites.toml").write_text(declared)
    (tmp_path / "real.toml").write_text(
        '[series]\nsites = ["beauce"]\nmax_scene_cloud = 50.0\n[series.dates]\n'
        "days = { offset_days = 0, within_days = 15 }\n"
        "season = { offset_days = 91, within_days = 30 }\n"
    )
    (tmp_path / "train.toml").write_text(
        '[train]\nmodel = "small"\nsteps = 3\nn_pairs = 2\ncheckpoint_every = 2\n'
        "validate_every = 2\n[pairs]\nsize = 128\ncross_date = 0.5\nseed = 3\n"
    )
    (tmp_path / "validation.toml").write_text(
        '[validate]\nchips = ["town"]\nscenarios = ["translation"]\n'
        'degradations = ["clean", "hard"]\npairs = 4\nlight_pairs = 2\nsize = 128\n'
        f'degradations_config = "{CONFIGS / "degradations.toml"}"\n'
    )
    config = load_training_chips(
        tmp_path / "train-sites.toml", load_sites(tmp_path / "sites.toml")
    )
    load_training_series(config, CONFIG, tmp_path / "data", None, scenes)
    load_validation_chips(config, CONFIG, tmp_path / "data", None, scenes)
    args = [
        "train",
        "--out",
        str(tmp_path / "out"),
        "--data-dir",
        str(tmp_path / "data"),
    ]
    for option, name in (
        ("--config", "train"),
        ("--validation-config", "validation"),
        ("--sites-config", "sites"),
        ("--train-config", "train-sites"),
        ("--series-config", "real"),
    ):
        args += [option, str(tmp_path / f"{name}.toml")]
    return args + ["--degradations-config", str(CONFIGS / "degradations.toml")]


@needs_raft
def test_train_validates_on_the_light_set_and_says_what_it_kept(
    tmp_path,
    capsys,
    scenes,  # noqa: F811
):
    args = validating_args(tmp_path, scenes)

    main(args + ["--max-minutes", "60"])

    printed = capsys.readouterr().out
    out = tmp_path / "out"
    assert "Light validation set (4 pairs), every 2 steps" in printed
    assert "| step | score (px) | clean: EPE (px) | failures | hard: EPE" in printed
    assert "Speed of this session, over 2 steps: " in printed
    assert "with 0 worker process(es)." in printed
    rows = read_validations(out / "validation.csv")
    assert [r.step for r in rows if r.degradation == ALL_PRESETS] == [0, 2, 3]
    assert [r.pairs for r in rows[:3]] == [2, 2, 4]
    kept = training.load_checkpoint(out / BEST)
    assert f"Kept: step {kept['step']}, score " in printed
    assert f"in {out / BEST}." in printed
    context = json.loads((out / "context.json").read_text())
    assert list(context["validation"]["chips"]) == ["town"]
    assert context["validation"]["pairs"] == 4
    assert context["validation"]["kept"]["step"] == kept["step"]
    assert context["sessions"][0]["timing"]["steps"] == 2
    assert context["sessions"][0]["peak_gpu_mib"] is None


@needs_raft
def test_train_stops_when_its_minutes_are_up(tmp_path, capsys, scenes):  # noqa: F811
    args = train_args(tmp_path, scenes)

    main(args + ["--max-minutes", "1e-9"])

    assert "steps 1 to 1 of 3" in capsys.readouterr().out
    with pytest.raises(SystemExit, match="need --max-minutes > 0"):
        main(args + ["--resume", "--max-minutes", "0"])

"""Fine-tuning RAFT on training pairs (N3).

The recipe is the one of RAFT's own fine-tuning stages, read from the original
training script and from torchvision's reference script: the sequence loss on
the pixels the loss mask keeps, AdamW under a one-cycle learning rate, the
gradient's norm clipped, batch normalisation frozen, every parameter trained.
Every few steps the network is scored on the light validation set, and the run
keeps the weights of its best validation next to its last checkpoint.
The network starts from the torchvision weights the ``raft`` method runs and
sees its pairs as that method sees a benchmark pair. A run writes a checkpoint
it can resume from, which the ``raft`` method loads from its path. Needs the
``dl`` extra. See docs/decisions.md.
"""

import csv
import dataclasses
import logging
import math
import multiprocessing
import os
import statistics
import tomllib
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import Future, ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from . import trainval
from .compute import MIB
from .methods import deep, raft
from .trainpairs import PairGenerator, TrainingPair
from .trainval import ValidationRow

logger = logging.getLogger(__name__)

# A pixel whose true flow is at least this long, in px, is left out of the
# loss, as in the reference scripts. Training pairs move by a few pixels, so
# it never applies here; kept so that the loss is the reference one.
MAX_FLOW = 400.0

# Shape of the one-cycle learning rate, as in the reference scripts: the share
# of the steps spent rising to the peak, linearly, before the linear descent.
WARMUP_SHARE = 0.05

# AdamW's epsilon in the reference scripts.
ADAM_EPS = 1e-8

CHECKPOINT = "checkpoint.pt"
LOG = "log.csv"
# The weights of the run's best validation, and its validations.
BEST = "best.pt"
VALIDATIONS = "validation.csv"

# Steps whose pairs worker processes prepare ahead of the training loop.
STEPS_AHEAD = 4

# Keys of a run's configuration that may change between two sessions: they say
# where and how fast the run is computed, not what it computes.
SESSION_KEYS = ("device", "workers")

# Scores a network in evaluation mode after a number of steps.
Validate = Callable[[Any, int], list[ValidationRow]]

# Fine-tuned method each model's checkpoint is for, in configs/methods.toml.
METHOD_NAMES = {"large": "raft_ft", "small": "raft_small_ft"}


@dataclass(frozen=True)
class TrainConfig:
    """A training run, besides what its pairs are made of.

    Attributes:
        model: ``"large"`` or ``"small"``, as in the ``raft`` method.
        steps: Optimiser steps of the whole run.
        batch_size: Pairs per step.
        learning_rate: Peak of the one-cycle learning rate.
        weight_decay: AdamW's weight decay.
        gamma: Weight of a refinement's loss relative to the next one's, in
            (0, 1]: the last refinement weighs 1, the one before ``gamma``.
        iterations: Recurrent refinements of the flow, as at inference.
        clip: Largest norm of the gradient, larger ones are scaled down to it.
        freeze_batch_norm: Keep the batch-normalisation layers on the
            statistics of the pretrained weights instead of the batches'.
        n_pairs: Distinct pairs the run cycles over, the first ones; 0 for a
            new pair at every draw. A few pairs make an overfit test.
        checkpoint_every: Steps between two checkpoints; one is always written
            at the end.
        validate_every: Steps between two validations on the light validation
            set, the last step being one too; 0 for none.
        workers: Processes that prepare the pairs ahead of the loop; 0 to make
            them in the loop itself. The pairs are the same either way.
        device: ``"cpu"``, ``"mps"`` or ``"cuda"``.
    """

    model: str = "large"
    steps: int = 100
    batch_size: int = 2
    learning_rate: float = 1e-4
    weight_decay: float = 1e-5
    gamma: float = 0.85
    iterations: int = 12
    clip: float = 1.0
    freeze_batch_norm: bool = True
    n_pairs: int = 0
    checkpoint_every: int = 100
    validate_every: int = 0
    workers: int = 0
    device: str = "cpu"

    def __post_init__(self) -> None:
        if self.model not in raft.MODELS:
            raise ValueError(
                f"model must be one of {', '.join(raft.MODELS)}, got {self.model!r}"
            )
        for name in ("steps", "batch_size", "iterations", "checkpoint_every"):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be positive, got {getattr(self, name)}")
        for name in ("learning_rate", "clip"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive, got {getattr(self, name)}")
        if self.weight_decay < 0 or self.n_pairs < 0:
            raise ValueError("weight_decay and n_pairs must not be negative")
        if self.validate_every < 0 or self.workers < 0:
            raise ValueError("validate_every and workers must not be negative")
        if not 0 < self.gamma <= 1:
            raise ValueError(f"gamma must be in (0, 1], got {self.gamma}")
        deep.check_device(self.device)


def load_train_config(path: Path) -> TrainConfig:
    """Read a training run's configuration.

    Args:
        path: TOML file with a ``[train]`` table whose keys are the attributes
            of ``TrainConfig``; a key left out takes its default.

    Returns:
        The configuration.

    Raises:
        ValueError: If the table is missing or has unknown or invalid keys.
    """
    with path.open("rb") as f:
        raw = tomllib.load(f)
    if "train" not in raw:
        raise ValueError(f"{path} needs a [train] table")
    known = [f.name for f in dataclasses.fields(TrainConfig)]
    if unknown := sorted(set(raw["train"]) - set(known)):
        raise ValueError(
            f"{path}: [train]: unknown key {unknown[0]!r} (keys: {', '.join(known)})"
        )
    try:
        return TrainConfig(**raw["train"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{path}: [train]: {exc}") from exc


def sequence_loss(
    predictions: Sequence[Any],
    flow: Any,
    mask: Any,
    gamma: float = 0.8,
    max_flow: float = MAX_FLOW,
) -> Any:
    """RAFT's sequence loss: the L1 error of every refinement, later ones heavier.

    As in the reference scripts, the error of a refinement is averaged over
    every pixel and both components, masked pixels counting for zero, and
    refinement ``i`` of ``n`` weighs ``gamma ** (n - 1 - i)``.

    Args:
        predictions: The flow after each refinement, first to last, each a
            tensor of shape ``(batch, 2, rows, cols)``.
        flow: True flow, same shape and component order as a prediction.
        mask: Pixels the loss may use, boolean, ``(batch, rows, cols)``.
        gamma: Weight of a refinement relative to the next one.
        max_flow: Pixels whose true flow is at least this long are left out.

    Returns:
        The loss, a scalar tensor.
    """
    import torch

    valid = mask & (torch.linalg.vector_norm(flow, dim=1) < max_flow)
    stacked = torch.stack(tuple(predictions))
    error = (stacked - flow).abs() * valid[None, :, None]
    per_refinement = error.mean(dim=(1, 2, 3, 4))
    n = len(per_refinement)
    weights = gamma ** torch.arange(n - 1, -1, -1, device=flow.device)
    return (per_refinement * weights.to(per_refinement.dtype)).sum()


def masked_epe(prediction: Any, flow: Any, mask: Any) -> Any:
    """Mean end-point error of each pair over the pixels its mask keeps.

    Args:
        prediction: Predicted flow, ``(batch, 2, rows, cols)``.
        flow: True flow, same shape.
        mask: Pixels counted, boolean, ``(batch, rows, cols)``.

    Returns:
        One value per pair, in px; NaN for a pair whose mask keeps nothing.
    """
    import torch

    error = torch.linalg.vector_norm(prediction - flow, dim=1) * mask
    return error.sum(dim=(1, 2)) / mask.sum(dim=(1, 2))


def pair_arrays(pair: TrainingPair) -> tuple[np.ndarray, ...]:
    """A training pair as the network and the loss take it.

    Args:
        pair: The pair.

    Returns:
        Reference and moving image, ``(3, rows, cols)`` float32; the true flow
        in the network's ``(dx, dy)`` order, ``(2, rows, cols)`` float32; the
        loss mask, ``(rows, cols)`` boolean.
    """
    reference, moving = pair.network_inputs()
    # The package's flow is (dy, dx), torchvision's RAFT gives (dx, dy).
    flow = np.ascontiguousarray(pair.flow[::-1], dtype=np.float32)
    return reference, moving, flow, pair.mask


def pair_indices(step: int, config: TrainConfig) -> list[int]:
    """Indices of the pairs of one step's batch.

    A pair depends on its index alone, so a run resumed at a step sees the
    pairs it would have seen uninterrupted.

    Args:
        step: Step, from 0.
        config: The run's configuration.

    Returns:
        ``batch_size`` indices: consecutive ones, cycling over the first
        ``n_pairs`` if it is set.
    """
    first = step * config.batch_size
    indices = range(first, first + config.batch_size)
    return [i % config.n_pairs if config.n_pairs else i for i in indices]


# The generator of a worker process, set once when the process starts.
_GENERATOR: PairGenerator | None = None


def _start_worker(generator: PairGenerator) -> None:
    global _GENERATOR
    _GENERATOR = generator


def _worker_arrays(index: int) -> tuple[np.ndarray, ...]:
    return pair_arrays(_GENERATOR(index))


class Batches:
    """Batches of training pairs by step, as tensors on the run's device.

    With ``config.workers``, worker processes prepare the pairs of the next
    steps while the network trains on the current one. A pair depends on its
    index alone, so the batches are the ones a single process makes.
    """

    def __init__(self, generator: PairGenerator, config: TrainConfig) -> None:
        self.generator = generator
        self.config = config
        # The pairs of a run that cycles over a few, made once.
        self._kept: dict[int, tuple[np.ndarray, ...]] = {}
        self._pool: ProcessPoolExecutor | None = None
        self._ahead: dict[int, list[Future]] = {}

    def _arrays(self, index: int) -> tuple[np.ndarray, ...]:
        if not self.config.n_pairs:
            return pair_arrays(self.generator(index))
        if index not in self._kept:
            self._kept[index] = pair_arrays(self.generator(index))
        return self._kept[index]

    def _prepared(self, step: int) -> list[tuple[np.ndarray, ...]]:
        """The pairs of a step from the workers, the next steps being queued."""
        if self._pool is None:
            # Started afresh, not forked: the parent may hold a CUDA context
            # and threads, which a fork would copy in an unusable state.
            self._pool = ProcessPoolExecutor(
                self.config.workers,
                mp_context=multiprocessing.get_context("spawn"),
                initializer=_start_worker,
                initargs=(self.generator,),
            )
        last = min(step + STEPS_AHEAD, self.config.steps - 1)
        for ahead in range(step, last + 1):
            if ahead not in self._ahead:
                indices = pair_indices(ahead, self.config)
                self._ahead[ahead] = [
                    self._pool.submit(_worker_arrays, i) for i in indices
                ]
        return [future.result() for future in self._ahead.pop(step)]

    def of(self, indices: Sequence[int]) -> tuple[Any, ...]:
        """Stack pairs into one batch: images, flow and mask."""
        return self._stack([self._arrays(i) for i in indices])

    def _stack(self, pairs: Sequence[tuple[np.ndarray, ...]]) -> tuple[Any, ...]:
        import torch

        return tuple(
            torch.from_numpy(np.stack(column)).to(self.config.device)
            for column in zip(*pairs, strict=True)
        )

    def __call__(self, step: int) -> tuple[Any, ...]:
        """The batch of a step."""
        if self.config.workers and not self.config.n_pairs:
            return self._stack(self._prepared(step))
        return self.of(pair_indices(step, self.config))

    def close(self) -> None:
        """Stop the worker processes, dropping the pairs still queued."""
        if self._pool is not None:
            self._pool.shutdown(cancel_futures=True)
            self._pool, self._ahead = None, {}


def build_network(config: TrainConfig) -> Any:
    """Build the network a run starts from, in training mode.

    Args:
        config: The run's configuration.

    Returns:
        The model with its pretrained torchvision weights, on the run's device,
        every parameter trainable. Not the copy the ``raft`` method runs.

    Raises:
        RuntimeError: If the device is not available on this machine.
    """
    deep.check_available(config.device)
    method = raft.Raft(model=config.model)
    network = raft.builder(config.model)(weights=method.weights(), progress=False)
    return set_training(network.to(config.device), config)


def set_training(network: Any, config: TrainConfig) -> Any:
    """Put a network in training mode, batch normalisation frozen if asked.

    A frozen batch-normalisation layer keeps the running statistics of the
    pretrained weights; its scale and offset still train. To call again after
    the network was put in evaluation mode.

    Args:
        network: The network.
        config: The run's configuration.

    Returns:
        The network.
    """
    import torch

    network.train()
    if config.freeze_batch_norm:
        for module in network.modules():
            if isinstance(module, torch.nn.BatchNorm2d):
                module.eval()
    return network


def optimiser_and_schedule(network: Any, config: TrainConfig) -> tuple[Any, Any]:
    """The optimiser and learning-rate schedule of the reference scripts.

    Args:
        network: The network to train.
        config: The run's configuration.

    Returns:
        AdamW over every parameter, and a one-cycle schedule over the run's
        steps, rising then falling linearly.
    """
    import torch

    optimiser = torch.optim.AdamW(
        network.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
        eps=ADAM_EPS,
    )
    schedule = torch.optim.lr_scheduler.OneCycleLR(
        optimiser,
        max_lr=config.learning_rate,
        total_steps=config.steps,
        pct_start=WARMUP_SHARE,
        cycle_momentum=False,
        anneal_strategy="linear",
    )
    return optimiser, schedule


def evaluate(network: Any, batches: Batches, indices: Sequence[int]) -> list[float]:
    """End-point error of a network on training pairs, as at inference.

    Args:
        network: The network; left in training mode.
        batches: Where the pairs come from.
        indices: Indices of the pairs.

    Returns:
        The masked end-point error of the last refinement on each pair, in px.
    """
    import torch

    config = batches.config
    network.eval()
    errors = []
    with torch.inference_mode():
        for index in indices:
            reference, moving, flow, mask = batches.of([index])
            predictions = network(reference, moving, num_flow_updates=config.iterations)
            errors.append(float(masked_epe(predictions[-1], flow, mask)))
    set_training(network, config)
    return errors


@dataclass(frozen=True)
class LogRow:
    """One training step.

    Attributes:
        step: Step, from 1.
        loss: Sequence loss of the step's batch.
        epe: Mean end-point error of the last refinement over the batch's
            masked pixels, in px, in training mode.
        learning_rate: Learning rate of the step.
        seconds: Time the step took, its pairs included.
        pair_seconds: The part of it spent getting the batch: making the pairs,
            or waiting for the workers to hand them over, and moving them to
            the device. NaN in a log written before this was recorded.
    """

    step: int
    loss: float
    epe: float
    learning_rate: float
    seconds: float
    pair_seconds: float = math.nan


@dataclass(frozen=True)
class Timing:
    """How fast a session trained.

    Attributes:
        steps: Steps the figures are read on: the session's, but for its first
            one, which pays for starting the device and the workers.
        seconds_per_step: Median time of a step, its pairs included.
        pair_share: Share of the steps' time spent getting their batches.
        pairs_per_second: Pairs the loop consumed per second.
    """

    steps: int
    seconds_per_step: float
    pair_share: float
    pairs_per_second: float


def timing(rows: Sequence[LogRow], batch_size: int) -> Timing | None:
    """Sum up how fast a session trained.

    Args:
        rows: The session's steps.
        batch_size: Pairs per step.

    Returns:
        The session's timing, ``None`` for a session without a step.
    """
    rows = list(rows[1:]) or list(rows)
    if not rows:
        return None
    total = sum(r.seconds for r in rows)
    return Timing(
        steps=len(rows),
        seconds_per_step=statistics.median(r.seconds for r in rows),
        pair_share=sum(r.pair_seconds for r in rows) / total,
        pairs_per_second=batch_size * len(rows) / total,
    )


@dataclass(frozen=True)
class TrainResult:
    """What a training session did.

    Attributes:
        checkpoint: The checkpoint written.
        first_step: Step the session started after, 0 unless it resumed.
        last_step: Step it stopped at.
        log: Every step of the run so far, earlier sessions included.
        epe_before: End-point error of the pretrained network on each pair the
            run cycles over, in px; ``None`` for a run on new pairs or a
            resumed session.
        epe_after: The same for the network as the session left it.
        validations: Every validation of the run so far, earlier sessions
            included; empty for a run without validation.
        peak_mib: Peak memory held by the session's CUDA tensors, the weights
            included, in MiB; ``None`` on another device.
    """

    checkpoint: Path
    first_step: int
    last_step: int
    log: list[LogRow]
    epe_before: list[float] | None
    epe_after: list[float] | None
    validations: list[ValidationRow] = dataclasses.field(default_factory=list)
    peak_mib: float | None = None

    @property
    def best(self) -> ValidationRow | None:
        """The validation whose weights are in ``BEST``, ``None`` before one."""
        return trainval.best(self.validations)


def read_log(path: Path) -> list[LogRow]:
    """Read a run's log, empty if there is none."""
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return [
            LogRow(**{k: int(v) if k == "step" else float(v) for k, v in r.items()})
            for r in csv.DictReader(f)
        ]


def _write_log(rows: Sequence[LogRow], path: Path) -> None:
    with path.open("w", newline="") as f:
        names = [x.name for x in dataclasses.fields(LogRow)]
        writer = csv.DictWriter(f, fieldnames=names)
        writer.writeheader()
        writer.writerows(dataclasses.asdict(row) for row in rows)


def save_checkpoint(
    path: Path,
    network: Any,
    optimiser: Any,
    schedule: Any,
    step: int,
    described: Mapping[str, object],
) -> None:
    """Write what a run needs to go on, and what a method needs to run it.

    The file holds tensors, numbers and text only, so it loads without running
    code. It replaces the previous checkpoint in one move: a session killed
    while writing leaves the previous one whole.

    Args:
        path: The checkpoint file.
        network: The network.
        optimiser: Its optimiser.
        schedule: Its learning-rate schedule.
        step: Steps done.
        described: The run: its ``train`` and ``pairs`` configurations, its
            ``ranges`` and its ``commit``.
    """
    import torch

    # Older versions of PyTorch keep the schedule's anneal function in its
    # state; it is rebuilt with the schedule and is not plain data.
    schedule_state = {k: v for k, v in schedule.state_dict().items() if not callable(v)}
    state = {
        "model": network.state_dict(),
        "optimizer": optimiser.state_dict(),
        "schedule": schedule_state,
        "step": step,
        **described,
    }
    partial = path.with_suffix(".partial")
    torch.save(state, partial)
    os.replace(partial, path)


def save_best(
    path: Path, network: Any, row: ValidationRow, described: Mapping[str, object]
) -> None:
    """Write the weights of a run's best validation so far.

    The file has what a method needs to run the weights, and the validation
    that chose them; a run is resumed from its checkpoint, not from this file.

    Args:
        path: The file.
        network: The network, as validated.
        row: Its validation over all presets.
        described: The run, as in ``save_checkpoint``.
    """
    import torch

    state = {
        "model": network.state_dict(),
        "step": row.step,
        "validation": dataclasses.asdict(row),
        **described,
    }
    partial = path.with_suffix(".partial")
    torch.save(state, partial)
    os.replace(partial, path)


def load_checkpoint(path: Path) -> dict[str, Any]:
    """Read a checkpoint written by ``save_checkpoint``, on the CPU."""
    return raft.read_checkpoint(str(path))


def train(
    generator: PairGenerator,
    config: TrainConfig,
    out: Path,
    described: Mapping[str, object] | None = None,
    resume: bool = False,
    stop_at: int | None = None,
    validate: Validate | None = None,
    budget_seconds: float | None = None,
) -> TrainResult:
    """Fine-tune RAFT on training pairs and write its checkpoint.

    Args:
        generator: Where the pairs come from.
        config: The run's configuration.
        out: Directory of the checkpoint and the log.
        described: What else the checkpoint says of the run, as plain data:
            the pairs configuration, the ranges, the commit.
        resume: Go on from the checkpoint in ``out`` instead of starting.
        stop_at: Stop at this step, short of the run's last, as a session that
            ends does; resuming goes on from there.
        validate: Scores the network on the light validation set; called on the
            pretrained weights, then every ``config.validate_every`` steps and
            at the run's last step. Needed if ``config.validate_every`` is set.
        budget_seconds: Stop at the first step that ends after this long,
            leaving a checkpoint, as a session whose time is up must.

    Returns:
        What the session did.

    Raises:
        FileNotFoundError: If resuming without a checkpoint.
        FileExistsError: If starting where a checkpoint already is.
        ValueError: If the checkpoint resumed is of another run, or the run
            validates and ``validate`` is missing.
        RuntimeError: If the device is not available on this machine.
    """
    import torch

    started = perf_counter()
    if config.validate_every and validate is None:
        raise ValueError("a run with validate_every needs a validation set")
    described = {"train": dataclasses.asdict(config), **(described or {})}
    path, log_path, validations_path = out / CHECKPOINT, out / LOG, out / VALIDATIONS
    network = build_network(config)
    optimiser, schedule = optimiser_and_schedule(network, config)
    batches = Batches(generator, config)
    kept = range(config.n_pairs)

    def validated(step: int) -> list[ValidationRow]:
        network.eval()
        rows = validate(network, step)
        set_training(network, config)
        return rows

    first_step, epe_before = 0, None
    if resume:
        if not path.exists():
            raise FileNotFoundError(f"no checkpoint to resume at {path}")
        state = load_checkpoint(path)
        # The commit, the device and the workers may change between sessions,
        # the run not.
        for key in ("train", "pairs", "ranges"):
            ours, theirs = described.get(key), state.get(key)
            if key == "train":
                # A key the checkpoint predates is at its default there.
                theirs = {**dataclasses.asdict(TrainConfig()), **theirs}
                ours, theirs = (
                    {k: v for k, v in x.items() if k not in SESSION_KEYS}
                    for x in (ours, theirs)
                )
            if ours != theirs:
                raise ValueError(
                    f"{path} is the checkpoint of another run: its [{key}] differs"
                )
        network.load_state_dict(state["model"])
        optimiser.load_state_dict(state["optimizer"])
        schedule.load_state_dict(state["schedule"])
        first_step = state["step"]
    elif path.exists():
        raise FileExistsError(
            f"{path} exists: resume it, or train in another directory"
        )
    elif config.n_pairs:
        epe_before = evaluate(network, batches, kept)

    out.mkdir(parents=True, exist_ok=True)
    log = [row for row in read_log(log_path) if row.step <= first_step]
    validations = [
        row
        for row in trainval.read_validations(validations_path)
        if row.step <= first_step
    ]
    if config.validate_every and not resume:
        # The pretrained weights, on the same pairs: what the run starts from.
        validations.extend(validated(0))
        trainval.write_validations(validations, validations_path)
    on_cuda = config.device == "cuda"
    if on_cuda:
        torch.cuda.reset_peak_memory_stats()

    last_step = min(config.steps, stop_at or config.steps)
    step = first_step
    try:
        for step in range(first_step + 1, last_step + 1):
            start = perf_counter()
            reference, moving, flow, mask = batches(step - 1)
            pair_seconds = perf_counter() - start
            predictions = network(reference, moving, num_flow_updates=config.iterations)
            loss = sequence_loss(predictions, flow, mask, config.gamma)
            optimiser.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(network.parameters(), config.clip)
            learning_rate = schedule.get_last_lr()[0]
            optimiser.step()
            schedule.step()
            epe = float(masked_epe(predictions[-1].detach(), flow, mask).nanmean())
            # Reading the loss waits for the device, so the clock counts the
            # whole step.
            loss_value = float(loss.detach())
            seconds = perf_counter() - start
            row = LogRow(step, loss_value, epe, learning_rate, seconds, pair_seconds)
            log.append(row)

            validating = config.validate_every and (
                step % config.validate_every == 0 or step == config.steps
            )
            out_of_time = (
                budget_seconds is not None and perf_counter() - started > budget_seconds
            )
            if validating:
                before = trainval.best(validations)
                rows = validated(step)
                validations.extend(rows)
                # Written before the checkpoint: a session killed in between
                # validates this step again on resuming and writes the same.
                if before is None or rows[-1].score < before.score:
                    save_best(out / BEST, network, rows[-1], described)
                logger.info(
                    "step %d: validation score %.4f px (best so far: step %d)",
                    step,
                    rows[-1].score,
                    trainval.best(validations).step,
                )
            last = step == last_step or out_of_time
            if validating or last or step % config.checkpoint_every == 0:
                save_checkpoint(path, network, optimiser, schedule, step, described)
                _write_log(log, log_path)
                if validations:
                    trainval.write_validations(validations, validations_path)
                logger.info(
                    "step %d of %d: loss %.4f, EPE %.4f px",
                    step,
                    config.steps,
                    row.loss,
                    epe,
                )
            if out_of_time:
                break
    finally:
        batches.close()

    peak_mib = torch.cuda.max_memory_allocated() / MIB if on_cuda else None
    epe_after = evaluate(network, batches, kept) if config.n_pairs else None
    return TrainResult(
        path, first_step, step, log, epe_before, epe_after, validations, peak_mib
    )


def log_markdown(log: Sequence[LogRow], parts: int = 10) -> str:
    """Render a run's log as markdown, averaged over consecutive stretches.

    Args:
        log: The run's steps.
        parts: Most rows of the table.

    Returns:
        The table, ending with a newline: steps, mean loss, mean training
        end-point error, last learning rate, mean time per step and the
        share of that time spent getting the batches.
    """
    header = (
        "| steps | loss | EPE (px) | learning rate | s/step | pairs |\n"
        "|---|---:|---:|---:|---:|---:|\n"
    )
    lines = []
    for chunk in np.array_split(np.arange(len(log)), min(parts, len(log))):
        rows = [log[i] for i in chunk]
        seconds = sum(r.seconds for r in rows)
        lines.append(
            f"| {rows[0].step}-{rows[-1].step} "
            f"| {np.mean([r.loss for r in rows]):.4f} "
            f"| {np.nanmean([r.epe for r in rows]):.4f} "
            f"| {rows[-1].learning_rate:.2e} "
            f"| {seconds / len(rows):.2f} "
            f"| {100 * sum(r.pair_seconds for r in rows) / seconds:.0f} % |\n"
        )
    return header + "".join(lines)

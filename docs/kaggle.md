# Running on a Kaggle GPU

Two notebooks: the benchmark, below, and the N3 trainings
([Training on a Kaggle GPU](#training-on-a-kaggle-gpu)).

The M1 has no CUDA device, so the deep-learning methods' GPU rows come from a
Kaggle notebook: [`kaggle/satreg-gpu-benchmark.ipynb`](../kaggle/satreg-gpu-benchmark.ipynb).
It clones this repository at a given commit, installs the `dl` extra (and RoMa),
fetches the weights, runs `satreg benchmark --config configs/gpu.toml --device cuda`
and saves the run's directory as the notebook's output. The chips are fetched by
the benchmark itself, from the Sentinel-2 COGs, as on the M1.

The GPU rows are then merged with the same run made on the M1, without re-running
either side.

## Run it

1. **Push the commit to run.** The notebook clones from GitHub; set `COMMIT` in
   its parameters cell to that commit's hash (`main` runs whatever `main` is when
   the notebook starts, which `context.json` records anyway).
2. **Give the notebook access to the repository**, while it is private: create a
   fine-grained GitHub token with read-only access to the contents of this one
   repository, and store it in the notebook as a Kaggle secret named
   `GITHUB_TOKEN` (*Add-ons → Secrets*). The token goes to git through the
   environment only, never on a command line or in a file, so it is in neither
   the clone nor the saved output. A public repository needs no secret.
3. **Push the notebook**, either with the Kaggle CLI, whose own credentials stay in
   `~/.kaggle/kaggle.json` outside the repository:

   ```bash
   kaggle kernels push -p kaggle/
   ```

   or by uploading the `.ipynb` in Kaggle's editor (*File → Import notebook*).
   [`kaggle/kernel-metadata.json`](../kaggle/kernel-metadata.json) asks for a GPU
   and for internet access, which the clone, the install and the chips need.
4. **Pick the accelerator** in *Settings → Accelerator*: *GPU T4 x2*. The
   benchmark uses the first GPU. Then *Save Version → Save & Run All*.
5. **Download the output** once the version has run:

   ```bash
   kaggle kernels output <user>/satreg-gpu-benchmark -p outputs/kaggle
   ```

   The run is in `outputs/kaggle/outputs/gpu/`.

## The M1 side and the merge

The M1 counterpart is the same config on the other device:

```bash
satreg benchmark --config configs/gpu.toml --device cpu --out outputs/gpu-m1
satreg merge outputs/gpu-m1 outputs/kaggle/outputs/gpu --out outputs/gpu-merged
```

`satreg merge` writes one `summary.md`, `summary.csv` and `pairs.csv` with a
`device` column, the rows of one method on each device side by side. Its
`context.json` lists each run's path and context. The merge refuses runs it
cannot put in one table:

- two runs that measured the same device: each device comes from one run, so the
  footnote can name the machine and the commit behind every row;
- runs that differ on an option that makes the pairs or reads their score or
  cost (sites, pairs, size, scenarios, presets, seed, motion ranges, failure
  threshold, warm-up, repeats): their rows would not be comparable.

Methods and their other parameters may differ between the runs: a method that
ran on one side only simply has one row.

## The N2 runs

N2 runs the notebook twice, from the same commit.

The GPU half of the simulated table is the same procedure on
[`configs/n2-gpu.toml`](../configs/n2-gpu.toml): set `CONFIG =
"configs/n2-gpu.toml"` in the notebook's parameters cell. The run lands in
`outputs/kaggle/outputs/n2-gpu/`, where `make n2-merge` looks for it, and merges
with the M1 run of [`configs/n2.toml`](../configs/n2.toml):

```bash
satreg benchmark --config configs/n2.toml      # or: make n2-m1
satreg merge outputs/n2-m1 outputs/kaggle/outputs/n2-gpu --out outputs/n2
```

A test checks that the two configs make the same pairs. The GPU run has 3,600
pairs and six methods, about 30 times the first GPU run: a little over two hours
on a T4, inside a Kaggle session's limit.

The inter-band table is split the same way. Its GPU half is
[`configs/n2-bands-gpu.toml`](../configs/n2-bands-gpu.toml), with
`CONFIG = "configs/n2-bands-gpu.toml"`: the six deep-learning methods on 600
pairs. It fetches the B08 and B03 bands of Beauce and Toulouse itself, and lands
in `outputs/kaggle/outputs/n2-bands-gpu/`; `make n2-bands-merge` joins it to the
classic methods, run on the M1 by `make n2-bands`. The notebook does not install
AROSICS (its GDAL bindings must match a system GDAL), so a config run on Kaggle
lists deep-learning methods only; a test checks every config on `cuda`.

## The training chips, as a Kaggle dataset

The N3 trainings read their pixels from a private Kaggle dataset, uploaded once,
instead of fetching 48 dates from the Sentinel-2 COGs at the start of every
session. The dataset is the twelve chips of
[`configs/train-sites.toml`](../configs/train-sites.toml), four dates each.

1. **Build the folder** on the M1. It fetches what is not in `data/` yet, checks
   every chip against the acceptance rule and stops if one is refused:

   ```bash
   make train-dataset
   ```

   `outputs/train-chips-dataset/` then holds `real/<chip>/<band>_<role>_<hash>.tif`,
   laid out as under `data/`, and `chips.json` (role, landscape, land-cover
   shares, and the scene id, date, satellite and hidden share of each date).
   `outputs/satreg-training-chips.zip` is the same two, zipped for the upload.
2. **Upload it**, once, on Kaggle's site: *Create → New Dataset*, drop the zip,
   title it `satreg training chips`, keep the visibility on *Private*. Kaggle
   derives the dataset's name from the title: `<user>/satreg-training-chips`.
   The subtitle and the description, which carries the Copernicus attribution,
   are pasted from [`dataset-metadata.json`](../kaggle/dataset-metadata.json).
   If a chip is ever replaced, the new zip is uploaded as a new version of the
   same dataset (*New Version*).

   The Kaggle CLI does the same from the folder, which holds a copy of
   `dataset-metadata.json` for it, once `<user>` in the `id` of that file is
   replaced by the account's user name: `kaggle datasets create -p
   outputs/train-chips-dataset --dir-mode zip`.
3. **Use it** from a notebook: *Add Input* in Kaggle's editor, or
   `<user>/satreg-training-chips` in `dataset_sources` of its kernel metadata.
   Kaggle mounts it read-only under
   `/kaggle/input/satreg-training-chips/`. Given as `--data-dir`, that folder has
   every series in the cache, so nothing is fetched. The cache names hash the
   chip's parameters, the catalogue and the series configuration: the notebook
   must run a commit whose `configs/train-sites.toml`, `configs/sites.toml`
   (`[stac]`) and `configs/real.toml` are the ones the folder was built with,
   or the dates are looked for under another name and fetched again.

**Data volume.** 48 GeoTIFFs, 95 MB: each is a 1024 x 1024 chip with two uint16
bands, B04 and the scene classification on the same grid.

The dataset contains modified Copernicus Sentinel data 2025-2026, free to
redistribute with that attribution, which its description carries.

## Training on a Kaggle GPU

The N3 trainings run in a second notebook,
[`kaggle/satreg-train.ipynb`](../kaggle/satreg-train.ipynb). It clones the
repository at a commit, installs the `dl` extra, copies the training chips
dataset to a writable folder and runs `satreg train` once per entry of `RUNS`,
on the first GPU. Each run's directory is saved as the notebook's output, under
`outputs/train/<run>/`: `checkpoint.pt`, `best.pt`, `log.csv`,
`validation.csv`, `summary.md` and `context.json`.

### Set it up, once

1. **Push the commit to run** and set `COMMIT` in the parameters cell. Its
   `configs/train-sites.toml`, `configs/sites.toml` and `configs/real.toml`
   must be the ones the chips dataset was built with (see above).
2. **Import the notebook** in Kaggle's editor (*File → Import notebook*).
   `kernel-metadata.json` describes the benchmark notebook only; the training
   notebook's settings are set in the editor.
3. **Settings**: internet on, accelerator *GPU T4 x2*, the only T4 choice the
   editor offers (a training uses one of the two GPUs).
4. **Inputs** (*Add Input*): the private dataset `<user>/satreg-training-chips`.
   The notebook finds it by its `chips.json`, wherever Kaggle mounts it, and
   stops if it is missing.
5. **Secret**: `GITHUB_TOKEN`, as for the benchmark notebook, while the
   repository is private.

### The parameters cell

- `CONFIG`: the run's config. Its `[train]` table sets the steps, the batch
  size, the validation interval and the worker processes.
- `RUNS`: one training per entry: the name of its directory, and the options of
  `satreg train` that override the config (`--model small`, for instance).
- `MAX_MINUTES`: the time the trainings may take in all. A run still going then
  stops on a checkpoint (`satreg train --max-minutes`), before Kaggle's own
  session limit cuts it without one.
- `COMPARE`: pairs of runs whose loss curves are printed side by side.

### Going on with a run in another session

A session's output is the only thing that survives it. To resume a run:

1. open the notebook again and add, as an input, the output of the version that
   started the run (*Add Input → Notebook Output Files*, pick that version);
2. keep the run's name in `RUNS`, with the same config and options;
3. *Save Version → Save & Run All*.

The notebook copies the run's directory from the input and passes `--resume`.
The new version's output then holds the whole run, the first session's files
included, so the next session needs this one's output only. Pair number `i`
depends on its index alone, so the resumed run trains on the pairs the
uninterrupted one would have seen. `context.json` lists every session with its
commit, its machine and its steps.

### The timing run

Done before any real training, to fix the step budget. The default parameters
are the timing run: [`configs/train-timing.toml`](../configs/train-timing.toml)
is 300 steps at the planned batch (8 pairs of 256 px), with a validation on the
light set at steps 0, 150 and 300.

**Session 1.** Run the notebook as it is. `RUNS` trains `timing-large`,
`timing-small`, and `timing-large-cut`, which is RAFT large stopped at step 150.

**Session 2.** Add the output of session 1 as an input, and set:

```python
RUNS = {"timing-large-cut": ["--model", "large"]}
COMPARE = [("timing-large", "timing-large-cut")]
```

The cut run resumes from its checkpoint to step 300, and the last cell prints
its loss next to the uninterrupted run's, by stretches of 25 steps.

**The quota.** Before and after each session, read the GPU time used this week
(*Session options*, under the accelerator, as `hh:mm / 30 hrs`), and note the
session's duration (the report cell prints it). Read on 2026-10-04: a *T4 x2*
version that ran 46 min took the quota from 00:00 to 00:46, so an hour of
*T4 x2* removes one hour, not two. The editor offers no single T4 to compare
with.

**What to read.** The report cell prints, per run: the median seconds per step,
the share of the time spent getting the pairs (`pair_share`), the pairs consumed
per second and the peak GPU memory. It also lists the files fetched besides the
dataset, which must be none. The time of one validation is the `seconds` column
of each run's `validation.csv`. The numbers read on 2026-10-04 and the step
budget drawn from them (10,000 steps a training, a validation every 500, a
checkpoint every 250) are in [`decisions.md`](decisions.md).

### The two trainings of the ablation

RAFT large, twice, 10,000 steps each, one session per training: 8.4 h for the
first and 9.1 h for the second, on 2026-10-05 and 2026-10-06.
The notebook's default parameters stay those of the timing run; for each
session, change the parameters cell in Kaggle's editor.

**Same-date pairs only.**

```python
COMMIT = "<the commit pushed for these trainings>"
CONFIG = "configs/train-same-date.toml"
RUNS = {"large-same-date": []}
COMPARE = []
```

**Same-date and cross-date pairs.**

```python
COMMIT = "<the same commit>"
CONFIG = "configs/train-cross-date.toml"
RUNS = {"large-cross-date": []}
COMPARE = []
```

Both sessions run the same commit: `context.json` records it, and the report of
the ablation prints it for each run. `MAX_MINUTES` stays at 600. A training
still going after 10 h stops on a checkpoint: go on with it in another session
(above), with the same `CONFIG` and `RUNS`. The two sessions took 17.5 h of
the week's 30 h of GPU; whether Kaggle runs two GPU sessions at once was not
checked, one after the other works.

Before leaving a session, check its log. The validation of the pretrained
weights (step 0) prints nothing, so the first line comes with the first
checkpoint, at step 250, 14 to 15 minutes in. There is then a line at each
checkpoint, every 250 steps, with the loss, and every 500 steps one more with
the validation score and the step kept so far.
Anything that goes wrong (a loss that diverges, a session lost) is noted in
[`failures.md`](failures.md).

Then bring both runs back (below), to `outputs/train/large-same-date/` and
`outputs/train/large-cross-date/`, and run `make ablation` on the M1: it scores
the two `best.pt` and pretrained RAFT on the validation set and on the real
triplets, and applies the rule of [`decisions.md`](decisions.md) (2026-10-05).
The rule is applied to two runs that went to step 10,000 and differ by the
share of cross-date pairs alone; to anything else `satreg ablation` writes the
tables and no choice. Bring the whole directory of each run, not `best.pt`
alone: the report reads `context.json`, `log.csv` and `validation.csv` next to
it.

### The training of RAFT small

RAFT small, once, 10,000 steps, with the pairs of the retained variant
([`configs/train-small.toml`](../configs/train-small.toml)). In the parameters
cell:

```python
COMMIT = "<the commit pushed for this training>"
CONFIG = "configs/train-small.toml"
RUNS = {"small-cross-date": []}
COMPARE = []
```

`MAX_MINUTES` stays at 600. The timing run measured 3.22 s a step for small,
89 % of it waiting for the pairs: count 9 h, as for RAFT large, and 1.9 GiB of
GPU memory. Read the quota before starting (*Session options*): the session
needs 9 to 10 h of the week's 30 h. If less is left, wait for the weekly
reset: what Kaggle does to a session that runs out of quota was not checked.

The session log reads as for the ablation: nothing for 14 to 15 minutes, then a
line every 250 steps and one more every 500 with the validation score. The
light validation score of pretrained RAFT small is 0.3224 px (step 0).

Then bring the whole run directory back (below) to
`outputs/train/small-cross-date/`, and run `make small` on the M1, lid open: it
scores RAFT small and RAFT large, pretrained and fine-tuned, on the validation
set and on the real triplets, and says whether the training was a gain, no gain
or worse ([`decisions.md`](decisions.md), 2026-10-06). `satreg small` reads
`outputs/train/large-cross-date/` too, for the training it puts next to it.

The session ran on 2026-10-06 from commit `deb3d1b`: 9 h 07 of training for
the 10,000 steps, 3.41 s a step, 89 % of it waiting for the pairs, 1.9 GiB of
GPU memory, and step 8,000 kept. The quota was at 18:29 of 30 h before it; it
was not read after. `make small` then took 71 minutes on the M1, and the
training is a gain ([`decisions.md`](decisions.md), 2026-10-07).

### Bring a run back

Download the version's output from Kaggle's site (*Output → Download All*) and
unpack it so that the run is in `outputs/train/<run>/`. `best.pt` holds the
weights of the kept checkpoint.

## What `context.json` records

Besides the machine, the thread settings and the library versions:

- `code`: the commit the run was made from, and whether tracked files were
  modified (`dirty`);
- `checkpoints`: for each fine-tuned method, the path of its checkpoint and
  the file's SHA-256, so that a table names the weights it scored;
- `gpu`: the CUDA device (name, memory, count, compute capability) and the CUDA
  and cuDNN versions PyTorch was built with, `null` when the run did not load
  PyTorch or found no CUDA device;
- `libraries.torch`: the PyTorch version;
- `devices`: each method's device;
- `cost.run_seconds`: how long the benchmark took, simulation and scoring
  included (the notebook fetches the weights before, so their download is not).

GPU timing synchronises the device before each clock read and makes a warm-up
call per method first; memory is `torch.cuda.max_memory_allocated`, the peak held
by CUDA tensors, reset before each call.

## Weights and duration

Kaggle starts every session from a fresh machine, so the weights are downloaded
again each time, to PyTorch's cache (`~/.cache/torch`), outside the saved output:
about 120 MB for RAFT and LightGlue, 1.7 GB for RoMa, DINOv2 included. The
notebook fetches them in their own cell, before the benchmark, and prints how long
each step took.
Set `WITH_ROMA = False` to skip RoMa (and its weights) for a quicker check.

The first full run of `configs/gpu.toml` (commit `0f96aa7`, `cost.run_seconds`)
took 4.6 min on a T4, weights excluded, and 63 min on the M1's CPU. RoMa's two
rows take most of the M1 run: about 2.5 s a call, four calls a pair, against
0.15 s on the T4. On the 8 GiB M1, RoMa does not fit in memory next to the other
methods and the run swaps, so close other applications while it runs.

## Known risks

- Kaggle's image ships `opencv-python`; this package depends on
  `opencv-python-headless`, and pip installs it next to it. Both provide `cv2`.
  If an import of `cv2` fails after the install, uninstall `opencv-python`.
- Kaggle unpacked the uploaded zip with `real/` and `chips.json` at the
  dataset's root (49 files, seen in its Data Explorer). The path a notebook
  sees it under is not checked until the training notebook's first run, so the
  notebook does not rely on it: it looks for `chips.json` next to `real/` under
  `/kaggle/input` and prints the folder it found.
- The timing run's two sessions ran on Kaggle on 2026-10-04 (commit `ee4ed40`),
  with the dataset found under `/kaggle/input` and nothing fetched besides it.
  The weekly quota (30 h) and the way it counts a *T4 x2* session were read
  there. The 12 h session limit is the one in Kaggle's notebooks documentation;
  no session here has come near it.
- On a GPU, two runs of the same training differ in the last digits from the
  first step on, so a resumed run follows the uninterrupted one closely, not bit
  for bit. They are equal on a CPU, which a test checks. On the T4, over 300
  steps, the run resumed at step 150 in a second session and the uninterrupted
  one have the same mean loss per stretch of 25 steps to 0.002, and no step
  differs by more than 0.03; they already differ by 0.004 within the first 25
  steps, before the cut.
- `pip install -e ".[dl]"` keeps Kaggle's own PyTorch, built for its CUDA, since
  it meets `torch>=2.0`. Installing another torch there would lose CUDA support.

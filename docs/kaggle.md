# Running the benchmark on a Kaggle GPU

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

## What `context.json` records

Besides the machine, the thread settings and the library versions:

- `code`: the commit the run was made from, and whether tracked files were
  modified (`dirty`);
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
  sees it under is not checked until the first training notebook runs: if it
  is not `/kaggle/input/satreg-training-chips/`, the notebook passes the path
  it finds as `--data-dir`.
- `pip install -e ".[dl]"` keeps Kaggle's own PyTorch, built for its CUDA, since
  it meets `torch>=2.0`. Installing another torch there would lose CUDA support.

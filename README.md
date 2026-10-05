# ai-satellite-image-registration

**Aligning satellite images to a tenth of a pixel: classic methods vs AI.**

[![CI](https://github.com/esamoun/ai-satellite-image-registration/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/esamoun/ai-satellite-image-registration/actions/workflows/ci.yml)

Two images of the same place never line up exactly. This project measures how well
classic and deep-learning methods recover the displacement between two Sentinel-2
images, on accuracy and on compute cost. Displacements are simulated on real
imagery, so the ground truth is exact down to a fraction of a pixel.

**Status: in progress, level N2 done** (classic methods against pretrained
deep-learning methods). The pipeline runs four classic methods (phase correlation,
with and without a Hann window, SIFT + RANSAC and AROSICS) and three pretrained
networks used as published (RAFT, LightGlue and RoMa), on four Sentinel-2 sites,
for translations, small affine motions and dense fields, under increasingly
degraded conditions. Next is N3: fine-tuning a network on this data.

**Results so far:** [the N2 tables](docs/evaluation.md), 3,600 simulated pairs on
four sites, plus inter-band pairs, real multi-temporal triplets and a false-change
count. In short:

- **AI wins where no global model describes the motion, and where the two images
  do not look alike.** On clean dense fields RoMa's dense output is at 0.053 px
  and RAFT at 0.095 px, against 0.133 px for SIFT. Red against near infrared,
  RoMa is the only method that holds (0.115 px, 15 % of failures).
- **Classic methods keep global motion on clean pairs.** Phase correlation with a
  Hann window is at 0.004 px on clean translations and SIFT at 0.012 px on clean
  affine pairs; the best pretrained method is at about 0.03 px on both.
- **No pretrained method is the best everywhere.** RAFT is as robust as phase
  correlation under clouds and blur, and fails four red/near-infrared pairs in
  five; RoMa declines 64 % of the hardest pairs.
- **It costs a hundred to eight hundred times more on a laptop CPU**: 370 ms a
  pair for RAFT and 3 s for RoMa, against 3.6 ms for phase correlation.

The classic baseline, [the N1 table](docs/evaluation.md#n1-the-classic-baseline),
is on the same page.

## Run it

Python 3.11 or later.

```bash
python -m venv .venv && source .venv/bin/activate
make install
make test
satreg benchmark
```

`satreg benchmark` simulates pairs with known sub-pixel motion, runs every installed
method but RoMa (about 3 s a pair on a laptop CPU, so it runs only when named),
prints the results table and writes it to `outputs/benchmark/` as `summary.md` and
`summary.csv`, with one row per pair and method in `pairs.csv`, and the machine it
ran on in `context.json`. `satreg benchmark --help` lists the options (number of
pairs, image size, motion ranges, seed, failure threshold, timing repeats).

### Methods

- `phase_correlation`: scikit-image's sub-pixel phase correlation, refined to
  1/100 px. It estimates a single translation.
- `sift_ransac`: OpenCV SIFT keypoints, matched with Lowe's ratio test, and an
  affine transform fitted by RANSAC. With too few inliers it declines the pair,
  which counts as a failure. Its match and inlier counts are in `pairs.csv`.
- `arosics`: [AROSICS](https://git.gfz-potsdam.de/danschef/arosics) global
  co-registration (`COREG`), the standard open-source tool for Sentinel-2. It
  phase-correlates a matching window in map coordinates, on the grid of the chip
  each pair was cut from, and estimates a single translation. It declines a pair
  when it finds no valid match or rates its own result below 40 % reliability.
  The reliability and the window it used are in `pairs.csv`. It is an optional
  extra (below); without it, the benchmark runs the other two.

`--methods` picks some. Method parameters (SIFT's ratio, RANSAC threshold and
minimum inlier count; AROSICS' window, maximum shift and reliability threshold)
are set in [`configs/methods.toml`](configs/methods.toml). A variant of a method,
with other parameters, is declared there too, as a table with a `method` key, and
runs under its own name: `phase_correlation_hann` (phase correlation with a Hann
window), `arosics_floor60` (AROSICS with a 60 % reliability floor),
`lightglue_disk` (LightGlue on DISK keypoints) and `roma_dense` (RoMa's warp as a
displacement for every pixel) are declared this way.

### AROSICS

AROSICS needs GDAL, whose Python bindings pip builds against a system GDAL of the
same version. On macOS:

```bash
brew install gdal
make install-arosics
```

`make install-arosics` pins the bindings to `gdal-config --version`, then installs
the `arosics` extra (`pip install -e ".[dev,arosics]"`). On Linux, install
`libgdal-dev` first. The test suite runs without it and skips the AROSICS tests,
saying why.

### Deep-learning methods

Three pretrained methods need PyTorch, an optional extra:

- RAFT (`raft`, torchvision's large model, and `raft_small`): optical flow, a
  displacement for every pixel.
- LightGlue (`lightglue`, on ALIKED keypoints, and `lightglue_disk`, on DISK
  keypoints), kornia's implementation: learned keypoints matched by a
  transformer, then the same RANSAC affine fit as `sift_ransac`. Its match and
  inlier counts are in `pairs.csv`.
- RoMa (`roma`, and `roma_dense`), the outdoor model from `romatch`: a dense
  matcher on a DINOv2 backbone that places every reference pixel in the moving
  image and rates each match with a certainty. `roma` fits the RANSAC affine of
  `sift_ransac` to the certain matches, `roma_dense` keeps the warp as a
  displacement for every pixel. Both decline a pair where less than 0.5 % of the
  pixels are certain. The certainty is in `pairs.csv`. RoMa takes about 3 s a
  pair on the M1's CPU and runs only when named, as in
  `satreg benchmark --methods roma roma_dense`.

```bash
make install-dl
make install-roma   # RoMa, on top of the dl extra
```

This installs the `dl` extra (`pip install -e ".[dev,dl]"`) and downloads the
pretrained weights once, to PyTorch's cache (`~/.cache/torch`), outside the
repository. `make install-roma` adds `romatch` 0.1.2 without the dependencies it
declares (see [`docs/decisions.md`](docs/decisions.md)) and its 1.7 GB of weights.
Each method runs on the device set in `configs/methods.toml` (`cpu` by default,
or `mps` or `cuda`); nothing picks one for you. `--device cuda` moves every
deep-learning method of a run to that device, the other methods staying on the
CPU, and stops before the first pair if the machine lacks it. The test suite runs
without the extra and skips the tests that run the networks, saying why.

### Translation, affine and dense motion

Each pair is simulated three times: shifted, under a small affine motion (rotation,
scale change and shear about the pair's centre, on top of the same shift), and
under a dense field (the same affine motion plus a smooth local displacement that
varies across the pair). All three versions share the reference image and the
global motion, so the difference between the rows of a method is the cost of its
motion model. The default affine ranges (±0.2°, ±0.2 % scale, ±0.002 shear) are
sized around the Sentinel-2 co-registration requirement of 0.3 px. The local field
stands for orthorectification residuals over relief: up to 0.8 px, correlated over
about 64 px (640 m). `--scenarios affine` runs one scenario, and `--max-rotation`,
`--max-scale-change`, `--max-shear`, `--max-local-shift` and `--local-length`
change the ranges. Every scenario is warped without the low-pass of a plain
spline. Pixels whose displaced position leaves the moving image are left out of
the metrics, and so are pixels of a dense pair that sit under opaque cloud.

### On Sentinel-2 imagery

```bash
satreg fetch                      # every site in configs/sites.toml
satreg benchmark --site beauce
```

`satreg fetch` finds the least cloudy Sentinel-2 L2A scene of each site in the
[Earth Search](https://earth-search.aws.element84.com/v1) STAC catalogue whose
scene classification (SCL) shows the chip itself free of cloud and cloud shadow,
and reads a 1024 × 1024 px window of its B04 COG, on the native 10 m grid with no
resampling. No account is needed. The chip (about 1.5 MB per site) is cached in
`data/chips/`, which is not committed: later runs make no network call, and
`satreg benchmark --site <name>` fetches a missing chip by itself. Sites, dates,
cloud limits, chip size and band are set in [`configs/sites.toml`](configs/sites.toml).
Without `--site`, the benchmark uses the synthetic texture and runs offline.

Six sites are declared: Beauce (fields), Toulouse (city), Alps (mountain),
Vosges (forest), Libya-4 (desert) and Marseille (coast). The Alps and Libya-4 are
held out for the final evaluation: the benchmark refuses them unless given
`--allow-held-out`, and a table that includes them says so.

### Across spectral bands

```bash
satreg benchmark --site toulouse --band-pair B04 B08
```

`--band-pair REFERENCE MOVING` (or `band_pairs = [["B04", "B08"]]` in a run
config) cuts the reference image from one band and the moving image from
another. Both come from the same scene and window as the site's chip, and the
moving image is then shifted exactly as in a single-band pair. Red against
near-infrared is the hard case: vegetation is dark in one and bright in the
other. Only the 10 m bands (B02, B03, B04, B08) are offered, so no band is
resampled. The bands are cached as one multi-band chip in `data/chips/`. The band
pair becomes a column of every table, and the option can be repeated. The
ground truth assumes the bands are co-registered, and ESA only guarantees that
to about 0.3 px. `--max-shift 0` measures what is left on a site (see
[`docs/decisions.md`](docs/decisions.md)).

### Real multi-temporal pairs

```bash
satreg real-pairs                 # fetch each site's dates and list its pairs
satreg check-presets              # measure real pairs next to the presets
```

Each site also gets a series of real dates, set in
[`configs/real.toml`](configs/real.toml). The series starts from the chip's own
scene and adds the clear dates nearest a few days, a season and a year later. All
dates are on the same tile and relative orbit, and are cut from the same window
of the grid. The four dates give six pairs and four triplets per site. A real
pair has no ground truth. It carries both dates, their scenes and satellites, and
a joint cloud and shadow mask from the SCL. Dates are cached in `data/real/`.
`satreg check-presets` measures noise, blur difference, contrast, tone and
correlation on real pairs and on the presets, without registering them, and
writes the comparison to `outputs/presets-check/`. Held-out sites are fetched
but not measured.

```bash
satreg cycle                      # closure of each method on the real triplets
```

A real pair has no truth to score a method against, but three dates do check
each other. For dates A < B < C, `satreg cycle` registers A to B, B to C and A
to C, each on the 256 px windows clear on all three dates. Chained, the first
two legs should give the third. The distance between them, the closure, is
reported per site, triplet and method like the benchmark's error. It has the
same columns: mean, share of pixels under 0.1 and 0.5 px, failures and cost. A
triplet fails if a leg declines or crashes, or if its mean closure exceeds 1 px.
The closure is not the error. An error that belongs to one date, or that
grows with the displacement, cancels out of it. So the same command also runs
simulated triplets, cut from each site's chip under every scenario and preset,
and shows their closure next to their true error. A second table sizes the
displacements the methods find between real dates, next to the simulated
ranges. Output goes to `outputs/cycle/`, with one row per registration in
`legs.csv` and one per triplet in `triplets.csv`. `--simulated-triplets 0`
skips the simulated triplets. Held-out sites are left out unless
`--allow-held-out` is given.

```bash
satreg false-change               # what a residual costs a change detector
```

`satreg false-change` asks what the accuracy is for. One fixed change detector
(a threshold at 3 σ of the pair's noise) is run after each method's correction,
and the pixels it flags where nothing changed are counted. On simulated pairs
nothing changed anywhere, and a reference curve gives the false-change rate as a
function of the residual. On real pairs the count is made on stable ground,
built-up and bare ground in ESA WorldCover. Output goes to
`outputs/false-change/`, with the figure `false_change.png`.

### Training chips

```bash
satreg fetch-train                # fetch and check the twelve training chips
```

Fine-tuning (N3) does not train on the benchmark chips. Its pixels are twelve
other chips, declared in [`configs/train-sites.toml`](configs/train-sites.toml):
three per landscape (open fields, urban, forest, coast), one of the three set
aside whole for validation, none in mountain or desert. Each gets the four dates
of the series rule above. `satreg fetch-train` fetches them and checks each
chip: its four dates are found, an urban chip is at least 55 % built-up and a
coast chip at most 40 % water in ESA WorldCover. A chip that fails is reported
with its shares and the command exits with an error. The tables go to
`outputs/train-chips/`, with the scene ids, dates and hidden shares in
`chips.json`. The configuration refuses a chip that could overlap a benchmark
chip or a held-out site, and training code gets its chips by role, through a
call that raises for any other chip. `--export DIR` copies the accepted chips to
a directory laid out like `data/`, which is what is uploaded to Kaggle
([docs/kaggle.md](docs/kaggle.md)).

### Training pairs

```bash
make train-pairs                  # draw 200 training pairs, time them, save a contact sheet
satreg train-pairs --cross-date 0 # same-date pairs only
```

A training pair is a 256 px window of a training chip, moved by a known
displacement and degraded by a random draw. The generator
([`trainpairs.py`](src/satreg/trainpairs.py)) calls the benchmark's simulator
and degradations, it does not copy them: with the exact parameters of a preset
it returns the benchmark's pair, and a test pins it. What differs from the
benchmark:

- **Degradations are drawn in continuous ranges**, from clean (the noise from
  nearly none, a ratio of 40 dB) to a bit beyond `hard`, declared under `[training]` in
  [`configs/degradations.toml`](configs/degradations.toml). The three presets
  stay the test's.
- **Clouds may fall on both images**: half of the pairs have a cloud on the
  moving image, three in ten on the reference.
- **Two kinds of pair**, in a share set by `cross_date` in
  [`configs/train-pairs.toml`](configs/train-pairs.toml): same-date (one date,
  exact truth) and cross-date (reference and moving from two dates of one chip).
- **A loss mask** comes with each pair: pixels pushed out of frame, pixels under
  an opaque cloud on either image and, on a cross-date pair, pixels the scene
  classification hides on either date are left out.

Pair number `i` of a seed is always the same pair, whatever was drawn before it.
Only training chips are read: asking for a validation chip raises. The network's
inputs are made by the conversion the `raft` method uses.

The command writes `summary.md`, `pairs.csv` (one row per pair, with its drawn
parameters) and `contact-sheet.png` to `outputs/train-pairs/`. On the M1, one
process makes 5.8 pairs per second: a translation or affine pair takes 11 to
26 ms, a dense pair 0.4 s.

### Training

```bash
make train-overfit                # the overfit run: RAFT large, then small, on 8 pairs (M1, about 11 min)
satreg train --config configs/train-overfit.toml --resume   # go on from the checkpoint
satreg validate --config configs/validation.toml --light --methods raft raft_ft
```

`satreg train` fine-tunes RAFT on training pairs ([`train.py`](src/satreg/train.py)).
The run is declared in one file: the model, the steps, the batch size, the
learning rate and the other settings under `[train]`, what the pairs are made
of, with their seed, under `[pairs]`. The recipe is the one of RAFT's own
fine-tuning stages, read from the original training script and torchvision's:

- **Sequence loss**: the L1 error of each of the 12 refinements, later ones
  weighing more, on the pixels of the loss mask.
- **AdamW under a one-cycle learning rate**, the gradient's norm clipped to 1.
- **Every parameter trains**; the batch-normalisation layers of RAFT large keep
  the statistics of the pretrained weights (RAFT small has none).
- **Same inputs as at inference**: the conversion of the `raft` method, 12
  refinements, 32-bit floats.

The output directory holds `checkpoint.pt` (weights, optimiser, schedule, step
and configuration), `log.csv` (one row per step), `summary.md` and
`context.json` (the configuration, and the commit and machine of each session).
A session that stops is resumed with `--resume`: pair number `i` depends on its
index alone, so a resumed run ends on the weights an uninterrupted one gives,
and a test pins it.

With `validate_every = N` in `[train]`, the run scores its network on the light
validation set before the first step and every `N` steps
([`trainval.py`](src/satreg/trainval.py)): the 360 pairs `satreg validate
--light` scores, drawn and scored by the same code. Each validation is a line of
`validation.csv` and of `summary.md`. The run keeps, in `best.pt`, the weights
of the validation with the lowest selection score: the mean error over the 360
pairs, the three presets weighing the same, a pair that fails (over 1 px)
counting for 1 px. The pretrained weights, step 0, are a reference and are never
the kept ones. The rule is in [`docs/decisions.md`](docs/decisions.md), written
before the first real run.

Pairs are made on the fly. `workers = N` prepares them in `N` processes, a few
steps ahead of the loop, and gives the same batches as one process: on the M1,
RAFT small at batch 4 goes from 1.49 s per step, 59 % of it making pairs, to
0.64 s with 3 workers. `--max-minutes` stops a run on a checkpoint after that
long, for a session with a time limit.

The real trainings run on a Kaggle GPU, from
[`kaggle/satreg-train.ipynb`](kaggle/satreg-train.ipynb). Its first use is the
timing run, [`configs/train-timing.toml`](configs/train-timing.toml): 300 steps
of RAFT large and small on a T4, to measure what the step budget is set from
([`docs/kaggle.md`](docs/kaggle.md#training-on-a-kaggle-gpu)). There, a step of
8 pairs takes 3.1 s for both networks, 70 % of it waiting for the pairs with
large and 89 % with small: Kaggle's 4 CPUs make 2.6 pairs a second. Each
training gets 10,000 steps, about 8.9 h, one session
([`docs/decisions.md`](docs/decisions.md), 2026-10-04).

RAFT large is trained twice, for the ablation:
[`configs/train-same-date.toml`](configs/train-same-date.toml) on same-date
pairs only, where the truth is exact and nothing changed on the ground, and
[`configs/train-cross-date.toml`](configs/train-cross-date.toml) with one pair
in two cross-date, where the ground really changed and the truth is off by what
the two dates are misregistered by. The two files differ by `cross_date` alone,
and a test checks it. The methods `raft_ft_same_date` and `raft_ft_cross_date`
load the `best.pt` each run kept, from `outputs/train/large-same-date/` and
`outputs/train/large-cross-date/`. How the two are compared is under
[Validation set](#validation-set).

The methods `raft_ft` and `raft_small_ft` of
[`configs/methods.toml`](configs/methods.toml) are RAFT with the weights of a
checkpoint at a local path, `outputs/train/<method>/checkpoint.pt`, where
`satreg train` writes by default. They run through the same commands as any
method; without the checkpoint, a command says where it is expected and their
tests are skipped.

The overfit run ([`configs/train-overfit.toml`](configs/train-overfit.toml))
checks the loop, it does not make a model: 300 steps on the same 8 training
pairs, on the M1 (MPS).

| model | s/step | loss, first 30 steps | loss, last 30 | EPE on the 8 pairs, pretrained | after 300 steps |
|---|---:|---:|---:|---:|---:|
| large | 1.80 | 1.572 | 0.054 | 4.241 px | 0.009 px |
| small | 0.33 | 3.380 | 0.140 | 6.248 px | 0.018 px |

The pretrained error is high because of one pair with a cloud on both images,
where the pretrained weights are 31 px off (46 px for small); the others are
between 0.04 and 3.1 px, and every pair ends under 0.03 px.

Both checkpoints then went through `satreg validate --light` like any method
(360 pairs of the validation chips, which the training never saw):

| preset | method | EPE (px) | failures |
|---|---|---:|---:|
| clean | raft | 0.062 | 0.0 % |
| clean | raft_ft | 0.067 | 0.0 % |
| clean | raft_small | 0.145 | 0.0 % |
| clean | raft_small_ft | 0.183 | 0.0 % |
| mild | raft | 0.073 | 0.0 % |
| mild | raft_ft | 0.076 | 0.0 % |
| mild | raft_small | 0.191 | 0.8 % |
| mild | raft_small_ft | 0.188 | 0.0 % |
| hard | raft | 0.253 | 11.7 % |
| hard | raft_ft | 0.242 | 0.0 % |
| hard | raft_small | 0.463 | 30.0 % |
| hard | raft_small_ft | 0.544 | 24.2 % |

These rows show that a checkpoint reaches the table by the normal path, and
nothing else: 8 pairs and 300 steps are not a training, the light set's failure
rate is not reliable under `hard`, and no conclusion is drawn from them. The
tables are in [`docs/results/n3/`](docs/results/n3/).

### Validation set

```bash
make validation                   # pretrained RAFT on the validation set (M1, about 27 min)
make validation-light             # its light version, the first 10 pairs of every cell
make validation-cycle             # closure on the real triplets of the twelve chips
make ablation                     # both, for raft and the two fine-tuned variants, then the choice
```

The validation set is what N3's choices are made on: 100 simulated pairs per
validation chip (Santerre, Lyon, Morvan, Sète), scenario and preset, 3,600 in
all, declared in [`configs/validation.toml`](configs/validation.toml).
`satreg validate` cuts them from the chips' anchor date and hands them to the
code `satreg benchmark` runs, with the ranges, presets and seed of the N2 table:
a validation row is computed like a row of the final table, on other chips. The
table comes over every chip, then by chip.

`satreg validate-cycle` scores the closure of the real triplets, as
`satreg cycle` does, on the four date series of the twelve chips: the validation
chips, which choose, and the training chips, which are reported. Both commands
take their chips from [`configs/train-sites.toml`](configs/train-sites.toml) by
role, so neither can read a benchmark chip or a held-out site.

Pair number `i` of a cell does not depend on how many pairs are asked for, so
`--light` runs the first `light_pairs` pairs of every cell (360 pairs): the set
scored during a training. The full run prints how light sets of several sizes
compare with it.

Pretrained RAFT, the bar a fine-tuned checkpoint is compared with, over the four
chips and the three scenarios (M1, MPS):

| preset | method | EPE (px) | failures |
|---|---|---:|---:|
| clean | raft | 0.063 | 0.0 % |
| clean | raft_small | 0.141 | 0.0 % |
| mild | raft | 0.081 | 0.0 % |
| mild | raft_small | 0.176 | 0.4 % |
| hard | raft | 0.242 | 5.8 % |
| hard | raft_small | 0.482 | 26.9 % |

On real triplets of the validation chips, RAFT closes at 0.21 px with 32 % of
failures and RAFT small at 0.29 px with 42 %; almost all of Santerre fails, as
Beauce does in N2. The full tables are in
[`docs/results/n3/`](docs/results/n3/).

`make ablation` runs both commands for pretrained `raft` and the two variants
of the ablation, then `satreg ablation` ([`ablation.py`](src/satreg/ablation.py))
reads the two tables. Each variant is put next to `raft`, and the two next to
each other, always on the same items: the mean error over the pairs neither of
the two fails, the mean closure over the triplets neither fails, and the
failure counts. It writes `summary.md`, `comparisons.csv`, the loss and
validation curves of the two trainings (`curves.png`) and `context.json` in
`outputs/ablation/`, and applies the rule written before the trainings:

1. a variant is eligible if it beats pretrained `raft` on the whole validation
   set (no more failed pairs, a lower mean error);
2. if neither is, nothing is retained, and that is the result;
3. if one is, it is retained;
4. if both are, the closure on the real triplets of the four validation chips
   chooses (fewer failed triplets, then a lower mean closure);
5. if it is equal, the lower validation error, then the same-date variant.

The closure on the eight training chips is reported and decides nothing: the
cross-date variant was trained on their dates. A run of `satreg validate` or
`satreg validate-cycle` records the SHA-256 of each fine-tuned method's
checkpoint in its `context.json`, and `satreg ablation` refuses two runs that
did not score the same weights. The rule and its limits (no margin, one seed)
are in [`docs/decisions.md`](docs/decisions.md), 2026-10-05. The two trainings
have not run yet.

### Under degraded conditions

Each pair is run clean and under named degradation presets, declared in
[`configs/degradations.toml`](configs/degradations.toml): `mild` and `hard` add
sensor noise, blur, a radiometric difference (contrast, level, tone curve) and
procedural clouds, at increasing strength. Every preset keeps the pair's
geometry, so the ground truth stays exact. `satreg benchmark` runs every preset;
`--degradations mild hard` picks some.

The table reports, per site, scenario, preset and method: the share of the moving image
under cloud, the mean end-point error (EPE, in pixels), the share of pixels whose
error is under 0.1 px and under 0.5 px, and the failure rate.

### Compute cost

Next to accuracy, the table reports what each method call costs: its wall-clock
time, the median of `--repeats` calls (default 3) after `--warmup` untimed calls
(default 1), and its peak memory as traced by Python's `tracemalloc`. Only the
method call is measured, not the simulation or the scoring. `tracemalloc` misses
memory that native code allocates for itself, so SIFT's figure is about a tenth of
what it really uses; the limits are measured in
[`docs/decisions.md`](docs/decisions.md). PyTorch methods are measured their own
way: the device is synchronised before each clock read, and memory is the peak
held by tensors (read by PyTorch's profiler on CPU, by CUDA's counter on GPU, and
not available on MPS). The table's footnote says which methods were measured
which way. `context.json` records the CPU, memory, thread settings, library
versions, the commit, the GPU if one was used, and each method's device, so
that runs on different machines are not mixed up. The table has a `device`
column.

### On a Kaggle GPU

The M1 has no CUDA device. [`kaggle/satreg-gpu-benchmark.ipynb`](kaggle/satreg-gpu-benchmark.ipynb)
runs [`configs/gpu.toml`](configs/gpu.toml) on a Kaggle GPU and saves the run as
its output; the same config runs on the M1 with `--device cpu`. `satreg merge`
puts the two runs in one table, by device, without re-running either:

```bash
satreg merge outputs/gpu-m1 outputs/kaggle/outputs/gpu --out outputs/gpu-merged
```

It refuses runs that measured the same device, or whose pairs or scoring differ.
The procedure, where the weights go and how long a run takes are in
[`docs/kaggle.md`](docs/kaggle.md).

### The N2 run

```bash
make install-dl install-arosics install-roma
make n2
```

`make n2` runs the M1 part of the published N2 tables (about 5 h 30) and merges
the GPU part, which the Kaggle notebook produces first from
[`configs/n2-gpu.toml`](configs/n2-gpu.toml) and
[`configs/n2-bands-gpu.toml`](configs/n2-bands-gpu.toml) (about 2 h 25 on a T4).
The commands, configs, pair counts and hardware are in
[`docs/evaluation.md`](docs/evaluation.md); the tables as the runs wrote them
are in [`docs/results/n2/`](docs/results/n2/).

### The N1 run

```bash
satreg benchmark --config configs/n1.toml   # or: make n1
```

[`configs/n1.toml`](configs/n1.toml) holds every option of the run that produced
the published table: sites, scenarios, presets, methods, number of pairs, motion
ranges and seed. Its keys are the options of `satreg benchmark`, and an option
given on the command line overrides its key (`--pairs 10` for a quick check).
Every option a run used is recorded in its `context.json`. The table and its
reading are in [`docs/evaluation.md`](docs/evaluation.md).

## Where the reasoning is

- [`docs/evaluation.md`](docs/evaluation.md): the N2 and N1 results tables, how
  to reproduce them, and what they show.
- [`docs/decisions.md`](docs/decisions.md): each choice and why it was made.
- [`docs/failures.md`](docs/failures.md): what did not work, and what it taught.
- [`docs/kaggle.md`](docs/kaggle.md): running the benchmark and the trainings on
  a Kaggle GPU.
- [`CONTEXT.md`](CONTEXT.md): the glossary, what each word means in the code and
  the docs (chip, pair, seen and held-out site, validation set).

## How this was built

I designed this project and I lead it: I set the question, the methods compared,
how they are evaluated and the plan, and I make the calls that shape the results.
Claude Code is my coding assistant: it writes most of the code and drafts the docs,
and I review its changes and check the results before they go in. The reasoning
behind each choice is in [`docs/decisions.md`](docs/decisions.md); the entries
marked *My call* are the ones where I chose between options.

## License

MIT

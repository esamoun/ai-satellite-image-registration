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
- [`docs/kaggle.md`](docs/kaggle.md): running the benchmark on a Kaggle GPU.

## How this was built

I designed this project and I lead it: I set the question, the methods compared,
how they are evaluated and the plan, and I make the calls that shape the results.
Claude Code is my coding assistant: it writes most of the code and drafts the docs,
and I review its changes and check the results before they go in. The reasoning
behind each choice is in [`docs/decisions.md`](docs/decisions.md); the entries
marked *My call* are the ones where I chose between options.

## License

MIT

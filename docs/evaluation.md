# Evaluation: the N1 results table

The first results table of the project: the three classic methods, and two
variants, on simulated displacements of two Sentinel-2 chips, from clean pairs to
hard ones. Everything here comes from one seeded run, which the command below
reproduces.

## What was run

- **Sites.** Beauce (open fields, low texture) and Toulouse (urban, dense texture):
  one least-cloudy Sentinel-2 L2A B04 chip each, 1024 × 1024 px at 10 m (see
  [`configs/sites.toml`](../configs/sites.toml)).
- **Pairs.** 100 windows of 256 × 256 px per site, each with a random sub-pixel
  shift of up to ±4 px per axis. Each pair is run twice: as a pure **translation**,
  and as a small **affine** motion (up to ±0.2° rotation, ±0.2 % scale change,
  ±0.002 shear) about the same centre, on top of the same shift.
- **Presets.** Each pair is run `clean`, `mild` and `hard` (noise, blur, a
  radiometric difference and procedural clouds, at increasing strength; see
  [`configs/degradations.toml`](../configs/degradations.toml)). The geometry does
  not change, so the ground truth stays exact.
- **Methods.** `phase_correlation` (scikit-image, unwindowed), `sift_ransac`
  (OpenCV) and `arosics` (AROSICS `COREG`, reliability floor 40 %), plus two
  variants: `phase_correlation_hann`, with a Hann window, and `arosics_floor60`,
  with AROSICS' earlier 60 % floor. The variants are there to settle two choices,
  recorded in [`decisions.md`](decisions.md).
- **Size.** 2 sites × 2 scenarios × 3 presets × 100 pairs = 1,200 simulated pairs,
  × 5 methods = 6,000 rows. **Every cell of the table is 100 pairs**, the same 100
  windows and displacements across scenarios, presets and methods.

A method **fails** a pair when it declines it (too few SIFT inliers, no AROSICS
match or a reliability under the floor), crashes, or is off by more than 1 px on
average. **The mean EPE is over the pairs a method did not fail**, so a method
that declines hard pairs can show a low error on the ones it kept: read it with
the failure rate, or with the share under 0.3 px below, which counts every
failure as a miss.

## How to reproduce it

```bash
satreg benchmark --config configs/n1.toml
```

AROSICS must be installed (`make install-arosics`, see the README). A missing chip
is fetched on the first run (about 1.5 MB per site) and cached in `data/chips/`,
and `make n1` runs the same command. The run takes
about 5 min 30 s on the machine below and writes `outputs/n1/`: `pairs.csv` (one
row per pair and method, with the truth, the estimate, each method's diagnostics
and its cost), `summary.csv` and `summary.md` (the table at the end of this page),
and `context.json` (the machine, the library versions and every option of the
run). Pair geometry depends only on the seed, the site and the pair index, so a
rerun gives the same accuracy figures; times move by about 1 %.

The config, [`configs/n1.toml`](../configs/n1.toml):

```toml
[benchmark]
sites = ["beauce", "toulouse"]
scenarios = ["translation", "affine"]
degradations = ["clean", "mild", "hard"]
methods = [
    "phase_correlation",
    "phase_correlation_hann",
    "sift_ransac",
    "arosics",
    "arosics_floor60",
]

pairs = 100
size = 256
seed = 0

max_shift = 4.0
max_rotation = 0.2
max_scale_change = 0.002
max_shear = 0.002

failure_threshold = 1.0
warmup = 1
repeats = 3

sites_config = "configs/sites.toml"
degradations_config = "configs/degradations.toml"
methods_config = "configs/methods.toml"
data_dir = "data"
out = "outputs/n1"
```

The method parameters and the two variants are in
[`configs/methods.toml`](../configs/methods.toml).

## Hardware

| | |
|---|---|
| Machine | Apple M1, 8 CPUs, 8 GiB, macOS 26.6.2 (arm64) |
| Threads | no thread variable set; OpenCV on 8 threads |
| Python | 3.13.7 |
| Libraries | numpy 2.5.3, scipy 1.18.1, scikit-image 0.26.0, opencv-python-headless 5.0.0.93, rasterio 1.5.1, arosics 1.13.2, GDAL 3.13.3 |
| Process peak memory | 317 MiB for the whole run |

## Results

Mean end-point error in pixels, over the pairs a method did not fail; the failure
rate is in brackets when it is not zero. 100 pairs per cell.

| site | scenario | preset | phase correlation | phase corr. + Hann | SIFT + RANSAC | AROSICS | AROSICS, 60 % floor |
|---|---|---|---:|---:|---:|---:|---:|
| Beauce | translation | clean | 0.026 | **0.004** | 0.022 | 0.061 | 0.061 |
| Beauce | translation | mild | 0.043 | **0.013** | 0.046 | 0.096 | 0.096 |
| Beauce | translation | hard | 0.407 (4 %) | 0.450 (13 %) | 0.560 (76 %) | 0.400 (50 %) | 0.421 (78 %) |
| Beauce | affine | clean | 0.229 | 0.223 | **0.021** | 0.234 (1 %) | 0.234 (1 %) |
| Beauce | affine | mild | 0.233 | 0.223 | **0.046** | 0.246 | 0.246 |
| Beauce | affine | hard | 0.479 (6 %) | 0.516 (12 %) | 0.520 (76 %) | 0.494 (47 %) | 0.476 (76 %) |
| Toulouse | translation | clean | 0.010 | **0.004** | 0.006 | 0.016 | 0.016 |
| Toulouse | translation | mild | 0.010 | **0.005** | 0.009 | 0.027 | 0.027 |
| Toulouse | translation | hard | **0.100** | 0.183 | 0.279 (11 %) | 0.303 (22 %) | 0.307 (41 %) |
| Toulouse | affine | clean | 0.220 | 0.220 | **0.005** | 0.220 | 0.220 |
| Toulouse | affine | mild | 0.221 | 0.220 | **0.009** | 0.223 | 0.223 |
| Toulouse | affine | hard | **0.253** | 0.298 | 0.289 (12 %) | 0.392 (21 %) | 0.382 (40 %) |

On `hard` pairs the mean error alone is misleading, because each method is
averaged over a different subset. The share of the 100 pairs registered to better
than 0.3 px (the Sentinel-2 co-registration requirement), counting every failure
as a miss:

| site | scenario | phase correlation | phase corr. + Hann | SIFT + RANSAC | AROSICS | AROSICS, 60 % floor |
|---|---|---:|---:|---:|---:|---:|
| Beauce | translation, hard | **38 %** | 26 % | 6 % | 21 % | 8 % |
| Beauce | affine, hard | **21 %** | 16 % | 4 % | 9 % | 5 % |
| Toulouse | translation, hard | **98 %** | 85 % | 62 % | 35 % | 23 % |
| Toulouse | affine, hard | **74 %** | 58 % | 57 % | 17 % | 14 % |
| both | affine, clean | 75–78 % | 78 % | **100 %** | 74–78 % | 74–78 % |

Every method registers every clean and mild translation pair under 0.3 px.

### Cost

Median over the 600 calls per site (all scenarios and presets), each call timed
as the median of 3 after one warm-up call.

| method | time, Beauce | time, Toulouse | traced memory |
|---|---:|---:|---:|
| phase correlation | 3.6 ms | 3.6 ms | 6.5 MiB |
| phase correlation + Hann | 5.8 ms | 5.8 ms | 8.0 MiB |
| SIFT + RANSAC | 14.1 ms | 24.9 ms | 1.7 / 2.2 MiB |
| AROSICS | 16.8 ms | 16.7 ms | 10.0 MiB |

`tracemalloc` only sees memory allocated through Python: SIFT's native buffers
are missed, and its real footprint is about nine times the figure shown (measured
in [`decisions.md`](decisions.md)). AROSICS' first call in a process takes about
2 s, which the warm-up call absorbs.

## Reading the table

**Clean and mild translations: every method is well inside the target.** The
worst mean error is 0.096 px. The Hann-windowed phase correlation is the most
accurate, at 0.004 px on both sites, because the window removes the border
discontinuity that biases the unwindowed version (0.026 px on Beauce). AROSICS is
the least accurate of the four, 0.06 px on clean Beauce, although it also
phase-correlates: its sub-pixel peak estimate is coarser than scikit-image's
upsampled one.

**Affine motion: only SIFT follows it.** Phase correlation and AROSICS estimate a
single translation, so a rotation or scale change of this size leaves them at a
floor of about 0.22 px, whatever the image quality: 0.220 px on clean Toulouse
for all three, with about one pair in five above 0.3 px. That floor is the motion
model, not the estimator. SIFT + RANSAC fits an affine transform and stays at
0.005 to 0.05 px, ten to forty times better, as long as it finds enough keypoints.

**Hard pairs: phase correlation is the most robust, and nothing is good on
Beauce.** Under clouds, blur and radiometric change, plain phase correlation never
declines, fails 4 to 6 % of Beauce pairs by a gross error and none of Toulouse,
and has the highest share under 0.3 px in every hard cell. SIFT and AROSICS break
the other way: they decline what they cannot match. On Beauce, SIFT declines three
pairs in four for lack of inliers, and AROSICS half of them. Even the best method
registers only 38 % of hard Beauce translations to 0.3 px; the degradations there
are beyond what any classic method handles, which is the gap the AI methods of
the next levels are measured against.

**The scene matters as much as the method.** Toulouse's urban texture gives SIFT
about four times more keypoints than Beauce's fields (1,291 against 313 at the
median, on clean pairs), and every method is better there: on hard translations,
phase correlation goes from 38 % to 98 % of pairs under 0.3 px, SIFT's failure
rate from 76 % to 11 %. A single-site table would have mixed up what belongs to
the method and what belongs to the ground.

**Where each method breaks.**

- **Phase correlation** breaks on any motion that is not a translation (the
  0.22 px floor), and on low-texture scenes under heavy cloud, where it fails
  without warning: it returns a shift for every pair, right or wrong.
- **Phase correlation + Hann** is the best on clean pairs and worse on hard ones.
  The window concentrates the correlation on the centre of the pair, and when a
  cloud bank sits there, it correlates the cloud: 13 % gross errors on hard
  Beauce translations against 4 %, some off by 50 px (see
  [`failures.md`](failures.md)).
- **SIFT + RANSAC** breaks on texture: on hard Beauce it declines 137 of 200
  pairs for too few inliers, and 15 of the ones it keeps are off by more than
  1 px. It is also the only method whose cost depends on the scene, 14 ms on
  Beauce and 25 ms on Toulouse.
- **AROSICS** breaks under clouds and blur by declining: on hard Beauce, 54 of
  200 pairs find no match and 43 rate under 40 % reliability. It never returned a
  gross error in this run: what it keeps, it keeps right. Once, it found no match
  on a clean pair, for no reason found yet (see [`failures.md`](failures.md)).

**The two open choices.** The Hann window does not replace the unwindowed
version: it wins clean and mild, loses hard, so both stay in the table and the
plain one stays the reference row. AROSICS' reliability floor drops from 60 to
40 %: the pairs rated between the two are as accurate as those above 60 %, and the
lower floor cuts AROSICS' failure rate on hard Beauce from 78 % to 50 % with no
added gross error. Both decisions are in [`decisions.md`](decisions.md).

## Limits

- **Simulated displacements.** The motion is exact because it is simulated on a
  single image. The presets approximate what separates two real acquisitions
  (noise, blur, radiometry, clouds), but not everything: no change on the ground,
  no parallax, no seasonal difference.
- **One scene per site, one band.** Each site is one B04 chip; 100 windows cut
  from it are not independent scenes. The site effect above rests on two chips.
- **Global motion only.** Translation and a small affine motion over 256 px.
  Dense, spatially varying fields come in N2, with the learned methods.
- **Uncertainty.** With 100 pairs per cell, a failure rate is known to about
  ±5 points (one standard error at most), enough for the differences discussed
  here, not for differences of a point or two.
- **Cost on one laptop.** Times are for one M1 and 256 px windows, with default
  thread settings; they compare methods on the same machine and say little about
  another. Memory is what `tracemalloc` sees.

## The full table

As written by the run to `outputs/n1/summary.md`. "clouds" is the mean share of
the moving image under cloud; "< 0.1 px" and "< 0.5 px" are shares of pixels,
over the pairs that did not fail.

| site | scenario | degradation | method | pairs | clouds | EPE (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| beauce | translation | clean | phase_correlation | 100 | 0.0 % | 0.0261 | 100.0 % | 100.0 % | 0.0 % | 3.6 | 6.5 |
| beauce | translation | clean | phase_correlation_hann | 100 | 0.0 % | 0.0043 | 100.0 % | 100.0 % | 0.0 % | 5.9 | 8.0 |
| beauce | translation | clean | sift_ransac | 100 | 0.0 % | 0.0220 | 99.8 % | 100.0 % | 0.0 % | 14.3 | 1.7 |
| beauce | translation | clean | arosics | 100 | 0.0 % | 0.0608 | 85.0 % | 100.0 % | 0.0 % | 17.0 | 10.0 |
| beauce | translation | clean | arosics_floor60 | 100 | 0.0 % | 0.0608 | 85.0 % | 100.0 % | 0.0 % | 17.0 | 10.0 |
| beauce | translation | mild | phase_correlation | 100 | 5.0 % | 0.0429 | 95.0 % | 100.0 % | 0.0 % | 3.6 | 6.5 |
| beauce | translation | mild | phase_correlation_hann | 100 | 5.0 % | 0.0126 | 100.0 % | 100.0 % | 0.0 % | 5.8 | 8.0 |
| beauce | translation | mild | sift_ransac | 100 | 5.0 % | 0.0461 | 93.3 % | 100.0 % | 0.0 % | 14.3 | 1.7 |
| beauce | translation | mild | arosics | 100 | 5.0 % | 0.0963 | 57.0 % | 100.0 % | 0.0 % | 16.7 | 10.0 |
| beauce | translation | mild | arosics_floor60 | 100 | 5.0 % | 0.0963 | 57.0 % | 100.0 % | 0.0 % | 16.7 | 10.0 |
| beauce | translation | hard | phase_correlation | 100 | 30.0 % | 0.4073 | 7.3 % | 70.8 % | 4.0 % | 3.6 | 6.5 |
| beauce | translation | hard | phase_correlation_hann | 100 | 30.0 % | 0.4503 | 8.0 % | 64.4 % | 13.0 % | 5.8 | 8.0 |
| beauce | translation | hard | sift_ransac | 100 | 30.0 % | 0.5595 | 7.6 % | 57.1 % | 76.0 % | 13.9 | 1.7 |
| beauce | translation | hard | arosics | 100 | 30.0 % | 0.3996 | 8.0 % | 72.0 % | 50.0 % | 16.7 | 10.0 |
| beauce | translation | hard | arosics_floor60 | 100 | 30.0 % | 0.4209 | 0.0 % | 77.3 % | 78.0 % | 16.6 | 10.0 |
| beauce | affine | clean | phase_correlation | 100 | 0.0 % | 0.2288 | 19.9 % | 95.0 % | 0.0 % | 3.6 | 6.5 |
| beauce | affine | clean | phase_correlation_hann | 100 | 0.0 % | 0.2225 | 20.7 % | 96.0 % | 0.0 % | 6.0 | 8.0 |
| beauce | affine | clean | sift_ransac | 100 | 0.0 % | 0.0209 | 99.9 % | 100.0 % | 0.0 % | 14.2 | 1.7 |
| beauce | affine | clean | arosics | 100 | 0.0 % | 0.2336 | 17.7 % | 94.9 % | 1.0 % | 17.0 | 10.0 |
| beauce | affine | clean | arosics_floor60 | 100 | 0.0 % | 0.2336 | 17.7 % | 94.9 % | 1.0 % | 16.9 | 10.0 |
| beauce | affine | mild | phase_correlation | 100 | 5.0 % | 0.2327 | 18.7 % | 94.5 % | 0.0 % | 3.6 | 6.5 |
| beauce | affine | mild | phase_correlation_hann | 100 | 5.0 % | 0.2228 | 20.5 % | 96.0 % | 0.0 % | 5.7 | 8.0 |
| beauce | affine | mild | sift_ransac | 100 | 5.0 % | 0.0463 | 93.0 % | 100.0 % | 0.0 % | 14.1 | 1.7 |
| beauce | affine | mild | arosics | 100 | 5.0 % | 0.2460 | 14.8 % | 94.2 % | 0.0 % | 16.7 | 10.0 |
| beauce | affine | mild | arosics_floor60 | 100 | 5.0 % | 0.2460 | 14.8 % | 94.2 % | 0.0 % | 16.7 | 10.0 |
| beauce | affine | hard | phase_correlation | 100 | 30.0 % | 0.4785 | 4.2 % | 57.3 % | 6.0 % | 3.6 | 6.5 |
| beauce | affine | hard | phase_correlation_hann | 100 | 30.0 % | 0.5162 | 4.2 % | 52.7 % | 12.0 % | 5.7 | 8.0 |
| beauce | affine | hard | sift_ransac | 100 | 30.0 % | 0.5197 | 6.8 % | 59.9 % | 76.0 % | 13.7 | 1.7 |
| beauce | affine | hard | arosics | 100 | 30.0 % | 0.4944 | 3.6 % | 56.8 % | 47.0 % | 16.7 | 10.0 |
| beauce | affine | hard | arosics_floor60 | 100 | 30.0 % | 0.4756 | 3.7 % | 61.7 % | 76.0 % | 16.6 | 10.0 |
| toulouse | translation | clean | phase_correlation | 100 | 0.0 % | 0.0095 | 100.0 % | 100.0 % | 0.0 % | 3.6 | 6.5 |
| toulouse | translation | clean | phase_correlation_hann | 100 | 0.0 % | 0.0040 | 100.0 % | 100.0 % | 0.0 % | 5.9 | 8.0 |
| toulouse | translation | clean | sift_ransac | 100 | 0.0 % | 0.0055 | 100.0 % | 100.0 % | 0.0 % | 25.7 | 2.2 |
| toulouse | translation | clean | arosics | 100 | 0.0 % | 0.0156 | 100.0 % | 100.0 % | 0.0 % | 17.0 | 10.0 |
| toulouse | translation | clean | arosics_floor60 | 100 | 0.0 % | 0.0156 | 100.0 % | 100.0 % | 0.0 % | 16.9 | 10.0 |
| toulouse | translation | mild | phase_correlation | 100 | 5.0 % | 0.0103 | 100.0 % | 100.0 % | 0.0 % | 3.6 | 6.5 |
| toulouse | translation | mild | phase_correlation_hann | 100 | 5.0 % | 0.0048 | 100.0 % | 100.0 % | 0.0 % | 5.7 | 8.0 |
| toulouse | translation | mild | sift_ransac | 100 | 5.0 % | 0.0090 | 100.0 % | 100.0 % | 0.0 % | 25.9 | 2.2 |
| toulouse | translation | mild | arosics | 100 | 5.0 % | 0.0267 | 100.0 % | 100.0 % | 0.0 % | 16.7 | 10.0 |
| toulouse | translation | mild | arosics_floor60 | 100 | 5.0 % | 0.0267 | 100.0 % | 100.0 % | 0.0 % | 16.6 | 10.0 |
| toulouse | translation | hard | phase_correlation | 100 | 30.0 % | 0.0997 | 59.0 % | 100.0 % | 0.0 % | 3.6 | 6.5 |
| toulouse | translation | hard | phase_correlation_hann | 100 | 30.0 % | 0.1833 | 32.0 % | 96.0 % | 0.0 % | 5.8 | 8.0 |
| toulouse | translation | hard | sift_ransac | 100 | 30.0 % | 0.2792 | 21.6 % | 86.7 % | 11.0 % | 17.6 | 2.1 |
| toulouse | translation | hard | arosics | 100 | 30.0 % | 0.3026 | 3.8 % | 97.4 % | 22.0 % | 16.7 | 10.0 |
| toulouse | translation | hard | arosics_floor60 | 100 | 30.0 % | 0.3069 | 5.1 % | 98.3 % | 41.0 % | 16.6 | 10.0 |
| toulouse | affine | clean | phase_correlation | 100 | 0.0 % | 0.2204 | 20.5 % | 96.2 % | 0.0 % | 3.6 | 6.5 |
| toulouse | affine | clean | phase_correlation_hann | 100 | 0.0 % | 0.2195 | 20.6 % | 96.3 % | 0.0 % | 6.0 | 8.0 |
| toulouse | affine | clean | sift_ransac | 100 | 0.0 % | 0.0054 | 100.0 % | 100.0 % | 0.0 % | 25.7 | 2.2 |
| toulouse | affine | clean | arosics | 100 | 0.0 % | 0.2204 | 20.5 % | 96.2 % | 0.0 % | 16.9 | 10.0 |
| toulouse | affine | clean | arosics_floor60 | 100 | 0.0 % | 0.2204 | 20.5 % | 96.2 % | 0.0 % | 16.9 | 10.0 |
| toulouse | affine | mild | phase_correlation | 100 | 5.0 % | 0.2206 | 20.5 % | 96.2 % | 0.0 % | 3.6 | 6.5 |
| toulouse | affine | mild | phase_correlation_hann | 100 | 5.0 % | 0.2196 | 20.6 % | 96.3 % | 0.0 % | 5.7 | 8.0 |
| toulouse | affine | mild | sift_ransac | 100 | 5.0 % | 0.0090 | 100.0 % | 100.0 % | 0.0 % | 25.8 | 2.2 |
| toulouse | affine | mild | arosics | 100 | 5.0 % | 0.2227 | 20.0 % | 96.0 % | 0.0 % | 16.7 | 10.0 |
| toulouse | affine | mild | arosics_floor60 | 100 | 5.0 % | 0.2227 | 20.0 % | 96.0 % | 0.0 % | 16.6 | 10.0 |
| toulouse | affine | hard | phase_correlation | 100 | 30.0 % | 0.2527 | 13.8 % | 93.2 % | 0.0 % | 3.6 | 6.5 |
| toulouse | affine | hard | phase_correlation_hann | 100 | 30.0 % | 0.2977 | 10.1 % | 87.3 % | 0.0 % | 5.7 | 8.0 |
| toulouse | affine | hard | sift_ransac | 100 | 30.0 % | 0.2894 | 20.5 % | 85.1 % | 12.0 % | 17.6 | 2.1 |
| toulouse | affine | hard | arosics | 100 | 30.0 % | 0.3915 | 4.1 % | 73.7 % | 21.0 % | 16.7 | 10.0 |
| toulouse | affine | hard | arosics_floor60 | 100 | 30.0 % | 0.3819 | 3.9 % | 75.8 % | 40.0 % | 16.6 | 10.0 |

Measured on Apple M1, 8 GiB, 8 CPUs, macOS-26.6.2-arm64-arm-64bit-Mach-O. Time is the median of 3 calls per pair, after 1 warm-up call(s) per method; memory is the peak traced by tracemalloc, which misses native allocations. Details in `context.json`.

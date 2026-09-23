# ai-satellite-image-registration

**Aligning satellite images to a tenth of a pixel: classic methods vs AI.**

Two images of the same place never line up exactly. This project measures how well
classic and deep-learning methods recover the displacement between two Sentinel-2
images, on accuracy and on compute cost. Displacements are simulated on real
imagery, so the ground truth is exact down to a fraction of a pixel.

**Status: in progress, level N1** (simulator, classic methods, metrics). So far the
pipeline runs end to end with phase correlation and SIFT + RANSAC, on a synthetic
texture or on a real Sentinel-2 chip, under increasingly degraded conditions, for
translations and small affine motions. AROSICS comes next.

## Run it

Python 3.11 or later.

```bash
python -m venv .venv && source .venv/bin/activate
make install
make test
satreg benchmark
```

`satreg benchmark` simulates pairs with known sub-pixel motion, runs every method,
prints the results table and writes it to `outputs/benchmark/` as `summary.md` and
`summary.csv`, with one row per pair and method in `pairs.csv`. `satreg benchmark
--help` lists the options (number of pairs, image size, motion ranges, seed, failure
threshold).

### Methods

- `phase_correlation`: scikit-image's sub-pixel phase correlation, refined to
  1/100 px. It estimates a single translation.
- `sift_ransac`: OpenCV SIFT keypoints, matched with Lowe's ratio test, and an
  affine transform fitted by RANSAC. With too few inliers it declines the pair,
  which counts as a failure. Its match and inlier counts are in `pairs.csv`.

`--methods` picks some. Method parameters (SIFT's ratio, RANSAC threshold and
minimum inlier count) are set in [`configs/methods.toml`](configs/methods.toml).

### Translation and affine motion

Each pair is simulated twice: shifted, and under a small affine motion (rotation,
scale change and shear about the pair's centre, on top of the same shift). Both
versions share the reference image and the displacement at the centre, so the
difference between the two rows of a method is the cost of its motion model.
The default ranges (±0.2°, ±0.2 % scale, ±0.002 shear) are sized around the
Sentinel-2 co-registration requirement of 0.3 px. `--scenarios affine` runs one
scenario, and `--max-rotation`, `--max-scale-change` and `--max-shear` change the
ranges. Both scenarios are warped with the same band-limited interpolation, and
pixels whose displaced position leaves the moving image are left out of the
metrics.

### On Sentinel-2 imagery

```bash
satreg fetch                      # every site in configs/sites.toml
satreg benchmark --site beauce
```

`satreg fetch` finds the least cloudy Sentinel-2 L2A scene of each site in the
[Earth Search](https://earth-search.aws.element84.com/v1) STAC catalogue and reads
a 1024 × 1024 px window of its B04 COG, on the native 10 m grid with no
resampling. No account is needed. The chip (about 1.5 MB per site) is cached in
`data/chips/`, which is not committed: later runs make no network call, and
`satreg benchmark --site <name>` fetches a missing chip by itself. Sites, dates,
cloud limit, chip size and band are set in [`configs/sites.toml`](configs/sites.toml).
Without `--site`, the benchmark uses the synthetic texture and runs offline.

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

## Where the reasoning is

- [`docs/decisions.md`](docs/decisions.md): each choice and why it was made.
- [`docs/failures.md`](docs/failures.md): what did not work, and what it taught.

## How this was built

I use Claude Code as an assistant throughout. It writes a share of the code and
prose, under review. The decisions are recorded in
[`docs/decisions.md`](docs/decisions.md), which is the place to judge whether I
understand what is here.

## License

MIT

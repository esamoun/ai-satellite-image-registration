# ai-satellite-image-registration

**Aligning satellite images to a tenth of a pixel: classic methods vs AI.**

Two images of the same place never line up exactly. This project measures how well
classic and deep-learning methods recover the displacement between two Sentinel-2
images, on accuracy and on compute cost. Displacements are simulated on real
imagery, so the ground truth is exact down to a fraction of a pixel.

**Status: in progress, level N1** (simulator, classic methods, metrics). So far the
pipeline runs end to end on a synthetic texture with phase correlation. Sentinel-2
ingestion, degradations, affine motion, SIFT + RANSAC and AROSICS come next.

## Run it

Python 3.11 or later.

```bash
python -m venv .venv && source .venv/bin/activate
make install
make test
satreg benchmark
```

`satreg benchmark` simulates pairs with known sub-pixel shifts, runs every method,
prints the results table and writes it to `outputs/benchmark/` as `summary.md` and
`summary.csv`, with one row per pair and method in `pairs.csv`. `satreg benchmark
--help` lists the options (number of pairs, image size, maximum shift, seed, failure
threshold).

The table reports, per method: mean end-point error (EPE, in pixels), the share of
pixels whose error is under 0.1 px and under 0.5 px, and the failure rate.

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

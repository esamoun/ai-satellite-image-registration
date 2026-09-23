# Decision log

Why each choice was made, dated, with the reasoning that produced it. Append; do not
rewrite history. When a decision turns out to be wrong, add a new entry that
supersedes the old one rather than editing it.

---

## 2026-09-23: Sentinel-2 from native COGs via STAC, not Google Earth Engine

**Decision.** Imagery comes from Sentinel-2 cloud-optimised GeoTIFFs, found through
a STAC catalogue (Planetary Computer or Earth Search) and read in their native grid.

**Why.** This project measures errors of a tenth of a pixel. Earth Engine exports
resample on the way out, and that resampling changes sub-pixel geometry by amounts
comparable to what is being measured. Reading the original COG window keeps the
pixel grid the sensor product was delivered on.

**Rejected.** Google Earth Engine (resampling on export).

---

## 2026-09-23: One displacement convention, always evaluated as a field

**Decision.** A displacement `d` at reference pixel `p` means
`moving(p + d) = reference(p)`, with components `(dy, dx)` in pixels. Every model
(translation now, affine and dense flow later) exposes the same operation:
evaluate itself as a `(2, rows, cols)` field on the reference grid. Ground truth and
estimates use the same types, and metrics only see fields.

**Why.** The project moves from global shifts to affine to dense fields. If each
model were scored its own way (comparing `dx` values for translations, matrices for
affine), results would stop being comparable between levels and each new model
would need new metric code. Evaluated per pixel, a translation estimate scored on
an affine pair gets the error it deserves with no special case. The convention is
stated once and pinned by tests, because libraries disagree: scikit-image, for
instance, returns the shift that registers the moving image back, which is `-d`.

---

## 2026-09-23: Sub-pixel shifts by Fourier phase ramp, with a mirrored window and a cropped margin

**Decision.** The simulator shifts a window larger than the pair with a Fourier
phase ramp, after mirroring it (symmetric padding), then crops both images to the
centre. The margin cropped on each side is `ceil(max shift) + 16` px.

**Why.** Spline interpolation low-passes the image it shifts, so the moving image
would be blurrier than the reference, and methods would be scored on a pair that
differs by more than a shift. A Fourier shift is band-limited interpolation and
does not blur. It assumes the image is periodic, which rings at the edges. Mirroring
makes the wrap-around continuous. Cropping a margin removes the edge band and means
the moving image shows real scene content entering at its borders, not padded or
wrapped pixels. Measured against an exact shift (a window cut from a periodic
texture shifted as a whole), the maximum error 16 px inside the window is 0.03
image standard deviations on the MTF texture described below.

**Rejected.** Cubic spline shift (`scipy.ndimage.shift`): on a texture without MTF,
its maximum error stayed at 0.58 standard deviations all the way to the centre,
against 0.07 for the mirrored Fourier shift, because of its low-pass effect.
Fourier shift without padding: 0.09 in the interior and 0.58 at the edges, against
0.07 and 0.39 with mirroring.

---

## 2026-09-23: Synthetic test site: 1/f texture seen through a sensor MTF

**Decision.** Until Sentinel-2 chips are wired in, and for every offline test, the
site image is a 1/f random texture multiplied by a Gaussian MTF equal to 0.3 at
Nyquist.

**Why.** Natural scenes have roughly 1/f amplitude spectra, so the texture has
structure at every scale, which matters to both correlation and feature methods.
Without an MTF it also carries full energy at Nyquist, which a sub-pixel shift
cannot represent unambiguously. In the Fourier-shift test above, the interior
error was 0.068 standard deviations without an MTF and 0.021 with 0.3 at Nyquist:
most of the simulation error came from that unrealistic energy. Sentinel-2 10 m
bands sit around 0.2-0.3 at Nyquist, so this is also closer to the real imagery.

---

## 2026-09-23: A failure is a crash, a non-finite estimate or a mean error above 1 px

**Decision.** A method fails on a pair if it raises, returns non-finite values, or
its mean end-point error exceeds 1 px (configurable with `--failure-threshold`).
The results table reports the failure rate, and averages EPE and the sub-pixel
shares over non-failed pairs only.

**Why.** The benchmark is about the sub-pixel regime. A method that lands 30 px
off has not been inaccurate, it has locked onto the wrong peak, and one such pair
would dominate a mean over twenty. Keeping gross failures out of the mean and
counting them separately gives two readable numbers instead of one polluted one.
The cost: a method can look accurate while failing often, so the two columns must
always be read together, and the table never shows one without the other. A crash
is caught and recorded rather than stopping the run, because a method that crashes
on some pairs is itself a result.

---

## 2026-09-23: Phase correlation as scikit-image ships it, refined to 1/100 px

**Decision.** `skimage.registration.phase_cross_correlation` with
`upsample_factor=100` and no apodisation window.

**Why.** The spec names the scikit-image implementation as the baseline, so it is
used as a practitioner would call it. An upsampling factor of 100 puts the
resolution at 0.01 px, ten times finer than the 0.1 px target. A Hann window
lowered the error slightly in an early probe on a texture without MTF (mean error
0.0042 px against 0.0063 px over 30 pairs). That is too small to matter on clean
pairs. Whether a window helps once clouds and noise arrive will be tested then,
not assumed now.

---

## 2026-09-23: Pair geometry depends only on seed, site and pair index

**Decision.** Each pair's window position and shift come from a generator seeded by
the run seed, the site name (hashed with CRC-32) and the pair index. Degradations
get their own generator, derived from the same keys plus the degradation name.

**Why.** Every method and every degradation then sees exactly the same
displacements, so differences in the table come from the methods and conditions,
not from luck of the draw. Hashing names rather than using positions means adding
a site or a degradation does not change the pairs of the others.

---

## 2026-09-23: Tooling: pip and venv, ruff, no pandas

**Decision.** The package installs with pip into a venv (`make install`), is linted
and formatted with ruff (88 columns) and tested with pytest. Core dependencies are
numpy, scipy and scikit-image. Tables are written with the standard `csv` module.

**Why.** The same `make lint` and `make test` must run on a laptop and in CI, and
pip is what CI will use. The conda install on the development machine is currently
broken, which was a nudge but not the reason. pandas would be one more dependency
for writing two small tables.

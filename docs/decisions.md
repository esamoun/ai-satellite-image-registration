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

---

## 2026-09-23: Chips are whole-pixel windows of the native COG, nothing else

**Decision.** A site's chip is read from the Sentinel-2 COG as an integer-aligned
window: the site centre is projected into the tile's UTM CRS, the pixel it falls in
is found, and a `chip_px` square around it is read. No resampling, no
reprojection, no warping. The chip is saved as a GeoTIFF with the source CRS and
the source geotransform offset by a whole number of pixels, plus the scene it came
from in its tags.

**Why.** The benchmark measures errors of a hundredth of a pixel. Any resampling
on the way in, even to "the same" grid, interpolates the image and changes its
sub-pixel content by amounts of that order, and a reprojection to another CRS also
bends the pixel grid. Reading whole source pixels means the chip is exactly what
the product delivered, and the test suite checks it pixel for pixel against the
source array and its geotransform. The price is that a chip always lives in its
tile's own UTM zone and cannot straddle two tiles. A scene where the window leaves
the tile or touches no-data (the edge of the swath) is skipped for the next one.

**Rejected.** `rasterio.warp` or a VRT to a common grid (resampling);
`stackstac`/`odc-stac` (built to mosaic and reproject, which is the opposite of
what is wanted here, and heavy dependencies for a single window).

---

## 2026-09-23: Earth Search, Sentinel-2 Collection 1 L2A

**Decision.** Scenes are searched in the `sentinel-2-c1-l2a` collection of Earth
Search (Element 84), through `pystac-client`. The catalogue URL and collection sit
in `configs/sites.toml`, not in the code.

**Why.** Its COGs are public over plain HTTPS: no account, no token, no URL
signing, so a fresh clone can fetch the data and nothing expires between runs.
Collection 1 is ESA's reprocessing of the archive with one processing baseline,
so two scenes from different years went through the same geometric processing,
which matters once real pairs arrive in N2. Planetary Computer also serves native
COGs, but its asset URLs must be signed with short-lived tokens, which adds a
dependency and a failure mode for no gain here. Band assets are found by their
`eo:bands` name (`B04`), not by Earth Search's asset keys (`red`), so switching
catalogue only means editing the configuration. Only single-band assets match,
so the 8-bit true-colour `visual` asset, which also lists B04, is never picked.

**Rejected.** Planetary Computer (signed URLs); Earth Search `sentinel-2-l2a`
(mixed processing baselines); Google Earth Engine (see the first entry).

---

## 2026-09-23: Sites are a centre and a size in pixels; the least cloudy scene wins

**Decision.** A site is declared in `configs/sites.toml` as a centre (lon, lat), a
chip size in source pixels (1024 by default, 10.24 km), a date range, a maximum
scene cloud cover and a band (B04 by default). The chip comes from the least
cloudy scene of the range, ties broken by item id. Beauce is the N1 site, Toulouse
is declared as the optional second one.

**Why.** A bounding box in degrees does not map to a square window of pixels in
UTM, and its size in pixels would change with latitude; a centre plus a size in
pixels gives the same square chip everywhere. The cloud filter uses the scene's
`eo:cloud_cover`, not a cloud mask of the chip itself. That is enough for N1: both
images of a simulated pair are cut from the same chip, so a cloud there is just
texture, present in both, and the ground truth is still exact. Real pairs (N2) will
need a chip-level mask, and it will be added then. The dates are in the
configuration, so the chosen scene is reproducible as long as the catalogue does
not change.

---

## 2026-09-23: Chips are cached under a key of the parameters that pick them

**Decision.** A chip is cached as `data/chips/<site>/<band>_<hash>.tif`, the hash
covering every site parameter and the catalogue. A cached chip is used without any
network call; a missing one is fetched on demand by `satreg benchmark` or ahead of
time by `satreg fetch`. `data/` is gitignored.

**Why.** Keyed on the site name alone, editing the dates or the size in the
configuration would silently keep benchmarking the old chip. With the parameters
in the key, a change fetches a new chip and the old one stays valid for its old
parameters. The file is written under a temporary name and renamed once complete,
so an interrupted download is never mistaken for a cached chip. Chips keep the
product's digital numbers (uint16): phase correlation, and the methods to come, do
not depend on an affine change of intensity, and converting to reflectance would
change nothing geometric.

---

## 2026-09-23: The test suite refuses the network

**Decision.** Every test runs with Python socket connections disabled
(`tests/conftest.py`). The STAC search is replaced by a fake, and COG reads are
served from tiny GeoTIFFs written by the tests themselves.

**Why.** CI must not depend on a public catalogue being up, and a test that
silently downloads a chip would pass locally and fail, or be slow, elsewhere.
Disabling sockets turns "the tests are offline" from an intention into a check.
The fixture rasters use a real UTM grid over the Beauce, so the lon/lat to pixel
path is exercised with a real projection.

---

## 2026-09-23: Degradations change pixel values only, in a fixed physical order

**Decision.** Four degradations make a simulated pair harder: a radiometric
difference, clouds, a Gaussian blur and white Gaussian noise. Each one is a small
parameterised object `(pair, rng) -> pair` that returns the ground truth it was
given, untouched, and draws all its randomness from the generator it receives. A
preset combines them, always in the order radiometry, clouds, blur, noise: the
ground changes appearance, clouds cover it, the moving acquisition's optics blur
everything they see, cloud edges included, and both detectors add noise last.
Named presets (`clean`, `mild`, `hard`) sit in `configs/degradations.toml`, with
fixed strengths rather than random ranges, so each row of the results table is
one well-defined condition. `satreg benchmark` runs every preset by default, or
the ones named with `--degradations`.

Units are chosen so that a preset means the same thing on the unit-variance
synthetic texture and on Sentinel-2 digital numbers, whose mean (2 300 on the
Beauce chip, against a spread of 680) is far above their spread:

- **Radiometry** (moving image): gamma bends the image's own range, mapped to
  [0, 1] by its minimum and maximum; gain scales deviations from the image mean
  (a contrast change); the offset shifts the level by a number of reference
  standard deviations. A plain `gain * x` would, on digital numbers, turn a 30 %
  contrast change into a level shift of several standard deviations.
- **Clouds** (moving image): see the next entry.
- **Blur** (moving image): Gaussian, sigma in pixels. It models a sharpness
  difference between the two acquisitions (viewing angle, detector, focus), not
  the sensor MTF itself, which the chips already carry.
- **Noise** (both images, drawn independently): the SNR is
  `20 log10(std(reference) / std(noise))`, the scene contrast over the noise,
  which is what registration works from. A radiometric SNR (mean over noise)
  would say little: two scenes with the same mean can have very different
  texture.

Preset values are judgement calls, to be checked against real pairs in N2:
`mild` is a good pair (30 dB, 0.4 px blur, 10 % contrast change, 5 % clouds, i.e.
what a scene-level cloud filter lets through); `hard` is a poor but usable one
(15 dB, 1 px blur, 30 % contrast loss with a strong tone-curve change, 30 %
clouds). For scale, the Beauce chip's own noise, estimated with Immerkær's
method on 256 px windows, sits at 29-35 dB by this definition. That noise is
identical in both images of a simulated pair, since both are cut from the same
chip, so it does not hurt registration; only the added noise, independent
between the images, does.

**Why.** "Degradations never change the geometry" has to hold by construction,
not by luck: pointwise changes (radiometry, noise) cannot move content, the
Gaussian kernel is symmetric, and clouds are blended in place. The test suite
checks the geometry on the pixels themselves (blurring the moving image equals
shifting a blurred scene, to 0.01 standard deviations), not through a
registration method, which has biases of its own (see `docs/failures.md`).
Each degradation takes a generator rather than a seed, and the benchmark derives
it from the run seed, site, pair index and preset name (entry above), so the
same seed gives the same pair bit for bit.

**Rejected.** Noise on the moving image only: it would make the reference an
idealised noise-free image, which no real pair has. Random strengths drawn per
pair within a range: the table would mix conditions inside one row.

---

## 2026-09-23: Clouds are left to the methods; metrics cover the whole grid

**Decision.** Clouds are laid over the moving image only, as a smooth random field
(1/f² spectrum) thresholded so that exactly the requested share of pixels is at
least half covered. Opacity ramps from 0 to 1 across the threshold, so banks have
opaque cores and thin edges, and the cloud level is the reference mean plus four
standard deviations. Methods get no cloud mask: they see the cloudy image, as
they would a real scene, and must cope. Metrics are computed over the whole
reference grid, cloud included. Each pair's cloud fraction (share at least half
covered) is reported in `pairs.csv`, and its mean per row in the results table.

**Why.** In N1 the displacement is global: it is defined, and known, under the
cloud as much as beside it, so there is no pixel where the truth is missing and
no reason to drop pixels from the metric. What clouds test is whether a method
is thrown off by bright, featureless, moving-image-only structure. Handing
methods a mask would test the mask instead. The L2A scene classification does
provide one in practice, but it misses thin cloud edges and haze, which is where
methods break. Reporting the cloud fraction next to the error keeps the two
readable together. When dense fields arrive (N2), a pixel under an opaque cloud
has no observable ground, so the validity mask introduced with affine warps
(ticket 04) will be extended to exclude opaque cloud from the dense metrics;
global models will still be scored everywhere.

**Rejected.** Masking clouds out of the metric for global models (it would score
nothing the method did); giving methods the true cloud mask (unrealistically
perfect); clouds on both images (a later option, but a cloud in the reference
only is symmetric to one in the moving image for a global shift, and one side
keeps the table readable).

---

## 2026-09-23: Affine motion in physical units, with ranges sized around the 0.3 px co-registration spec

**Decision.** An affine displacement is given as a rotation (degrees), a scale
factor, a shear and a translation (px), applied about the pair's centre: shear,
then scale, then rotation, then the centre moves by `(dx, dy)`. Rotation is
counter-clockwise on screen (rows point down), and the shear is `x' = x + shear·y`.
The truth is stored as the resulting matrix and offset (`q = M p + o` in row and
column indices), so metrics still see only a field (entry "One displacement
convention"). Benchmark defaults draw each parameter uniformly within:

| parameter | range | largest effect at the corner of a 256 px pair |
|---|---|---:|
| rotation | ±0.2° | 0.63 px |
| scale | 1 ± 0.002 | 0.36 px |
| shear | ±0.002 | 0.26 px |
| translation | ±4 px | (same as the translation scenario) |

On the default run the part of the truth that is not a translation averages
0.45 px at the worst corner of a pair, up to 0.89 px.

**Why.** Physical units make the ranges checkable against the sensor. The
Sentinel-2 multi-temporal co-registration requirement is 0.3 px at 95 % for the
10 m bands, and orthorectified L2A pairs of one tile are close to pure
translations. The lower half of each range is what a pair within spec can show.
The upper half stands for pairs outside it: before orthorectification, across
sensors, or with residual terrain effects. The ranges cross the project's 0.1 px
target on purpose, so the table separates methods that model the motion from
methods that do not. They are judgement calls, not measured on real pairs.
Checking them against real Sentinel-2 residuals is N2's job. Applying the
transform about the pair's centre keeps `(dx, dy)` the displacement at the
centre, so an affine pair and its translation twin share it (entry below).

**Rejected.** A raw 2 × 3 matrix as the input: its entries have no range anyone
can check against a spec. Degree-level rotations and percent-level scale changes:
they describe airborne or uncorrected imagery, not orthorectified Sentinel-2.

---

## 2026-09-23: One band-limited warp for every scenario, and a validity mask from the truth

**Decision.** Affine warps use the same interpolation as translations: band-limited
(Fourier) resampling. The warp is split into two 1-D shear-and-scale passes (the
Catmull–Smith decomposition): rows, then columns. Each line is mirrored like the
translation window, then resampled at evenly spaced positions by evaluating its
Fourier series there. With no linear part, the warp reduces to `fourier_shift`, to
5.5e-5 of the image range and exactly for integer shifts, so both scenarios share
one interpolation. Transforms that two passes cannot handle (rotations beyond
about 45°, reflections) are refused. They are far outside the ranges above.

The margin cropped around a pair covers the largest displacement any scenario of
the run can produce. It is bounded analytically from the configured ranges
(7.1 px by default, hence a 24 px margin, up from 20 px for translations alone).
`simulate_affine` refuses a margin below what its transform needs.

A reference pixel is valid when its displaced position falls inside the moving
image, between the first and last pixel centres. The mask is computed from the
truth, so it cannot go stale and degradations keep it. The benchmark averages
errors over valid pixels only. That is 97 to 98 % of the pixels on the default run.

**Why.** The previous entry on Fourier shifts holds for warps too: a spline or a
windowed-sinc kernel low-passes the moving image, so methods would face a blur
on top of the motion. That blur would also land in the affine scenario only,
since the translation scenario uses a Fourier shift. Measured on sub-pixel shifts
of (0.5, 0.5) px, the maximum error against an exact shift was:

| interpolation | MTF texture | Beauce |
|---|---:|---:|
| Fourier | 0.036 | 0.026 |
| cubic spline | 0.235 | 0.164 |
| quintic spline | 0.160 | 0.100 |
| Lanczos-4 | 0.168 | not measured |
| Lanczos-6 | 0.123 | not measured |

Against an analytic rendering of Gaussian spots under a 2° rotation, 2 % zoom and
0.01 shear, the two-pass warp is off by 8.5e-6 (the cubic spline by 3.4e-3). It
moves spot centroids to within 1.4e-5 px of the truth. It takes about 5 ms on a
200 px image. The mask matters because at the edge of an affine pair the
reference shows content that the moving image does not. Scoring those pixels
would score the simulator, not the method. For a translation the mask removes
the band that a shift uncovers. The clouds entry still holds: pixels under cloud
stay in the metric, because the truth is defined there.

**Rejected.** `scipy.ndimage.affine_transform` at spline order 3 or 5, and Lanczos
kernels: numbers above. A 2-D Fourier warp by chirp-z or a non-uniform FFT: more
code and a dependency, for the same band-limited result as two exact 1-D passes.
Excluding border pixels by a fixed band: too wide for a translation, and still
wrong at the corners of a rotation.

---

## 2026-09-23: Affine pairs are twins of translation pairs

**Decision.** Scenarios are a column of the results table (`translation`,
`affine`, set with `--scenarios`). For a given seed, site and pair index, both
scenarios draw the window, the shift and the affine parameters in the same
order. The margin is the same whichever scenarios run. So the affine pair has the
same reference image and the same displacement at its centre as its translation
twin. It differs only by the linear part of the motion. Degradations are seeded
the same way in both scenarios.

**Why.** The difference between the two rows of a method is then the cost of the
motion model alone. That is the question the affine scenario exists to answer.
First finding: phase correlation on affine pairs sits at the floor of any
translation model, meaning the best single translation, the componentwise median
of the true field over valid pixels. On 20 clean pairs of 256 px it scores
0.2315 px against a floor of 0.2311 px on the synthetic site, and 0.2179 px
against 0.2126 px on Beauce. It finds the right translation, and its whole error
is the model's. A method that reaches 0.1 px on these pairs has to model the
affine part.

This changes the numbers of earlier runs. The margin grew from 20 to 24 px, so
the same seed now cuts different windows.

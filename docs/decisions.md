# Decision log

Why each choice was made, dated, with the reasoning that produced it. Append; do not
rewrite history. When a decision turns out to be wrong, add a new entry that
supersedes the old one rather than editing it.

Entries are drafted with Claude Code and reviewed by me. Those marked *My call*
are the ones where I chose between options.

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

---

## 2026-09-23: SIFT + RANSAC as OpenCV ships it, always fitting an affine

**Decision.** The second classic method (`sift_ransac`) detects SIFT keypoints in
both images with OpenCV's defaults, matches their descriptors by brute force with
Lowe's ratio test (0.75), and fits an affine transform to the matches with
`cv2.estimateAffine2D`: RANSAC with a 1 px reprojection threshold, then
Levenberg-Marquardt refinement on the inliers. It fits an affine on every pair,
translation pairs included. With fewer than 10 matches or 10 inliers it declines
the pair (entry below). Ratio, threshold and minimum inlier count are set in
`configs/methods.toml`. OpenCV comes from the `opencv-python-headless` wheel, a
core dependency.

SIFT in OpenCV reads 8-bit images, so each image is stretched linearly between
its own 1st and 99th percentiles to 0-255, then clipped and rounded. The mapping
uses nothing but the image it converts: it does not know which preset the pair
went through, and a gain or offset between the two images leaves it unchanged
(tested). Clouds do move the 99th percentile, which is intended: a method sees
the cloudy image as it is.

**Why.** It is the textbook feature-based pipeline, called as a practitioner
would call it, which is what a baseline should be. It models the affine part that
phase correlation cannot. On 20 clean affine pairs it scores 0.005 px on the
synthetic site and 0.023 px on Beauce, against 0.23 and 0.22 px for phase
correlation, which is stuck at the floor of a translation model. On translation
pairs it matches phase correlation on Beauce (0.023 px both) and costs nothing
measurable for its four extra parameters. Fitting one model everywhere keeps the
method blind to the scenario, as a real user would be. `hard` is where it breaks:
on Beauce, 15 dB of noise and a 1 px blur on flat agricultural parcels leave
about 6 inliers per pair, and it fails 75 % (translation) and 80 % (affine) of
the pairs, where phase correlation fails 0 and 5 %. On the pairs SIFT keeps it is
the more accurate of the two (0.38 against 0.44 px on translations, 0.32 against
0.50 px on affine pairs), but it keeps few. On the synthetic texture, which has
structure at every scale, it never fails on `hard`.

The 8-bit stretch was probed on the same pairs: full range (0-100 %), 0.1-99.9 %,
1-99 % and 2-98 % give the same clean and mild results to within about 0.01 px. On
`hard` the full range fails less (12/20 against 15/20) but with a mean error of
0.62 px on the pairs it keeps, against 0.38 px. The RANSAC threshold was probed
at 0.5, 1 and 3 px: 0.5 px lowers the clean error (0.015 against 0.023 px) and
fails as often on `hard` (16/20), 3 px raises it (0.035 px). The threshold is a
trade that ticket 09's full run can settle; 1 px is the common choice. None of these
changes the picture, so the values stay at the textbook ones.

**Rejected.** A FLANN matcher: approximate and not deterministic across runs,
for no speed need on 256 px pairs. Fitting a translation on translation pairs:
it would tell the method the answer's model. SIFT on 16-bit or float input:
OpenCV's SIFT refuses anything but 8 bits. A fixed stretch in reflectance units:
it would not apply to the synthetic texture, and a radiometric preset would push
the moving image out of range.

---

## 2026-09-23: Methods can decline a pair and report diagnostics; their parameters live in a file

**Decision.** A method may return a bare displacement or an `Estimate` carrying
diagnostics (for SIFT: keypoints, matches, inliers). It may also raise
`RegistrationFailure`, with a reason and the diagnostics it had. The benchmark
records that as a failed pair, with the reason in the `error` column, as it
already did for crashes. Diagnostics go to a `diagnostics` column of `pairs.csv`,
as a JSON object. Method parameters are read from `configs/methods.toml`
(`--methods-config`), one `[methods.<name>]` table per configurable method; a
method with no table keeps its defaults.

**Why.** A method that knows it has too little evidence should say so rather than
return a guess, because in real use there is no ground truth to catch the guess.
On `hard` Beauce, 30 of SIFT's 31 failed pairs were declined this way (fewer than
10 inliers). Only one produced an estimate off by more than 1 px. In a probe
over 120 hard Beauce pairs, 66 of the 99 fits with at least 5 inliers were more
than 1 px off, against 8 of the 35 with at least 10. The table cannot tell the two kinds of
failure apart, but `pairs.csv` can, through the `error` column. Declining is
logged at debug level, since on `hard` it is the common case, while a crash
still logs a warning. Diagnostics stay a free-form JSON cell because each method
has its own (AROSICS reports a reliability, RAFT nothing), and one column per
diagnostic would fill the table with blanks.

---

## 2026-09-23: AROSICS is a compared method, not a reference

**Decision.** AROSICS runs in the benchmark as the third classic method, scored
against the simulated ground truth like the other two. Its estimates are never
used as the truth for anything, and nothing is tuned to agree with it.

**Why.** AROSICS is the tool a Sentinel-2 practitioner would reach for, which
makes it the baseline an AI method has to beat, not the yardstick it is measured
with. It is also a phase correlation with its own sub-pixel step, so treating it
as a reference would hide exactly the errors this project measures. On clean
Beauce translations it scores 0.059 px, against 0.023 px for scikit-image's phase
correlation (see the next entries).

**Rejected.** Validating the simulator against AROSICS: the simulator's truth is
exact by construction, and AROSICS' is not.

---

## 2026-09-23: AROSICS and GDAL are an optional extra: brew GDAL, pinned pip bindings

**Decision.** AROSICS is the `arosics` extra of `pyproject.toml`. GDAL, which it
needs, comes from Homebrew (`brew install gdal`), and its Python bindings are
installed by pip pinned to that version (`make install-arosics` runs
`pip install "gdal==$(gdal-config --version)"` before the extra). The package
imports AROSICS only when the method runs. `satreg benchmark` leaves it out of the
default methods when it is not installed, and says what is missing when it is
asked for. Its tests skip, saying why.

**Why.** There is no pip wheel of GDAL's bindings: pip builds them against a system
GDAL, and only the same version builds. conda would ship both, but conda is broken
on this machine and the project is pip and venv (see the tooling entry). Keeping it
optional keeps `make install` and the test suite light and portable: AROSICS pulls
in geopandas, cartopy, plotly and folium, and importing it takes 1.7 s. The suite
was run with AROSICS and GDAL blocked: 173 tests pass and the 8 that need AROSICS
skip. rasterio ships its own GDAL (3.12) next to Homebrew's (3.13), and both load in
the same process without trouble.

**Rejected.** AROSICS as a core dependency (every install would need a system
GDAL). conda for GDAL alone (a second environment manager for one method). Docker
(heavy for one optional method on a laptop).

---

## 2026-09-23: Simulated pairs keep the grid of the chip they were cut from

**Decision.** A simulated pair carries a `Georef` (CRS and pixel-to-map transform):
the site's grid, with its origin moved to the window the pair covers. Both images
share it. The synthetic site gets a nominal grid, 10 m pixels in UTM 31N. Methods
that work in map coordinates subclass `GeoreferencedMethod` and are called with the
grid. The others never see it.

**Why.** AROSICS matches in map coordinates, so it needs the grid, and the chip's
real one is on hand. Two orthorectified acquisitions share their grid, and the
displacement is content moving on it, so giving both images the same grid is the
situation AROSICS is built for. The grid is the one it would get in real use: a
pixel window of the tile, with no resampling. Passing it as an array in memory
avoids temporary files.

**Rejected.** Giving the moving image a grid offset by the true shift: that would
tell AROSICS the answer. Writing each pair to a GeoTIFF: slower, and AROSICS takes
in-memory arrays.

---

## 2026-09-23: AROSICS' shift is read in map units and turned back into pixels

**Decision.** AROSICS reports the correction to apply to the moving image's
origin, in map units. The displacement is minus that correction, brought back to
pixels by the inverse of the grid's linear part. A test pins the sign on a whole
shift of (3, -2) px on the real-chip fixture, and the conversion is tested on a
rotated, south-up grid with unequal pixel sizes.

**Why.** The sign convention is the classic trap of wrapping a registration tool,
and a whole shift makes it unambiguous: AROSICS finds whole shifts exactly. Going
through map units, rather than AROSICS' own pixel shift, stays right on any grid
orientation.

---

## 2026-09-23: AROSICS parameters, and a reliability floor of 60 %

**Decision.** `COREG` runs with a 256 px matching window, a 5 px maximum shift and 5
attempts at a valid peak, all set in `configs/methods.toml`. A result is kept when
AROSICS rates its reliability at 60 % or more, the default AROSICS itself uses in
its local co-registration. A pair with no valid match, a shift beyond the maximum,
or a lower reliability is declined, with AROSICS' reason in the `error` column. The
reliability and the side of the window AROSICS actually correlated go to
`pairs.csv`.

**Why.** AROSICS already sorts its own results, and a method that declines is what
the benchmark rewards over one that guesses. A probe over 60 `hard` Beauce pairs,
with no floor:

| reliability | pairs | median EPE | pairs off by > 1 px |
|---|---:|---:|---:|
| no match | 18 | | |
| 0-20 % | 8 | 0.92 px | 4 |
| 20-40 % | 4 | 0.85 px | 2 |
| 40-60 % | 19 | 0.40 px | 0 |
| 60 % and above | 11 | 0.28 px | 0 |

Every pair off by more than 1 px is below 40 %. A floor of 40 % would keep 30 pairs
instead of 11, at a median error of 0.40 px on the added ones. That trade is left
to ticket 09's full run. On `mild`, all 60 pairs rate 80 % or more.

**Rejected.** No floor (AROSICS' own global default), which keeps the guesses below
20 %.

---

## 2026-09-23: What AROSICS does on the benchmark

**Finding.** 20 pairs per row, default presets:

| site | scenario | preset | AROSICS | phase correlation | SIFT + RANSAC |
|---|---|---|---:|---:|---:|
| Beauce | translation | clean | 0.059 px | 0.023 px | 0.023 px |
| Beauce | translation | mild | 0.100 px | 0.039 px | 0.048 px |
| Beauce | translation | hard | 0.205 px, 90 % failed | 0.441 px | 0.382 px, 75 % failed |
| Beauce | affine | clean | 0.227 px | 0.218 px | 0.023 px |
| synthetic | translation | clean | 0.021 px | 0.011 px | 0.005 px |
| synthetic | translation | hard | 0.188 px, 20 % failed | 0.146 px | 0.115 px |

**Why.** AROSICS' clean error is its sub-pixel step: it takes the ratio of the
correlation peak to its larger neighbour, which is exact on whole shifts and off by
up to 0.1 px near half pixels (at most 0.096 px over 16 shifts on the fixture).
scikit-image upsamples the correlation around the peak instead, which is why it is
more accurate here. On affine pairs AROSICS sits at the same floor as phase
correlation, since both fit a translation. On `hard` Beauce it declines 18 of the 20
pairs (no match, or reliability below 60 %), and keeps the 2 it trusts, at 0.21 px.
It is the most cautious of the three.

---

## 2026-09-23: A 320 px piece of the Beauce chip is committed as a test fixture

**Decision.** `tests/data/beauce_b04_320.tif` (140 KB) is rows and columns 352 to 671
of the Beauce chip, uint16, on its real UTM 31N grid, with the source scene id in
its tags. It contains modified Copernicus Sentinel data 2025.

**Why.** The ticket asks for a known sub-pixel shift recovered on a real chip, and
the test suite refuses the network. 320 px holds a pair the size of AROSICS'
default 256 px window, with a 32 px margin, and no more.
Copernicus Sentinel data is free to redistribute with that attribution.

---

## 2026-09-23: Compute cost is the median of timed calls and a tracemalloc peak, per pair

**Decision.** Every method call in the benchmark is measured on its own, after the
pair has been simulated and degraded and before it is scored. Each method is
first called `--warmup` times (default 1) on the first pair it gets, untimed. On
every pair it is then called `--repeats` times (default 3), timed with
`time.perf_counter`, and the median goes to `time_ms`. One more call runs under
`tracemalloc`, and the peak it traces above what was already allocated goes to
`peak_mib`. The estimate scored is the first timed call's. A call that declines
or crashes is timed like any other, and the table takes the median over all the
pairs of a row, failed ones included, since declining a pair costs time too.
Each run writes `context.json` next to its tables, with the CPU, memory, thread
settings, Python and library versions, the timing settings and the process's
peak resident memory. `summary.md` ends with a one-line version of it.

**Why.** The warm-up pays one-off costs that are not the method's cost per pair.
On a 256 px Beauce pair, AROSICS' first call in a process takes 2.0 s, its lazy
imports included, and every later one 16 ms. SIFT goes from 33 to 14 ms, phase
correlation from 5.5 to 3.6 ms. The median of three calls ignores the one call
the OS interrupts. Two runs of 10 pairs gave the same times to within 2 %. Memory
is measured in a separate call because tracing slows Python code down, and would
inflate the time of a method that loops in Python. `tracemalloc` is also the only
per-call measure that the standard library offers: the resident-memory high-water
mark covers the whole process and never goes back down, so after the first call it
says nothing about the next one. The context file exists so that runs on the 8 GB
M1 and on Kaggle can be told apart and not averaged together.

**Limits.** `tracemalloc` counts what goes through Python's allocators, NumPy's
array buffers included. It misses memory that native code allocates for itself:
OpenCV's image pyramids, GDAL's datasets and caches, FFT and BLAS scratch. To see how
much, each method was called once on a Beauce pair in a fresh process, after its
libraries were loaded, and the rise of the process's resident high-water mark was
compared with the traced peak of the same call:

| method | pair | resident high-water rise | traced peak |
|---|---:|---:|---:|
| phase correlation | 512 px | 23.6 MiB | 22.9 MiB |
| SIFT + RANSAC | 256 px | 15.4 MiB | 1.7 MiB |
| SIFT + RANSAC | 512 px | 61.2 MiB | 6.6 MiB |
| AROSICS | 256 px | 10.3 MiB | 10.0 MiB |

Phase correlation and AROSICS do their work in NumPy arrays, and the two agree.
SIFT's pyramids live in OpenCV, and the traced peak sees about a tenth of them. The
high-water rise is itself a lower bound: at 256 px, phase correlation's call does
not rise above what loading the pair had already reached, and reads 0. So
`peak_mib` compares methods that keep their data in NumPy fairly, and understates
SIFT's memory about ninefold. The same will hold for a PyTorch model whose tensors
live outside Python's allocator, which is why RAFT at N2 will need its own
measure (`torch.cuda.max_memory_allocated` on GPU). The process peak in
`context.json` includes native memory but covers the whole run. Repeating calls on
the same pair also leaves its data in the CPU caches, which flatters the times
somewhat; by how much was not measured.

**Rejected.** Sampling resident memory from a thread (`psutil`): it catches native
allocations, but with calls of 3 to 17 ms it would have to sample well under a
millisecond not to miss their peaks, and it adds a dependency. Measuring time and memory in
the same call: tracing would slow down the time it measures.

---

## 2026-09-23: One run config for the N1 table, its options recorded with the results

**Decision.** `configs/n1.toml` describes the whole N1 run in a `[benchmark]`
table: sites, scenarios, presets, methods, pairs per site, image size,
displacement ranges, seed, failure threshold, timing settings, the other config
files and the output folder. `satreg benchmark --config configs/n1.toml` runs it.
Its keys are the options of `satreg benchmark` with underscores, an option given
on the command line overrides its key, and an unknown key stops the run. Each run
writes every option it used, wherever it came from, to `context.json` under
`run`.

**Why.** The ticket asks for one command that reproduces the table. A config file
that mirrors the command-line options adds no second vocabulary: whatever the
file says can be tried on the command line first, and `--pairs 5` still gives a
quick run of the same design. Rejecting unknown keys catches a misspelt option,
which would otherwise fall back to its default without a word. Recording the
resolved options makes a results folder self-describing, even when it was produced
by a mix of file and flags.

**Rejected.** A separate schema for run files (a `[run]` table with nested
`[run.ranges]`): tidier to read, but a second set of names to keep in step with
the CLI.

---

## 2026-09-23: Method variants are declared in the methods config

**Decision.** A `[methods.<name>]` table with a `method` key declares a variant: a
new method `<name>`, built like the configurable method it names, with the
table's other keys as parameters. It cannot take a built-in method's name. It runs
only when named in `--methods` or a run config, and inherits its method's optional
dependencies. Phase correlation became configurable for this, with one parameter,
an apodisation window (`window = "hann"`): each image is centred on its own mean,
then multiplied by the window.

**Why.** Two choices were left to the N1 run: whether phase correlation should be
windowed (see `failures.md`), and whether AROSICS' reliability floor should drop
from 60 to 40 %. Both need the two settings side by side on the same pairs, in
the same table, from the same command. A variant is the smallest thing that does
that, and later levels will need it again (a network at two iteration counts, for
instance). Centring before windowing matters on Sentinel-2 digital numbers, whose
mean is far above their spread: the window would otherwise add the same large bump
to both images, a component that does not move and peaks at zero shift.

---

## 2026-09-23: The N1 run: two sites, 100 pairs per site, every scenario and preset

**Decision.** The N1 table crosses Beauce and Toulouse, translation and affine,
`clean`, `mild` and `hard`, on 100 pairs per site at 256 px, seed 0, with the
default displacement ranges. Each pair is run under every scenario and preset, so
every cell of the table has the same 100 windows and displacements. That is 1,200
simulated pairs and 6,000 method calls, in under six minutes on the M1.

**Why.** Toulouse was optional in N1, and its chip was cached, so it is in: an urban
texture and an open-field one behave very differently, and one site alone would
have made the `hard` numbers look like a property of the methods rather than of
the scene. 100 pairs puts the standard error of a failure rate at 5 points at
most, enough to tell 4 % from 13 % or 22 % from 41 %, which are the differences
the table turns on. Doubling it would halve nothing that changes a conclusion,
and would double the time of every rerun.

---

## 2026-09-23: Phase correlation stays unwindowed; the Hann variant is reported next to it

**Decision.** `phase_correlation` stays as scikit-image ships it, with no window.
The Hann variant, `phase_correlation_hann`, is in the N1 table as its own row.

**Why.** On the 1,200 pairs of the N1 run, neither dominates. The Hann window
removes the border bias: on clean Beauce translations it brings the mean error
from 0.026 to 0.004 px and is better on 93 of 100 pairs, and it stays ahead on
`mild`. On `hard` it loses everywhere. On Beauce it fails 13 % of translation
pairs against 4 %, some of them by 10 to 53 px, and on Toulouse its mean error goes
from 0.100 to 0.183 px. The window concentrates the correlation on the centre of
the pair, and when a cloud bank sits there, the cloud is most of what it sees (see
`failures.md`). A baseline that is excellent on clean pairs and falls off a cliff
under clouds is not a better baseline, it is a different trade-off, and the table
is where that trade-off belongs. The unwindowed version stays the reference row
because it is what the spec names and what a practitioner calls first.

---

## 2026-09-23: AROSICS' reliability floor drops to 40 %

**Decision.** AROSICS keeps a shift it rates at 40 % reliability or more, instead
of 60 %. The 60 % setting stays in the N1 table as `arosics_floor60`. This
supersedes the floor in "AROSICS parameters, and a reliability floor of 60 %".

**Why.** The earlier probe, 60 `hard` Beauce pairs, suggested that reliability
tracked accuracy above 40 % (median error 0.40 px between 40 and 60 %, 0.28 px
above). The N1 run, with 200 `hard` pairs per site, does not bear that out:

| site | kept at 60 % | kept at 40 % | mean EPE, 60 % and above | mean EPE, 40 to 60 % | kept pairs off by > 1 px |
|---|---:|---:|---:|---:|---:|
| Beauce | 46 | 103 | 0.449 px | 0.448 px | 0 |
| Toulouse | 119 | 157 | 0.345 px | 0.356 px | 0 |

Between 40 and 60 %, the added shifts are as accurate as the ones AROSICS trusted
already, and none is a gross error. The 60 % floor was declining good estimates:
on `hard` Beauce, AROSICS failed 78 % of pairs with it and 50 % without. The
floor stays at 40 % rather than lower because the probe's gross errors, all six of
them, were rated below 40 %. On `clean` and `mild`, every shift rates 80 % or more,
so the floor changes nothing there.

**Rejected.** Keeping 60 % because AROSICS uses it in its local co-registration:
that default is tuned for a grid of many windows, where a declined window costs
little, not for a single global shift.

---

## 2026-09-23: CI runs the same two make targets as a laptop, without AROSICS

**Decision.** A GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every
push, on any branch, and on every pull request, with read-only permissions. It has
two jobs: `lint` runs `make lint` on Python 3.11, and `test` runs `make test` on
3.11 and 3.13. Both install with `pip install -e ".[dev]"`, without the `arosics`
extra. A newer run on the same branch cancels the older one, except on `main`.

**Why.** The Makefile targets are the one definition of lint and tests: CI calling
them means a green laptop and a green CI check the same thing, and a change to a
target cannot leave CI behind. 3.11 is the floor `requires-python` declares, and
nothing else checks that claim, since the development machine runs 3.13. AROSICS
is left out because it needs a system GDAL matching pip's bindings (see the
AROSICS extra entry); the suite already skips its 8 tests without it, saying why,
and the network is refused by the suite itself, so CI needs no secret and no
catalogue. Run that way in a fresh 3.13 venv: lint clean, 211 tests pass, 8 skip.
Lint is a separate job so a formatting slip and a failing test show up as two
different red checks. `main` runs are never cancelled because the README badge
reports `main`, and a cancelled run is neither pass nor fail.

**Rejected.** An AROSICS job with `libgdal-dev` from apt: Ubuntu's GDAL version
would have to match the pinned bindings, and it would test an optional method on
every push at the cost of the slowest install in the project. Running on `main`
only: most pushes on a repository worked on alone land on branches.

---

## 2026-09-23: PyTorch is an optional extra; weights live in PyTorch's cache; the device is named

**Decision.** PyTorch and torchvision are the `dl` extra of `pyproject.toml`
(`make install-dl` installs it and downloads the pretrained weights). The package
imports them only inside the methods that need them, which are declared optional in
the method registry like AROSICS: `satreg benchmark` leaves them out of its default
methods when torch is missing, and says what to install when one is asked for.
Weights are downloaded by torchvision, once, to PyTorch's own cache
(`~/.cache/torch/hub/checkpoints`, or under `TORCH_HOME`), never into the
repository. Each method runs on the device its configuration names (`cpu`, `mps`
or `cuda`, default `cpu`), and a device that is not available is an error, never a
silent fall back. Networks are built once per process and per device.

**Why.** torch and torchvision take about 600 MB installed and 1.1 s to import: the
core suite and CI have no use for them, and the same split already works for
AROSICS. The CI installs `.[dev]` only, so the deep-learning tests skip there,
saying why; the suite was run with torch and torchvision blocked: 245 pass and 5
skip. The weights (21 MB for RAFT large, 4 MB for small) are artefacts that
torchvision already versions and verifies by hash, so a second copy in the
repository or in `data/` would only drift. The conftest refuses the network, so
tests never download them: the tests that run a network skip, naming the missing
file and `make install-dl`. An explicit device is what makes a number reproducible:
the same config gives the same run on the M1 and on Kaggle, and `context.json`
records which device each method ran on. Picking the fastest device automatically
would change results between machines without anything saying so; on MPS, RAFT's
estimates happen to be identical to the CPU's to four decimals, but that is a
finding, not a guarantee.

**Rejected.** torch as a core dependency (every install and every CI run would pay
for it). Weights committed or stored in `data/` (duplicates torchvision's cache and
its hash check). Automatic device choice (results would depend on the machine
silently). ONNX Runtime instead of torch (ticket 02 looks at it as a spike, for
inference only).

## 2026-09-23: Dense displacements exist on one grid only

**Decision.** A `Dense` displacement holds a `(2, rows, cols)` field, `dy` then
`dx`, copied to a read-only float array. `field(shape)` returns a copy of it and
refuses any other shape. Its text form, which goes into the per-pair table, is its
shape and mean components, not its values.

**Why.** Unlike a translation or an affine model, a flow has no formula to evaluate
on another grid, and resampling it silently would score something the method did
not estimate. The metrics only ever see fields, so a dense estimate is scored by
the same code as the others; a test pins that a translation or an affine model,
sampled into a `Dense`, scores exactly like itself. The copy protects the estimate
from the caller and the caller from it. A 256 px field written in full would be
131 072 numbers in one CSV cell.

## 2026-09-23: RAFT as torchvision ships it, 12 refinements, one stretch per image

**Decision.** RAFT is the method `raft` (torchvision's `raft_large`, weights
`C_T_SKHT_V2`) with a `raft_small` variant (`raft_small`, weights `C_T_V2`), 12
refinement iterations and the CPU by default, all set in `configs/methods.toml`.
Weights are pinned by name, not by torchvision's `DEFAULT`. It is used as
shipped, without fine-tuning. Each image of the pair goes through the same
conversion, which depends on that image alone:

1. **Stretch.** Values are stretched linearly so that the image's own 1st and
   99th percentiles land on -1 and 1, then clipped, in float32. A flat image
   gives zeros.
2. **Three channels.** The band is repeated into the three input channels.
3. **Padding.** Rows and columns are added after the last ones, by edge
   replication, up to the next multiple of 8 and to at least 128 px.
4. **Crop.** The flow of the last refinement is cropped back to the image's
   rows and columns and put in `(dy, dx)` order.

torchvision's flow maps image1 to image2 (`image2(p + flow) = image1(p)`,
components `(dx, dy)`). With the reference as image1, it is the displacement of
the project's convention. A test pins this against a shift of 3 px right and 2 px
up on the synthetic texture, for both models.

**Why.** *Weights.* `C_T_SKHT_V2` is torchvision's default for the large model:
trained on FlyingChairs and FlyingThings, then fine-tuned on Sintel, KITTI and
HD1K. `C_T_V2` is the only set torchvision ships for the small model. Pinning them
by name keeps a torchvision upgrade from changing the numbers.
*Iterations.* 12 is torchvision's default. On clean Beauce translations, 24
iterations gained 0.003 px of mean error (0.034 to 0.031 px on a probe of a few
pairs), and 32 another 0.001, at twice and three times the time.
*Stretch.* The weights expect RGB frames scaled to [-1, 1]; Sentinel-2 bands are
uint16 reflectance numbers with most of the range unused. A stretch computed on
each image is blind to any gain or offset between the two images, works on the
synthetic texture, which has no reflectance scale, and does not depend on which
degradation made the pair. It is the rule SIFT's 8-bit conversion already uses.
The choice barely matters for accuracy. On 20 Beauce translation pairs (RAFT
large, MPS), the mean errors were:

| stretch | clean | mild | hard |
|---|---:|---:|---:|
| percentiles 1 to 99, per image (kept) | 0.043 | 0.078 | 0.228 |
| percentiles 2 to 98, per image | 0.043 | 0.095 | 0.222 |
| minimum to maximum, per image | 0.044 | 0.131 | 0.230 |
| fixed, digital numbers 1000 to 4000 | 0.043 | 0.119 | 0.194 |

Clean pairs do not tell them apart. On mild pairs the clipped percentile stretches
do best, and min-max suffers from the outliers that the noise adds. On hard pairs
the fixed stretch does best, but on only 20 pairs, and it assumes a reflectance
scale that holds neither for the synthetic texture nor for another sensor.
*Three channels.* The network was trained on colour. Copying one band into all
three keeps the input in the range it saw, and costs nothing next to the network.
*Padding.* RAFT computes features at 1/8 resolution and builds a four-level
correlation pyramid on them, so each side must be a multiple of 8 and at least 128
px: torchvision raises an error on smaller images. Padding only after the last
row and column leaves every pixel where it was, so cropping needs no shift. The
128 px floor lets RAFT run on the test suite's 64 px pairs, but it costs accuracy:
0.14 to 0.30 px of mean error on 64 px synthetic pairs, against 0.02 to 0.07 px at
256 px. The benchmark runs at 256 px.

**Rejected.** A fixed reflectance stretch (see the table). Tiling images larger
than the network was trained on: not needed at 256 px, and ticket 03 will say if it
is at larger sizes. torchvision's `DEFAULT` weights (can change between releases).
Fine-tuning at this stage (the walking skeleton measures the pretrained network).

## 2026-09-23: A PyTorch method's memory is the peak its tensors hold, read by the profiler

**Decision.** The time and memory of a method call are read by the method's
*meter*. Methods without one keep `tracemalloc`. RAFT's meter depends on its
device:

- **Time.** On every device, the meter synchronises the device before each clock
  read: `torch.cuda.synchronize` on CUDA, `torch.mps.synchronize` on MPS.
- **CPU memory.** It is the peak of bytes held by CPU tensors during the call,
  above what they held before it. PyTorch's profiler records every tensor
  allocation and release with its size (`profile_memory=True`), and summing those
  raw events in time order gives the bytes held at each moment.
- **CUDA memory.** It is `torch.cuda.max_memory_allocated`, reset before the call,
  minus what was allocated before it.
- **MPS memory.** There is no figure: the table says `n/a`.

`context.json` records what each method's memory figure is and the device each
method ran on, along with torch's version and thread count. The table's footnote
says which methods were measured which way. This supersedes the plan, in the
ticket, of reading the resident high-water mark on CPU.

**Why.** *Time.* CUDA and MPS kernels run asynchronously, so a call can return
before its work is done. Synchronising around the call puts that work inside the
timed interval. On CPU there is nothing to wait for.
*CPU memory.* `tracemalloc` does not see tensors, and three ways of reading the
process's memory failed to give a per-call figure on the M1:

- Sampling the resident set every millisecond from a thread read 0 on most warm
  calls of RAFT large, and anything from 0 to 725 MiB on others. The allocator
  keeps freed pages, so a warm call reuses them and the resident set does not
  move.
- macOS's own peak counter (`ri_interval_max_phys_footprint`, reset before the
  call) behaves the same: a second 200 MiB NumPy array read 0 for the same
  reason.
- The profiler's event list (`key_averages`) counted more releases than
  allocations, because it loses the ones made on worker threads.

The raw events are exact on a known case: allocating 100, then 50, releasing the
100, then allocating 30 MiB reads 150.0 MiB, and a test pins that. On RAFT they
are stable from call to call: 105.5 MiB for the large model at 256 px and 422 MiB
at 512 px; 25.0 and 132 MiB for the small model. Profiling adds no time that
could be measured, and in any case memory has its own call. What the figure
leaves out: the model's weights, the allocator's cache and the NumPy input
conversion. Those are either paid once per process or small next to the
activations. The process's peak resident memory stays in `context.json` (721 MiB
for a 20-pair RAFT run of both models).
*MPS memory.* Metal allocations reach neither the profiler nor a peak counter,
and the process's resident memory has the problem described above. A wrong
number would be worse than none. Kaggle's GPU runs (ticket 06) will read the CUDA
peak.

**Limits.** Kineto writes two lines to stderr each time the profiler starts or
stops, from native code that no environment variable silences, so stderr is sent
to the null device during those two steps only. The method's own call keeps its
stderr. torch also warns once per process that a block was allocated before
profiling started. That block's release is then not counted, so the peak cannot
be understated by it.

**Rejected.** The resident high-water mark and the other process-wide readings
above (no per-call figure on warm calls). `psutil`, which was only needed for
sampling. The profiler's aggregated event list (drops worker-thread events).
Profiling the timed calls (would mix the two measurements).

## 2026-09-23: What RAFT does on the benchmark, first measurement on the M1

**Decision.** None yet: this records the first measurement, to compare against
from ticket 03 onwards. It was run with `satreg benchmark --site beauce --scenarios
translation affine --degradations clean --pairs 20`, at 256 px, with RAFT on CPU
and on MPS. The machine was the M1 with 8 GB, and torch 2.14 with 4 threads.

| method | scenario | mean error (px) | < 0.1 px | time (ms) | memory (MiB) |
|---|---|---:|---:|---:|---:|
| phase correlation | translation | 0.023 | 100 % | 5.2 | 6.5 |
| SIFT + RANSAC | translation | 0.023 | 100 % | 14.6 | 1.7 |
| RAFT large, CPU | translation | 0.043 | 95.9 % | 371 | 105.5 |
| RAFT large, MPS | translation | 0.043 | 95.9 % | 138 | n/a |
| RAFT small, CPU | translation | 0.119 | 46.1 % | 105 | 25.0 |
| RAFT small, MPS | translation | 0.119 | 46.1 % | 56 | n/a |
| RAFT large, CPU | affine | 0.052 | 92.2 % | 371 | 105.5 |
| RAFT small, CPU | affine | 0.120 | 45.2 % | 104 | 25.0 |

The cost columns do not measure the same thing for every method: see the entries
on compute cost.

**Why it is worth noting.** Out of the box, RAFT large is half as accurate as the
classic methods on clean pairs and 25 to 70 times slower, but it reads the
per-pixel field. On affine pairs it degrades less than phase correlation
(0.052 px, against the 0.218 px phase correlation's global model reaches there).
MPS gives the same estimates about three times faster than the CPU for the large
model. The small model's errors are about three times larger than the large one's.
It has five times fewer parameters, and its weights skipped the fine-tuning on
Sintel, KITTI and HD1K, so which of the two costs more is not known.

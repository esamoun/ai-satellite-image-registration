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

## 2026-09-24: RAFT exports to ONNX as it is; it stays the model N3 fine-tunes

**Decision.** RAFT stays the N3 model: both torchvision models export to ONNX and
run under ONNX Runtime on the CPU with the same flow as PyTorch. Which of the two
sizes N3 fine-tunes is left to N3. The export that works with the least fuss is
the TorchScript-based one (`torch.onnx.export(..., dynamo=False)`) at opset 17,
with the image size dynamic. The number of refinements is fixed when the model is
exported. The spike's script is `scripts/raft_onnx_spike.py` (it needs `onnx`,
`onnxruntime` and `onnxscript` on top of the `dl` extra, installed by hand: they
are not an extra until N3 uses them).

**What was measured.** One simulated Beauce translation pair (1.37, -2.61 px),
12 refinements, M1 8 GB, torch 2.14, ONNX Runtime 1.30, 4 threads on both sides,
median of 5 calls after one untimed call. Times vary by about 15 % from run to
run, so ranges are given.

| model | export | size (MiB) | largest flow difference vs torch (px) | torch (ms) | ONNX Runtime (ms) |
|---|---|---:|---:|---:|---:|
| large | TorchScript, 256 px fixed | 20.4 | 3.4e-4 | 380-470 | 630-700 |
| large | TorchScript, dynamic size | 20.5 | 1.5e-4 (1.2e-4 at 512 px) | 410 | 670 |
| large | dynamo, dynamic size, opset 18 | 22.2 | 3.6e-4 (2.6e-4 at 512 px) | 360 | 720 |
| small | TorchScript, dynamic size | 4.1 | 3e-5 (7e-5 at 512 px) | 100 | 240 |
| large | int8, dynamic quantization | 6.0 | 0.14 (mean 0.03) | | 470-530 |
| small | int8, dynamic quantization | 1.8 | 0.97 (mean 0.24) | | 230 |

**What breaks, and what does not.**
- RAFT's correlation lookup samples the correlation volume with `grid_sample`
  (48 `GridSample` nodes for 12 refinements and 4 pyramid levels). ONNX has it from
  opset 16 on; at opset 15 the export stops with `UnsupportedOperatorError` on
  `aten::grid_sampler`. No other operator is missing.
- The refinement loop is a Python loop, so both exporters unroll it: the graph
  holds exactly the 12 refinements it was exported with (2 562 nodes with
  TorchScript, 1 333 with dynamo), with no ONNX `Loop`. Another iteration count
  means another export, which is cheap (2 s).
- The dynamo exporter has no opset 17 for `Pad`: asked for 17, it builds at 18,
  fails to convert down and keeps 18, with a long traceback on the way. It
  otherwise works, dynamic size included, but takes 7 to 17 s against 2.
- The TorchScript exporter warns that `instance_norm` is exported with
  `train=True`. That is what RAFT's feature encoder does in PyTorch too: its
  instance norms keep no running statistics and always use the image's own. The
  flow agreeing to 3e-4 px confirms it.
- The legacy exporter prints a deprecation warning: PyTorch made dynamo the
  default in 2.9. It still works in 2.14, and the dynamo route is the fallback if
  it goes.

**Why it is worth noting.** The spec asked to check this before any fine-tuning,
because N3 exports and quantizes the fine-tuned model: the answer is yes, with no
change to torchvision's code. Two things N3 should know:
- On the M1 CPU, ONNX Runtime is slower than PyTorch, 1.6 times for the large
  model and 2.4 times for the small one. What ONNX brings is a model that runs
  without PyTorch and can be quantized, not speed on this machine.
- Dynamic int8 quantization runs and shrinks the files 3.4 and 2.3 times, but gains
  only 25 % of time on the large model and almost nothing on the small one, and
  moves the flow by the size of the model's own error (large: mean 0.03 px, against
  0.043 px of error on clean pairs) or more (small: mean 0.24 px, against 0.119).
  This is one pair and no accuracy study, which is N3's; but it says the default
  dynamic quantization, applied as it is, costs accuracy that matters at a tenth of
  a pixel.

**Rejected.** A fallback model (not needed: RAFT exports). The dynamo exporter as
the default (slower to export and cannot target opset 17; kept as the fallback).
Rewriting the correlation lookup without `grid_sample` (opset 16 came with ONNX
1.11 in early 2022, so no runtime N3 targets lacks it).

---

## 2026-09-24: Dense pairs: a smooth random field on top of the affine twin, warped by Fourier oversampling

*My call*: the local peak (up to 0.8 px, drawn uniformly), the correlation length
(64 px), the opaque-cloud threshold (0.9) and the ×4 cubic warp over ×2 quintic.

**Decision.** A third scenario, `dense`. Its truth is the affine motion of its twin
plus a smooth local field `l(p)`: `d(p) = A p + o - p + l(p)`. The local field is
a stationary Gaussian random field with correlation `exp(-h² / 2L²)`, built from
64 random Fourier features. Its frequencies are drawn from N(0, 1/L²) and its
phases uniformly. It is then scaled so that its largest magnitude over the pair
is a peak drawn uniformly in `[0, max_local_shift]`. Two run options set it:

| option | default | what it is |
|---|---:|---|
| `max_local_shift` | 0.8 px (8 m) | largest local displacement of a pair |
| `local_length` | 64 px (640 m) | correlation length |

At the full peak the field's largest gradient is 0.026 px per px (0.014 median
over 200 draws), so it stretches the image by under 3 %.

The field stands for orthorectification residuals: relief seen from two viewing
angles through an elevation model that is wrong by some metres. The parallax is
`Δh · (tan θ₁ - tan θ₂)`. Sentinel-2 views up to about 10° off nadir, so an error
of 20 m seen from opposite edges of two swaths moves the ground by about 7 m,
0.7 px. The error follows the relief, over hundreds of metres. These are judgement
calls in the same spirit as the affine ranges, not measurements: real pairs
(ticket 08) are what checks them. Attitude jitter is not modelled. On Sentinel-2
it is a high-frequency, along-track effect that a Gaussian field of this length
does not describe.

For a given seed, site and pair, the dense pair draws its peak and its field after
everything its twins draw. It therefore has their window, their shift and their
affine part, and the three rows of a method compare pair by pair. The margin
bound gains `max_local_shift` (7.1 + 0.8 = 7.9 px by default), which still gives
24 px. N1's pairs are unchanged: all 400 clean truths of `outputs/n1/pairs.csv`
are drawn again identically.

**The inverse mapping.** The field is defined on the reference grid, so the
moving image needs, for each moving pixel `q`, the source `p` with
`p + d(p) = q`. It is found by fixed-point iteration, `p ← p - (p + d(p) - q)`.
Each step gains a factor of the field's largest gradient, a few hundredths here.
It stops at a residual of 1e-8 px and refuses the map if 50 steps do not get
there. On the benchmark's fields that takes 3 to 5 steps (30 draws), and a test field
reaches 1e-13 px. Random Fourier features were chosen because they can be
evaluated exactly anywhere. A field sampled on a grid would have to be
interpolated at the off-grid points of the iteration, and the truth would carry
that interpolation error.

**The warp.** Fourier oversampling, then a spline. The window is mirrored, then
upsampled ×4 along each axis by zero-padding its spectrum (`scipy.signal.resample`).
The moving image is read from it at the sources with a cubic spline
(`map_coordinates`, order 3). Oversampling puts the scene far below the new
Nyquist frequency, where a cubic spline no longer low-passes. N1's two-pass
Fourier warp only exists for affine maps, so it cannot do this.

Measured on a 128 px pair with a strong field (0.8 px local peak, L = 64, and
N1's strongest affine), against the band-limited interpolant of the same mirrored
window evaluated exactly at the sources. The error is in image standard
deviations:

| warp | MTF texture, max | Beauce, max | Toulouse, max |
|---|---:|---:|---:|
| cubic spline | 0.18 | 0.096 | 0.44 |
| quintic spline | 0.12 | 0.075 | 0.26 |
| ×2, cubic | 4.5e-3 | 4.3e-3 | 1.3e-2 |
| ×2, quintic | 3.3e-4 | 3.0e-4 | 7.9e-4 |
| ×4, linear | 3.9e-2 | 2.5e-2 | 9.9e-2 |
| **×4, cubic** | **2.6e-4** (rms 4.3e-5) | **1.6e-4** (rms 1.3e-5) | **6.2e-4** (rms 7.6e-5) |
| ×4, quintic | 3.4e-5 | 2.5e-6 | 6.7e-5 |
| ×8, cubic | 4.3e-5 | 1.1e-5 | 8.3e-5 |

Against the exact scene (a periodic MTF texture, known everywhere), every
oversampled warp sits at 0.021 max (rms 0.004). That floor is the mirroring at
the window's edges, the same effect as the translation warp's 0.03 in N1, so
×4 cubic is 30 times below what the simulator already accepts. With no local
field, a dense pair differs from its affine twin by 0.021 max on the texture and
0.012 on Beauce, which is the two warps' edge effects. The tests bound three
errors:
- against the exact periodic scene: 0.05 max and 0.01 rms, measured 0.021 and
  0.0034;
- against an analytic rendering of Gaussian spots: 1e-4, measured 1.5e-5;
- against the affine twin: 0.05 max, measured 0.032.

A 256 px dense pair takes about 0.4 s to simulate on the M1: 0.3 s to invert,
0.06 s to warp.

**Clouds.** As the clouds entry planned: for a dense truth, a reference pixel is
also invalid when the cloud opacity at its displaced position, read by linear
interpolation, is at least 0.9. At that opacity a tenth of the ground's contrast
gets through at most. Global truths are still scored everywhere, because their
displacement under the cloud is the one beside it. A dense truth has no such
link, and a pixel whose ground is hidden has no displacement a method could
observe. The threshold sits well above the 0.5 that defines a pixel as "under
cloud" in the cloud fraction, so thin edges and haze stay in the metric, where
methods break. On 20 dense pairs per site the mask removes 2.5 % of the valid
pixels under `mild` (5 % of the image at least half cloud) and 23.7 % under
`hard` (30 %).

**First run.** 20 pairs per site, N1's ranges and presets, clean pairs, mean EPE
in px. Each method's global model is compared with the best that model can do on
the true field over valid pixels. For a translation that is the componentwise
median. For an affine model it is the least-squares fit, which is close to the
EPE optimum but not equal to it.

| | phase correlation | SIFT + RANSAC | AROSICS | RAFT | best translation | best affine |
|---|---:|---:|---:|---:|---:|---:|
| Beauce | 0.302 | 0.139 | 0.307 | **0.092** | 0.294 | 0.126 |
| Toulouse | 0.274 | 0.121 | 0.273 (10 %) | **0.100** | 0.273 | 0.121 |

The global methods run unchanged and land on the floor of their model. RAFT is
the only one below the affine floor. Its margin is small: the mean local
displacement is 0.19 and 0.17 px, since the peak is drawn anywhere up to 0.8 px, and
RAFT's own error on clean translations is 0.04 to 0.05 px. Under `hard`, RAFT
scores 0.260 and 0.188 px and fails no pair, against 0.49 and 0.30 px for phase
correlation. Running the three scenarios with four methods on 2 × 20 pairs and
three presets took 6.5 min on the M1.

**Rejected.**
- A plain cubic or quintic spline: numbers above, the low-pass N1 rejected.
- ×2 quintic: about as accurate as ×4 cubic, a quarter of the memory, three
  times faster (15 ms against 46 ms at 256 px). It was not kept because ×4 cubic
  is simpler to argue for and its cost is small next to the inversion.
- A field sampled on a coarse grid and interpolated: the truth would be only as
  exact as that interpolation.
- Inverting by building the inverse field on the grid (scattered interpolation):
  the error lands in the moving image, where nothing measures it.
- Scoring pixels under any cloud (opacity ≥ 0.5): that would drop the thin edges
  the degradation exists to test.

---

## 2026-09-24: LightGlue from kornia, on ALIKED keypoints, with a DISK variant

*My call*: kornia's implementation rather than the authors' repository, and ALIKED
as the extractor of `lightglue`, with DISK as the `lightglue_disk` variant.

**Decision.** `lightglue` is kornia 0.8.3's LightGlue on ALIKED keypoints (model
`aliked-n16`), and `lightglue_disk` is the same matcher on DISK keypoints (model
`depth`). Each uses the LightGlue weights trained on its extractor. Both are used
as shipped, without fine-tuning. Parameters are set in `configs/methods.toml`: at
most 2048 keypoints per image, LightGlue's match threshold 0.1 (kornia's
default), then the RANSAC settings of `sift_ransac` (1 px, 10 inliers). The
matches go through the same RANSAC affine fit as SIFT's, moved to
`methods/ransac.py`, so the two methods differ only in how they find their
matches. That includes the failure: fewer than 10 matches or inliers declines the
pair. The keypoint, match and inlier counts go to `pairs.csv`.

Each image goes through the same conversion, which depends on that image alone:

1. **Stretch.** RAFT's stretch (1st and 99th percentiles of the image to the
   ends of the range, clipped), moved to [0, 1], the range both extractors were
   trained on.
2. **Three channels.** The band is repeated into three channels.
3. **Padding.** ALIKED pads its input itself, by edge replication, to a multiple
   of 32. DISK's U-Net needs sides that are multiples of 16. kornia pads with
   zeros, so the input is padded here instead, after the last row and column, by
   edge replication, and keypoints that land on the padding are dropped.

Keypoints come out in `(x, y)` order with pixel centres on integers, which is
the convention the RANSAC fit already takes from SIFT.

**Why.** *kornia.* It is on PyPI under Apache-2.0, pinned like torchvision, and
ships LightGlue with its weights and two extractors. The authors' repository
(`cvg/LightGlue`) is not on PyPI and would be installed from git. ALIKED appears
in kornia 0.8.3, so the `dl` extra requires that version.
*ALIKED rather than DISK.* DISK keeps its keypoints on whole pixels (the maxima
of its heatmap, with no sub-pixel refinement), and only the averaging over many
inliers brings its fit under a pixel. ALIKED refines each keypoint below the
pixel. On clean synthetic pairs at 256 to 300 px, ALIKED lands at 0.015 to
0.023 px on translations and 0.041 px on an affine pair, DISK at 0.11 to 0.14 px
and 0.078 px. DISK is kept as a variant because it is the other extractor
LightGlue has weights for, and it declines fewer hard pairs (next entry).
*Licences.* LightGlue's code and weights are Apache-2.0, DISK's too, and
ALIKED's are BSD-3-Clause. SuperPoint, the extractor LightGlue was first trained
on, has Magic Leap's non-commercial licence, and kornia has no SuperPoint
extractor to load it with.
*Keypoints and threshold.* 2048 is LightGlue's usual budget. ALIKED keeps
keypoints scoring above 0.2, the value LightGlue's own ALIKED wrapper uses.
*The shared fit.* A copy of the fit would let the two methods drift apart, and
the comparison would no longer isolate the matching.
*stdout.* kornia prints a line when it loads LightGlue's weights. The benchmark's
summary table goes to stdout, so that line is redirected to stderr.

**Rejected.**
- `cvg/LightGlue` installed from git: not on PyPI, and kornia has the same model.
- SuperPoint: non-commercial licence, and no extractor in kornia.
- DISK as the main extractor: its whole-pixel keypoints, numbers above.
- kornia's zero padding for DISK: the edge of the zeros draws keypoints.
- A threshold on LightGlue's matches other than kornia's default: nothing
  measured yet argues for one.

---

## 2026-09-24: What LightGlue does on the benchmark, first measurement on the M1

**Decision.** None yet: this records the first measurement, to compare against
in later tickets. It was run with `satreg benchmark --site beauce --scenarios
translation affine --degradations clean hard --pairs 100 --methods sift_ransac
lightglue lightglue_disk`, at 256 px, on CPU. The machine was the M1 with 8 GB.
Failures are split into the pairs the method declined (too few matches or
inliers) and the pairs where it answered with a mean error above 1 px. The mean
error is over the pairs that did not fail, as in the benchmark's table.

| method | scenario | clean error (px) | hard error (px) | hard: declined | hard: above 1 px | time (ms) | memory (MiB) |
|---|---|---:|---:|---:|---:|---:|---:|
| SIFT + RANSAC | translation | 0.022 | 0.560 | 69 % | 7 % | 15 | 1.7 |
| LightGlue, ALIKED | translation | 0.043 | 0.566 | 21 % | 23 % | 150 | 99.5 |
| LightGlue, DISK | translation | 0.161 | 0.550 | 4 % | 52 % | 484 | 600 |
| SIFT + RANSAC | affine | 0.021 | 0.520 | 68 % | 8 % | 15 | 1.7 |
| LightGlue, ALIKED | affine | 0.047 | 0.576 | 23 % | 30 % | 148 | 99.5 |
| LightGlue, DISK | affine | 0.165 | 0.619 | 3 % | 42 % | 496 | 600 |

Time is the clean pairs' median. The cost columns do not measure the same thing
for SIFT and for the PyTorch methods: see the entries on compute cost.

**Why it is worth noting.** On clean pairs, learned matching does not beat SIFT:
ALIKED's error is twice SIFT's, DISK's seven times, for ten and thirty times the
time. Under `hard`, LightGlue fails fewer pairs (44 to 53 % with ALIKED, against
76 % for SIFT), but mostly by answering where SIFT declines. Its pairs above 1 px
are off by 1.5 px at the median, with 10 to 28 inliers, so the 10-inlier floor
that makes SIFT a cautious method does not do the same for LightGlue. On the pairs
it does register, its error is no better than SIFT's: on the 21 hard pairs (both
scenarios together) that all three methods register, the errors are within
0.15 px of each other, with no method best on both scenarios. DISK declines almost nothing and
is wrong on half the hard pairs, with 44 inliers at the median. What LightGlue
adds is reach: on hard translations it registers 35 pairs SIFT fails, SIFT only
3 that LightGlue fails. A later ticket can say whether a stricter inlier floor
or match threshold turns the pairs above 1 px into declined ones.

---

## 2026-09-24: RoMa from romatch 0.1.2, installed without the dependencies it declares

**Decision.** RoMa is the outdoor model of `romatch` 0.1.2, the authors' package on
PyPI, used as shipped, without fine-tuning. `make install-roma` installs it with
`pip install --no-deps "romatch==0.1.2"`, on top of the `dl` extra and a `roma`
extra that adds the two packages it imports that the project does not already
have, `einops` and `loguru`. Its weights are two files, fetched once to PyTorch's
cache by the same target and loaded with `weights_only=True`:

| file | size | SHA-256 |
|---|---:|---|
| `roma_outdoor.pth` | 0.4 GB | `c7a45c80d41ad788a63c641d1b686d7cb3f297f40097c6f4e75039889e5cc8ba` |
| `dinov2_vitl14_pretrain.pth` | 1.2 GB | `d5383ea8f4877b2472eb973e0fd72d557c7da5d3611bd527ceeb1d7162cbf428` |

The files are not versioned upstream, so the hashes identify the ones measured.

**Why.** *romatch.* It is the reference implementation, on PyPI, and the version
can be pinned. *Without its dependencies.* romatch declares the packages of its
training and evaluation code: `albumentations`, `h5py`, `matplotlib`, `poselib`,
`timm`, `tqdm`, `wandb`, and `opencv-python`, which would install a second OpenCV
over the project's `opencv-python-headless`. Building the model and matching a
pair imports only `einops`, `loguru` and `cv2`, besides torch and torchvision
(checked by listing the modules loaded). *Licences.* romatch's code and RoMa's
weights are MIT (Johan Edstedt), DINOv2's weights Apache-2.0. *The outdoor
model.* It is trained on MegaDepth, outdoor photographs, the nearest of RoMa's
two models to overhead imagery; the indoor one is trained on ScanNet.

**Rejected.**
- romatch with its declared dependencies: a second OpenCV and a dozen packages
  inference never imports.
- Tiny RoMa, the ticket's fallback if the full model did not fit the M1: the full
  model fits (a later entry), and tiny RoMa loads XFeat through `torch.hub.load`,
  which runs code fetched from GitHub at load time.

---

## 2026-09-24: RoMa's warp is read at the pixel centres of the pair

**Decision.** Both images are resized to RoMa's square working grid (bicubic,
PyTorch's `align_corners=False`) after LightGlue's conversion (1st and 99th
percentiles stretched to [0, 1], three equal channels), then normalised with
ImageNet's statistics as romatch's own loader does. RoMa returns, for every cell
of the working grid, the matching position in the moving image in normalised
coordinates, and a certainty. Both are brought to the pair's grid in two steps:

1. **Grid to grid.** Pair pixel `i` of `n` sits at `(i + 0.5) * m / n - 0.5` on a
   working side of `m`: the two grids cover the image edge to edge and sample
   the centres of their cells. The warp and certainty are interpolated linearly
   there (`to_pair_grid`).
2. **Normalised to pixels.** RoMa's -1 and 1 are the outer edges of the image, so
   pixel centre `i` of `n` is at `(2 i + 1) / n - 1`, and a normalised `x`
   becomes `(x + 1) * n / 2 - 0.5` (`to_pixels`).

The displacement of a pixel is then its matched position minus its own. For the
affine output, the matches are the certain pixels of a regular lattice centred on
the pair, at most 5000 pixels (every 4th row and column at 256 px), given to the
RANSAC affine fit shared with SIFT and LightGlue.

**Why.** *The half pixel.* romatch's `to_pixel_coordinates` computes
`(x + 1) * n / 2`, which puts the centre of the first pixel at 0.5. Used as is,
it would shift every estimate by half a pixel on each axis, more than the error
of every method measured. A test pins the mapping by feeding a known warp through
it, at the working grid's own size and at others, and one shows that leaving the
half pixel out moves the field by 0.5 px. *A lattice, not romatch's `sample`.*
`sample` draws matches at random, weighted by certainty, and balanced by a kernel
density estimate: the same pair would give a different fit on each run, and the
draw would favour the textured areas that already hold most matches. The lattice
is the same on every run and covers the pair evenly; the certainty threshold is
what removes the pixels RoMa does not trust.

**Rejected.**
- romatch's `to_pixel_coordinates`: half a pixel off, as above.
- romatch's `sample`: random, above.

---

## 2026-09-24: RoMa works on a 280 px grid, in one pass and one direction

*My call*: 280 px rather than 560 px (romatch's default) or 224 px.

**Decision.** RoMa's working grid is 280 px on a side (20 DINOv2 patches), set as
`resolution` in `configs/methods.toml`. The second, refining pass at a higher
resolution (`upsample_resolution`) is off. The network matches the reference to
the moving image only (`symmetric=False`), and computes its local correlation
with PyTorch's portable code (`use_custom_corr=False`).

**Why.** *280 px.* The pairs are 256 px, so 280 px is the smallest multiple of
14 above them: no pixel of the pair is lost to the resize. On the same 10 Beauce
pairs, 560 px was slightly better on clean pairs (0.039 to 0.043 px for the dense
output against 0.045 to 0.051 px; 0.025 px against 0.026 px for the affine one),
but worse under `hard`, where the affine fit failed 50 to 70 % of the pairs
against 30 to 40 % at 280 px, and the fraction of certain pixels fell from about
1 % to 0.2 %. At 560 px a pair takes 12 s instead of 2.9 s, its tensors hold
1751 MiB at their peak instead of 438 MiB, and the process's memory footprint
reached 7.5 GB of the M1's 8 GB. *No refining pass.* It would upsample a 256 px
pair further, for the same cost as a larger grid. *One direction.* The symmetric
pass adds the moving-to-reference warp, which nothing reads. *The portable
correlation.* romatch's fused kernel is Linux-only, and the same code on every
platform lets a Linux GPU and the M1 compute the same thing.

**Rejected.**
- 560 px, romatch's default: four times the time and memory, and more failures
  under clouds and blur, for 0.01 px on clean pairs.
- 224 px, below the pair's size: it would throw away pixels. The network tests
  use it, because it is faster (2 s a call on the M1).

---

## 2026-09-24: RoMa declines a pair where less than 0.5 % of the pixels are certain

**Decision.** A pixel is certain when RoMa's certainty is at least 0.5. When
fewer than 0.5 % of the pair's pixels are certain, RoMa declines the pair, which
counts as a failure. The mean certainty and the certain fraction go to
`pairs.csv` for every pair; the affine fit adds its match and inlier counts, and
declines too with fewer than 10 of either, as SIFT does. Both numbers are in
`configs/methods.toml` (`certainty_threshold`, `min_certain_fraction`).

**Why.** RoMa's certainty is a sigmoid, so 0.5 is where it rates a match more
likely right than wrong. The floor was first set at 50 %, from synthetic pairs,
where every clean texture is certain almost everywhere and a flat or unrelated
pair almost nowhere. On Beauce it would have declined every pair: clean pairs
have 9 to 36 % of their pixels certain (28 to 31 % at the median). Under `hard`, the certain fraction is 0 to 4 %,
and the pairs at 0.1 % or less were all wrong by 50 to 140 px as dense fields, or
declined by the affine fit's RANSAC. 0.5 % sits between the two groups, and
still declines the flat, ramp and unrelated test pairs. It has a cost: one
`hard` dense pair, at 0.49 % certain, is now declined, where the affine fit had
registered it at 0.42 px. The floor was chosen on the same 20 pairs it is
measured on, so it is fitted to them; a later ticket with other sites can check
it.

**Rejected.**
- 50 %, the synthetic calibration: it declines every Beauce pair.
- No floor: the dense output would return fields 100 px wrong as answers.

---

## 2026-09-24: The `roma` row is the affine fit; the dense warp is the `roma_dense` variant

*My call*: the affine fit as the headline row, rather than the dense warp.

**Decision.** `roma` fits the RANSAC affine to RoMa's certain matches.
`roma_dense`, declared in `configs/methods.toml`, returns RoMa's warp as a
displacement for every pixel.

**Why.** On the 20 Beauce pairs (last entry of the day), the affine fit is the
more accurate of the two on clean translations and affine pairs, and it fails
half as many `hard` pairs. The dense warp keeps the pixels RoMa is unsure of, the
ones under cloud included, and a `Dense` displacement has no mask to leave them
out, so its field is wrong where the certainty is low. The affine row also puts
RoMa next to SIFT and LightGlue with the same fit, so the comparison isolates the
matching. What the affine row loses is the local field of the `dense` scenario,
which no affine fit follows: `roma_dense` is there for it.

**Rejected.**
- The dense warp as the headline: fails most `hard` pairs, as above.
- The dense warp with uncertain pixels filled from their certain neighbours:
  possible, but a method of its own, left to a later ticket.

---

## 2026-09-24: RoMa runs only when named

*My call*: RoMa is left out of the default `satreg benchmark` run.

**Decision.** Without `--methods`, the benchmark runs every built-in method
whose dependencies are installed, except those in `OPT_IN` in
`methods/__init__.py`, which is RoMa. `--methods roma roma_dense` runs it, as a
run config listing it does.

**Why.** RoMa takes about 3 s a call on the M1's CPU. The default run (20 pairs,
three scenarios, three presets, three timed calls and one traced call a pair)
would take over half an hour more with it, and the full test suite, which runs
the default methods several times, took over ten minutes instead of a minute and
a half.

**Rejected.**
- RoMa in the default run: above.
- RoMa left out only when it is not installed, like AROSICS: the cost is the
  reason, not the install.

---

## 2026-09-24: The PyTorch memory meter frees the profiler's trace

**Decision.** After reading a peak, the torch meter deletes its profiler and
runs Python's garbage collector (`gc.collect`).

**Why.** PyTorch's profiler sits in a reference cycle that keeps its whole trace
alive after the call. Python's cyclic collector reaches it only now and then, and
a RoMa call's trace, with `profile_memory=True`, is about 1 GB. Over a benchmark
run the traces piled up (12 GB after eight pairs) until macOS killed the process,
twice. RAFT and LightGlue go through the same meter; their runs finished, and
this fix applies to them too. A test checks that no profiler is left alive after a reading, with the
collector disabled around it; it fails without the fix.

---

## 2026-09-24: What RoMa does on the benchmark, first measurement on the M1

**Decision.** None: this records the first measurement, to compare against in
later tickets. It was run with `satreg benchmark --site beauce --scenarios
translation affine dense --degradations clean hard --pairs 20 --repeats 1
--methods roma roma_dense`, at 256 px, on the M1's CPU, with the settings of
`configs/methods.toml`. SIFT, RAFT and LightGlue ran on the same 20 pairs. Only
20 pairs, because RoMa takes 2.9 s a call: the numbers below move by a pair
(5 %) at a time. Failures are split as in the LightGlue entry; errors are over
the pairs that did not fail.

| method | scenario | clean error (px) | hard error (px) | hard: declined | hard: above 1 px |
|---|---|---:|---:|---:|---:|
| SIFT + RANSAC | translation | 0.023 | 0.382 | 70 % | 5 % |
| RAFT | translation | 0.043 | 0.228 | 0 % | 0 % |
| LightGlue, ALIKED | translation | 0.039 | 0.541 | 20 % | 30 % |
| RoMa, affine (`roma`) | translation | 0.041 | 0.500 | 35 % | 0 % |
| RoMa, dense (`roma_dense`) | translation | 0.053 | 0.685 | 35 % | 50 % |
| SIFT + RANSAC | affine | 0.023 | 0.322 | 80 % | 0 % |
| RAFT | affine | 0.052 | 0.224 | 0 % | 0 % |
| LightGlue, ALIKED | affine | 0.044 | 0.619 | 20 % | 40 % |
| RoMa, affine (`roma`) | affine | 0.032 | 0.499 | 35 % | 5 % |
| RoMa, dense (`roma_dense`) | affine | 0.049 | 0.728 | 35 % | 50 % |
| SIFT + RANSAC | dense | 0.139 | 0.431 | 70 % | 10 % |
| RAFT | dense | 0.092 | 0.260 | 0 % | 0 % |
| LightGlue, ALIKED | dense | 0.146 | 0.493 | 25 % | 35 % |
| RoMa, affine (`roma`) | dense | 0.137 | 0.463 | 40 % | 5 % |
| RoMa, dense (`roma_dense`) | dense | 0.050 | 0.585 | 40 % | 30 % |

Cost, for both RoMa outputs: 2.9 s a call (median), 438 MiB held by tensors at
the peak, and a process memory footprint (`footprint`, what macOS counts before
it kills a process) of about 4 GB, the 1.7 GB of weights included. RoMa runs on
the M1's CPU, so its rows need no GPU runner. MPS was not measured.

**Why it is worth noting.** On clean pairs, RoMa's affine fit is as accurate as
LightGlue's on translations and the most accurate learned method on affine
pairs, still above SIFT's 0.023 px. `roma_dense` is the most accurate method on
the clean dense scenario (0.050 px, against 0.092 px for RAFT), the only one
where a field for every pixel beats a single transform, and the least accurate of
the two RoMa rows elsewhere. Under `hard`, every RoMa decline comes from the
certainty floor, and the affine fit then answers above 1 px on one pair in
twenty at most: RoMa is cautious where LightGlue is not. It registers 4 to 5
pairs per scenario that LightGlue fails and 8 that SIFT fails, against 1 to 2
and 0 to 1 the other way. But on the hard pairs RoMa registers, RAFT's error is
half RoMa's (0.23 to 0.26 px against 0.46 to 0.50 px), and RAFT registers every
pair, in a seventh of the time. `roma_dense` answers half the hard pairs of the
first two scenarios wrong, by 3 px at the median: the certainty that selects the
affine fit's matches does not mask the field.

---

## 2026-09-25: `--device` moves every deep-learning method of a run

**Decision.** `satreg benchmark --device cuda` (or `mps`, `cpu`) replaces the
device of every method that has one, keeping its other parameters; the other
methods run on the CPU as before. A device the machine lacks stops the run before
the first pair.

**Why.** The GPU run on Kaggle and its M1 counterpart use the same methods: one
config, [`configs/gpu.toml`](../configs/gpu.toml), and one option to switch the
device, rather than a copy of `methods.toml` per machine that could drift. Before
this, a method configured on a missing device failed on every pair and filled the
table with failures; checking first gives one clear error instead.

---

## 2026-09-25: Runs from two machines merge into one table, one run per device

**Decision.** Rows carry a `device` column. `satreg merge` reads the tables and
context of two or more runs, without running anything, and writes one table with
the rows of a method on each device side by side. It refuses two runs that
measured the same device, and runs that differ on an option that makes the pairs
or reads their score or cost (sites, pairs, size, scenarios, presets, seed, motion
ranges, failure threshold, warm-up, repeats). Rows written before the column
existed take their device from the run's context, the CPU if it names none.

**Why.** The M1 and a Kaggle GPU cannot run in one process. Comparing their rows
is only meaningful on the same pairs, scored and timed the same way, so the merge
checks those options instead of trusting file names. Taking each device from one
run lets the footnote name, for every row, the machine and commit it came from.
Methods may differ between the runs, so a method measured on one side only keeps
a single row.

**Limit.** A run made before an option existed has no value for it and differs
from a newer run on it, so it is refused rather than guessed. Re-running it is
the fix.

---

## 2026-09-25: `context.json` records the commit and the GPU

**Decision.** Each run records the commit it was made from and whether tracked
files were modified, and, when PyTorch is loaded and sees a CUDA device, that
device (name, memory, count, compute capability) with the CUDA and cuDNN versions
PyTorch was built with. The footnote names the GPU; the merged footnote also
names the commit of each device's rows. The benchmark's total time is recorded
as `cost.run_seconds`.

**Why.** A run on Kaggle happens on a clone, away from the working copy, so the
commit is the only link back to the code that produced its rows. The GPU model
and CUDA version decide GPU timings the way the CPU model decides CPU timings.
Reading the GPU only when PyTorch is already loaded keeps runs of the classic
methods from importing it.

---

## 2026-09-25: The Kaggle notebook clones with a token from a Kaggle secret

**Decision.** The notebook clones the repository from GitHub with a read-only,
fine-grained token stored as the Kaggle secret `GITHUB_TOKEN`. The token reaches
git through an environment variable read by a credential helper passed with
`-c`, after an empty `credential.helper=` that drops any helper the machine
configured. The clone is a full one, not a partial one.

**Why.** The repository is private. A token in the URL would be written to the
clone's `.git/config` and could appear in the saved output; in the environment it
appears in neither. Git asks its helpers in order, so without the reset a helper
configured on the machine answered first, with other credentials: checked
locally, where the Mac's own helper did. A partial clone fetches missing objects
later, which would need the token again after it is gone. No Kaggle or GitHub
credential is in the repository; a test checks the Kaggle files for token
patterns.

---

## 2026-09-28: Six sites: fields, city, mountain, forest, desert, coast

*My call*: the Briançonnais for the mountain site, rather than Chamonix or the
Maurienne, and the Calanques of Marseille for the coast, rather than the Arcachon
basin or the Brest roadstead.

**Decision.** Four sites join Beauce and Toulouse in `configs/sites.toml`, each
with a comment on what it stands for: `alps` (the Briançonnais, 44.90° N,
6.64° E, July to September only), `vosges` (the Donon massif, 48.51° N, 7.12° E),
`libya4` (the CEOS Libya-4 site, 28.55° N, 23.39° E) and `marseille` (the
Calanques, 43.23° N, 5.44° E). They share Beauce's chip size, band and scene
cloud limit.

**Why.** The spec asks for six landscapes, and the N1 table already showed that one
texture can make a method's weakness look like a property of the method. The
Briançonnais has strong relief, which is what a mountain site is for (relief
displacement, cast shadows), with little glacier; Chamonix's snow and ice would
fill much of the chip, and change between dates. The Donon is a large, nearly
continuous forest: low contrast, repetitive canopy, few straight edges. Libya-4 is
a pseudo-invariant calibration site, so its dunes barely change between dates and
it has no man-made edge at all. For the coast, the Mediterranean has almost no
tide, so the shoreline does not move between two dates, which matters for the real
multi-temporal pairs to come (ticket 08); Arcachon and Brest have strong tides and
wide intertidal flats. The Marseille centre sits north of the shoreline: the SCL
counts 25 % water over the chip, so land stays the larger part.

**Check.** Each new site was fetched once and run on 20 clean translation pairs
with the five installed methods (phase correlation, SIFT, AROSICS, RAFT,
LightGlue). No method failed a pair on any of them, so no site was replaced.
For the two held-out sites only the failure column was read (see the held-out
entry).
Refetching Beauce and Toulouse under the chip-level cloud rule gave the same
scenes and byte-identical chips, so the N1 table stands.

---

## 2026-09-28: A chip is used only if its scene classification shows it clear

*My call*: the first scene, in the existing order, whose chip passes a limit,
rather than the clearest chip among several scenes.

**Decision.** Scenes are still tried least cloudy first by `eo:cloud_cover`, but a
scene is now used only if the L2A scene classification (SCL, 20 m) over the chip
window counts at most `max_chip_cloud` percent (default 1 %) of cloud (classes 8,
9 and 10: medium and high probability cloud, thin cirrus) and cloud shadow
(class 3). The chip's shares of cloud, shadow, snow (11) and water (6) are
written to its GeoTIFF tags (`chip_cloud_pct` and so on). Snow and water are
recorded, not rejected. The SCL pixels read are every 20 m pixel the chip touches,
so a chip starting on an odd 10 m pixel counts a half pixel of margin on each
side.

**Why.** The scene cloud cover is an average over a 110 km tile: a scene at 3 %
can have all of it on the chip, and one at 20 % can leave the chip clear. Simulated
pairs could live with that (a cloud in the chip is texture in both images), but
real pairs (ticket 08) cannot, because the cloud is on one date only. Keeping the
existing order and taking the first chip under the limit means a site whose chip
was already clear keeps its scene: Beauce and Toulouse did. Ranking all candidates
by their chip's cloud share would read more SCL files for little gain, and could
change the N1 chips. Shadow counts with cloud because it hides the ground as much.
Snow does not, since on a mountain site in summer it is ground, but its share is
kept so that a snowy chip can be spotted. `max_chip_cloud` is part of the cache
key like every other parameter that picks the chip.

**Rejected.** The `CLD_20m` cloud probability layer: it misses cloud shadow, and a
threshold on a probability is one more choice where the classification already
makes it.

---

## 2026-09-28: Held-out sites stay out of every N2 table

*My call*: held-out sites appear in no N2 table, rather than in a separate table or
in the main one with a marker.

**Decision.** A site can declare `held_out = true` in `configs/sites.toml`; the
Alps and Libya-4 do, the spec's default. `satreg benchmark` refuses a held-out
site, before fetching or running anything, unless given `--allow-held-out`. A run
that uses one lists it under `held_out_sites` in `context.json`, and its table,
merged or not, ends with a line naming the held-out sites and saying that no
choice may be made on their rows. Being held out is not part of the chip's cache
key, since it does not change the chip. `satreg fetch` fetches held-out sites like
any other.

**Why.** Pretrained methods never saw these sites, but N2 chooses thresholds,
presets and variants, and every choice made while looking at a site leaks into
its score. A separate table would rely on good faith not to look at it; keeping
held-out sites out of N2 altogether makes N3 their first real measurement. The
refusal turns the rule into a check, and the flag keeps a deliberate exception
possible and visible. The only look before N3 is the sanity check of the six-sites
entry: whether any method fails a clean pair for a reason unrelated to
registration, which is a check of the data, not of a method. Of that run, only the
failure column was read (no failure).

---

## 2026-09-28: Real pairs: the chip's date, then a few days, a season and a year later

*My call*: four dates per site (the anchor, then targets 0, 91 and 365 days
away), rather than three, or dates spread evenly over a year; and Sentinel-2A, 2B
and 2C mixed freely, with each date's satellite recorded.

**Decision.** A site's series starts from the scene of its benchmark chip, the
*anchor*. `configs/real.toml` then gives each further role a target offset from
the anchor and a tolerance: `days` (0 ± 15 days), `season` (91 ± 30) and `year`
(365 ± 30). A role takes the scene nearest its target that is on the anchor's
MGRS tile (`grid:code`) and relative orbit (read from `s2:product_uri`, since
Earth Search's Collection 1 items have no `sat:relative_orbit`), is not on a date
another role already took, and gives a chip under the site's chip cloud limit.
Ties go to the earlier date. Every date is the same window of the tile grid as the
anchor, checked by comparing geotransforms, so two dates share one grid. The
anchor's own day is excluded, which rules out its duplicate datastrip. Four dates
give six pairs and four triplets. The earlier date is always the reference.
`satreg real-pairs` fetches and lists them. Dates are cached under
`data/real/<site>/`, keyed like N1 chips plus the whole series configuration.

**Why.** Same tile and same orbit means the same viewing geometry, so two dates
differ by what the product leaves: residual misregistration, season, ground
change. The three spacings span that range. A few days apart, the ground barely
changes. A season apart, crops, leaves and sun elevation do. A year apart, the
season is the same but the ground has had a year to change. Anchoring on the
chip's own scene keeps the N1 chip in every series. Mixing satellites is what an
operational pair looks like, and the constellation's inter-satellite
registration is part of what the methods face. Recording the platform lets a
later table split on it.

**Series fetched.** All six sites (dates, satellite): Beauce 2025-07-01 2B, 06-21
2B, 09-19 2B, 2026-06-23 2A. Toulouse 06-28, 06-18, 10-01 2C, 2026-06-23. Vosges
08-11 2A, 08-14 2B, 11-22 2B (about 3 % snow), 2026-08-14 2C. Marseille 06-29 2A,
06-27 2C, 10-05 2C, 2026-06-27 2B. The two held-out sites were fetched too, since
N3 needs them. Their dates are listed by `satreg real-pairs` and measured
nowhere. Every pair's joint mask hides at most 0.1 % of the chip.

---

## 2026-09-28: A real pair's mask: scene classification on the chip grid, no data hidden like cloud

**Decision.** Each date stores its chip and its SCL, the 20 m classification
mapped onto the 10 m chip grid by looking up the classification pixel under each
chip pixel's centre, with no resampling. A pair's `cloud` mask is the union of
both dates' hidden pixels: cloud (8, 9, 10), cloud shadow (3) and no data. Snow
is ground, as for chips. A non-anchor date may have a few no-data pixels in its
band. They are set to SCL class 0 and count against the same 1 % chip limit as
cloud. The anchor and the N1 chips still refuse any no-data pixel.

**Why.** The mask belongs to the chip grid, where methods and metrics work, and a
lookup keeps the classes exact. Averaging 20 m classes onto 10 m would invent
fractional clouds. No data was the Vosges `season` role's only obstacle: its one
clear date within 30 days (2025-11-22, 0.04 % cloud) had 18 no-data pixels on the
chip. Those 18 pixels (0.2 %) hide ground exactly as cloud does, so they are
masked the same way.

**Rejected.** Widening the `season` tolerance until a complete chip turns up. That
would bend the date rule for one site.

---

## 2026-09-28: A pair's appearance is measured without registering it

**Decision.** `satreg/appearance.py` measures how the moving image of a pair
differs from its reference. It uses each image's statistics or power spectrum,
which a shift does not change, so the measurement does not depend on how well the
pair is registered.

- **Noise.** Immerkær's estimator gives σ, and the SNR is `20 log10(std / σ)`,
  the definition the `noise` degradation uses.
- **Blur difference.** Take the log ratio of the two Hann-windowed radial power
  spectra, and fit it against f² over 0.05 to 0.25 cycles/px. It gives
  `sign(d) √|d|` with `d = σ_moving² − σ_reference²`, in pixels.
- **Contrast and level.** Contrast is the ratio of standard deviations. Level is
  the mean difference in reference standard deviations.
- **Tone bend.** Take 19 quantiles (5 % to 95 %) of each image. Fit the moving
  image's quantiles as an affine function of the reference's, and report the RMS
  residual over the moving image's quantile spread. It is 0 for any gain and
  offset.
- **Correlation.** Pearson correlation, pixel by pixel. This is the only
  measurement that does depend on registration and on ground change.

`satreg check-presets` measures each real pair on its 256 px windows with at most
1 % hidden pixels, and takes the median. Each preset is measured the same way, on
zero-shift windows of the same sites' anchor chips, without its clouds, whose
nominal cover is reported instead.

**Why.** The degradation presets entry asked for this check against real pairs.
Registration-free estimators compare real and simulated pairs on equal terms,
with no method's bias in between.

**Findings on the estimators.** They were checked on known degradations.

- **Blur.** The estimator recovers σ = 1.0 and 1.5 within 5 %. `mild`'s σ = 0.4
  reads 0.28, which is what it really does. A 0.4 px Gaussian sampled on the
  pixel grid is a kernel whose frequency response matches a 0.28 px Gaussian.
- **Noise.** Immerkær reads fine texture as noise, so on 10 m chips the SNR is a
  lower bound: about 18 dB on a clean city, forest or coast chip, 32 dB on
  Beauce's fields. Only differences between rows mean something.
- **Tone.** A fitted gamma was tried first and dropped. With the curve's ends
  normalised by percentiles, a true 1.5 read 1.26. With them normalised by
  min/max and an affine term, it was exact on synthetic images but read `hard`'s
  1.5 as 1.07 on Toulouse and 0.23 on Vosges. A few bright pixels stretch a real
  window's range, so the gamma is not identifiable. The tone bend assumes no
  curve shape.

---

## 2026-09-28: The presets stay as they are; real pairs cover ground change

*My call*: keep `mild` and `hard` unchanged, rather than tuning them to the real
pairs' values or adding a preset that imitates ground change.

**Finding.** Beauce, Toulouse, Vosges and Marseille, from
`outputs/presets-check/summary.md`. Each cell is the median [min, max] across
sites. Each measurement is its distance from an unchanged pair: |blur|, contrast
factor max(g, 1/g), |offset|. The SNR is the lower of the two images'.

| pairs | gap (days) | SNR (dB) | blur (px) | contrast × | offset (std) | tone bend | correlation |
|---|---:|---:|---:|---:|---:|---:|---:|
| preset `clean` | 0 | 18.5 [17.9, 31.8] | 0 | 1 | 0 | 0 | 1 |
| preset `mild` | 0 | 18.1 [17.6, 27.3] | 0.27 [0.26, 0.28] | 1.16 [1.12, 1.18] | 0.52 [0.37, 0.61] | 0.008 | 1.00 |
| preset `hard` | 0 | 7.8 [6.7, 10.7] | 0.58 [0.39, 0.74] | 2.34 [1.68, 2.66] | 1.32 [1.07, 1.57] | 0.028 [0.009, 0.044] | 0.84 [0.81, 0.92] |
| anchor-days | 6 | 18.5 [17.9, 28.1] | 0.14 [0.05, 0.33] | 1.05 [1.01, 1.28] | 0.32 [0.01, 0.70] | 0.014 [0.002, 0.062] | 0.96 [0.73, 0.99] |
| anchor-season | 96 | 18.5 [17.2, 28.6] | 0.31 [0.21, 0.50] | 1.33 [1.08, 5.31] | 0.59 [0.28, 2.98] | 0.042 [0.023, 0.078] | 0.65 [0.39, 0.90] |
| anchor-year | 362 | 18.5 [17.9, 29.5] | 0.12 [0.00, 0.33] | 1.14 [1.02, 1.50] | 0.13 [0.04, 0.52] | 0.015 [0.006, 0.059] | 0.90 [-0.04, 0.98] |
| days-season | 100 | 18.7 [17.2, 28.1] | 0.25 [0.06, 0.47] | 1.11 [1.04, 5.20] | 0.52 [0.35, 2.21] | 0.034 [0.022, 0.061] | 0.60 [0.35, 0.90] |
| days-year | 366 | 18.8 [17.9, 28.1] | 0.20 [0.01, 0.31] | 1.09 [1.02, 1.48] | 0.20 [0.03, 0.61] | 0.029 [0.008, 0.062] | 0.88 [0.11, 0.97] |
| season-year | 265 | 19.9 [17.2, 28.6] | 0.25 [0.17, 0.28] | 1.18 [1.01, 3.43] | 0.46 [0.35, 0.75] | 0.039 [0.025, 0.073] | 0.62 [0.13, 0.89] |

Nominal values are `mild`: 30 dB added, σ 0.4, gain 1.1, offset 0.2, gamma 0.9,
5 % clouds. `hard`: 15 dB added, σ 1, gain 0.7 (×1.43), offset 0.5, gamma 1.5,
30 % clouds. Real pairs are clear by construction (at most 0.1 % hidden), so
their cloud share says nothing about the presets'.

**Reading.**

- **`mild` sits where a real pair a few days apart does.** Its blur, contrast
  and tone bend are within the range of the `days` pairs. Its offset (0.52) is
  in the upper half. Its gamma moves the mean, so the measured offset is more
  than the nominal 0.2. Its added noise is invisible next to the texture the
  estimator reads.
- **`hard` is harsher than any clear real pair on noise.** Its median is about
  10 dB below the real rows, and every site's value is at least 6 dB below any
  real pair's.
- **`hard` is harsher than most real pairs on contrast.** Its gamma compresses
  the moving image's spread on top of the 0.7 gain, so the effective loss is
  ×2.3, not ×1.43. Only pairs with the Vosges November date go further (up to
  ×5.3, with a low sun and some snow). Its blur (0.58) is beyond every real
  pair's (at most 0.50).
- **No preset models ground change.** Season pairs correlate at 0.60–0.65 and a
  year apart Beauce falls to −0.04, since the fields changed crop. `hard` keeps
  0.84 and `mild` 1.00: the presets change appearance, the ground stays the
  same. That is what the real pairs add, and what tickets 09 and 11 measure on
  them.

**Decision.** `mild` and `hard` stay as `configs/degradations.toml` has them. Their
nominal values keep describing what the code applies. The measured values above
say what that means on real chips: `mild`'s blur acts like 0.28 px, and `hard`'s
gamma makes its contrast loss about ×2.3.

**Why.** The presets vary one thing, how the moving acquisition looks, while the
ground and the truth stay fixed. That is what makes a failure on `hard` readable
as sensitivity to noise, blur or radiometry. `mild` already sits where a pair a few
days apart does. `hard` is a stress case beyond clear real pairs, which a
robustness test needs; on contrast, only the Vosges November pairs go further.
Retuning them would also change the N1 table, which stays comparable as
long as they do not move. Ground change is what the presets lack, and real pairs
measure it directly: cycle consistency (ticket 09) and the false-change
experiment (ticket 11) run on them, not on a simulated imitation.

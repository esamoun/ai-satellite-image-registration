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

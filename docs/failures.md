# Failure log

What was tried and did not work, and what it cost. Kept deliberately: the dead ends
are part of the method, and a benchmark whose limits are known is more useful than
one whose limits are not.

Each entry: what was attempted, what happened, why, and what was done instead.

---

## 2026-09-23: A round-trip test that measured itself

**What was attempted.** To check how much the Fourier shift rings at image edges,
an image was shifted by (+0.5, +0.3) px, shifted back by (-0.5, -0.3) px, and
compared with the original.

**What happened.** With mirrored padding, the round trip left errors of 0.16 image
standard deviations deep inside the image, worse than with no padding at all
(0.085). That seemed to argue against padding.

**Why.** The test was wrong, not the padding. The second shift mirrors an image that
has already been shifted, so it pads with different content than the first shift
saw, and the two errors add up instead of cancelling. Without padding, the round
trip is exact up to the wrap-around, which flatters the unpadded version.

**What was done instead.** Compare against a shift known to be exact: shift a
periodic texture as a whole (where the Fourier shift is exact), cut a window from
it, and compare that with the same window shifted on its own. That test is what
`docs/decisions.md` quotes, and it is in the test suite.

---

## 2026-09-23: Checking the blur's geometry with phase correlation

**What was attempted.** To show that the blur, radiometric and noise degradations
move no content, a test ran phase correlation on a degraded pair and expected
the simulated shift to within 0.03 px.

**What happened.** It failed by 0.03 px. Over 20 pairs, a 1 px blur of the moving
image alone biased phase correlation by 0.12 px on average (up to 0.15 px), and
blurring both images made it worse: 0.57 px on average, up to 1.15 px. The
radiometric change and 30 dB noise did not move the estimate.

**Why.** The blur did not move anything: blurring the shifted image equals
shifting the blurred scene, to 0.01 standard deviations. The bias is the
method's. Phase correlation without an apodisation window treats the image as
periodic, so the jump between opposite borders adds a component that does not
move with the content and peaks at zero shift. Phase correlation whitens the
spectrum, and once blur has removed the scene's high frequencies, that border
component dominates what is left and pulls the peak towards zero. With a Hann
window, the same blurred pairs gave exactly the simulated shift.

**What was done instead.** The geometry test now compares pixels, with no
registration method involved. A quick run of both variants on the presets
(30 pairs each) shows the Hann window is not a free win: on Beauce it lowers the
mean error from 0.020 to 0.004 px (clean) and from 0.034 to 0.013 px (mild), but
on `hard` it fails more often (23 % against 10 %), because the window weights
the centre, where a cloud bank can sit. The phase-correlation entry in
`docs/decisions.md` said windowing would be tested once degradations arrived; it
now has its evidence, and the choice is left to the N1 results table (ticket
09), where both variants can be reported.

---

## 2026-09-23: A window size read from the wrong place

**What was attempted.** To report the matching window AROSICS used, the first
version read the shape of its `matchWin` attribute.

**What happened.** On 128 px pairs it reported 126 px, and a test expecting 128
failed. AROSICS had in fact correlated a 64 px window.

**Why.** AROSICS cuts the matching window to fit the pair, then shrinks it to the
largest power of two before the FFT, and does not update `matchWin` (its source
says so in a FIXME). The attribute describes the window it cut, not the one it
correlated.

**What was done instead.** The diagnostic applies AROSICS' own shrinking function to
that shape, so it reports the window correlated. The benchmark and tests use 256 px
pairs, where both agree.

---

## 2026-09-23: A Hann window that looked at the clouds

**What was attempted.** The N1 run reported phase correlation with and without a
Hann window, since the window had removed the blur bias on clean and mild pairs.

**What happened.** On `hard` Beauce, the windowed version failed 13 of 100
translation pairs, against 4 for the plain one, and not by a little: 12 of the 13
were off by 10 to 53 px, far beyond the 4 px shifts simulated. All but one failed
in the affine scenario too, by the same amounts. Only one pair failed both
versions.

**Why.** The window weights the centre of the pair and mutes its borders. With a
30 % cloud cover, whether a cloud bank lands in the centre decides what the
correlation sees. Weighting each pair's cloud opacity by the same Hann window: on
the 13 pairs the windowed version failed, 53 % of the window's weight was under
cloud on average (29 % at least); on the 87 it registered, 25 %. Clouds are only
in the moving image, so a window full of cloud correlates a cloud edge with ground
texture, and the peak lands anywhere. The plain version spreads its attention over
the whole pair, including the clear borders.

**What was done instead.** Nothing was fixed, because nothing is broken: both
versions are in the table, and the plain one stays the reference row (see
`decisions.md`). A cloud mask would help either version, and is what an
operational chain would do; the benchmark leaves clouds to the methods on purpose.

---

## 2026-09-23: A probe that made reliability look informative

**What was attempted.** AROSICS' reliability floor was set at 60 % after a probe on
60 `hard` Beauce pairs, where the shifts rated between 40 and 60 % had a median
error of 0.40 px against 0.28 px above 60 %.

**What happened.** On the 400 `hard` pairs of the N1 run, the two bands have the
same accuracy: 0.448 against 0.449 px on Beauce, 0.356 against 0.345 px on
Toulouse. The floor was declining estimates as good as the ones it kept, and
AROSICS' failure rate on `hard` Beauce owed about 28 points to it.

**Why.** 19 and 11 pairs per band: a difference of 0.12 px between two medians that
small is within what the draw of the pairs gives. The probe was read as a trend
when it was noise.

**What was done instead.** The floor is now 40 %, the band below which every gross
error of the probe sat, and the 60 % setting is kept in the table as a variant so
the comparison stays visible. Thresholds are set on the full run, not on probes.

---

## 2026-09-23: AROSICS found no match on one clean pair

**What happened.** In the N1 run, AROSICS declined one `clean` pair, Beauce affine
pair 31, with "No match found in the given window". It is the only clean or mild
pair it declined out of 800. The translation version of the same pair, same window
and same shift, it registered to 0.060 px, rated 96 % reliable. Plain phase
correlation got 0.35 px on the affine version and SIFT 0.02 px, so the pair itself
is not hard.

**Why.** Not found. The motion does not explain it: pair 31's rotation, about
0.17°, is only the 19th largest of the 100 affine pairs, and AROSICS registered the
18 above it. Its correlation-peak checks rejected this one peak, and without a
closer look inside AROSICS the reason stays unknown.

**What was done instead.** Nothing: it is one pair in 800, and the table counts it
as a failure like any other. It is logged because a classic method declining a
clean, textured pair is not what one expects, and a later level that runs AROSICS
on more pairs should check whether it recurs.

---

## 2026-09-25: The first Kaggle run stopped before its first pair

**Attempted.** The first run of `configs/gpu.toml` on a Kaggle GPU, from the
notebook in `kaggle/`.

**What happened.** The clone, the install and the weights went through; the
benchmark stopped while reading the first chip, with `TypeError: unsupported
operand type(s) for @: 'Affine' and 'tuple'`. The notebook showed only that the
command had failed: the error itself was in Kaggle's Logs tab.

**Why.** Georeferencing maps a point with `transform @ (x, y)`, an operator that
the `affine` library added in 3.0. The M1 had 3.0.1, installed with rasterio;
Kaggle's image ships affine 2.x, which rasterio accepts, and nothing in
`pyproject.toml` asked for more. Every test ran on the M1, so none could see it.
The notebook's commands wrote to the kernel's own streams, which Kaggle does not
show in the cell.

**What was done instead.** `pyproject.toml` requires `affine>=3.0`, so the
install upgrades it. The notebook reads each command's output and prints it in
the cell, so the next failure shows its message where it happened.

---

## 2026-09-25: A device gap that was RANSAC's noise

**What was attempted.** `configs/gpu.toml` was run on the M1's CPU and on a
Kaggle T4, at the same commit, and the two runs merged by device, to compare
the learned methods' cost and check that their accuracy does not depend on the
device.

**What happened.** RAFT and RAFT small gave the same error on both devices, to
1e-5 px on every pair, and every method agreed on `clean` pairs. On `hard`
pairs, LightGlue and RoMa did not: 7 of the 60 `hard` pairs switched between
success and failure for LightGlue on ALIKED, 29 for LightGlue on DISK, and
`lightglue` on hard translations failed 50 % of the pairs on the CPU against
65 % on the GPU.

**Why.** Two effects add up. The networks do not compute the same thing on both
devices: kornia's LightGlue prunes keypoints layer by layer on the CPU but, on
CUDA, only above 1536 keypoints (the pairs have about 800), and runs attention
in float16 on CUDA; romatch runs RoMa under float16 autocast on CUDA and in
float32 on the CPU. RAFT does neither, hence its identical rows. The keypoints
were identical, but 1 to 4 % of the matches changed. RANSAC then turns that into
a different model: on `hard` pairs only a fifth to a third of the matches are
inliers, and which ones its samples draw depends on the order and number of the
matches. Handing the same matches to RANSAC in five shuffled orders, on the same
CPU, switched 7 to 15 pairs out of 60 for `lightglue` and 25 to 29 for
`lightglue_disk`, as many as the change of device. `lightglue_disk`'s failure
rate on `hard` pairs ranged from 30 to 45 % across those orders; the GPU's 37 %
is inside that range. Rerunning with the original order reproduced the CPU run
exactly.

**What was done instead.** Nothing in the code: the rows are right, they are
noisier than one run shows. The device comparison is read for time and memory
only, and the `hard` rows of the RANSAC-fitted methods (LightGlue, RoMa's affine
fit, and likely SIFT, which shares the fit) carry roughly 5 to 15 points of
failure-rate spread from RANSAC alone. RoMa and SIFT were not rerun with shuffled
matches. Whether to reduce that spread, or report it, is left to the N2 results
table (ticket 12).

## 2026-09-29: A one-site check that ran every site

**What happened.** A quick check of the N2 false-change settings, `satreg
false-change --config configs/n2.toml --site toulouse --methods
phase_correlation roma --pairs 1`, was meant to run Toulouse alone. It ran
Beauce, Toulouse, Vosges, Marseille, then Toulouse again, for 67 minutes;
`context.json` listed the five sites. Timed as one site, it put RoMa's cost in
the false-change run at five times its real value.

**Why.** `--site` and `--band-pair` are repeatable options: argparse appends
each value to the option's default. With `--config`, that default is the
config's list, so the command line added to the list where it should have
replaced it, as it replaces every other key. No test crossed a config with a
repeatable option.

**What was done instead.** `parse_args` now keeps the command line's list for
an option it gave that has no default of its own, which is what a repeatable
option is, and a test checks that `--site` and `--band-pair` replace the
config's lists. The false-change settings themselves ran without error.

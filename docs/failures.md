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

---

## 2026-09-30: The inter-band run on Kaggle stopped at its method check

**Attempted.** The N2 inter-band run, `configs/n2-bands.toml` with its ten
methods, on a Kaggle T4 from the notebook in `kaggle/`.

**What happened.** The install and the B08 and B03 chips of Beauce and Toulouse
went through; after 140 s the benchmark stopped with `satreg: method arosics
needs arosics, not installed`, before its first pair.

**Why.** The notebook installs the dl extra and RoMa, not AROSICS, whose GDAL
bindings must be built against a system GDAL. Every earlier Kaggle config listed
deep-learning methods only, so the gap never showed; moving the inter-band run
to Kaggle, with the classic methods on Kaggle's CPU, was decided without
checking what the notebook installs. No test tied a config's methods to where it
runs.

**What was done instead.** The config is split like the simulated table:
`configs/n2-bands.toml` runs the classic methods on the M1, where AROSICS is
installed, `configs/n2-bands-gpu.toml` the deep-learning ones on Kaggle, on the
same pairs, and `make n2-bands-merge` joins them. A test checks that every
config on `cuda` lists deep-learning methods only.

---

## 2026-10-01: RoMa's hard failures on the T4 looked like a device effect

**Attempted.** Reading the N2 simulated table against RoMa's first measurement
(decisions.md, 2026-09-24): 20 Beauce pairs on the M1's CPU, where `roma`
declined 35 to 40 % of `hard` pairs.

**What happened.** On the T4, `roma` fails 48 % of hard Beauce translations,
83 % at Toulouse, 81 % in the Vosges and 61 % at Marseille: 68 % over the four
sites, almost all declined for lack of certain pixels. The first suspect was the
device: on CUDA, romatch computes in half precision, on a CPU in float32.

**Why.** It is the site and the sample, not the device. The N2 false-change run
has RoMa on the M1's CPU, on 20 hard pairs per site and scenario: it fails 35 %
at Beauce, 85 % at Toulouse, 80 to 85 % in the Vosges and 50 to 55 % at
Marseille. The first 20 pairs of the same cells on the T4 give 35 to 40 %, 85 %,
65 to 70 % and 60 %. The two runs do not draw the same pairs, and with 20 pairs
a rate moves by 5 points a pair: the two devices are within one to three pairs
in twenty of each other, the Vosges furthest apart. The first measurement was
Beauce only, the site where RoMa declines least, and on 20 pairs: the first 20
Beauce pairs of the T4 run give the same 35 to 40 %, against 48 to 50 % over
the 100.

**What was done instead.** Nothing rerun. The two devices are still not compared
pair by pair on `hard`; evaluation.md says so in its limits. Why RoMa finds
fewer certain pixels on hard Toulouse pairs than on hard Beauce ones, the
opposite of every keypoint method, is not explained.


## 2026-10-11: An int8 RAFT calibrated on clean pairs failed the hard ones

**Attempted.** The trial of static int8 quantization, on pretrained RAFT large
(`scripts/raft_int8_trial.py`): every convolution computed on 8-bit integers
but the 25 that read the flow, write its update or write the upsampling mask,
the scales set on 12 validation pairs, the file then scored on 36 others, one
per chip, scenario and preset.

**What happened.** The file failed 7 of the 36 pairs, all of the `hard`
preset, where the float file fails none: its flow was 0.46 px from the float
file's on average and 2.1 px on the worst pair. One scale per channel, the
entropy calibration and the percentile one failed the same 7. A variant with
only the convolution that writes the flow update left in float failed 9, its
flow about 10 px off on those pairs.

**Why.** The 12 calibration pairs were all clean. They were taken as one pair
in three of a list in which the preset is the innermost loop (clean, mild,
hard), so one in three is one preset. A static file fixes the range of every
tensor from what the calibration pairs showed it; the `hard` preset (clouds on
a third of the image, noise at 15 dB, a darker and blurred moving image) sends
tensors outside those ranges, where the values are clipped. It is not the
graph optimizer: the numbers are the same with ONNX Runtime's optimizations
turned off. Not explained: with the same 12 pairs, the file with every
convolution on integers failed no pair.

**What was done instead.** With 4 clean, 4 mild and 4 hard pairs, no failure
and a flow 0.07 px from the float file's. `quantize.calibration_pairs` draws
one pair per chip, scenario and preset, 36 pairs, and a test checks every cell
is among them. A static file is only as wide as its calibration set: a
degradation no calibration pair has is not covered, and nothing in the file
says so.

## 2026-10-11: ONNX Runtime's quantization pre-processing does not get through RAFT's graph

**Attempted.** `quant_pre_process`, the step ONNX Runtime asks for before a
static quantization, on the exported RAFT files, with its defaults
(onnxruntime 1.30.0, onnx 1.23.0).

**What happened.** It raises "Incomplete symbolic shape inference", and leaves
`sym_shape_infer_temp.onnx` and a 21 MB `.data` file in the working directory,
the repository's root.

**Why.** Not looked into further than the message. The files are exported with
a free image size, and the unrolled refinements build the lookup coordinates
from that size: the symbolic pass does not resolve those shapes.

**What was done instead.** The step runs with `skip_symbolic_shape=True`: it
still folds constants and runs ONNX's own shape inference, which is enough for
the quantizer. A test quantizes a file twice and checks the working directory
is left as it was. A second trap of the same tool: the calibrator raises "No
data is collected" when `CalibMaxIntermediateOutputs`, the number of pairs it
holds before folding them into ranges, divides the number of calibration
pairs, as it then ends on an empty batch. `quantize._chunk` picks a size that
does not divide it.

## 2026-10-12: The first draft of the N3 write-up chose a deployment point on the held-out rows

**Attempted.** The N3 write-up was to say which point of the cost curve one
would deploy, as its plan asked.

**What happened.** The draft named two points, chosen on the held-out rows
after they were read, and presented the freeze as silent on the matter. It
was not committed.

**Why.** The plan's line is older than the freeze, and the freeze was not
reread against it. The rule of 2026-10-02 allows no choice on the rows of the
held-out sites, cost figures included, and the freeze says that a point picked
after the read is such a choice. The options I chose from had been laid out
without that sentence.

**What was done instead.** A review of the draft against `decisions.md` and
the glossary caught it. The write-up names no point: it says what the curve
shows for each constraint, and leaves the choice to the use and to the
validation set ([`decisions.md`](decisions.md), same date). The same review
corrected figures of the draft before the commit: a rounding in the int8
table, a 5 ms time given to phase correlation with a Hann window when it is
the time of the plain variant, and a gain "about twice as large on `hard`
pairs" that holds for two scenarios of three.

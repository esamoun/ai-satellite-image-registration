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

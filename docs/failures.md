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

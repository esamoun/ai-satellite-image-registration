import math

import numpy as np
import pytest

from satreg.displacement import Affine, Displacement, Translation
from satreg.metrics import (
    FAILURE_EPE_PX,
    PairScore,
    endpoint_error,
    is_failure,
    score,
)


class Field(Displacement):
    """A displacement given pixel by pixel, to test metrics beyond translations."""

    def __init__(self, values: np.ndarray) -> None:
        self.values = values

    def field(self, shape: tuple[int, int]) -> np.ndarray:
        return self.values


def test_epe_is_the_euclidean_distance_between_shifts():
    # A 3-4-5 triangle: 0.3 px and 0.4 px apart gives 0.5 px everywhere.
    epe = endpoint_error(Translation(0.3, 0.4), Translation(0.0, 0.0), (4, 5))

    assert epe.shape == (20,)
    np.testing.assert_allclose(epe, 0.5)


def test_translation_scored_on_an_affine_truth_by_hand():
    # A 10 % zoom about the centre of a 5 x 5 grid, estimated as no motion: each
    # pixel's error is 0.1 times its distance to the centre.
    truth = Affine.about((2.0, 2.0), scale=1.1)

    epe = endpoint_error(truth, Translation(0.0, 0.0), (5, 5)).reshape(5, 5)

    assert epe[2, 2] == pytest.approx(0.0, abs=1e-12)
    assert epe[0, 2] == pytest.approx(0.2)  # 2 px above the centre
    assert epe[1, 3] == pytest.approx(0.1 * math.sqrt(2))
    assert epe[0, 0] == pytest.approx(0.1 * math.sqrt(8))
    assert epe[4, 3] == pytest.approx(0.1 * math.sqrt(5))
    # Distances over the grid: 1 at 0, 4 at 1, 4 at sqrt 2, 4 at 2, 8 at sqrt 5
    # and 4 at sqrt 8, which sum to 12 + 12 sqrt 2 + 8 sqrt 5.
    mean = 0.1 * (12 + 12 * math.sqrt(2) + 8 * math.sqrt(5)) / 25
    assert score(truth, Translation(0.0, 0.0), (5, 5)).mean_epe == pytest.approx(mean)


def test_shares_count_pixels_strictly_under_each_threshold():
    truth = Translation(0.0, 0.0)
    values = np.zeros((2, 2, 2))
    values[1] = [[0.05, 0.3], [0.5, 2.0]]  # dx errors of 4 pixels

    result = score(truth, Field(values), (2, 2))

    assert result.mean_epe == pytest.approx((0.05 + 0.3 + 0.5 + 2.0) / 4)
    assert result.share_below_0_1 == 0.25
    assert result.share_below_0_5 == 0.5


def test_mask_keeps_only_valid_pixels():
    values = np.zeros((2, 2, 2))
    values[0, 0, 0] = 10.0
    mask = np.ones((2, 2), dtype=bool)
    mask[0, 0] = False

    result = score(Translation(0, 0), Field(values), (2, 2), mask)

    assert result.mean_epe == 0.0
    assert result.share_below_0_1 == 1.0


@pytest.mark.parametrize(
    "mask", [np.ones((3, 3), bool), np.zeros((2, 2), bool)], ids=["shape", "empty"]
)
def test_bad_masks_are_rejected(mask):
    with pytest.raises(ValueError):
        endpoint_error(Translation(0, 0), Translation(0, 0), (2, 2), mask)


def test_non_finite_estimate_scores_nan_and_fails():
    result = score(Translation(0, 0), Translation(math.nan, 0), (2, 2))

    assert math.isnan(result.mean_epe)
    assert result.share_below_0_1 == 0.0
    assert is_failure(result)


@pytest.mark.parametrize(
    ("epe", "failed"),
    [(0.0, False), (FAILURE_EPE_PX, False), (FAILURE_EPE_PX + 1e-6, True)],
)
def test_failure_is_a_mean_error_above_the_threshold(epe, failed):
    assert is_failure(PairScore(epe, 0.0, 0.0)) is failed
    assert is_failure(PairScore(epe, 0.0, 0.0), threshold=10.0) is False

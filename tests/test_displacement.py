import numpy as np
import pytest

from satreg.displacement import Affine, Dense, Translation
from satreg.metrics import score


def test_translation_field_is_constant_dy_then_dx():
    field = Translation(dx=1.5, dy=-0.25).field((3, 4))

    assert field.shape == (2, 3, 4)
    np.testing.assert_array_equal(field[0], -0.25)
    np.testing.assert_array_equal(field[1], 1.5)


def test_affine_without_linear_part_is_a_translation():
    affine = Affine.about((10.0, 20.0), dx=1.5, dy=-0.25)

    np.testing.assert_allclose(
        affine.field((3, 4)), Translation(dx=1.5, dy=-0.25).field((3, 4)), atol=1e-12
    )


def test_affine_moves_its_centre_by_the_translation():
    affine = Affine.about(
        (5.0, 7.0), rotation_deg=3.0, scale=1.01, shear=0.02, dx=0.4, dy=-1.2
    )

    field = affine.field((11, 15))

    np.testing.assert_allclose(field[:, 5, 7], [-1.2, 0.4], atol=1e-12)


def test_positive_rotation_turns_counter_clockwise_as_displayed():
    # Rows point down: a point right of the centre moves up.
    affine = Affine.about((0.0, 0.0), rotation_deg=90.0)

    right = affine.apply(np.array([0.0, 1.0]))

    np.testing.assert_allclose(right, [-1.0, 0.0], atol=1e-12)


def test_shear_moves_rows_below_the_centre_to_the_right():
    affine = Affine.about((0.0, 0.0), shear=0.1)

    field = affine.field((3, 3))

    np.testing.assert_allclose(field[1, :, 0], [0.0, 0.1, 0.2], atol=1e-12)
    np.testing.assert_allclose(field[0], 0.0, atol=1e-12)


def test_scale_moves_pixels_away_from_the_centre():
    affine = Affine.about((1.0, 1.0), scale=1.5)

    field = affine.field((3, 3))

    np.testing.assert_allclose(field[:, 0, 2], [-0.5, 0.5])
    np.testing.assert_allclose(field[:, 1, 1], [0.0, 0.0])


def test_affine_rejects_a_non_positive_scale():
    with pytest.raises(ValueError, match="scale"):
        Affine.about((0.0, 0.0), scale=0.0)


@pytest.mark.parametrize(
    "model",
    [
        Translation(dx=1.5, dy=-0.25),
        Affine.about((4.0, 6.0), rotation_deg=2.0, scale=1.01, dx=0.3, dy=0.7),
    ],
)
def test_a_dense_field_scores_like_the_model_it_was_sampled_from(model):
    shape = (9, 13)
    truth = Translation(dx=1.0, dy=-0.5)

    dense = Dense(model.field(shape))

    assert score(truth, dense, shape) == score(truth, model, shape)
    np.testing.assert_array_equal(dense.field(shape), model.field(shape))


def test_a_dense_field_exists_on_its_own_grid_only():
    dense = Dense(np.zeros((2, 4, 5)))

    assert dense.shape == (4, 5)
    with pytest.raises(ValueError, match="given on \\(4, 5\\)"):
        dense.field((5, 4))


@pytest.mark.parametrize("shape", [(4, 5), (3, 4, 5), (2, 4, 5, 1)])
def test_a_dense_field_needs_two_components_on_a_grid(shape):
    with pytest.raises(ValueError, match="shape \\(2, rows, cols\\)"):
        Dense(np.zeros(shape))


def test_a_dense_field_cannot_be_changed_through_its_input_or_output():
    values = np.zeros((2, 3, 3), dtype=np.float32)
    dense = Dense(values)

    values[0] = 1.0
    dense.field((3, 3))[0] = 1.0

    np.testing.assert_array_equal(dense.field((3, 3)), 0.0)
    assert dense.values.dtype == float
    assert not dense.values.flags.writeable


def test_a_dense_field_is_shown_by_its_mean_not_its_values():
    field = np.stack([np.full((50, 60), -0.25), np.full((50, 60), 1.5)])

    assert repr(Dense(field)) == "Dense(shape=(50, 60), mean_dx=1.5, mean_dy=-0.25)"

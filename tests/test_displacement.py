import numpy as np
import pytest

from satreg.displacement import Affine, Dense, Translation, compose
from satreg.metrics import score
from satreg.simulate import SmoothField


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


def _chained(first, second, points):
    """Where content at ``points`` in A lands in C, applying each map in turn."""
    return second.apply(first.apply(points))


def test_two_translations_compose_to_their_sum():
    composed = compose(Translation(dx=1.5, dy=-0.25), Translation(dx=-0.5, dy=2.0))

    assert composed == Translation(dx=1.0, dy=1.75)


def test_two_affines_compose_to_the_map_applied_in_turn():
    first = Affine.about((10.0, 20.0), rotation_deg=0.3, scale=1.002, dx=1.5)
    second = Affine.about((5.0, 5.0), shear=0.004, scale=0.998, dy=-2.0)
    points = np.indices((6, 7), dtype=float)

    composed = compose(first, second)

    assert isinstance(composed, Affine)
    np.testing.assert_allclose(
        composed.apply(points), _chained(first, second, points), atol=1e-12
    )


def test_a_translation_and_an_affine_compose_either_way():
    shift = Translation(dx=0.7, dy=-1.2)
    affine = Affine.about((3.0, 4.0), rotation_deg=-0.5, dx=0.1)
    shift_map = Affine(((1.0, 0.0), (0.0, 1.0)), (-1.2, 0.7))
    points = np.indices((5, 5), dtype=float)

    for first, second, maps in (
        (shift, affine, (shift_map, affine)),
        (affine, shift, (affine, shift_map)),
    ):
        np.testing.assert_allclose(
            compose(first, second).apply(points),
            _chained(*maps, points),
            atol=1e-12,
        )


def test_an_affine_composed_with_its_inverse_is_no_displacement():
    affine = Affine.about((8.0, 8.0), rotation_deg=0.2, scale=1.001, shear=0.002, dx=3)
    matrix = np.linalg.inv(np.asarray(affine.matrix))
    inverse = Affine(
        matrix=tuple(map(tuple, matrix)), offset=tuple(-matrix @ affine.offset)
    )

    composed = compose(affine, inverse)

    np.testing.assert_allclose(composed.field((9, 9)), 0.0, atol=1e-12)


def _smooth_leg(seed, shape):
    """A global map plus a smooth field, as a callable map and a dense field."""
    rng = np.random.default_rng(seed)
    affine = Affine.about(
        ((shape[0] - 1) / 2, (shape[1] - 1) / 2), rotation_deg=0.2, dx=1.3, dy=-0.7
    )
    local = SmoothField.draw(rng, 16.0, 0.8, shape)

    def forward(points):
        return affine.apply(points) + local(points)

    grid = np.indices(shape, dtype=float)
    return forward, Dense(forward(grid) - grid)


@pytest.mark.parametrize("order", [1, 3])
def test_two_dense_fields_compose_up_to_the_interpolation_error(order):
    shape = (64, 64)
    forward1, first = _smooth_leg(1, shape)
    forward2, second = _smooth_leg(2, shape)
    grid = np.indices(shape, dtype=float)
    truth = forward2(forward1(grid)) - grid
    # Away from the border, where the displaced points stay on the grid.
    inside = (slice(4, -4), slice(4, -4))

    composed = compose(first, second, order=order)

    assert isinstance(composed, Dense)
    error = np.hypot(*(composed.values - truth))[inside]
    assert error.max() < (0.02 if order == 1 else 0.002)


def test_a_dense_field_and_a_global_one_compose_exactly_where_the_global_is_second():
    shape = (32, 32)
    forward, first = _smooth_leg(3, shape)
    second = Affine.about((10.0, 10.0), rotation_deg=0.4, scale=1.003, dx=-2.0)
    grid = np.indices(shape, dtype=float)

    composed = compose(first, second)

    np.testing.assert_allclose(
        composed.values, second.apply(forward(grid)) - grid, atol=1e-10
    )


def test_a_global_field_then_a_dense_one_gives_a_dense_one_on_its_grid():
    shape = (32, 32)
    _, second = _smooth_leg(4, shape)

    composed = compose(Translation(dx=0.0, dy=0.0), second)

    assert isinstance(composed, Dense)
    np.testing.assert_allclose(composed.values, second.values, atol=1e-12)


def test_dense_fields_on_different_grids_do_not_compose():
    with pytest.raises(ValueError, match="cannot compose"):
        compose(Dense(np.zeros((2, 4, 4))), Dense(np.zeros((2, 5, 5))))

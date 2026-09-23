import numpy as np

from satreg.displacement import Translation


def test_translation_field_is_constant_dy_then_dx():
    field = Translation(dx=1.5, dy=-0.25).field((3, 4))

    assert field.shape == (2, 3, 4)
    np.testing.assert_array_equal(field[0], -0.25)
    np.testing.assert_array_equal(field[1], 1.5)

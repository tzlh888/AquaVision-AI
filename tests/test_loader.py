"""Synthetic arrays verify storage layout, dtype, and unsafe format rejection."""

import numpy as np
import pytest

from aquavision.data.loader import BANDS, load_pair


def test_load_preserves_all_bands_and_reference(synthetic_pair):
    image, reference = load_pair(*synthetic_pair)
    assert image.shape == (len(BANDS), 64, 64)
    assert reference.shape == (1, 64, 64)
    assert image.dtype == np.uint16
    assert reference.dtype == np.uint8
    assert reference[0, 0, -57] == 255
    assert BANDS[8] == "B8A" and "B10" not in BANDS


@pytest.mark.parametrize("shape,dtype", [((64, 64, 12), "uint16"), ((3, 64, 64), "uint16"), ((12, 64, 64), "float32")])
def test_wrong_image_format_rejected(synthetic_pair, shape, dtype):
    np.save(synthetic_pair[0], np.zeros(shape, dtype=dtype))
    with pytest.raises(ValueError):
        load_pair(*synthetic_pair)


def test_object_pickle_rejected(synthetic_pair):
    np.save(synthetic_pair[0], np.array([{"synthetic": True}], dtype=object))
    with pytest.raises(ValueError):
        load_pair(*synthetic_pair)


def test_mismatched_reference_rejected(synthetic_pair):
    np.save(synthetic_pair[1], np.zeros((1, 32, 32), dtype=np.uint8))
    with pytest.raises(ValueError, match="reference shape"):
        load_pair(*synthetic_pair)

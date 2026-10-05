"""Synthetic native-DN boundary and flag tests; cells/mL remains blocked."""

import numpy as np
import pytest

from aquavision.data.labels import inspect_reference, to_cells_per_ml

UNITS = "processed_cyan_digital_number"


def test_native_bin_boundaries_preserve_original():
    values = np.array([0, 99, 100, 199, 200, 253, 254, 255], dtype=np.uint8)
    original = values.copy()
    result = inspect_reference(values, units=UNITS)
    np.testing.assert_array_equal(result["bins"], [0, 0, 1, 1, 2, 2, -1, -1])
    np.testing.assert_array_equal(values, original)
    assert result["no_detection"].sum() == 1
    assert result["land"].sum() == result["masked"].sum() == 1


def test_invalid_values_never_become_low_risk():
    values = np.array([np.nan, np.inf, -1, 256, 0.5, 99.5, -np.inf])
    result = inspect_reference(values, units=UNITS)
    assert result["invalid"].all()
    assert (result["bins"] == -1).all()


def test_configurable_native_edges():
    result = inspect_reference([49, 50, 149, 150], units=UNITS, bin_edges=(50, 150))
    np.testing.assert_array_equal(result["bins"], [0, 1, 1, 2])


@pytest.mark.parametrize("edges", [(200, 100), (0, 200), (100, 254), (100,), (100.1, 200)])
def test_invalid_edges_rejected(edges):
    with pytest.raises(ValueError):
        inspect_reference([10], units=UNITS, bin_edges=edges)


def test_units_cannot_be_assumed():
    with pytest.raises(ValueError, match="conversion is blocked"):
        inspect_reference([20000], units="cells/mL")
    with pytest.raises(NotImplementedError, match="not verified"):
        to_cells_per_ml([100])


def test_empty_reference():
    assert inspect_reference(np.array([], dtype=np.uint8), units=UNITS)["valid"].sum() == 0

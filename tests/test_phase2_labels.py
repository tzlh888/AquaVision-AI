"""Synthetic unit data only; these tests never validate an empirical calibration."""

import numpy as np
import pytest

from aquavision.data.labels import aggregate_native_reference, inspect_reference, to_cells_per_ml


@pytest.mark.parametrize("value", [19999,20000,20001,99999,100000,100001])
def test_requested_cell_boundaries_remain_blocked(value):
    # Required boundary values must NOT be accidentally accepted as archive DN.
    with pytest.raises(NotImplementedError, match="not verified"):
        to_cells_per_ml(value)
    result = inspect_reference([value], units="processed_cyan_digital_number")
    assert result["invalid"].all()


def test_aggregation_sensitivity_and_raw_preservation():
    raw = np.array([[0,0,0],[0,0,0],[0,100,200]],dtype=np.uint8)
    copy=raw.copy()
    result=aggregate_native_reference(raw)
    assert result["median_dn_bin"] == result["majority_bin"] == 0
    assert result["max_dn_bin"] == result["upper_quantile_dn_bin"] == 2
    assert result["fraction_valid_dn_ge_100"] == pytest.approx(2/9)
    assert result["fraction_valid_dn_ge_200"] == pytest.approx(1/9)
    assert result["final_risk_class"] == "UNKNOWN"
    np.testing.assert_array_equal(raw,copy)


def test_flags_and_nan_excluded_from_aggregation():
    raw=np.array([[0,100,200],[254,255,np.nan],[np.inf,-1,0.5]])
    result=aggregate_native_reference(raw)
    assert result["valid_pixels"] == 3
    assert result["masked_pixels"] == result["land_flag_pixels"] == 1
    assert result["invalid_pixels"] == 4
    assert result["mean_dn"] == 100
    assert result["majority_bin"] is None  # tied counts cannot select a favored class
    assert result["center_consensus_bin"] is None


def test_no_valid_pixels_does_not_become_bin_zero():
    result=aggregate_native_reference([[255,254],[np.nan,255]])
    for key in ("median_dn","mean_dn","max_dn","majority_bin","upper_quantile_dn","center_consensus_bin"):
        assert result[key] is None
    assert result["valid_reference_fraction"] == 0


def test_even_center_uses_four_pixels_and_requires_consensus():
    result=aggregate_native_reference([[0,0],[100,100]])
    assert result["center_raw_dn"] == [0,0,100,100]
    assert result["center_consensus_bin"] is None
    assert result["majority_status"] == "tie_or_no_valid_data"


@pytest.mark.parametrize("bad", [[],[1,2],np.zeros((2,3,4)),np.array([[1+2j]])])
def test_bad_reference_layout_or_type_rejected(bad):
    with pytest.raises(ValueError):aggregate_native_reference(bad)


@pytest.mark.parametrize("q", [-0.1,1.1,float('nan')])
def test_invalid_quantile_rejected(q):
    with pytest.raises(ValueError):aggregate_native_reference([[0]],quantile=q)

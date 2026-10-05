"""All invented geography below is explicitly SYNTHETIC UNIT-TEST DATA."""

import pytest

from aquavision.data.geography import adjacent_components, temporal_summary, require_verified_geography


def sample(tile,x,y,day):
    return {"sen2_member":f"{tile}_X{x:04d}_Y{y:04d}_S050_2019_01_{day:02d}_x0_y0_64x64_1_sen2.npy"}


def test_adjacent_chain_and_diagonal_stay_in_one_component():
    rows=[sample("6_2",0,0,1),sample("6_2",50,50,2),sample("6_2",100,50,3),sample("6_2",300,300,4)]
    groups=adjacent_components(rows)
    assert len(set(groups.values())) == 2
    assert groups["6_2_X0000_Y0000_S050"] == groups["6_2_X0100_Y0050_S050"]
    assert groups == adjacent_components(rows[::-1])


def test_different_dates_share_parent_group_but_other_tiles_not_inferred():
    rows=[sample("6_2",0,0,1),sample("6_2",0,0,2),sample("7_2",0,0,1)]
    groups=adjacent_components(rows)
    assert len(groups) == 2 and len(set(groups.values())) == 2


def test_temporal_density_counts_dates_not_patches():
    rows=[{"location":"synthetic_lake","acquisition_date":d} for d in ["2019-01-01","2019-01-01","2019-01-11"]]
    result=temporal_summary(rows,"location")[0]
    assert result["sample_count"] == 3 and result["unique_dates"] == 2
    assert result["same_group_date_extra_samples"] == 1
    assert result["min_gap_days"] == result["median_gap_days"] == 10
    assert result["observed_dates_per_30_days"] == pytest.approx(60/11)


def test_unknown_location_cannot_count_as_one_lake():
    with pytest.raises(ValueError):temporal_summary([{"location":"UNKNOWN","acquisition_date":"2019-01-01"}],"location")


def test_candidate_identity_is_not_verified_geography():
    with pytest.raises(ValueError,match="not VERIFIED"):require_verified_geography({"geography_status":"UNVERIFIED"})
    with pytest.raises(ValueError,match="spatial_group_id"):
        require_verified_geography({"geography_status":"VERIFIED","spatial_group_id":"candidate_component:a"})

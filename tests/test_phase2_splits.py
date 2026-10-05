"""Synthetic split records only; no real dataset partition is generated here."""

from copy import deepcopy
import json

import pytest

from aquavision.data.splits import geographic_partition, random_partition, validate_partition, freeze_partition


@pytest.fixture
def synthetic_rows():
    return [{"sample_id":f"synthetic_{g}_{c}_{i}", "class_id":c, "label_status":"VERIFIED",
             "geography_status":"VERIFIED", "geography_evidence":"SYNTHETIC TEST ONLY",
             "spatial_group_id":g,"waterbody_ids":[f"synthetic_lake_{g}"],
             "footprint_id":f"synthetic_footprint_{g}_{i}","latitude":0.0,"longitude":0.0}
            for g in ["A","B","C"] for c in range(3) for i in range(10)]


def test_no_group_or_waterbody_overlap_in_geographic_split(synthetic_rows):
    mapping={"A":"train","B":"validation","C":"test"}
    split=geographic_partition(synthetic_rows,mapping)
    validate_partition(synthetic_rows,split)
    train={r["spatial_group_id"] for r in synthetic_rows if split[r["sample_id"]]=="train"}
    test={r["spatial_group_id"] for r in synthetic_rows if split[r["sample_id"]]=="test"}
    assert not train.intersection(test)
    assert geographic_partition(synthetic_rows[::-1],mapping)==split


def test_same_lake_in_different_groups_is_rejected(synthetic_rows):
    synthetic_rows[-1]["waterbody_ids"]=["synthetic_lake_C","synthetic_lake_A"]
    with pytest.raises(ValueError,match="waterbody_ids"):
        geographic_partition(synthetic_rows,{"A":"train","B":"validation","C":"test"})


def test_same_footprint_at_different_dates_cannot_cross_splits(synthetic_rows):
    synthetic_rows[-1]["footprint_id"]=synthetic_rows[0]["footprint_id"]
    with pytest.raises(ValueError,match="footprint_id"):
        geographic_partition(synthetic_rows,{"A":"train","B":"validation","C":"test"})


def test_group_leakage_rejected(synthetic_rows):
    split=geographic_partition(synthetic_rows,{"A":"train","B":"validation","C":"test"})
    split[synthetic_rows[0]["sample_id"]]="test"
    with pytest.raises(ValueError,match="spatial_group_id"):validate_partition(synthetic_rows,split)


def test_random_stratification_deterministic_and_counts(synthetic_rows):
    split=random_partition(synthetic_rows,seed=42)
    assert split==random_partition(synthetic_rows[::-1],seed=42)
    for c in range(3):
        counts={s:sum(r["class_id"]==c and split[r["sample_id"]]==s for r in synthetic_rows) for s in ("train","validation","test")}
        assert counts=={"train":24,"validation":3,"test":3}


@pytest.mark.parametrize("change", [{"label_status":"UNVERIFIED"},{"geography_status":"UNVERIFIED"},{"waterbody_ids":[]},{"latitude":float('nan')}])
def test_unverified_or_missing_metadata_fails_closed(synthetic_rows,change):
    synthetic_rows[0].update(change)
    with pytest.raises(ValueError):random_partition(synthetic_rows)


def test_duplicate_missing_and_inadequate_class_support_rejected(synthetic_rows):
    with pytest.raises(ValueError,match="Duplicate"):random_partition(synthetic_rows+[deepcopy(synthetic_rows[0])])
    with pytest.raises(ValueError,match="ten samples"):random_partition(synthetic_rows[:3])
    split=geographic_partition(synthetic_rows,{"A":"train","B":"validation","C":"test"})
    split.pop(synthetic_rows[0]["sample_id"])
    with pytest.raises(ValueError,match="every eligible sample"):validate_partition(synthetic_rows,split)


def test_frozen_split_cannot_be_overwritten(synthetic_rows,tmp_path):
    split=geographic_partition(synthetic_rows,{"A":"train","B":"validation","C":"test"})
    path=tmp_path/"synthetic_split.json"
    freeze_partition(path,synthetic_rows,split,protocol={"scope":"synthetic_test"})
    data=json.loads(path.read_text());assert len(data["metadata_sha256"])==64
    with pytest.raises(FileExistsError):freeze_partition(path,synthetic_rows,split,protocol={"scope":"synthetic_test"})

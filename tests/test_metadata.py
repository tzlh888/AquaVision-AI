"""Synthetic filenames and ZIP directories; no invented research geography."""

import io
import zipfile

import pytest

from aquavision.data.metadata import build_inventory, parse_member, select_inspection_pairs

NAME = "6_2/6_2_X0650_Y0900_S050_2019_04_19_x0_y512_64x64_5_sen2.npy"


def test_parse_grid_metadata_without_fabricating_coordinates():
    result = parse_member(NAME)
    assert result["acquisition_date"] == "2019-04-19"
    assert result["spatial_group_candidate"] == "6_2_X0650_Y0900_S050"
    assert result["patch_row"] == 0 and result["patch_col"] == 512
    assert result["latitude"] is result["longitude"] is result["water_body_id"] is None


@pytest.mark.parametrize("name", ["../" + NAME, "/" + NAME, "unknown.npy", NAME.replace("04_19", "02_30")])
def test_bad_names_rejected(name):
    with pytest.raises(ValueError):
        parse_member(name)


def test_inventory_pairs_by_id_not_archive_order(synthetic_zip):
    with zipfile.ZipFile(io.BytesIO(synthetic_zip)) as archive:
        members, pairs, summary = build_inventory(archive)
    assert len(members) == 2 and len(pairs) == 1
    assert summary["paired_samples"] == 1
    assert not summary["unpaired_sample_ids"]


def test_unpaired_reference_reported():
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        archive.writestr(NAME, b"synthetic test bytes")
    with zipfile.ZipFile(data) as archive:
        _, pairs, summary = build_inventory(archive)
    assert not pairs
    assert len(summary["unpaired_sample_ids"]) == 1


def test_selection_is_bounded_and_deterministic():
    rows = [{"sample_id": f"synthetic_{i:02d}"} for i in range(12)]
    assert select_inspection_pairs(rows, 4) == [rows[i] for i in [0, 3, 7, 11]]
    assert select_inspection_pairs(rows[::-1], 4) == select_inspection_pairs(rows, 4)
    with pytest.raises(ValueError):
        select_inspection_pairs(rows, 9)

"""Generate Phase 3A-1 evidence catalogs without inventing geographic identity."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from phase3a1_audit import CANDIDATE, CONFIRMED, UNVERIFIED, verify_file


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SAMPLE_PATTERN = re.compile(
    r"^(?P<parent>\d_\d_X\d{4}_Y\d{4}_S\d{3})_(?P<year>\d{4})_(?P<month>\d{2})_(?P<day>\d{2})_x(?P<row>\d+)_y(?P<col>\d+)_(?P<size>\d+)x(?P=size)_(?P<index>\d+)$"
)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"Refusing to write empty evidence table: {path.name}")
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    selection = json.loads((ROOT / "data/metadata/phase3_5/geographic_split_v2.json").read_text())
    split_rows = read_csv(ROOT / "data/metadata/phase3_5/geographic_split_v2.csv")
    split = {row["sample_id"]: row for row in split_rows}
    census = {
        row["sample_id"]: row
        for row in read_csv(ROOT / "data/metadata/phase3_5/reference_census_round2.csv")
    }

    patch_rows = []
    scene_rows = []
    waterbody_rows = []
    for row in sorted(selection["samples"], key=lambda item: item["sample_id"]):
        match = SAMPLE_PATTERN.fullmatch(row["sample_id"])
        if not match:
            raise ValueError(f"Unexpected frozen sample ID: {row['sample_id']}")
        parsed = match.groupdict()
        date_value = f"{parsed['year']}-{parsed['month']}-{parsed['day']}"
        parent = parsed["parent"]
        relative_window = (
            f"row[{parsed['row']}:{int(parsed['row']) + int(parsed['size'])}),"
            f"col[{parsed['col']}:{int(parsed['col']) + int(parsed['size'])})"
        )
        candidate_cyan = (
            f"L{parsed['year']}DDD.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m_"
            f"{row['tile']}.tif"
        )
        common = {
            "sample_id": row["sample_id"],
            "split": split[row["sample_id"]]["split"],
            "acquisition_date": date_value,
            "cyan_tile_id": row["tile"],
            "author_parent_id": parent,
            "author_component_id": split[row["sample_id"]]["spatial_group_id"],
            "relative_pixel_window": relative_window,
            "patch_size_pixels": parsed["size"],
            "sentinel_sha256": row["sen2_sha256"],
            "sentinel_artifact_status": verify_file(ROOT / row["sen2_path"], row["sen2_sha256"]),
            "cyan_sha256": row["cyan_sha256"],
            "cyan_artifact_status": verify_file(ROOT / row["cyan_path"], row["cyan_sha256"]),
        }
        patch_rows.append(
            {
                **common,
                "sentinel_product_id": "",
                "sentinel_product_status": UNVERIFIED,
                "sentinel_acquisition_timestamp": "",
                "timestamp_status": UNVERIFIED,
                "scene_id": "",
                "scene_status": UNVERIFIED,
                "mgrs_tile_id": "",
                "mgrs_status": UNVERIFIED,
                "original_crs": "",
                "crs_status": UNVERIFIED,
                "source_affine_transform": "",
                "affine_status": UNVERIFIED,
                "original_crop_window": "",
                "crop_window_status": UNVERIFIED,
                "patch_footprint_wkt": "",
                "footprint_status": UNVERIFIED,
                "waterbody_id": "",
                "waterbody_status": UNVERIFIED,
                "waterbody_geometry": "",
                "cyan_product_candidate": candidate_cyan,
                "cyan_product_status": CANDIDATE,
                "cyan_processing_version": "",
                "cyan_version_status": UNVERIFIED,
                "matchup_status": CANDIDATE,
                "evidence_note": "date, author-grid IDs, relative crop offsets and exact arrays verified; data.json/UUID/transform absent",
            }
        )
        scene_rows.append(
            {
                "sample_id": row["sample_id"],
                "split": common["split"],
                "date_only": date_value,
                "author_parent_id": parent,
                "candidate_processing_run_group": f"{parent}|{date_value}",
                "processing_run_group_status": CANDIDATE,
                "stac_endpoint": "https://stac.dataspace.copernicus.eu/v1/",
                "stac_collection": "sentinel-2-l2a",
                "stac_query_status": "BLOCKED_MISSING_CONFIRMED_GEOMETRY",
                "candidate_product_count": "",
                "candidate_product_ids": "",
                "historical_product_id": "",
                "scene_status": UNVERIFIED,
                "reason": "date-only STAC search is non-identifying; historical sen2_uuid and window were discarded",
            }
        )
        waterbody_rows.append(
            {
                "sample_id": row["sample_id"],
                "split": common["split"],
                "author_parent_id": parent,
                "patch_footprint_wkt": "",
                "footprint_status": UNVERIFIED,
                "waterbody_id": "",
                "waterbody_name": "",
                "waterbody_geometry_source": "",
                "waterbody_geometry_version": "",
                "waterbody_status": UNVERIFIED,
                "hydrography_query_status": "BLOCKED_MISSING_CONFIRMED_FOOTPRINT",
                "reason": "author-grid component is not a waterbody identity",
            }
        )

    support = read_csv(ROOT / "research_upgrade_v3/phase3a/HIGH_SUPPORT_BY_GROUP.csv")
    high_dates_by_group: dict[str, set[str]] = {}
    for census_row in census.values():
        if int(census_row["high_pixels"]) > 0:
            high_dates_by_group.setdefault(census_row["spatial_group_id"], set()).add(census_row["date"])
    candidates = []
    for row in support:
        if int(row["screened_high_pixels"]) <= 0:
            continue
        selected = row["v2_split"] != "NOT_SELECTED"
        candidates.append(
            {
                "candidate_id": row["geographic_group_id"],
                "source_scope": "LEGACY_ZENODO_DEPOSIT_ALREADY_LABEL_SCREENED",
                "cyan_tile_id": row["geographic_group_id"].split(":", 1)[1].split("_X", 1)[0],
                "waterbody_id": "",
                "waterbody_status": UNVERIFIED,
                "scene_id": "",
                "scene_status": UNVERIFIED,
                "acquisition_dates": "|".join(sorted(high_dates_by_group.get(row["geographic_group_id"], set()))),
                "high_date_count": row["screened_high_dates"],
                "footprint_wkt": "",
                "footprint_status": UNVERIFIED,
                "cyan_source": "processed CyAN CI_cyano DN; exact processing version unverified",
                "cyan_version_status": UNVERIFIED,
                "high_pixels": row["screened_high_pixels"],
                "high_patches": row["screened_high_patches"],
                "high_date_span_days": row["screened_high_date_span_days"],
                "data_license": "CC-BY-4.0 per frozen Zenodo record snapshot",
                "historical_overlap_status": "LEGACY_V2_SELECTED" if selected else "LEGACY_SCREENED_NOT_BLIND",
                "provenance_confidence": "CANDIDATE_AUTHOR_GRID_ONLY",
                "eligible_for_v3_validation": "NO",
                "eligible_for_confirmation": "NO",
                "rejection_reason": "missing verified waterbody/scene/footprint/CyAN version; label support already inspected",
            }
        )

    write_csv(OUT / "PATCH_IDENTITY_CATALOG.csv", patch_rows)
    write_csv(OUT / "SCENE_MATCHING_EVIDENCE.csv", scene_rows)
    write_csv(OUT / "WATERBODY_MATCHING_EVIDENCE.csv", waterbody_rows)
    write_csv(OUT / "INDEPENDENT_HIGH_CANDIDATES.csv", candidates)
    print(
        json.dumps(
            {
                "patch_rows": len(patch_rows),
                "sentinel_verified": sum(row["sentinel_artifact_status"] == "VERIFIED" for row in patch_rows),
                "confirmed_locations": sum(row["footprint_status"] == CONFIRMED for row in patch_rows),
                "confirmed_scenes": sum(row["scene_status"] == CONFIRMED for row in patch_rows),
                "confirmed_waterbodies": sum(row["waterbody_status"] == CONFIRMED for row in patch_rows),
                "high_candidates": len(candidates),
                "qualified_high_candidates": sum(row["eligible_for_v3_validation"] == "YES" for row in candidates),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

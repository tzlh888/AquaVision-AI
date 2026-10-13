"""Run the bounded six-product CyAN label-integration pilot. No model code."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from cyan_label_integration import (
    LAND_VALUE,
    NODATA_VALUE,
    PatchSpec,
    count_classes,
    integrate_patch,
    native_values_for_polygon,
    product_date,
    sha256_file,
    utc_now,
)


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[1]
PHASE3A2 = HERE.parent / "phase3a2"
RAW_DIR = REPOSITORY / "data" / "raw" / "final_label_pilot" / "cyan"
PROCESSED_DIR = REPOSITORY / "data" / "processed" / "final_label_pilot"
CATALOG_PATH = PHASE3A2 / "V3_METADATA_CATALOG.csv"
PHASE3A2_MANIFEST_PATH = PHASE3A2 / "V3_DATA_PROVENANCE_MANIFEST.json"

OFFICIAL_SEARCH_URL = "https://oceandata.sci.gsfc.nasa.gov/api/cyan_file_search"
OFFICIAL_GETFILE_ROOT = "https://oceandata.sci.gsfc.nasa.gov/getfile/"
V6_DOCUMENTATION = (
    "https://oceancolor.gsfc.nasa.gov/images/cyan/version/6/"
    "CyAN_NASA_MERISOLCI_CI_release_notes_V6_Aug_2025.pdf"
)


def _write_csv_atomic(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("Cannot write an empty High-support audit")
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _save_npz_atomic(path: Path, **arrays: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    os.replace(temporary, path)


def _count_dn(values: np.ndarray) -> dict[str, int]:
    classes = count_classes(values)
    classes["land"] = int(np.sum(values == LAND_VALUE))
    classes["nodata"] = int(np.sum(values == NODATA_VALUE))
    classes["valid"] = classes["low"] + classes["moderate"] + classes["high"]
    classes["total"] = int(values.size)
    return classes


def _download_timestamp(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def main() -> None:
    with CATALOG_PATH.open(newline="", encoding="utf-8") as handle:
        candidates = list(csv.DictReader(handle))
    if len(candidates) != 6:
        raise ValueError(f"Expected exactly six frozen candidates, got {len(candidates)}")
    if len({row["scene_id"] for row in candidates}) != 6:
        raise ValueError("Frozen candidates must contain six unique Sentinel scenes")
    if len({row["waterbody_id"] for row in candidates}) != 3:
        raise ValueError("Frozen candidates must contain three waterbody groups")

    expected_products = {row["cyan_product_id"] for row in candidates}
    actual_products = {path.name for path in RAW_DIR.glob("*.tif")}
    if expected_products != actual_products:
        raise ValueError(
            f"Raw product set differs from frozen set; missing={sorted(expected_products - actual_products)}, "
            f"extra={sorted(actual_products - expected_products)}"
        )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    preliminary: list[dict[str, Any]] = []
    product_manifest: list[dict[str, Any]] = []
    processed_hashes: dict[str, str] = {}

    for candidate in candidates:
        product_path = RAW_DIR / candidate["cyan_product_id"]
        if product_date(product_path.name).isoformat() != candidate["acquisition_timestamp"][:10]:
            raise ValueError(f"Date mismatch for {candidate['candidate_id']}")
        patch = PatchSpec(
            crs=candidate["scene_crs"],
            transform=tuple(json.loads(candidate["patch_affine"])),
            width=int(candidate["patch_width"]),
            height=int(candidate["patch_height"]),
        )
        result = integrate_patch(product_path, patch)
        metadata = result["metadata"]
        if metadata.processing_version != "6.0":
            raise ValueError(
                f"Frozen product {metadata.product_id} is not confirmed OBPG version 6.0"
            )
        native_values = result["native_values"]
        nearest_values = result["nearest_values"]
        native = _count_dn(native_values)
        nearest = _count_dn(nearest_values)
        bilinear_classes = result["bilinear_classes"]
        bilinear_valid = int(np.sum(bilinear_classes >= 0))
        sensitivity_counts = []
        for shift_x, shift_y in (
            (0.0, 0.0),
            (-10.0, 0.0),
            (10.0, 0.0),
            (0.0, -10.0),
            (0.0, 10.0),
            (-10.0, -10.0),
            (10.0, 10.0),
        ):
            shifted_polygon = [
                (x + shift_x, y + shift_y) for x, y in result["patch_polygon_albers"]
            ]
            _, shifted_values = native_values_for_polygon(
                product_path, metadata.grid, shifted_polygon
            )
            sensitivity_counts.append(_count_dn(shifted_values))

        output_name = candidate["candidate_id"] + "__cyan_labels.npz"
        output_path = PROCESSED_DIR / output_name
        trace = {
            "candidate_id": candidate["candidate_id"],
            "scene_id": candidate["scene_id"],
            "waterbody_id": candidate["waterbody_id"],
            "cyan_product_id": metadata.product_id,
            "cyan_source_sha256": metadata.sha256,
            "cyan_processing_version": metadata.processing_version,
            "sentinel_patch_crs": patch.crs,
            "sentinel_patch_affine": list(patch.transform),
            "primary_support_rule": "native CyAN 300 m cell centers inside Sentinel patch polygon",
            "label_resampling": "nearest neighbor on source DN, then frozen class mapping",
            "bilinear_role": "diagnostic only; interpolate valid DN before class mapping",
        }
        _save_npz_atomic(
            output_path,
            source_dn_nearest=np.asarray(nearest_values, dtype=np.uint8),
            class_nearest=np.asarray(result["nearest_classes"], dtype=np.int8),
            source_dn_bilinear=np.asarray(result["bilinear_values"], dtype=np.float32),
            class_bilinear=np.asarray(bilinear_classes, dtype=np.int8),
            native_center_dn=np.asarray(native_values, dtype=np.uint8),
            native_center_row_col=np.asarray(result["native_indices"], dtype=np.int32),
            patch_polygon_albers=np.asarray(result["patch_polygon_albers"], dtype=np.float64),
            traceability_json=np.asarray(json.dumps(trace, sort_keys=True)),
        )
        output_relative = output_path.relative_to(REPOSITORY).as_posix()
        processed_hash = sha256_file(output_path)
        processed_hashes[output_relative] = processed_hash

        preliminary.append(
            {
                "candidate_id": candidate["candidate_id"],
                "waterbody_id": candidate["waterbody_id"],
                "waterbody_name": candidate["waterbody_name"],
                "independent_group_id": candidate["waterbody_id"],
                "scene_id": candidate["scene_id"],
                "sentinel_acquisition_timestamp": candidate["acquisition_timestamp"],
                "sentinel_patch_crs": candidate["scene_crs"],
                "sentinel_patch_affine": candidate["patch_affine"],
                "sentinel_patch_geometry_native_wkt": candidate[
                    "patch_geometry_native_wkt"
                ],
                "cyan_product_id": metadata.product_id,
                "cyan_processing_version": metadata.processing_version,
                "cyan_sha256": metadata.sha256,
                "cyan_crs": metadata.crs_equivalent,
                "cyan_resolution_m": metadata.grid.pixel_size_x,
                "temporal_match_days": candidate["temporal_match_days"],
                "native_center_pixels_total": native["total"],
                "native_center_pixels_valid": native["valid"],
                "native_center_low": native["low"],
                "native_center_moderate": native["moderate"],
                "native_center_high": native["high"],
                "native_center_land": native["land"],
                "native_center_nodata": native["nodata"],
                "sensitivity_shift_m": 10,
                "native_center_total_sensitivity_min": min(
                    count["total"] for count in sensitivity_counts
                ),
                "native_center_total_sensitivity_max": max(
                    count["total"] for count in sensitivity_counts
                ),
                "native_high_sensitivity_min": min(
                    count["high"] for count in sensitivity_counts
                ),
                "native_high_sensitivity_max": max(
                    count["high"] for count in sensitivity_counts
                ),
                "scene_high_status_stable_under_10m_shift": str(
                    len({count["high"] > 0 for count in sensitivity_counts}) == 1
                ).lower(),
                "nearest_target_pixels_total": nearest["total"],
                "nearest_target_pixels_valid": nearest["valid"],
                "nearest_target_low": nearest["low"],
                "nearest_target_moderate": nearest["moderate"],
                "nearest_target_high": nearest["high"],
                "nearest_target_land": nearest["land"],
                "nearest_target_nodata": nearest["nodata"],
                "nearest_valid_coverage": round(nearest["valid"] / nearest["total"], 8),
                "bilinear_comparable_target_pixels": result[
                    "bilinear_comparable_pixels"
                ],
                "bilinear_valid_target_pixels": bilinear_valid,
                "bilinear_class_disagreement_pixels": result[
                    "bilinear_class_disagreement_pixels"
                ],
                "scene_contains_high": str(native["high"] > 0).lower(),
                "processed_label_path": output_relative,
                "processed_label_sha256": processed_hash,
            }
        )
        product_manifest.append(
            {
                "product_id": metadata.product_id,
                "source_url": OFFICIAL_GETFILE_ROOT + metadata.product_id,
                "search_url": OFFICIAL_SEARCH_URL,
                "search_parameters": {
                    "region": 1,
                    "wgetflag": 1,
                    "period": 2,
                    "product": 1,
                    "areaids": "all",
                    "sdate": metadata.acquisition_date,
                    "edate": metadata.acquisition_date,
                    "addurl": 1,
                    "results_as_file": 1,
                },
                "acquisition_or_compositing_date": metadata.acquisition_date,
                "period": "daily",
                "processing_version": metadata.processing_version,
                "processing_version_evidence": "GeoTIFF GDALMetadata OBPG_version",
                "native_crs": metadata.crs_name,
                "crs_equivalent": metadata.crs_equivalent,
                "crs_authority_embedded": False,
                "crs_evidence": {
                    "geokey_directory": list(metadata.geokey_directory),
                    "albers_parameters": list(metadata.albers_parameters),
                },
                "native_affine": [
                    metadata.grid.pixel_size_x,
                    0.0,
                    metadata.grid.origin_x,
                    0.0,
                    metadata.grid.pixel_size_y,
                    metadata.grid.origin_y,
                ],
                "native_resolution_m": metadata.grid.pixel_size_x,
                "shape": [metadata.height, metadata.width],
                "data_type": metadata.dtype,
                "samples_per_pixel": metadata.samples_per_pixel,
                "bits_per_sample": metadata.bits_per_sample,
                "photometric_interpretation": "palette_index",
                "compression": "LZW",
                "variable": "CI_cyano",
                "valid_data_range": [0, 253],
                "land_value": LAND_VALUE,
                "nodata_value": NODATA_VALUE,
                "sha256": metadata.sha256,
                "byte_size": metadata.byte_size,
                "downloaded_at_utc": _download_timestamp(product_path),
                "local_relative_path": product_path.relative_to(REPOSITORY).as_posix(),
                "authentication": "Earthdata OAuth browser session; no credential retained",
                "documentation": V6_DOCUMENTATION,
            }
        )

    group_records: list[dict[str, Any]] = []
    for group_id in sorted({row["independent_group_id"] for row in preliminary}):
        members = [row for row in preliminary if row["independent_group_id"] == group_id]
        dates = sorted(
            datetime.fromisoformat(row["sentinel_acquisition_timestamp"].replace("Z", "+00:00"))
            for row in members
        )
        high_patch_count = sum(int(row["native_center_high"] > 0) for row in members)
        high_scene_count = high_patch_count
        high_native_pixels = sum(int(row["native_center_high"]) for row in members)
        high_native_sensitivity_min = sum(
            int(row["native_high_sensitivity_min"]) for row in members
        )
        high_native_sensitivity_max = sum(
            int(row["native_high_sensitivity_max"]) for row in members
        )
        date_span = (dates[-1].date() - dates[0].date()).days if len(dates) > 1 else 0
        qualified = (
            len(dates) >= 2
            and date_span >= 30
            and high_patch_count >= 3
            and high_native_pixels >= 100
        )
        failures = []
        if len(dates) < 2:
            failures.append("fewer_than_2_dates")
        if date_span < 30:
            failures.append("date_span_below_30_days")
        if high_patch_count < 3:
            failures.append("fewer_than_3_high_patches")
        if high_native_pixels < 100:
            failures.append("fewer_than_100_native_high_pixels")
        group_records.append(
            {
                "independent_group_id": group_id,
                "waterbody_name": members[0]["waterbody_name"],
                "candidate_scenes": len(members),
                "date_span_days": date_span,
                "high_patch_count": high_patch_count,
                "high_scene_count": high_scene_count,
                "native_high_pixel_count": high_native_pixels,
                "native_high_pixel_sensitivity_min": high_native_sensitivity_min,
                "native_high_pixel_sensitivity_max": high_native_sensitivity_max,
                "waterbody_contains_high": high_patch_count > 0,
                "qualified_independent_high_unit": qualified,
                "qualification_failure": ";".join(failures),
            }
        )
        for row in members:
            row.update(
                {
                    "waterbody_contains_high": str(high_patch_count > 0).lower(),
                    "group_date_span_days": date_span,
                    "group_high_patch_count": high_patch_count,
                    "group_high_scene_count": high_scene_count,
                    "group_native_high_pixels": high_native_pixels,
                    "group_native_high_sensitivity_min": high_native_sensitivity_min,
                    "group_native_high_sensitivity_max": high_native_sensitivity_max,
                    "qualified_independent_high_unit": str(qualified).lower(),
                    "qualification_failure": ";".join(failures),
                }
            )

    high_support_path = HERE / "HIGH_SUPPORT_PILOT.csv"
    _write_csv_atomic(high_support_path, preliminary)
    phase3a2_manifest_sha = sha256_file(PHASE3A2_MANIFEST_PATH)
    payload = {
        "schema_version": "1.0",
        "generated_at_utc": utc_now(),
        "research_stage": "final bounded CyAN label integration pilot",
        "model_training_performed": False,
        "target_product_set_changed": False,
        "credentials_stored": False,
        "raw_files_git_ignored": True,
        "frozen_input": {
            "phase3a2_manifest": PHASE3A2_MANIFEST_PATH.relative_to(REPOSITORY).as_posix(),
            "phase3a2_manifest_sha256": phase3a2_manifest_sha,
            "candidate_catalog": CATALOG_PATH.relative_to(REPOSITORY).as_posix(),
            "candidate_catalog_sha256": sha256_file(CATALOG_PATH),
            "candidate_count": len(candidates),
            "waterbody_group_count": len(group_records),
        },
        "source_definition": {
            "provider": "NASA Ocean Biology Processing Group / CyAN",
            "search_url": OFFICIAL_SEARCH_URL,
            "processing_documentation": V6_DOCUMENTATION,
            "variable": "CI_cyano",
            "valid_data_range": [0, 253],
            "land_value": 254,
            "nodata_value": 255,
            "frozen_class_mapping": {
                "low": [0, 99],
                "moderate": [100, 199],
                "high": [200, 253],
                "invalid": [254, 255],
            },
        },
        "alignment_protocol": {
            "primary_support_unit": "native 300 m CyAN cell center inside Sentinel patch polygon",
            "target_grid": "original 64x64 Sentinel B05_20m patch grid",
            "discrete_resampling": "nearest neighbor source DN, then class mapping",
            "continuous_proxy_diagnostic": (
                "bilinear interpolation of four valid 0-253 source DN values, then class mapping; "
                "never used for qualification"
            ),
            "invalid_propagation": "bilinear result invalid if any of four neighbors is 254 or 255",
            "cloud_land_mask": "CyAN 254=land and 255=no-data/cloud/ice; both excluded",
            "qualification_counts": "native source pixels only; target-grid replication is not independent support",
        },
        "products": product_manifest,
        "group_support": group_records,
        "summary": {
            "products_downloaded": len(product_manifest),
            "products_version_confirmed": sum(
                product["processing_version"] == "6.0" for product in product_manifest
            ),
            "scenes_credibly_aligned": len(preliminary),
            "waterbody_groups_with_high": sum(
                bool(group["waterbody_contains_high"]) for group in group_records
            ),
            "qualified_independent_high_units": sum(
                bool(group["qualified_independent_high_unit"]) for group in group_records
            ),
        },
        "generated_artifact_sha256": {
            high_support_path.name: sha256_file(high_support_path),
            **processed_hashes,
            Path(__file__).name: sha256_file(Path(__file__)),
            "cyan_label_integration.py": sha256_file(HERE / "cyan_label_integration.py"),
        },
        "rebuild_command": (
            "PYTHONPATH=research_upgrade_v3/final_label_pilot "
            "python3 research_upgrade_v3/final_label_pilot/run_final_label_pilot.py"
        ),
    }
    _write_json_atomic(HERE / "CYAN_PRODUCT_MANIFEST.json", payload)
    print(json.dumps(payload["summary"], sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Screen the frozen authoritative waterbody pool on verified local CyAN V6 rasters."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FINAL_PILOT = HERE.parent / "final_label_pilot"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(FINAL_PILOT))

from phase3a3_audit import Grid, class_counts, rasterize_center_mask, sha256_file  # noqa: E402
from cyan_label_integration import read_cyan_metadata  # noqa: E402


QUERY_PATH = ROOT / "data" / "raw" / "phase3a3" / "usgs" / "frozen_candidate_identity_queries.json"
EXISTING_PATH = ROOT / "data" / "raw" / "phase3a3" / "usgs" / "existing_pilot_geometries.json"
CYAN_DIR = ROOT / "data" / "raw" / "final_label_pilot" / "cyan"
OUTPUT_DIR = ROOT / "data" / "processed" / "phase3a3"
OUTPUT_PATH = OUTPUT_DIR / "candidate_native_screen.json"


def _properties(feature: dict) -> dict:
    return {str(key).lower(): value for key, value in feature["properties"].items()}


def main() -> int:
    query_document = json.loads(QUERY_PATH.read_text(encoding="utf-8"))
    existing_document = json.loads(EXISTING_PATH.read_text(encoding="utf-8"))
    cyan_paths = sorted(CYAN_DIR.glob("*.tif"))
    if len(cyan_paths) != 6:
        raise ValueError(f"Expected six frozen CyAN inputs, found {len(cyan_paths)}")
    metadata = [read_cyan_metadata(path) for path in cyan_paths]
    first = metadata[0]
    grid = Grid(
        width=first.width,
        height=first.height,
        origin_x=first.grid.origin_x,
        origin_y=first.grid.origin_y,
        pixel_size=first.grid.pixel_size_x,
    )
    for item in metadata[1:]:
        if item.grid != first.grid or item.processing_version not in {"6.0", "V6"}:
            raise ValueError("CyAN grid/version mismatch")

    records: list[dict] = []
    inputs = list(query_document["results"])
    for result in existing_document["results"]:
        pilot = result["candidate"]
        result = dict(result)
        result["candidate"] = {
            "name": pilot["name"],
            "state_hint": "existing_final_label_pilot",
        }
        result["candidate_origin"] = "existing_final_label_pilot"
        inputs.append(result)

    for result in inputs:
        candidate = result["candidate"]
        features = result.get("payload", {}).get("features", [])
        base = {
            "candidate_name": candidate["name"],
            "state_hint": candidate["state_hint"],
            "identity_query_status": result.get("http_status"),
            "identity_query_error": result.get("error_type"),
            "feature_count": len(features),
            "screening_status": "IDENTITY_UNAVAILABLE",
            "source_query_sha256": result.get("response_sha256"),
            "candidate_origin": result.get("candidate_origin", "phase3a3_new_pool"),
        }
        if not features:
            records.append(base)
            continue
        props = [_properties(feature) for feature in features]
        names = {prop.get("gnis_name") for prop in props}
        if names != {candidate["name"]}:
            base["screening_status"] = "IDENTITY_NAME_MISMATCH"
            records.append(base)
            continue
        geometries = [feature["geometry"] for feature in features]
        mask, (row0, row1, col0, col1) = rasterize_center_mask(geometries, grid)
        date_support: list[dict] = []
        output_arrays: dict[str, np.ndarray] = {}
        for path, item in zip(cyan_paths, metadata):
            with Image.open(path) as image:
                crop = np.asarray(image.crop((col0, row0, col1, row1)), dtype=np.uint8)
            counts = class_counts(crop, mask)
            counts["high_if_threshold_199"] = int(
                np.sum(mask & (crop >= 199) & (crop <= 253))
            )
            counts["high_if_threshold_201"] = int(
                np.sum(mask & (crop >= 201) & (crop <= 253))
            )
            high_local_rows, high_local_cols = np.where(mask & (crop >= 200) & (crop <= 253))
            high_rows = high_local_rows.astype(np.int32) + row0
            high_cols = high_local_cols.astype(np.int32) + col0
            output_arrays[f"{item.product_id}__rows"] = high_rows
            output_arrays[f"{item.product_id}__cols"] = high_cols
            date_support.append(
                {
                    "product_id": item.product_id,
                    "acquisition_date": item.acquisition_date,
                    "processing_version": item.processing_version,
                    "raw_sha256": item.sha256,
                    **counts,
                }
            )
        waterbody_id = str(props[0].get("gnis_id") or props[0].get("permanent_identifier"))
        safe_id = waterbody_id.replace("{", "").replace("}", "").replace("-", "")
        array_path = OUTPUT_DIR / f"native_high_{safe_id}.npz"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(array_path, **output_arrays)
        base.update(
            {
                "screening_status": "SCREENED",
                "waterbody_id": waterbody_id,
                "gnis_id": props[0].get("gnis_id"),
                "permanent_identifiers": sorted(
                    str(prop.get("permanent_identifier")) for prop in props
                ),
                "nhdplus_ids": sorted(str(prop.get("nhdplusid")) for prop in props),
                "area_sq_km_sum": sum(float(prop.get("areasqkm", 0.0)) for prop in props),
                "native_bbox": [row0, row1, col0, col1],
                "mask_native_pixel_count": int(np.sum(mask)),
                "geometry_sha256": __import__("hashlib").sha256(
                    json.dumps(geometries, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest(),
                "native_high_array_path": str(array_path.relative_to(ROOT)),
                "native_high_array_sha256": sha256_file(array_path),
                "date_support": date_support,
            }
        )
        records.append(base)

    document = {
        "schema_version": "phase3a3-native-screen-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "design": "high-enriched; not prevalence representative",
        "uses_model_predictions": False,
        "new_cyan_downloads": 0,
        "cyan_input_bytes": sum(path.stat().st_size for path in cyan_paths),
        "cyan_products": [
            {
                "product_id": item.product_id,
                "date": item.acquisition_date,
                "version": item.processing_version,
                "sha256": item.sha256,
            }
            for item in metadata
        ],
        "records": records,
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    screened = [record for record in records if record["screening_status"] == "SCREENED"]
    print(
        json.dumps(
            {
                "candidate_count": len(records),
                "screened": len(screened),
                "with_high_on_any_date": sum(
                    any(day["high"] for day in record["date_support"]) for record in screened
                ),
                "output": str(OUTPUT_PATH),
                "sha256": sha256_file(OUTPUT_PATH),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

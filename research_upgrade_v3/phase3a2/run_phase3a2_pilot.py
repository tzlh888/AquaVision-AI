"""Run the bounded Phase 3A-2 metadata-first pilot.

This script queries official metadata services and writes catalogs/manifests. It
does not download Sentinel imagery, does not obtain CyAN raster bytes, and has
no model fitting, prediction, threshold tuning, or legacy-test access.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from phase3a2_audit import (
    EvidenceLevel,
    canonical_json_sha256,
    cyan_filename_for_date,
    derive_contained_patch,
    grid_from_stac_item,
    parse_utc,
    patch_corners,
    representative_point,
    sha256_bytes,
    temporal_match_days,
    validate_waterbody_feature,
)


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "phase3a2_pilot_config.json"
CATALOG_PATH = ROOT / "V3_METADATA_CATALOG.csv"
IDENTITY_PATH = ROOT / "V3_GEOGRAPHIC_IDENTITY.csv"
HIGH_PATH = ROOT / "V3_HIGH_SUPPORT_AUDIT.csv"
MANIFEST_PATH = ROOT / "V3_DATA_PROVENANCE_MANIFEST.json"
TIMEOUT_SECONDS = 30


class SourceError(RuntimeError):
    pass


def request_json(
    session: requests.Session,
    method: str,
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    body: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        response = session.request(
            method,
            url,
            params=params,
            json=body,
            timeout=TIMEOUT_SECONDS,
            headers={"Accept": "application/geo+json, application/json"},
        )
    except requests.RequestException as exc:
        raise SourceError(f"Official source request failed after bounded retries: {url}") from exc
    if response.status_code != 200:
        raise SourceError(f"{url} returned HTTP {response.status_code}")
    try:
        data = response.json()
    except ValueError as exc:
        raise SourceError(f"{url} did not return JSON") from exc
    if isinstance(data, dict) and data.get("error"):
        raise SourceError(f"{url} returned an ArcGIS error: {data['error']}")
    evidence = {
        "requested_url": response.request.url,
        "status_code": response.status_code,
        "content_type": response.headers.get("content-type"),
        "retrieved_at_utc": datetime.now().astimezone().isoformat(),
        "raw_sha256": sha256_bytes(response.content),
        "canonical_json_sha256": canonical_json_sha256(data),
        "bytes": len(response.content),
    }
    return data, evidence


def fetch_waterbody(
    session: requests.Session,
    source_url: str,
    expected: Mapping[str, Any],
    *,
    out_sr: int,
    simplification: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    data, evidence = request_json(
        session,
        "GET",
        f"{source_url}/query",
        params={
            "objectIds": expected["object_id"],
            "outFields": (
                "OBJECTID,PERMANENT_IDENTIFIER,GNIS_ID,GNIS_NAME,AREASQKM,"
                "FTYPE,FCODE,NHDPLUSID,VPUID"
            ),
            "returnGeometry": "true",
            "outSR": out_sr,
            "maxAllowableOffset": simplification,
            "geometryPrecision": 6 if out_sr == 4326 else 2,
            "f": "geojson",
        },
    )
    features = data.get("features", [])
    if len(features) != 1:
        raise SourceError("Expected exactly one USGS waterbody feature")
    validate_waterbody_feature(features[0], expected)
    evidence["source_crs"] = f"EPSG:{out_sr}"
    evidence["simplification_tolerance_source_units"] = simplification
    return features[0], evidence


def select_scene(
    session: requests.Session,
    stac_url: str,
    collection: str,
    point: tuple[float, float],
    window: Mapping[str, str],
    asset_name: str,
    maximum_cloud: float,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    body = {
        "collections": [collection],
        "intersects": {"type": "Point", "coordinates": list(point)},
        "datetime": f"{window['start_utc']}/{window['end_utc']}",
        "limit": 100,
    }
    search, search_evidence = request_json(
        session, "POST", f"{stac_url}/search", body=body
    )
    eligible: list[dict[str, Any]] = []
    for item in search.get("features", []):
        cloud = item.get("properties", {}).get("eo:cloud_cover")
        if not isinstance(cloud, (int, float)) or float(cloud) > maximum_cloud:
            continue
        if asset_name not in item.get("assets", {}):
            continue
        grid_from_stac_item(item, asset_name)
        eligible.append(item)
    if not eligible:
        raise SourceError(
            f"No eligible STAC scene for {window['window_id']} within cloud gate"
        )
    eligible.sort(
        key=lambda item: (
            float(item["properties"]["eo:cloud_cover"]),
            item["properties"]["datetime"],
            item["id"],
        )
    )
    selected_id = eligible[0]["id"]
    item, item_evidence = request_json(
        session,
        "GET",
        f"{stac_url}/collections/{collection}/items/{selected_id}",
    )
    grid_from_stac_item(item, asset_name)
    search_evidence.update(
        {
            "query_body": body,
            "returned_count": len(search.get("features", [])),
            "eligible_count": len(eligible),
            "selected_item": selected_id,
            "selection_key": [
                item["properties"]["eo:cloud_cover"],
                item["properties"]["datetime"],
                selected_id,
            ],
        }
    )
    return item, search_evidence, item_evidence


def fetch_cyan_listing(
    session: requests.Session, base_url: str, scene_datetime: str
) -> tuple[str, dict[str, Any]]:
    observed = parse_utc(scene_datetime)
    directory = observed.strftime("%d-%b-%Y")
    listing_url = f"{base_url}/{observed.year}/{directory}/"
    response = session.get(listing_url, timeout=TIMEOUT_SECONDS)
    if response.status_code != 200:
        raise SourceError(f"CyAN listing returned HTTP {response.status_code}")
    filenames = sorted(
        set(
            re.findall(
                r'href="https://oceandata\.sci\.gsfc\.nasa\.gov/getfile/([^"?]+)"',
                response.text,
            )
        )
    )
    expected = cyan_filename_for_date(scene_datetime)
    if expected not in filenames:
        raise SourceError(f"Expected daily CyAN product is absent: {expected}")
    file_url = f"https://oceandata.sci.gsfc.nasa.gov/getfile/{quote(expected)}"
    access = session.head(
        file_url,
        timeout=TIMEOUT_SECONDS,
        allow_redirects=False,
    )
    evidence = {
        "listing_url": listing_url,
        "listing_status_code": response.status_code,
        "listing_raw_sha256": sha256_bytes(response.content),
        "listing_semantic_sha256": canonical_json_sha256(filenames),
        "listed_file_count": len(filenames),
        "target_filename": expected,
        "target_present": True,
        "file_url": file_url,
        "bounded_access_method": "HEAD",
        "bounded_access_status_code": access.status_code,
        "bounded_access_location": access.headers.get("location", ""),
        "raster_bytes_retrieved": False,
        "access_disposition": "EARTHDATA_AUTHENTICATION_REQUIRED",
    }
    return expected, evidence


def patch_wkt(corners: tuple[tuple[float, float], ...]) -> str:
    closed = list(corners) + [corners[0]]
    return "POLYGON ((" + ", ".join(f"{x:.2f} {y:.2f}" for x, y in closed) + "))"


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    session = requests.Session()
    session.headers.update({"User-Agent": "AquaVision-Phase3A2-MetadataPilot/1.0"})
    retry = Retry(
        total=2,
        connect=2,
        read=2,
        status=2,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=None,
        raise_on_status=False,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))

    catalog_rows: list[dict[str, Any]] = []
    identity_rows: list[dict[str, Any]] = []
    high_rows: list[dict[str, Any]] = []
    source_evidence: list[dict[str, Any]] = []
    normalized_evidence: dict[str, Any] = {"waterbodies": {}, "scenes": {}}

    stac_url = config["sources"]["copernicus_stac"]
    usgs_url = config["sources"]["usgs_nhdplus_hr_waterbody"]
    cyan_url = config["sources"]["nasa_cyan_daily"]
    asset_name = config["sentinel_asset"]

    for waterbody in config["waterbodies"]:
        wgs_feature, wgs_evidence = fetch_waterbody(
            session,
            usgs_url,
            waterbody,
            out_sr=4326,
            simplification=0.0001,
        )
        wgs_point = representative_point(wgs_feature["geometry"])
        wgs_evidence.update(
            {
                "source_type": "USGS_NHDPLUS_HR_WATERBODY",
                "pilot_id": waterbody["pilot_id"],
                "representative_point": list(wgs_point),
            }
        )
        source_evidence.append(wgs_evidence)
        normalized_evidence["waterbodies"][waterbody["pilot_id"]] = {
            "identity": waterbody,
            "properties": wgs_feature["properties"],
            "geometry_wgs84": wgs_feature["geometry"],
        }

        projected_cache: dict[int, tuple[dict[str, Any], dict[str, Any]]] = {}
        for window in config["scene_windows"]:
            item, search_evidence, item_evidence = select_scene(
                session,
                stac_url,
                config["sentinel_collection"],
                wgs_point,
                window,
                asset_name,
                float(config["maximum_tile_cloud_cover_percent"]),
            )
            grid = grid_from_stac_item(item, asset_name)
            epsg = int(grid.crs.split(":", 1)[1])
            if epsg not in projected_cache:
                projected_cache[epsg] = fetch_waterbody(
                    session,
                    usgs_url,
                    waterbody,
                    out_sr=epsg,
                    simplification=5.0,
                )
                source_evidence.append(
                    {
                        **projected_cache[epsg][1],
                        "source_type": "USGS_NHDPLUS_HR_WATERBODY_PROJECTED",
                        "pilot_id": waterbody["pilot_id"],
                    }
                )
            projected_feature = projected_cache[epsg][0]
            patch = derive_contained_patch(
                grid,
                projected_feature["geometry"],
                int(config["patch_size_pixels"]),
            )
            corners = patch_corners(patch)
            cyan_filename, cyan_evidence = fetch_cyan_listing(
                session, cyan_url, item["properties"]["datetime"]
            )
            candidate_id = f"{waterbody['pilot_id']}__{window['window_id']}"
            patch_identity = (
                f"{item['id']}::{asset_name}::r{patch.row_offset}::c{patch.col_offset}"
            )
            asset = item["assets"][asset_name]
            common = {
                "candidate_id": candidate_id,
                "pilot_status": "METADATA_COMPLETE_LABEL_UNAVAILABLE",
                "split_membership": "PILOT_CANDIDATE_UNASSIGNED",
                "waterbody_id": waterbody["permanent_identifier"],
                "waterbody_nhdplus_id": waterbody["nhdplus_id"],
                "waterbody_name": waterbody["gnis_name"],
                "waterbody_status": EvidenceLevel.CONFIRMED,
                "scene_id": item["id"],
                "scene_status": EvidenceLevel.CONFIRMED,
                "acquisition_timestamp": item["properties"]["datetime"],
                "mgrs_tile": item["properties"]["grid:code"],
                "sentinel_processing_version": item["properties"][
                    "processing:version"
                ],
                "scene_crs": grid.crs,
                "scene_asset": asset_name,
                "scene_asset_checksum_multihash": asset["file:checksum"],
                "scene_asset_affine": json.dumps(grid.transform),
                "scene_asset_shape": json.dumps(grid.shape),
                "scene_cloud_cover_percent": item["properties"]["eo:cloud_cover"],
                "patch_row_offset": patch.row_offset,
                "patch_col_offset": patch.col_offset,
                "patch_height": patch.height,
                "patch_width": patch.width,
                "patch_affine": json.dumps(patch.transform),
                "patch_bbox_native": json.dumps(patch.bbox),
                "patch_geometry_native_wkt": patch_wkt(corners),
                "patch_geometry_status": EvidenceLevel.CONFIRMED,
                "patch_identity": patch_identity,
                "cyan_product_id": cyan_filename,
                "cyan_product_status": EvidenceLevel.CONFIRMED,
                "cyan_processing_version": "V6_CURRENT_CATALOG_CANDIDATE",
                "cyan_version_status": EvidenceLevel.CANDIDATE,
                "cyan_source_label_access": cyan_evidence["access_disposition"],
                "source_label_hash_status": EvidenceLevel.UNVERIFIED,
                "temporal_match_days": temporal_match_days(
                    item["properties"]["datetime"], cyan_filename
                ),
                "high_support_status": EvidenceLevel.UNVERIFIED,
                "high_pixel_count": "",
                "qualified_high_unit": "false",
                "qualification_failure": (
                    "cyan_version_not_confirmed;source_label_not_downloaded_or_hashed;"
                    "high_support_not_measured;pilot_has_one_patch_per_date;"
                    "cross_v2_geographic_overlap_unverifiable"
                ),
                "legacy_v2_overlap_status": EvidenceLevel.UNVERIFIED,
                "model_prediction_used_for_selection": "false",
                "label_accessed": "false",
            }
            catalog_rows.append(common)
            identity_rows.append(
                {
                    **common,
                    "relation_chain": (
                        "patch->Sentinel scene->NHDPlusHR waterbody->native footprint"
                        "->acquisition time->listed CyAN daily product"
                    ),
                    "same_waterbody_temporal_group": waterbody["permanent_identifier"],
                    "geographic_identity_complete": "true",
                    "label_identity_complete": "false",
                }
            )
            high_rows.append(
                {
                    "candidate_id": candidate_id,
                    "waterbody_id": waterbody["permanent_identifier"],
                    "scene_id": item["id"],
                    "acquisition_timestamp": item["properties"]["datetime"],
                    "cyan_product_id": cyan_filename,
                    "cyan_version_status": EvidenceLevel.CANDIDATE,
                    "source_label_hash_status": EvidenceLevel.UNVERIFIED,
                    "high_support_status": EvidenceLevel.UNVERIFIED,
                    "high_patch_count": "",
                    "high_pixel_count": "",
                    "qualified_high_unit": "false",
                    "rejection_reason": common["qualification_failure"],
                    "screening_bias_note": (
                        "Waterbody and scene metadata were selected before CyAN pixel access;"
                        " the three named large lakes are a purposive pipeline sample."
                    ),
                }
            )
            source_evidence.extend(
                [
                    {
                        **search_evidence,
                        "source_type": "COPERNICUS_STAC_SEARCH",
                        "candidate_id": candidate_id,
                    },
                    {
                        **item_evidence,
                        "source_type": "COPERNICUS_STAC_ITEM",
                        "candidate_id": candidate_id,
                    },
                    {
                        **cyan_evidence,
                        "source_type": "NASA_CYAN_DAILY_LISTING_AND_BOUNDED_ACCESS",
                        "candidate_id": candidate_id,
                    },
                ]
            )
            normalized_evidence["scenes"][candidate_id] = {
                "id": item["id"],
                "bbox_wgs84": item.get("bbox"),
                "geometry_wgs84": item.get("geometry"),
                "properties": {
                    key: item["properties"].get(key)
                    for key in (
                        "datetime",
                        "platform",
                        "grid:code",
                        "processing:level",
                        "processing:version",
                        "eo:cloud_cover",
                        "sat:relative_orbit",
                    )
                },
                "asset": {
                    key: asset.get(key)
                    for key in (
                        "href",
                        "file:size",
                        "file:checksum",
                        "proj:code",
                        "proj:transform",
                        "proj:shape",
                        "gsd",
                        "data_type",
                        "raster:scale",
                        "raster:offset",
                    )
                },
                "projected_waterbody_geometry": projected_feature["geometry"],
                "patch": asdict(patch),
                "cyan_product_id": cyan_filename,
            }

    catalog_fields = list(catalog_rows[0])
    identity_fields = list(identity_rows[0])
    high_fields = list(high_rows[0])
    write_csv(CATALOG_PATH, catalog_fields, catalog_rows)
    write_csv(IDENTITY_PATH, identity_fields, identity_rows)
    write_csv(HIGH_PATH, high_fields, high_rows)

    generated_hashes = {
        path.name: sha256_bytes(path.read_bytes())
        for path in (CONFIG_PATH, CATALOG_PATH, IDENTITY_PATH, HIGH_PATH)
    }
    manifest = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now().astimezone().isoformat(),
        "research_stage": "Phase 3A-2 metadata-first pilot",
        "model_training_performed": False,
        "legacy_test_metrics_accessed_for_design": False,
        "pilot_config_sha256": generated_hashes[CONFIG_PATH.name],
        "candidate_rows": len(catalog_rows),
        "waterbody_count": len(config["waterbodies"]),
        "scene_count": len({row["scene_id"] for row in catalog_rows}),
        "qualified_high_units": 0,
        "confirmation_members": 0,
        "source_licenses_and_terms": {
            "copernicus": {
                "status": "free_full_open_subject_to_legal_notice_and_attribution",
                "url": "https://dataspace.copernicus.eu/terms-and-conditions",
            },
            "usgs": {
                "status": "public_domain_acknowledgment_requested",
                "url": "https://www.usgs.gov/faqs/are-usgs-reportspublications-copyrighted",
            },
            "nasa": {
                "status": "freely_accessible_citation_requested; authentication_required_for_file_transfer",
                "url": "https://www.earthdata.nasa.gov/engage/open-data-services-software/data-use-policy",
            },
        },
        "source_evidence": source_evidence,
        "normalized_evidence": normalized_evidence,
        "generated_artifact_sha256": generated_hashes,
        "rebuild_command": (
            "PYTHONPATH=research_upgrade_v3/phase3a2 "
            "python3 research_upgrade_v3/phase3a2/run_phase3a2_pilot.py"
        ),
        "stopping_condition": (
            "CyAN raster bytes require Earthdata authentication; no source-label checksum,"
            " processing-version sidecar, or High-support census was obtained."
        ),
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "candidate_rows": len(catalog_rows),
                "waterbodies": len(config["waterbodies"]),
                "unique_scenes": len({row["scene_id"] for row in catalog_rows}),
                "metadata_complete_rows": sum(
                    row["patch_geometry_status"] == EvidenceLevel.CONFIRMED
                    for row in catalog_rows
                ),
                "qualified_high_units": 0,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

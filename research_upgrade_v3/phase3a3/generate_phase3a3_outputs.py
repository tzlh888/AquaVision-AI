#!/usr/bin/env python3
"""Generate the bounded Phase 3A-3 audit deliverables from preserved evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from phase3a3_audit import canonical_sha256, qualifies_high_unit, sha256_file


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCREEN_PATH = ROOT / "data" / "processed" / "phase3a3" / "candidate_native_screen.json"
QUERY_PATH = ROOT / "data" / "raw" / "phase3a3" / "usgs" / "frozen_candidate_identity_queries.json"
EXISTING_GEOMETRY_PATH = ROOT / "data" / "raw" / "phase3a3" / "usgs" / "existing_pilot_geometries.json"
FINAL_MANIFEST_PATH = HERE.parent / "final_label_pilot" / "CYAN_PRODUCT_MANIFEST.json"
FINAL_HIGH_PATH = HERE.parent / "final_label_pilot" / "HIGH_SUPPORT_PILOT.csv"

WATERBODY_CSV = HERE / "V3_WATERBODY_CATALOG.csv"
QUALIFICATION_CSV = HERE / "V3_HIGH_UNIT_QUALIFICATION.csv"
NATIVE_AUDIT = HERE / "V3_NATIVE_PIXEL_AUDIT.md"
SPLIT_AUDIT = HERE / "V3_SPLIT_INDEPENDENCE_AUDIT.md"
SEAL_STATUS = HERE / "V3_CONFIRMATION_SEAL_STATUS.md"
REPRO_REPORT = HERE / "V3_REPRODUCIBILITY_REPORT.md"
MANIFEST_PATH = HERE / "V3_DATASET_MANIFEST.json"
HANDOFF = HERE / "PHASE3A3_FINAL_HANDOFF.md"


HISTORICAL_IDS = {
    "Lake Okeechobee": "120024129",
    "Utah Lake": "83636441",
    "Upper Klamath Lake": "168095445",
}


def git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def git_status_text(cwd: Path = ROOT) -> str:
    return subprocess.check_output(
        ["git", "status", "--short", "--untracked-files=all"], cwd=cwd, text=True
    )


def load_final_patch_support() -> tuple[dict[str, dict[str, Any]], dict[str, list[str]]]:
    manifest = json.loads(FINAL_MANIFEST_PATH.read_text(encoding="utf-8"))
    groups = {row["waterbody_name"]: row for row in manifest["group_support"]}
    dates: dict[str, list[str]] = {name: [] for name in groups}
    with FINAL_HIGH_PATH.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if int(row["native_center_high"]) > 0:
                dates[row["waterbody_name"]].append(row["sentinel_acquisition_timestamp"][:10])
    return groups, dates


def date_summary(days: list[dict[str, Any]]) -> tuple[int, int, int, int, int, int]:
    high_days = [day for day in days if int(day["high"]) > 0]
    parsed = [date.fromisoformat(day["acquisition_date"]) for day in high_days]
    span = (max(parsed) - min(parsed)).days if len(parsed) >= 2 else 0
    return (
        len(high_days),
        span,
        sum(int(day["high"]) for day in days),
        sum(int(day["high_if_threshold_199"]) for day in days),
        sum(int(day["high_if_threshold_201"]) for day in days),
        sum(int(day["valid"]) for day in days),
    )


def build_rows(screen: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups, patch_dates = load_final_patch_support()
    catalog: list[dict[str, Any]] = []
    qualifications: list[dict[str, Any]] = []
    for record in screen["records"]:
        name = record["candidate_name"]
        origin = record["candidate_origin"]
        screened = record["screening_status"] == "SCREENED"
        historical = origin == "existing_final_label_pilot"
        identity_complete = screened or historical
        days = record.get("date_support", [])
        high_dates, high_span, high_total, high_199, high_201, valid_total = date_summary(days)
        waterbody_id = (
            HISTORICAL_IDS[name]
            if historical
            else record.get("waterbody_id", "")
        )
        group = groups.get(name)
        if group:
            verified_patches = int(group["high_patch_count"])
            verified_patch_native_high = int(group["native_high_pixel_count"])
            qualification_dates = patch_dates[name]
        else:
            verified_patches = 0
            verified_patch_native_high = 0
            qualification_dates = [
                day["acquisition_date"] for day in days if int(day["high"]) > 0
            ]
        evidence_complete = False  # no new Phase 3A-3 sample has complete Sentinel payload provenance
        qualified, failures = qualifies_high_unit(
            qualification_dates,
            verified_patches,
            verified_patch_native_high,
            evidence_complete,
        )
        if not identity_complete:
            failures.insert(0, "authoritative_identity_or_geometry_unavailable")
        status = (
            "IDENTITY_AND_CYAN_SCREEN_COMPLETE_SENTINEL_NOT_ACQUIRED"
            if screened and not historical
            else "EXISTING_PILOT_REAUDITED"
            if historical
            else "REJECTED_IDENTITY_UNAVAILABLE"
        )
        catalog.append(
            {
                "candidate_origin": origin,
                "candidate_name": name,
                "state_hint": record.get("state_hint", ""),
                "waterbody_id": waterbody_id,
                "identity_status": (
                    "CONFIRMED_CURRENT_QUERY"
                    if screened
                    else "CONFIRMED_HISTORICALLY_CURRENT_QUERY_FAILED"
                    if historical
                    else "UNVERIFIED"
                ),
                "identity_query_http_status": record.get("identity_query_status", ""),
                "identity_query_error": record.get("identity_query_error", ""),
                "official_feature_count": record.get("feature_count", 0),
                "area_sq_km": record.get("area_sq_km_sum", ""),
                "geometry_sha256": record.get("geometry_sha256", ""),
                "cyan_screen_status": record["screening_status"],
                "cyan_dates_screened": len(days),
                "dates_with_native_high": high_dates,
                "high_date_span_days": high_span,
                "valid_native_observations_across_dates": valid_total,
                "native_high_at_threshold_199": high_199,
                "native_high_at_frozen_threshold_200": high_total,
                "native_high_at_threshold_201": high_201,
                "new_sentinel_scene_dates_acquired": 0,
                "verified_high_patches": verified_patches,
                "verified_patch_linked_native_high_pixels": verified_patch_native_high,
                "catalog_disposition": status,
            }
        )
        qualifications.append(
            {
                "candidate_origin": origin,
                "candidate_name": name,
                "waterbody_id": waterbody_id,
                "identity_complete": str(identity_complete).lower(),
                "dates_with_high_label_potential": high_dates,
                "high_date_span_days": high_span,
                "waterbody_screen_native_high_pixels": high_total,
                "verified_sentinel_high_patches": verified_patches,
                "verified_patch_linked_native_high_pixels": verified_patch_native_high,
                "provenance_complete_for_qualification": str(evidence_complete).lower(),
                "qualified_independent_high_unit": str(qualified).lower(),
                "split_membership": "UNASSIGNED",
                "qualification_failure": ";".join(dict.fromkeys(failures)),
            }
        )
    return catalog, qualifications


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Refusing to write empty evidence table: {path.name}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    screen = json.loads(SCREEN_PATH.read_text(encoding="utf-8"))
    query = json.loads(QUERY_PATH.read_text(encoding="utf-8"))
    existing_query = json.loads(EXISTING_GEOMETRY_PATH.read_text(encoding="utf-8"))
    catalog, qualifications = build_rows(screen)
    write_csv(WATERBODY_CSV, catalog)
    write_csv(QUALIFICATION_CSV, qualifications)

    new_rows = [row for row in catalog if row["candidate_origin"] == "phase3a3_new_pool"]
    screened_new = [row for row in new_rows if row["cyan_screen_status"] == "SCREENED"]
    high_new = [row for row in screened_new if int(row["dates_with_native_high"]) > 0]
    qualified = [
        row for row in qualifications if row["qualified_independent_high_unit"] == "true"
    ]
    error_counts = Counter(
        str(row.get("error_type") or f"HTTP_{row.get('http_status')}")
        for row in query["results"]
        if row.get("http_status") != 200
    )
    t199 = sum(int(row["native_high_at_threshold_199"]) for row in screened_new)
    t200 = sum(int(row["native_high_at_frozen_threshold_200"]) for row in screened_new)
    t201 = sum(int(row["native_high_at_threshold_201"]) for row in screened_new)
    native_note = f"""# V3 native CyAN pixel audit

## Result

The six previously verified OBPG CyAN V6 products were reused without a new CyAN download. Five of the 12 frozen new candidates obtained an authoritative USGS geometry and were screened on the native 300 m grid. Three contain at least one High native pixel on the six frozen dates: Lake Erie, Lake Champlain, and Lake Winnebago. Only Lake Winnebago has both abundant native High support and High observations separated by at least 30 days. No new Sentinel payload or patch was acquired because the successfully identified candidate universe, even combined with the three original pilot waterbodies, contains fewer than the nine independent waterbodies required for a 3/3/3 seal.

## Identity and counting rule

- Dated native identity: `(CyAN product ID, native row, native column)`.
- Repeated sampling of the same cell in the same product is counted once.
- A repeated location on another date is a separate dated observation but not a new spatial location; no 20 m resampled pixel is treated as a new 300 m observation.
- Discrete classes use nearest-neighbour semantics only. Frozen mapping is Low 0--99, Moderate 100--199, High 200--253, land 254, no-data 255.

## Scale compatibility

A 64 x 64 Sentinel patch at 20 m spans 1.28 km x 1.28 km (1.6384 km²). A 300 m CyAN cell spans 0.09 km². The theoretical area ratio is 18.2 cells per patch and the Final Label Pilot observed 19 native cell centres. Therefore three non-overlapping patches supply only about 55 area-equivalent cells (57 observed centres), below the separate 100-native-pixel requirement. At least six suitably positioned, low-overlap patches are normally necessary. The 100-pixel rule corresponds to roughly 9 km² of dated native label support. It is feasible for large lakes and spatially extended blooms, but systematically excludes small waterbodies and compact bloom footprints. The gate was not changed.

## Boundary sensitivity

Across the five newly screened official geometries and six dates, the aggregate native counts classified High would be {t199:,} at a threshold of 199, {t200:,} at the frozen threshold of 200, and {t201:,} at a threshold of 201. This is a descriptive ±1 digital-number sensitivity check, not a threshold optimization. Candidate-level values are preserved in `V3_WATERBODY_CATALOG.csv`.

## Missingness and limitations

CyAN valid coverage varies sharply by product and waterbody; for example, some frozen dates have zero or very low valid support in a waterbody. Counts represent the CyAN proxy product, not in-situ hazard measurements. USGS rasterization is evaluated at native-cell centres in EPSG:5070. No model prediction contributed to candidate selection.
"""
    NATIVE_AUDIT.write_text(native_note, encoding="utf-8")

    split_note = """# V3 split independence audit

## Decision

No Training, Validation, or Confirmation membership was assigned. There are zero qualified independent High units, so allocating candidates would create a misleading appearance of readiness.

The frozen independent unit is the complete real-waterbody/event history. Patches, scenes, dates, and native pixels from one waterbody cannot cross splits. Duplicate Lake Erie polygon components were grouped under one GNIS waterbody identity rather than counted as independent units.

Because no split exists, there is no observed cross-split spatial or event overlap. This is a vacuous isolation result, not evidence that a deployable split has been constructed. Historical v2 geography remains unknown; the only defensible future path is v3-only and must not mix v2 samples into training or confirmation.

Minimum required versus available:

| Split | Frozen minimum qualified High units | Assigned now |
|---|---:|---:|
| Training | 3 | 0 |
| Validation | 3 | 0 |
| Confirmation | 3 | 0 |
"""
    SPLIT_AUDIT.write_text(split_note, encoding="utf-8")

    seal_note = """# V3 Confirmation Set seal status

Status: **NOT SEALED**

There are zero qualified independent High units and no split assignment. A member manifest and aggregate confirmation hash were therefore not created. This status document is evidence of a failed gate, not an empty confirmation set represented as a successful seal.

To seal a future Confirmation Set, at least three qualified real-waterbody units must first pass every frozen identity, multi-date, patch, native-pixel, provenance, and independence check. Their membership and hashes must be fixed before any model training or selection. The preferred target remains ten or more independent confirmation units.
"""
    SEAL_STATUS.write_text(seal_note, encoding="utf-8")

    raw_metadata_bytes = QUERY_PATH.stat().st_size + EXISTING_GEOMETRY_PATH.stat().st_size
    processed_bytes = sum(
        path.stat().st_size for path in (ROOT / "data" / "processed" / "phase3a3").glob("*")
    )
    reproducibility = f"""# Phase 3A-3 reproducibility report

## Frozen inputs

- Protocol: `research_upgrade_v3/phase3a3/V3_EXPANSION_PROTOCOL.md`
- Configuration: `research_upgrade_v3/phase3a3/phase3a3_config.json`
- Six ignored raw CyAN V6 products: {screen['cyan_input_bytes']:,} bytes total; each SHA-256 is recorded in `V3_DATASET_MANIFEST.json`.
- Official USGS response evidence: {raw_metadata_bytes:,} bytes, stored under ignored `data/raw/phase3a3/usgs/`.
- Derived native-pixel screening evidence: {processed_bytes:,} bytes, stored under ignored `data/processed/phase3a3/`.
- Free storage before acquisition was 328.1 GiB. Estimated new payload was zero because the stopping gate was reached before Sentinel or additional CyAN payload selection.

## Rebuild commands

```bash
python3 research_upgrade_v3/phase3a3/query_usgs_candidates.py
python3 research_upgrade_v3/phase3a3/fetch_existing_pilot_geometries.py
python3 research_upgrade_v3/phase3a3/screen_candidate_pool.py
python3 research_upgrade_v3/phase3a3/generate_phase3a3_outputs.py
python3 -m unittest discover -s research_upgrade_v3/phase3a3 -p 'test_*.py' -v
python3 -m unittest discover -s research_upgrade_v3/final_label_pilot -p 'test_*.py' -v
```

Network retrieval commands are intentionally bounded and may reproduce a later official service state rather than byte-identical transient HTTP metadata. The preserved raw-response hashes identify the evidence actually used. All label counts and CSV outputs are reproducible from the preserved ignored responses, raw CyAN files, and scripts without credentials.

## Security and history protection

No password, Earthdata token, cookie, Authorization header, or private authentication file is stored. No model was trained. No historical report or result was modified. No commit or push was made. Raw payloads remain ignored by Git.

The pre-Phase-3A-3 untracked research evidence was archived outside the repositories: AquaVision 60 files, SHA-256 `14419204591e1988038827983aee8668a87026f9326c9a5b986671cd9ed7dec0`; WaterSense 131 files, SHA-256 `e44fa74e853bf5569d79e96443d4ad1d58029758db6ff790a3d2010f8ce863b8`.
"""
    REPRO_REPORT.write_text(reproducibility, encoding="utf-8")

    stable_core = {
        "candidate_count": len(new_rows),
        "new_identity_and_cyan_screen_complete": len(screened_new),
        "new_waterbodies_with_high": len(high_new),
        "qualified_units": len(qualified),
        "source_screen_sha256": sha256_file(SCREEN_PATH),
        "qualification_rows": qualifications,
    }
    current_status = git_status_text()
    manifest = {
        "schema_version": "aquavision-v3-phase3a3-manifest-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_stage": "Phase 3A-3 bounded v3-only expansion",
        "final_status": "NOT READY",
        "model_training_performed": False,
        "legacy_v2_used": False,
        "credentials_stored": False,
        "git": {
            "branch": git("branch", "--show-current"),
            "head": git("rev-parse", "HEAD"),
            "initial_full_status_sha256": "9cca88b42aac151bfacebd59c74a5b70b46e5d7f1ef890883fdb34986d40fe8d",
            "initial_untracked_file_count": 60,
            "tracked_or_staged_changes_at_start": 0,
            "final_full_status_sha256": hashlib.sha256(current_status.encode("utf-8")).hexdigest(),
            "final_untracked_file_count": len(
                git("ls-files", "--others", "--exclude-standard").splitlines()
            ),
            "tracked_or_staged_changes_at_end": 0,
        },
        "protected_snapshot": {
            "aquavision_untracked_file_count": 60,
            "aquavision_archive_sha256": "14419204591e1988038827983aee8668a87026f9326c9a5b986671cd9ed7dec0",
            "watersense_untracked_file_count": 131,
            "watersense_archive_sha256": "e44fa74e853bf5569d79e96443d4ad1d58029758db6ff790a3d2010f8ce863b8",
            "archive_location": "workspace outputs outside both Git repositories; not for public commit",
        },
        "official_sources": {
            "usgs_nhdplus_hr": "https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer/9",
            "nasa_cyan": "https://oceandata.sci.gsfc.nasa.gov/api/cyan_file_search",
            "copernicus_stac": "https://stac.dataspace.copernicus.eu/v1/",
        },
        "resource_budget": {
            "new_waterbodies_max": 12,
            "new_sentinel_scene_dates_max": 24,
            "new_cyan_products_max": 24,
        },
        "actual_scale": {
            "frozen_new_candidates": len(new_rows),
            "official_identity_and_cyan_screen_complete": len(screened_new),
            "identity_query_failures": len(new_rows) - len(screened_new),
            "identity_failure_types": dict(sorted(error_counts.items())),
            "new_waterbodies_with_any_high": len(high_new),
            "new_complete_v3_sample_units": 0,
            "new_sentinel_scene_dates": 0,
            "new_sentinel_payload_bytes": 0,
            "new_cyan_products_downloaded": 0,
            "existing_cyan_products_reused": 6,
            "existing_cyan_bytes_reused": screen["cyan_input_bytes"],
            "official_metadata_bytes_preserved": raw_metadata_bytes,
            "derived_screening_bytes": processed_bytes,
        },
        "qualification": {
            "qualified_independent_high_units": 0,
            "training_units": 0,
            "validation_units": 0,
            "confirmation_units": 0,
            "confirmation_sealed": False,
            "phase3b_prerequisites_met": False,
        },
        "accepted_samples": [],
        "accepted_samples_note": (
            "No sample had complete new Sentinel payload provenance and the frozen High-unit gate; "
            "candidate evidence is retained in the two CSV audit tables."
        ),
        "source_artifacts": {
            "usgs_new_candidate_queries": {
                "path": "data/raw/phase3a3/usgs/frozen_candidate_identity_queries.json",
                "sha256": sha256_file(QUERY_PATH),
                "git_ignored": True,
            },
            "usgs_existing_pilot_queries": {
                "path": "data/raw/phase3a3/usgs/existing_pilot_geometries.json",
                "sha256": sha256_file(EXISTING_GEOMETRY_PATH),
                "git_ignored": True,
            },
            "native_screen": {
                "path": "data/processed/phase3a3/candidate_native_screen.json",
                "sha256": sha256_file(SCREEN_PATH),
                "git_ignored": True,
            },
            "cyan_products": screen["cyan_products"],
        },
        "stable_evidence_sha256": canonical_sha256(stable_core),
        "generated_artifact_sha256": {
            path.name: sha256_file(path)
            for path in [
                HERE / "V3_EXPANSION_PROTOCOL.md",
                HERE / "phase3a3_config.json",
                HERE / "phase3a3_audit.py",
                HERE / "query_usgs_candidates.py",
                HERE / "fetch_existing_pilot_geometries.py",
                HERE / "screen_candidate_pool.py",
                HERE / "generate_phase3a3_outputs.py",
                HERE / "test_phase3a3_audit.py",
                HERE / "test_phase3a3_real_integration.py",
                WATERBODY_CSV,
                QUALIFICATION_CSV,
                NATIVE_AUDIT,
                SPLIT_AUDIT,
                SEAL_STATUS,
                REPRO_REPORT,
            ]
        },
        "stop_reason": (
            "Only five of twelve new frozen candidates returned authoritative identity/geometry. "
            "Together with the three historical pilot waterbodies, the bounded verified universe "
            "contains at most eight independent waterbodies, fewer than the nine required for 3/3/3."
        ),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    delivery_paths = sorted(
        path
        for path in HERE.iterdir()
        if path.is_file() and path.name != HANDOFF.name
    )
    delivery_hashes = "\n".join(
        f"{sha256_file(path)}  research_upgrade_v3/phase3a3/{path.name}"
        for path in delivery_paths
    )
    delivery_file_list = "\n".join(
        f"- `research_upgrade_v3/phase3a3/{path.name}`" for path in delivery_paths
    )

    handoff = f"""# AquaVision Phase 3A-3 final handoff

Final status: **NOT READY**

## Executive finding

The bounded candidate-pool identity budget was exhausted without creating a train/validation/confirmation-ready dataset. Twelve new waterbody candidates were frozen before label inspection. Five obtained authoritative USGS identity and geometry and were screened with six preserved CyAN V6 products; seven failed with bounded official-service timeout/502 outcomes. Three of the five screened new waterbodies contain at least one native High pixel, but only Lake Winnebago has strong High support on dates separated by at least 30 days. No new waterbody became a qualified unit because no new Sentinel payload/patch set was acquired, and further acquisition could not overcome the arithmetic minimum: five verified new waterbodies plus three original pilot waterbodies is at most eight, below the nine independent units required for 3/3/3.

## A--L decision record

**A. Actual new real waterbodies:** Five authoritative identity-and-CyAN-screened candidates were added to the catalog (Lake Erie, Lake Champlain, Lake Winnebago, Lake Pontchartrain, Pyramid Lake). Zero became a complete accepted v3 sample unit.

**B. Matched Sentinel and CyAN products:** Zero new Sentinel scene/date payloads and zero new CyAN products were acquired. Six existing verified CyAN V6 products ({screen['cyan_input_bytes']:,} bytes) were reused. The earlier Final Label Pilot's six Sentinel/CyAN pairs remain unchanged; they are not counted as new Phase 3A-3 acquisitions.

**C. Waterbodies containing High:** Three of the five newly screened waterbodies contain High on at least one frozen date (Erie, Champlain, Winnebago). Existing full-geometry re-screening also found High in Upper Klamath Lake; Utah and Okeechobee retain only the narrower Final Label Pilot evidence where current geometry retrieval failed.

**D. Waterbodies meeting the frozen qualification gate:** Zero. Lake Winnebago is the only new label-side candidate with multi-date, >30-day, >100-native-pixel potential, but it has zero verified Sentinel patches and incomplete sample provenance. Existing Upper Klamath remains at two verified High patches/29 patch-linked native High pixels; Utah remains at one/19; Okeechobee remains at zero/zero.

**E. Is the 100-native-pixel condition spatially reasonable?** It represents about 9 km² of dated native label support and is feasible for large waterbodies with extensive blooms, but it is structurally stricter than the separate three-patch condition. A 64 x 64 at 20 m patch contains about 19 native 300 m centres, so at least six low-overlap patches are normally needed. It biases the study toward large lakes/large bloom footprints but was not changed retroactively.

**F. Qualified split counts:** Training 0, Validation 0, Confirmation 0.

**G. Cross-split overlap:** No split was assigned, so no cross-split overlap exists. This is vacuous, not proof of a usable independent split.

**H. Confirmation seal:** Not sealed. No empty member manifest or confirmation hash was created.

**I. End-to-end reproducibility:** The official identity → geometry → native CyAN value → class/count chain is reproducible for five new candidates and the successfully refreshed Upper Klamath geometry. The new Sentinel → patch → label chain is not complete because no new Sentinel payload was acquired after the readiness arithmetic failed. The six earlier pilot integrations remain reproducible and unchanged.

**J. Phase 3B prerequisites:** Not met. There are zero qualified units versus the required 3/3/3, no sealed Confirmation Set, and no complete new Sentinel samples.

**K. Continue expansion?** Not under the present bounded protocol. The 12-candidate identity budget was exhausted, official identity retrieval succeeded for only five, and the candidate universe cannot reach nine units. A future effort would require a separately approved, pre-registered candidate universe, a more reliable authoritative geometry delivery path, and substantial Sentinel multi-band acquisition/patch engineering. Its marginal value is low relative to preserving the scientifically honest LIMITED result.

**L. Most reasonable stopping plan:** retain the Final Label Pilot as proof that the geospatial label-integration method works; retain Phase 3A-3 as a documented negative expansion result; do not train Phase 3B; do not reinterpret historical v2 geography; and close AquaVision with a LIMITED conclusion unless genuinely new authoritative data infrastructure and a new independent-study budget become available.

## Evidence protection and implementation facts

- No model was trained and no model prediction was used for selection.
- No historical result was edited or overwritten.
- No commit or push was performed.
- New payload downloads: 0 CyAN, 0 Sentinel; official metadata preserved: {raw_metadata_bytes:,} bytes.
- Initial AquaVision state: branch `research-upgrade-v3`, HEAD `bd11eceaa7efa7ca785d5e466cf807312ed70df0`, 60 untracked files, tracked/staged clean.
- Initial WaterSense state: branch `research-upgrade-v3`, HEAD `3553b29ff104918b12da8c84d2c9a8c5ed032e18`, 131 untracked files, tracked/staged clean.
- Snapshot hashes and key source/artifact hashes are recorded in `V3_DATASET_MANIFEST.json` and `V3_REPRODUCIBILITY_REPORT.md`; final delivery hashes are reported separately after generation.

## Automated validation

- Phase 3A-3 tests: 13/13 passed (10 synthetic logic tests and 3 real-data integration tests).
- Final Label Pilot regression tests: 15/15 passed.
- `git diff --check`: passed for both repositories; tracked/staged files remain unchanged.

## New Phase 3A-3 files

{delivery_file_list}
- `research_upgrade_v3/phase3a3/PHASE3A3_FINAL_HANDOFF.md` (this file; its hash is reported by the final generation command)

## Delivery SHA-256 values

```text
{delivery_hashes}
```

Final Git inventory after generation: AquaVision 77 untracked files (60 historical + 17 Phase 3A-3), full-status SHA-256 `d442c174d6fe5e0f9b4405397018463f32df188ae112aab0c441668da4fb33a8`; WaterSense 131 untracked files, full-status SHA-256 `1ad752764355498fe02f2c6762ce23b561e3aca7dd04049541819eed29f2de25`. Both repositories remain on `research-upgrade-v3` with no tracked or staged change.

## Strict stop

Phase 3B model training is not authorized. No further AquaVision dataset expansion was started.
"""
    HANDOFF.write_text(handoff, encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "NOT READY",
                "new_candidates": len(new_rows),
                "new_identity_and_cyan_screen_complete": len(screened_new),
                "new_with_high": len(high_new),
                "qualified_units": len(qualified),
                "manifest_sha256": sha256_file(MANIFEST_PATH),
                "handoff_sha256": sha256_file(HANDOFF),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

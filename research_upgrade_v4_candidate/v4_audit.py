#!/usr/bin/env python3
"""Generate fail-closed AquaVision V4 geographic/readiness evidence."""

from __future__ import annotations

import hashlib
import csv
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / "research_upgrade_v3"
OUT = ROOT / "research_upgrade_v4_candidate"
PILOT = V3 / "final_label_pilot/HIGH_SUPPORT_PILOT.csv"
POOL = V3 / "phase3a3/V3_WATERBODY_CATALOG.csv"
QUAL = V3 / "phase3a3/V3_HIGH_UNIT_QUALIFICATION.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def write_text(name: str, value: str) -> None:
    (OUT / name).write_text(value.rstrip() + "\n", encoding="utf-8")


def write_json(name: str, value: object) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise RuntimeError(f"Refusing to write empty audit: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def as_bool(value: object) -> bool:
    return str(value).strip().lower() == "true"


def as_int(value: object) -> int:
    text = str(value).strip()
    return int(float(text)) if text else 0


def as_tristate(value: object) -> bool | None:
    """Parse explicit evidence without treating missing or ambiguous text as true."""
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "pass", "passed"}:
        return True
    if text in {"false", "0", "no", "fail", "failed"}:
        return False
    return None


def canonical_unit_key(record: dict[str, object]) -> str:
    waterbody_id = str(record.get("waterbody_id", "")).strip()
    if waterbody_id and waterbody_id.lower() not in {"nan", "none"}:
        return f"id:{waterbody_id}"
    return "name:" + " ".join(str(record.get("waterbody_name", "")).lower().split())


def evaluate_unit(record: dict[str, object]) -> dict[str, object]:
    """Evaluate every frozen gate from explicit fields; missing evidence fails closed."""
    result = dict(record)
    failures: list[str] = []
    missing: list[str] = []
    boolean_gates = {
        "identity_complete": "verified_waterbody_identity_or_geometry",
        "provenance_complete_for_qualification": "complete_sentinel_cyan_provenance",
        "registration_mask_product_checks_pass": "registration_mask_product_version_checks",
        "independence_resolved": "spatial_event_independence",
    }
    for field, label in boolean_gates.items():
        observed = as_tristate(record.get(field))
        result[field] = observed if observed is not None else "UNKNOWN"
        if observed is None:
            missing.append(label)
        elif not observed:
            failures.append(label)

    numeric_gates = {
        "dates_with_high": (2, "at_least_2_high_dates"),
        "high_date_span_days": (30, "high_dates_separated_at_least_30_days"),
        "verified_high_patches": (3, "at_least_3_nonoverlapping_high_patches"),
        "distinct_native_high_support": (100, "at_least_100_unique_dated_native_high_identities"),
    }
    for field, (minimum, label) in numeric_gates.items():
        raw = record.get(field)
        if raw is None or str(raw).strip() == "":
            result[field] = "UNKNOWN"
            missing.append(label)
            continue
        try:
            observed = as_int(raw)
        except (TypeError, ValueError):
            result[field] = "UNKNOWN"
            missing.append(label)
            continue
        result[field] = observed
        if observed < minimum:
            failures.append(label)

    if as_tristate(record.get("evidence_conflict")) is True:
        result["qualification_status"] = "BLOCKED_CONFLICTING_EVIDENCE"
        result["qualified_independent_high_unit"] = False
        result["exclusion_reason"] = "conflicting_evidence"
    elif failures:
        result["qualification_status"] = "EXCLUDED_NOT_QUALIFIED"
        result["qualified_independent_high_unit"] = False
        result["exclusion_reason"] = ";".join(failures + [f"missing_evidence:{item}" for item in missing])
    elif missing:
        result["qualification_status"] = "BLOCKED_MISSING_EVIDENCE"
        result["qualified_independent_high_unit"] = False
        result["exclusion_reason"] = ";".join(f"missing_evidence:{item}" for item in missing)
    else:
        result["qualification_status"] = "QUALIFIED"
        result["qualified_independent_high_unit"] = True
        result["exclusion_reason"] = ""
    result["split_membership"] = "UNASSIGNED"
    return result


def audit_normalized_units(records: list[dict[str, object]]) -> list[dict[str, object]]:
    """Collapse duplicate waterbody identities before counting qualification."""
    grouped: dict[str, list[dict[str, object]]] = {}
    for record in records:
        grouped.setdefault(canonical_unit_key(record), []).append(record)
    audited: list[dict[str, object]] = []
    evidence_fields = [
        "identity_complete", "dates_with_high", "high_date_span_days",
        "verified_high_patches", "distinct_native_high_support",
        "provenance_complete_for_qualification",
        "registration_mask_product_checks_pass", "independence_resolved",
    ]
    for key in sorted(grouped):
        sources = grouped[key]
        first = dict(sources[0])
        conflicting = any(
            any(str(source.get(field, "")) != str(first.get(field, "")) for field in evidence_fields)
            for source in sources[1:]
        )
        first["evidence_conflict"] = conflicting
        result = evaluate_unit(first)
        result["canonical_unit_key"] = key
        result["duplicate_source_records"] = len(sources)
        audited.append(result)
    return audited


def geographic_identity_audit() -> list[dict[str, object]]:
    pilot = read_csv(PILOT)
    rows: list[dict[str, object]] = []
    for record in pilot:
        rows.append({
            "evidence_stage": "v3_verified_label_pilot",
            "waterbody_id": record["waterbody_id"],
            "waterbody_name": record["waterbody_name"],
            "scene_product_id": record["scene_id"],
            "acquisition_date": str(record["sentinel_acquisition_timestamp"])[:10],
            "geographic_footprint": record["sentinel_patch_geometry_native_wkt"],
            "cyan_product_version": f"{record['cyan_product_id']} / V{record['cyan_processing_version']}",
            "spatial_overlap_check": "PASS_NATIVE_CENTER_INTERSECTION",
            "valid_reference_support": as_int(record["native_center_pixels_valid"]),
            "high_class_support": as_int(record["native_center_high"]),
            "qualification_status": "EXCLUDED_NOT_QUALIFIED",
            "exclusion_reason": record["qualification_failure"],
            "independent_unit_rule": "one waterbody history; scenes are not separate units",
        })
    pool = read_csv(POOL)
    for record in pool:
        if record["candidate_origin"] == "existing_final_label_pilot":
            continue
        identity_ok = str(record["identity_status"]).startswith("CONFIRMED")
        rows.append({
            "evidence_stage": "v3_bounded_candidate_pool",
            "waterbody_id": record.get("waterbody_id", ""),
            "waterbody_name": record["candidate_name"],
            "scene_product_id": "",
            "acquisition_date": "",
            "geographic_footprint": f"geometry_sha256={record.get('geometry_sha256', '')}" if identity_ok else "",
            "cyan_product_version": "V6 screen only" if record["cyan_screen_status"] == "SCREENED" else "",
            "spatial_overlap_check": "NOT_RUN_NO_SENTINEL_PATCH" if identity_ok else "NOT_RUN_IDENTITY_UNAVAILABLE",
            "valid_reference_support": as_int(record["valid_native_observations_across_dates"]),
            "high_class_support": as_int(record["native_high_at_frozen_threshold_200"]),
            "qualification_status": "EXCLUDED_INCOMPLETE_UNIT",
            "exclusion_reason": "no verified Sentinel scene/patch linkage" if identity_ok else "authoritative identity/geometry unavailable",
            "independent_unit_rule": "candidate waterbody; no modelling unit without full provenance",
        })
    return rows


def independent_high_audit() -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for record in read_csv(QUAL):
        normalized.append({
            "origin": record["candidate_origin"],
            "waterbody_id": record.get("waterbody_id", ""),
            "waterbody_name": record["candidate_name"],
            "identity_complete": record.get("identity_complete"),
            "dates_with_high": record.get("dates_with_high_label_potential"),
            "high_date_span_days": record.get("high_date_span_days"),
            "verified_high_patches": record.get("verified_sentinel_high_patches"),
            "distinct_native_high_support": record.get("verified_patch_linked_native_high_pixels"),
            "provenance_complete_for_qualification": record.get("provenance_complete_for_qualification"),
            # V3 does not expose these as independently reviewable unit-level fields.
            "registration_mask_product_checks_pass": None,
            "independence_resolved": None,
            "source_qualification_failure": record.get("qualification_failure", ""),
        })
    return audit_normalized_units(normalized)


def baseline_manifest() -> dict[str, object]:
    keys = [
        "README.md", "configs/phase4.json", "data/metadata/phase3_5/geographic_split_v2.json",
        "research_outputs/tables/final_results.csv", "research_outputs/reports/FINAL_RELIABILITY_ASSESSMENT.md",
        "research_upgrade_v3/final_label_pilot/HIGH_SUPPORT_PILOT.csv",
        "research_upgrade_v3/final_label_pilot/CYAN_PRODUCT_MANIFEST.json",
        "research_upgrade_v3/phase3a3/V3_WATERBODY_CATALOG.csv",
        "research_upgrade_v3/phase3a3/V3_HIGH_UNIT_QUALIFICATION.csv",
        "research_upgrade_v3/phase3a3/V3_DATASET_MANIFEST.json",
        "research_upgrade_v3/final_closeout/FINAL_SCIENTIFIC_REPORT.md",
    ]
    usage = shutil.disk_usage(ROOT)
    raw = list((ROOT / "data/raw/final_label_pilot/cyan").glob("*.tif"))
    arrays = list((ROOT / "data/raw/phase3_5_pairs").glob("**/*.npy"))
    return {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(), "branch": git("branch", "--show-current"),
        "head": git("rev-parse", "HEAD"),
        "preexisting_status": ["?? research_upgrade_v3/final_closeout/RESEARCH_CONTRIBUTION_STATEMENT.md"],
        "python": sys.version, "platform": platform.platform(), "dependencies": "standard_library_only", "disk_available_bytes": usage.free,
        "data_access": {"cyan_v6_geotiffs": len(raw), "phase3_5_npy_arrays": len(arrays), "historical_models_directory": (ROOT / "research_outputs/models").is_dir()},
        "key_files": {path: sha256(ROOT / path) for path in keys},
    }


def write_release_candidate_manifest() -> None:
    required_paths = [
        ROOT / "README.md",
        ROOT / "scripts/audit_final_release.py",
        ROOT / "tests/test_phase4_reliability.py",
        ROOT / "tests/test_manifest_v4_migration.py",
        ROOT / "data/metadata/phase5/preservation_manifest_v4_amendment.json",
        ROOT / "data/metadata/phase5/preservation_manifest_v4_current.json",
        ROOT / "research_outputs/phase5/claim_occurrences.json",
        ROOT / "research_outputs/phase5/metadata_audit.json",
        V3 / "final_closeout/RESEARCH_CONTRIBUTION_STATEMENT.md",
    ]
    tracked = set(git("ls-files").splitlines())
    untracked_required = [
        str(path.relative_to(ROOT)) for path in required_paths
        if str(path.relative_to(ROOT)) not in tracked
    ]
    if untracked_required:
        raise RuntimeError(f"Required release-candidate files are not Git-tracked: {untracked_required}")
    paths = list(required_paths)
    paths.extend(
        path for path in sorted(OUT.rglob("*"))
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.name != "V4_RELEASE_CANDIDATE_MANIFEST.json"
        and str(path.relative_to(ROOT)) in tracked
    )
    write_json("V4_RELEASE_CANDIDATE_MANIFEST.json", {
        "schema": "aquavision-v4-release-candidate-v1",
        "scope": "Git-tracked V4 release-candidate evidence required in a clean public checkout",
        "self_reference_policy": "This manifest excludes its own SHA-256 to avoid recursive hashing; an external review records the final manifest hash.",
        "files": {str(path.relative_to(ROOT)): sha256(path) for path in paths if path.is_file()},
    })


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write_json("BASELINE_INTEGRITY_MANIFEST.json", baseline_manifest())
    geo = geographic_identity_audit()
    high = independent_high_audit()
    write_csv(OUT / "GEOGRAPHIC_IDENTITY_AUDIT.csv", geo)
    write_csv(OUT / "INDEPENDENT_HIGH_UNIT_AUDIT.csv", high)
    qualified = sum(bool(row["qualified_independent_high_unit"]) for row in high)
    readiness = "NOT READY" if qualified < 9 else "READY FOR SPLIT REVIEW; TRAINING NOT AUTHORIZED"
    write_text("DATASET_READINESS_DECISION.md", f"""# AquaVision V4 dataset readiness decision

## Decision: **{readiness}**

The frozen minimum is nine qualified independent real-waterbody units: 3 Training, 3 Validation, and 3 Confirmation. A dynamic, fail-closed review of the **current frozen V3 evidence pool** found **{qualified}** qualified units. Because the pool remains below the gate, it assigns **0/0/0** members. This is not a claim that new external data were audited, no confirmation set is sealed, and no new model training is permitted.

The evaluator derives the outcome from explicit identity, date span, non-overlapping High-patch support, unique dated native High identity support, complete Sentinel/CyAN provenance, registration/mask/product-version checks, and resolved independence. Missing or conflicting evidence fails closed. The V3 table does not expose the last two gates as independently reviewable unit-level fields, so those fields are reported as `UNKNOWN`, never inferred from `provenance_complete_for_available_scenes`. The audit treats a waterbody history—not a 64×64 patch, Sentinel crop, resampled target pixel, or native CyAN pixel—as the independent unit and deduplicates repeated waterbody identities before counting.

This is a scientific stop decision, not a failed software run. See `GEOGRAPHIC_IDENTITY_AUDIT.csv` and `INDEPENDENT_HIGH_UNIT_AUDIT.csv` for every inclusion/exclusion reason.
""")
    write_text("AQUAVISION_V4_SCIENTIFIC_REPORT.md", """# AquaVision AI — Research Upgrade V4 Candidate

## Evidence status

- **HISTORICAL:** 288 Sentinel/CyAN patch pairs, not 288 independent waterbodies; validation-selected NDCI; Logistic Regression geographic-Test High F1 0.5803 is post-hoc and not selection evidence.
- **REPRODUCED:** On 2026-10-14, `python -m pytest -q` in a clean Python 3.12 checkout produced 126 passed and one documented complete-frozen-environment skip. In the prepared full-artifact audit environment, all 60 research-upgrade tests passed; their ignored-array integration checks are not available in a clean public checkout.
- **NEW METHOD VALIDATION + DATA INTEGRATION:** V4 normalized the frozen V3 scene/product/footprint and waterbody-unit evidence into two reviewable audit tables and applied a dynamic fail-closed readiness gate. No new external records were added.
- **CONFIRMED:** no model-performance claim.
- **NOT READY:** 0 qualified independent High units; 0/0/0 Training/Validation/Confirmation members.

## Geographic evidence recovery

The project has strong traceability for six prospective pilot scene pairs: named waterbody, Sentinel product, date, patch CRS/affine/footprint, same-day CyAN V6 product and hash, native-grid overlap, and reference support. This is engineering and provenance evidence. It does not make six independent waterbodies: the scenes collapse to three waterbody histories.

The historical 288-pair benchmark remains geographically unresolved. Its author-grid components cannot be promoted to verified lakes, and 64×64 pixels cannot be counted as 4,096 independent labels. Resampling a roughly 300 m CyAN cell to a 20 m grid does not add independent evidence.

## Conditional model experiment

Not run. The frozen A2 gate failed before training. Consequently no new NDCI, Logistic Regression, Random Forest, or CNN comparison exists in V4, no Confirmation labels were accessed for model choice, and the final scientific status remains **LIMITED / NOT READY**.

## Scientific improvement

V4 makes the negative readiness decision machine-readable and separates three claims that are often conflated: exact array reproducibility, scene/label provenance, and independent cross-waterbody evidence. Only the first two are demonstrated for bounded portions of the project. This is **METHOD VALIDATION + DATA INTEGRATION**, not independent model confirmation.
""")
    write_text("AQUAVISION_REPRODUCIBILITY.md", """# AquaVision V4 reproducibility

Status: **PARTIAL**. Code and preserved v3 evidence are reproducible; independent confirmation is unavailable.

```bash
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python scripts/run_research_upgrade_tests.py
PYTHONPATH=src python research_upgrade_v4_candidate/v4_audit.py
PYTHONPATH=src python -m unittest discover -s research_upgrade_v4_candidate -p 'test_*.py' -v
```

The public suite retains one explicit complete-frozen-environment skip. The v3 upgrade suites remain separately tested. The version-scoped preservation amendment records three reproducible packaging-metadata files and the changed tracked reliability test without rewriting the frozen manifest; `audit_final_release.py --metadata-only` must verify that exact amendment. No model was trained by V4.
""")
    artifacts = {
        str(path.relative_to(OUT)): sha256(path)
        for path in sorted(OUT.rglob("*"))
        if path.is_file()
        and path.name not in {"V4_ARTIFACT_MANIFEST.json", "V4_RELEASE_CANDIDATE_MANIFEST.json"}
        and "__pycache__" not in path.parts
    }
    write_json("V4_ARTIFACT_MANIFEST.json", {"schema": "aquavision-v4-candidate-artifacts-v1", "files": artifacts})
    write_release_candidate_manifest()
    print(json.dumps({"geographic_rows": len(geo), "independent_units": len(high), "qualified": qualified}))


if __name__ == "__main__":
    main()

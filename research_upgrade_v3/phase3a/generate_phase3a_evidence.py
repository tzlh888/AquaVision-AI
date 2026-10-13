"""Generate Phase 3A machine-readable audit tables and artifact manifest."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from phase3a_audit import (
    build_identity_table,
    build_overlap_audit,
    high_support_by_selected_group,
    read_csv,
    sha256_file,
    summary_counts,
    validate_split_membership,
    verify_expected_file,
    write_csv,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def artifact_manifest(v2: dict) -> dict:
    preserved = json.loads((ROOT / "data/metadata/phase5/preservation_manifest.json").read_text())
    records = [verify_expected_file(ROOT, path, digest) for path, digest in sorted(preserved["files"].items())]

    sanitized = json.loads((ROOT / "data/metadata/phase5/public_release_sanitization.json").read_text())
    sanitization_records = sanitized.get("files", sanitized.get("changes", []))
    sanitization_paths = set()
    for item in sanitization_records:
        if isinstance(item, str):
            sanitization_paths.add(item)
        elif isinstance(item, dict) and item.get("path"):
            sanitization_paths.add(item["path"])
    for record in records:
        if record["status"] == "HASH_MISMATCH" and record["path"] in sanitization_paths:
            details = sanitization_records[record["path"]] if isinstance(sanitization_records, dict) else {}
            record["sanitized_expected_sha256"] = details.get("after_sha256")
            if record["actual_sha256"] == details.get("after_sha256"):
                record["status"] = "DOCUMENTED_PUBLIC_RELEASE_SANITIZATION"
            else:
                record["status"] = "UNEXPLAINED_HASH_MISMATCH"

    arrays = []
    recovery_log_path = OUT / "CYAN_ARRAY_RECOVERY_LOG.json"
    recovered_cyan = set()
    if recovery_log_path.exists():
        recovery_log = json.loads(recovery_log_path.read_text())
        recovered_cyan = {
            record["sample_id"]
            for record in recovery_log.get("records", [])
            if record.get("disposition") in {"RECOVERED_AND_VERIFIED", "PREEXISTING_VERIFIED"}
        }
    source_files = {item["key"]: item for item in json.loads((ROOT / "data/metadata/sources/zenodo_record.json").read_text())["files"]}
    for row in v2["samples"]:
        source = source_files[row["archive"]]
        for kind, path_key, hash_key, member_key in (
            ("cyan_reference_array", "cyan_path", "cyan_sha256", "member"),
            ("sentinel2_input_array", "sen2_path", "sen2_sha256", "sen2_member"),
        ):
            path = row[path_key]
            record = verify_expected_file(ROOT, path, row[hash_key])
            if record["status"] == "VERIFIED" and kind == "cyan_reference_array" and row["sample_id"] in recovered_cyan:
                rebuild_status = "RECOVERED_FROM_ZENODO_RANGE_AND_HASH_VERIFIED_2026-10-12"
            elif record["status"] == "VERIFIED":
                rebuild_status = "LOCAL_FILE_HASH_VERIFIED_2026-10-12"
            elif kind == "sentinel2_input_array":
                rebuild_status = "NOT_RECOVERED; REQUIRES_VERIFIED_ZIP_CENTRAL_DIRECTORY_ENTRY"
            else:
                rebuild_status = "NOT_RECOVERED"
            record.update(
                {
                    "kind": kind,
                    "sample_id": row["sample_id"],
                    "dataset_record": "https://doi.org/10.5281/zenodo.14230064",
                    "dataset_archive": row["archive"],
                    "dataset_archive_md5": source["checksum"],
                    "source_member": row[member_key],
                    "rebuild_status": rebuild_status,
                    "rebuild_command": "python scripts/index_phase3_5.py && python scripts/prepare_phase3_5_pairs.py",
                }
            )
            arrays.append(record)

    return {
        "schema_version": "phase3a_artifact_provenance_v1",
        "generated_date": "2026-10-12",
        "repository_head": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "model_training_performed": False,
        "source_snapshot": {
            "path": "data/metadata/sources/zenodo_record.json",
            "sha256": sha256_file(ROOT / "data/metadata/sources/zenodo_record.json"),
            "record": "https://doi.org/10.5281/zenodo.14230064",
            "license_in_snapshot": "cc-by-4.0",
            "upstream_code_commit": "e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37",
        },
        "phase5_preservation_inventory": {
            "source_manifest": "data/metadata/phase5/preservation_manifest.json",
            "source_manifest_sha256": sha256_file(ROOT / "data/metadata/phase5/preservation_manifest.json"),
            "record_count": len(records),
            "status_counts": summary_counts(records),
            "records": records,
        },
        "v2_pair_arrays": {
            "expected_arrays": len(arrays),
            "expected_samples": len(v2["samples"]),
            "status_counts": summary_counts(arrays),
            "records": arrays,
        },
        "recovery_search": {
            "local_repository_copies_searched": True,
            "git_history_searched": True,
            "git_lfs_entries": 0,
            "large_artifact_local_hits": 0,
            "remote_attempts": [
                "Zenodo API content endpoint returned HTTP 504 for an exact range request.",
                "Official Zenodo record file endpoint returned HTTP 206; all 288 frozen v2 CyAN arrays were recovered and SHA-256 verified.",
            ],
            "cyan_recovery_log": (
                {
                    "path": "research_upgrade_v3/phase3a/CYAN_ARRAY_RECOVERY_LOG.json",
                    "sha256": sha256_file(recovery_log_path),
                    "verified_arrays": len(recovered_cyan),
                }
                if recovery_log_path.exists()
                else None
            ),
        },
    }


def main() -> None:
    split_path = ROOT / "data/metadata/phase3_5/geographic_split_v2.csv"
    census_path = ROOT / "data/metadata/phase3_5/reference_census_round2.csv"
    split_rows = read_csv(split_path)
    census_rows = read_csv(census_path)
    census = {row["sample_id"]: row for row in census_rows}
    validate_split_membership(split_rows)

    identities = build_identity_table(split_rows, census)
    write_csv(OUT / "GEOGRAPHIC_IDENTITY_TABLE.csv", identities, list(identities[0]))

    overlaps = build_overlap_audit(split_rows)
    write_csv(OUT / "SPLIT_OVERLAP_AUDIT.csv", overlaps, list(overlaps[0]))

    selected_support = high_support_by_selected_group(split_rows, census)
    screened = json.loads((ROOT / "research_outputs/phase3_5/group_support.json").read_text())
    selected = {row["geographic_group_id"]: row for row in selected_support}
    support_rows = []
    for row in screened:
        current = selected.get(row["geographic_group_id"], {})
        support_rows.append(
            {
                "geographic_group_id": row["geographic_group_id"],
                "evidence_scope": "38,002_DECODED_SUPPORT_SCREENING_MASKS_NOT_FULL_DEPOSIT",
                "screened_patches": row["patches"],
                "screened_high_patches": row["high_patches"],
                "screened_high_pixels": row["high_pixels"],
                "screened_valid_pixels": row["valid_pixels"],
                "screened_high_percent_valid": row["high_percent"],
                "screened_high_dates": row["high_date_count"],
                "screened_high_date_span_days": row["high_date_span_days"],
                "screened_high_patch_positions": row["high_patch_positions"],
                "historical_support_gate_qualifies": row.get("qualifies", False),
                "v2_split": current.get("split", "NOT_SELECTED"),
                "v2_selected_patches": current.get("selected_patches", 0),
                "v2_high_patches": current.get("high_patches", 0),
                "v2_high_pixels": current.get("high_pixels", 0),
                "v2_valid_pixels": current.get("valid_pixels", 0),
                "v2_high_percent_valid": current.get("high_percent_valid", 0.0),
                "component_identity_status": "VERIFIED_AUTHOR_GRID_COMPONENT_ONLY",
                "lake_identity_status": "UNVERIFIED",
                "scene_identity_status": "UNVERIFIED",
                "bloom_event_identity_status": "UNVERIFIED",
            }
        )
    write_csv(OUT / "HIGH_SUPPORT_BY_GROUP.csv", support_rows, list(support_rows[0]))

    v2 = json.loads((ROOT / "data/metadata/phase3_5/geographic_split_v2.json").read_text())
    manifest = artifact_manifest(v2)
    (OUT / "ARTIFACT_PROVENANCE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )

    result = {
        "identity_rows": len(identities),
        "overlap_rows": len(overlaps),
        "group_rows": len(support_rows),
        "artifact_status": manifest["phase5_preservation_inventory"]["status_counts"],
        "array_status": manifest["v2_pair_arrays"]["status_counts"],
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()


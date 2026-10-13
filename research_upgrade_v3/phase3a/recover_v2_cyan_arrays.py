"""Recover only the frozen v2 CyAN label arrays from verified ZIP byte ranges.

This is a bounded artifact-recovery utility, not a model-training program.  It
never downloads a complete archive, refuses HTTP 200 fallbacks, verifies the
ZIP member identity/CRC/size, and verifies the historical SHA-256 before save.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests

from aquavision.data.download import save_member
from aquavision.data.reference_ranges import coalesce_touching, decode_zip_member, parse_multipart


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SELECTION = ROOT / "data/metadata/phase3_5/geographic_split_v2.json"
SOURCE_SNAPSHOT = ROOT / "data/metadata/sources/zenodo_record.json"
LOG_PATH = OUT / "CYAN_ARRAY_RECOVERY_LOG.json"
RECORD_ID = 14230064
BATCH_SIZE = 24
MAX_TOTAL_RESPONSE_BYTES = 8_000_000


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def source_url(archive: str) -> str:
    """Use the record file endpoint; the API content endpoint returned 504."""
    return f"https://zenodo.org/records/{RECORD_ID}/files/{archive}?download=1"


def read_exact_ranges(
    session: requests.Session,
    url: str,
    archive_size: int,
    ranges: list[tuple[int, int]],
) -> dict[tuple[int, int], bytes]:
    ranges = coalesce_touching(ranges)
    cap = sum(end - start + 1 for start, end in ranges) + 1024 * len(ranges) + 4096
    if cap > MAX_TOTAL_RESPONSE_BYTES:
        raise ValueError(f"Bounded response cap exceeded: {cap}")
    header = "bytes=" + ",".join(f"{start}-{end}" for start, end in ranges)
    with session.get(
        url,
        headers={"Range": header, "Accept-Encoding": "identity"},
        stream=True,
        timeout=(15, 60),
    ) as response:
        if response.status_code != 206:
            raise ValueError(f"Expected HTTP 206, got {response.status_code}; full response refused")
        if response.headers.get("Content-Encoding", "identity") != "identity":
            raise ValueError("Encoded byte ranges are not accepted")
        declared = response.headers.get("Content-Length")
        if declared is not None and int(declared) > cap:
            raise ValueError("Declared response exceeds bounded cap")
        body = response.raw.read(cap + 1)
        if len(body) > cap:
            raise ValueError("Response exceeds bounded cap")
        if len(ranges) == 1:
            start, end = ranges[0]
            expected = f"bytes {start}-{end}/{archive_size}"
            if response.headers.get("Content-Range") != expected or len(body) != end - start + 1:
                raise ValueError("Single-range response identity mismatch")
            return {ranges[0]: body}
        return parse_multipart(body, ranges, archive_size)


def recover_batch(
    session: requests.Session,
    archive: str,
    archive_size: int,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    individual = [
        (int(row["header_offset"]), int(row["header_offset"]) + int(row["span_bytes"]) - 1)
        for row in rows
    ]
    if any(end - start + 1 > 200_000 for start, end in individual):
        raise ValueError("Unexpectedly large CyAN member range")
    requested = coalesce_touching(individual)
    parts = read_exact_ranges(session, source_url(archive), archive_size, requested)
    recovered = []
    for row, (start, end) in zip(rows, individual):
        owner = next((a, b) for a, b in requested if a <= start <= end <= b)
        payload = parts[owner][start - owner[0] : end - owner[0] + 1]
        raw = decode_zip_member(payload, row)
        actual = sha256_bytes(raw)
        if actual != row["cyan_sha256"]:
            raise ValueError(f"Historical SHA-256 mismatch for {row['sample_id']}")
        destination = ROOT / row["cyan_path"]
        if destination.exists():
            if hashlib.sha256(destination.read_bytes()).hexdigest() != actual:
                raise ValueError(f"Refusing to overwrite mismatched file: {row['cyan_path']}")
            disposition = "PREEXISTING_VERIFIED"
        else:
            save_member(destination, raw)
            disposition = "RECOVERED_AND_VERIFIED"
        recovered.append(
            {
                "sample_id": row["sample_id"],
                "archive": archive,
                "member": row["member"],
                "destination": row["cyan_path"],
                "sha256": actual,
                "size_bytes": len(raw),
                "disposition": disposition,
            }
        )
    return recovered


def main() -> None:
    selection = json.loads(SELECTION.read_text())
    catalog = json.loads(SOURCE_SNAPSHOT.read_text())
    source = {item["key"]: item for item in catalog["files"]}
    by_archive: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in selection["samples"]:
        by_archive[row["archive"]].append(row)

    records: list[dict[str, Any]] = []
    requests_made = 0
    with requests.Session() as session:
        for archive, rows in sorted(by_archive.items()):
            rows.sort(key=lambda row: int(row["header_offset"]))
            for offset in range(0, len(rows), BATCH_SIZE):
                batch = rows[offset : offset + BATCH_SIZE]
                records.extend(recover_batch(session, archive, int(source[archive]["size"]), batch))
                requests_made += 1
                print(f"{archive}: {min(offset + BATCH_SIZE, len(rows))}/{len(rows)} verified", flush=True)

    if len(records) != len(selection["samples"]):
        raise ValueError("Recovery did not cover every frozen v2 CyAN label array")
    records.sort(key=lambda row: row["sample_id"])
    log = {
        "schema_version": "phase3a_cyan_recovery_v1",
        "recovery_date": "2026-10-12",
        "record": "https://doi.org/10.5281/zenodo.14230064",
        "source_snapshot": "data/metadata/sources/zenodo_record.json",
        "method": "bounded HTTP byte ranges; HTTP 206 required; ZIP CRC/size/member and historical SHA-256 verified",
        "model_training_performed": False,
        "full_archive_downloaded": False,
        "requests_made": requests_made,
        "expected_arrays": len(selection["samples"]),
        "verified_arrays": len(records),
        "records": records,
    }
    LOG_PATH.write_text(json.dumps(log, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verified_arrays": len(records), "requests_made": requests_made}, indent=2))


if __name__ == "__main__":
    main()

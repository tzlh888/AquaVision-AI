"""Recover frozen v2 Sentinel-2 arrays from exact Zenodo ZIP members.

The utility performs no model fitting.  It first reads only the required ZIP
central directories through bounded HTTP ranges, then fetches only the 288
frozen members.  Existing files are never overwritten unless already identical.
"""

from __future__ import annotations

import hashlib
import json
import struct
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests

from aquavision.data.download import ByteBudget, HTTPRangeReader, save_member
from aquavision.data.reference_ranges import coalesce_touching, decode_zip_member, parse_multipart


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SELECTION = ROOT / "data/metadata/phase3_5/geographic_split_v2.json"
SOURCE_SNAPSHOT = ROOT / "data/metadata/sources/zenodo_record.json"
PAIR_ACCESS = ROOT / "data/metadata/phase3_5/pair_access.jsonl"
PRESERVATION_MANIFEST = ROOT / "data/metadata/phase5/preservation_manifest.json"
LOG_PATH = OUT / "SENTINEL_ARRAY_RECOVERY_LOG.json"
RECORD_ID = 14230064
INDEX_BUDGET_BYTES = 80_000_000
MAX_BATCH_RESPONSE_BYTES = 8_000_000
BATCH_SIZE = 24
INDEX_RANGE_CHUNK_BYTES = 2_000_000
LOGGED_RANGE_BATCH_SIZE = 8


class ChunkedRangeReader(HTTPRangeReader):
    """Keep central-directory reads bounded to avoid one 48 MB response."""

    def read(self, size: int = -1) -> bytes:
        available = max(0, self.size - self.position)
        wanted = available if size < 0 else min(available, size)
        parts = []
        remaining = wanted
        while remaining:
            count = min(remaining, INDEX_RANGE_CHUNK_BYTES)
            parts.append(super().read(count))
            remaining -= count
        return b"".join(parts)


def source_url(archive: str) -> str:
    return f"https://zenodo.org/records/{RECORD_ID}/files/{archive}?download=1"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def local_entry(payload: bytes, archive: str) -> dict[str, Any]:
    """Read a small member's authoritative local ZIP header."""
    if len(payload) < 30:
        raise ValueError("Truncated local ZIP header")
    values = struct.unpack("<4s5H3I2H", payload[:30])
    signature, _, flags, compression, _, _, crc32, compressed, size, name_len, extra_len = values
    if signature != b"PK\x03\x04" or flags & 1:
        raise ValueError("Invalid or encrypted local ZIP member")
    if flags & 8:
        raise ValueError("Data-descriptor member cannot be verified from the frozen range log")
    if compressed == 0xFFFFFFFF or size == 0xFFFFFFFF:
        raise ValueError("Unexpected ZIP64 size in small member local header")
    name = payload[30 : 30 + name_len].decode("utf-8" if flags & 0x800 else "cp437")
    expected_span = 30 + name_len + extra_len + compressed
    if expected_span > len(payload):
        raise ValueError("Logged range truncates ZIP member")
    return {
        "archive": archive,
        "member": name,
        "compression": compression,
        "compressed_bytes": compressed,
        "size_bytes": size,
        "crc32": f"{crc32:08x}",
    }


def index_required_members(
    catalog: dict[str, dict[str, Any]], required: dict[str, set[str]]
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], int]:
    """Read central directories and return metadata only for frozen members."""
    entries: dict[str, dict[str, Any]] = {}
    access: list[dict[str, Any]] = []
    budget = ByteBudget(INDEX_BUDGET_BYTES)
    with requests.Session() as session:
        for archive_name in sorted(required):
            source = catalog[archive_name]
            with ChunkedRangeReader(
                source_url(archive_name), int(source["size"]), budget, session=session
            ) as remote:
                with zipfile.ZipFile(remote) as archive:
                    infos = sorted(
                        (info for info in archive.infolist() if not info.is_dir()),
                        key=lambda info: info.header_offset,
                    )
                    start_dir = archive.start_dir
                    for index, info in enumerate(infos):
                        if info.filename not in required[archive_name]:
                            continue
                        next_offset = infos[index + 1].header_offset if index + 1 < len(infos) else start_dir
                        entries[info.filename] = {
                            "archive": archive_name,
                            "member": info.filename,
                            "header_offset": info.header_offset,
                            "span_bytes": next_offset - info.header_offset,
                            "compressed_bytes": info.compress_size,
                            "size_bytes": info.file_size,
                            "crc32": f"{info.CRC:08x}",
                            "compression": info.compress_type,
                        }
                access.append(
                    {
                        "archive": archive_name,
                        "source_url": source_url(archive_name),
                        "requests": remote.requests_log,
                        "charged_index_bytes_so_far": budget.used,
                    }
                )
    expected = set().union(*required.values())
    missing = sorted(expected - set(entries))
    if missing:
        raise ValueError(f"Frozen Sentinel members missing from central directories: {missing[:3]}")
    return entries, access, budget.used


def read_exact_ranges(
    session: requests.Session,
    url: str,
    archive_size: int,
    ranges: list[tuple[int, int]],
) -> dict[tuple[int, int], bytes]:
    ranges = coalesce_touching(ranges)
    cap = sum(end - start + 1 for start, end in ranges) + 1024 * len(ranges) + 4096
    if cap > MAX_BATCH_RESPONSE_BYTES:
        raise ValueError(f"Bounded member-response cap exceeded: {cap}")
    with session.get(
        url,
        headers={
            "Range": "bytes=" + ",".join(f"{start}-{end}" for start, end in ranges),
            "Accept-Encoding": "identity",
        },
        stream=True,
        timeout=(15, 60),
    ) as response:
        if response.status_code != 206:
            raise ValueError(f"Expected HTTP 206, got {response.status_code}; full response refused")
        if response.headers.get("Content-Encoding", "identity") != "identity":
            raise ValueError("Encoded byte-range response refused")
        declared = response.headers.get("Content-Length")
        if declared is not None and int(declared) > cap:
            raise ValueError("Declared member response exceeds cap")
        body = response.raw.read(cap + 1)
        if len(body) > cap:
            raise ValueError("Member response exceeds cap")
        if len(ranges) == 1:
            start, end = ranges[0]
            expected = f"bytes {start}-{end}/{archive_size}"
            if response.headers.get("Content-Range") != expected or len(body) != end - start + 1:
                raise ValueError("Single-range identity mismatch")
            return {ranges[0]: body}
        return parse_multipart(body, ranges, archive_size)


def recover_batch(
    session: requests.Session,
    source: dict[str, Any],
    rows: list[dict[str, Any]],
    entries: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    infos = [entries[row["sen2_member"]] for row in rows]
    individual = [
        (int(info["header_offset"]), int(info["header_offset"]) + int(info["span_bytes"]) - 1)
        for info in infos
    ]
    if any(end - start + 1 > 200_000 for start, end in individual):
        raise ValueError("Unexpectedly large Sentinel member range")
    requested = coalesce_touching(individual)
    parts = read_exact_ranges(
        session, source_url(source["key"]), int(source["size"]), requested
    )
    records = []
    for row, info, (start, end) in zip(rows, infos, individual):
        owner = next((a, b) for a, b in requested if a <= start <= end <= b)
        payload = parts[owner][start - owner[0] : end - owner[0] + 1]
        raw = decode_zip_member(payload, info)
        actual = sha256_bytes(raw)
        if actual != row["sen2_sha256"]:
            raise ValueError(f"Frozen Sentinel SHA-256 mismatch for {row['sample_id']}")
        destination = ROOT / row["sen2_path"]
        if destination.exists():
            if hashlib.sha256(destination.read_bytes()).hexdigest() != actual:
                raise ValueError(f"Refusing to overwrite mismatched file: {row['sen2_path']}")
            disposition = "PREEXISTING_VERIFIED"
        else:
            save_member(destination, raw)
            disposition = "RECOVERED_AND_VERIFIED"
        records.append(
            {
                "sample_id": row["sample_id"],
                "archive": source["key"],
                "member": row["sen2_member"],
                "destination": row["sen2_path"],
                "sha256": actual,
                "size_bytes": len(raw),
                "shape": [12, 64, 64],
                "dtype": "uint16",
                "disposition": disposition,
            }
        )
    return records


def recover_from_frozen_range_log(
    catalog: dict[str, dict[str, Any]], selection: dict[str, Any]
) -> tuple[list[dict[str, Any]], int, str]:
    preservation = json.loads(PRESERVATION_MANIFEST.read_text())["files"]
    expected_log_hash = preservation["data/metadata/phase3_5/pair_access.jsonl"]
    actual_log_hash = hashlib.sha256(PAIR_ACCESS.read_bytes()).hexdigest()
    if actual_log_hash != expected_log_hash:
        raise ValueError("Frozen pair-access log hash mismatch")
    rows_by_member = {row["sen2_member"]: row for row in selection["samples"]}
    ranges_by_archive: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for line in PAIR_ACCESS.read_text().splitlines():
        event = json.loads(line)
        if event.get("status") != 206:
            raise ValueError("Historical pair-access log contains a non-206 response")
        ranges_by_archive[event["archive"]].extend(tuple(pair) for pair in event["ranges"])
    if sum(len(items) for items in ranges_by_archive.values()) != len(rows_by_member):
        raise ValueError("Historical pair-access range count disagrees with frozen selection")

    recovered: list[dict[str, Any]] = []
    seen_members: set[str] = set()
    requests_made = 0
    with requests.Session() as session:
        for archive_name, ranges in sorted(ranges_by_archive.items()):
            ranges.sort()
            for offset in range(0, len(ranges), LOGGED_RANGE_BATCH_SIZE):
                batch = ranges[offset : offset + LOGGED_RANGE_BATCH_SIZE]
                parts = read_exact_ranges(
                    session,
                    source_url(archive_name),
                    int(catalog[archive_name]["size"]),
                    batch,
                )
                requests_made += 1
                for byte_range in batch:
                    payload = parts[byte_range]
                    entry = local_entry(payload, archive_name)
                    member = entry["member"]
                    if member not in rows_by_member or member in seen_members:
                        raise ValueError(f"Unexpected or duplicate frozen member: {member}")
                    row = rows_by_member[member]
                    raw = decode_zip_member(payload, entry)
                    actual = sha256_bytes(raw)
                    if actual != row["sen2_sha256"]:
                        raise ValueError(f"Frozen Sentinel SHA-256 mismatch for {row['sample_id']}")
                    destination = ROOT / row["sen2_path"]
                    if destination.exists():
                        if hashlib.sha256(destination.read_bytes()).hexdigest() != actual:
                            raise ValueError(f"Refusing to overwrite mismatched file: {row['sen2_path']}")
                        disposition = "PREEXISTING_VERIFIED"
                    else:
                        save_member(destination, raw)
                        disposition = "RECOVERED_AND_VERIFIED"
                    recovered.append(
                        {
                            "sample_id": row["sample_id"],
                            "archive": archive_name,
                            "member": member,
                            "destination": row["sen2_path"],
                            "sha256": actual,
                            "size_bytes": len(raw),
                            "shape": [12, 64, 64],
                            "dtype": "uint16",
                            "disposition": disposition,
                        }
                    )
                    seen_members.add(member)
                print(
                    f"{archive_name}: {min(offset + LOGGED_RANGE_BATCH_SIZE, len(ranges))}/{len(ranges)} verified",
                    flush=True,
                )
    if seen_members != set(rows_by_member):
        raise ValueError("Frozen range recovery did not cover every Sentinel member")
    return recovered, requests_made, actual_log_hash


def main() -> None:
    selection = json.loads(SELECTION.read_text())
    source_items = json.loads(SOURCE_SNAPSHOT.read_text())["files"]
    catalog = {item["key"]: item for item in source_items}
    recovered, member_requests, pair_access_sha256 = recover_from_frozen_range_log(
        catalog, selection
    )

    if len(recovered) != len(selection["samples"]):
        raise ValueError("Recovery did not cover every frozen v2 Sentinel array")
    recovered.sort(key=lambda row: row["sample_id"])
    log = {
        "schema_version": "phase3a1_sentinel_recovery_v1",
        "recovery_date": "2026-10-12",
        "record": "https://doi.org/10.5281/zenodo.14230064",
        "source_snapshot": "data/metadata/sources/zenodo_record.json",
        "method": "historical exact-member ranges from hash-verified pair_access.jsonl; bounded HTTP 206; local ZIP header/member/CRC/size and frozen SHA-256 verified",
        "model_training_performed": False,
        "full_archive_downloaded": False,
        "index_bytes_charged": 0,
        "member_requests": member_requests,
        "expected_arrays": len(selection["samples"]),
        "verified_arrays": len(recovered),
        "historical_pair_access_log": {
            "path": "data/metadata/phase3_5/pair_access.jsonl",
            "sha256": pair_access_sha256,
            "range_count": 288,
        },
        "records": recovered,
    }
    LOG_PATH.write_text(json.dumps(log, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verified_arrays": len(recovered), "index_bytes": 0, "member_requests": member_requests}, indent=2))


if __name__ == "__main__":
    main()

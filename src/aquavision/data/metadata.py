"""Parse published filenames without pretending grid indices are coordinates."""

from __future__ import annotations

import csv
import re
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path, PurePosixPath

PATTERN = re.compile(
    r"(?P<region>\d+_\d+)_X(?P<subtile_x>\d+)_Y(?P<subtile_y>\d+)_S(?P<subtile_size>\d+)_"
    r"(?P<year>\d{4})_(?P<month>\d{2})_(?P<day>\d{2})_"
    r"x(?P<patch_row>\d+)_y(?P<patch_col>\d+)_"
    r"(?P<height>\d+)x(?P<width>\d+)_(?P<sequence>\d+)_(?P<kind>sen2|cyan)\.npy"
)


def parse_member(name: str) -> dict:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name:
        raise ValueError(f"Unsafe archive member: {name}")
    match = PATTERN.fullmatch(path.name)
    if not match:
        raise ValueError(f"Unrecognized sample filename: {name}")
    parts = match.groupdict()
    for key in parts.keys() - {"region", "kind"}:
        parts[key] = int(parts[key])
    parts["acquisition_date"] = date(parts["year"], parts["month"], parts["day"]).isoformat()
    parts["sample_id"] = path.name.rsplit("_", 1)[0]
    parts["spatial_group_candidate"] = path.name.split(f"_{parts['year']}_")[0]
    parts["grid_position_candidate"] = (
        f"{parts['spatial_group_candidate']}_x{parts['patch_row']}_y{parts['patch_col']}"
    )
    # The names contain no measured coordinates or water-body identifier.
    parts.update(latitude=None, longitude=None, water_body_id=None)
    return parts


def build_inventory(archive: zipfile.ZipFile) -> tuple[list[dict], list[dict], dict]:
    members, pairs = [], defaultdict(dict)
    unrecognized, duplicates = [], []
    seen = set()
    for info in archive.infolist():
        if info.is_dir():
            continue
        if info.filename in seen:
            duplicates.append(info.filename)
        seen.add(info.filename)
        row = {"member": info.filename, "size_bytes": info.file_size,
               "compressed_bytes": info.compress_size, "crc32": f"{info.CRC:08x}"}
        members.append(row)
        try:
            parsed = parse_member(info.filename)
        except ValueError:
            unrecognized.append(info.filename)
            continue
        record = pairs[parsed["sample_id"]]
        if parsed["kind"] in record:
            raise ValueError(f"Ambiguous sample/kind: {info.filename}")
        record[parsed["kind"]] = info.filename
        record["metadata"] = {k: v for k, v in parsed.items() if k != "kind"}
    if duplicates:
        raise ValueError(f"Duplicate archive names: {duplicates[:5]}")
    rows, unpaired = [], []
    for sample_id, record in sorted(pairs.items()):
        if not {"sen2", "cyan"} <= record.keys():
            unpaired.append(sample_id)
            continue
        rows.append({**record["metadata"], "sen2_member": record["sen2"], "cyan_member": record["cyan"]})
    summary = {"file_members": len(members), "paired_samples": len(rows),
               "unpaired_sample_ids": unpaired, "unrecognized_members": unrecognized,
               "regions": sorted({r["region"] for r in rows}),
               "candidate_spatial_groups": len({r["spatial_group_candidate"] for r in rows}),
               "date_min": min((r["acquisition_date"] for r in rows), default=None),
               "date_max": max((r["acquisition_date"] for r in rows), default=None)}
    return members, rows, summary


def select_inspection_pairs(rows: list[dict], count: int) -> list[dict]:
    """Evenly spaced sorted IDs: reproducible access probe, not statistical sampling."""
    if not 1 <= count <= 8:
        raise ValueError("Phase 1 allows 1-8 pairs per archive")
    if len(rows) < count:
        raise ValueError("Not enough pairs")
    rows = sorted(rows, key=lambda row: row["sample_id"])
    indices = [0] if count == 1 else [i * (len(rows) - 1) // (count - 1) for i in range(count)]
    return [rows[i] for i in indices]


def write_csv(path: Path, rows: list[dict], fieldnames=None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows and not fieldnames:
        raise ValueError("Empty CSV needs explicit columns")
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

"""Phase 3A evidence audit helpers.

This module is deliberately independent of the historical training code.  It reads
saved metadata and results, never fits a model, and represents missing geographic
provenance as UNKNOWN rather than manufacturing identifiers.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence


UNKNOWN = "UNVERIFIED"
SPLITS = ("train", "validation", "test")
SAMPLE_RE = re.compile(
    r"(?P<tile>\d+_\d+)_X(?P<subtile_x>\d+)_Y(?P<subtile_y>\d+)_S(?P<subtile_size>\d+)_"
    r"(?P<year>\d{4})_(?P<month>\d{2})_(?P<day>\d{2})_"
    r"x(?P<patch_row>\d+)_y(?P<patch_col>\d+)_"
    r"(?P<height>\d+)x(?P<width>\d+)_(?P<sequence>\d+)"
)


class AuditError(ValueError):
    """Raised when evidence violates a frozen audit invariant."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def cyan_dn_class(value: int) -> str:
    """Map a stored processed CyAN DN to the paper's diagnostic pixel bin."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise AuditError("CyAN DN must be an integer")
    if 0 <= value <= 99:
        return "Low"
    if 100 <= value <= 199:
        return "Moderate"
    if 200 <= value <= 253:
        return "High"
    if value in (254, 255):
        return "IGNORE"
    raise AuditError("CyAN DN must be in [0, 255]")


def parse_sample_id(sample_id: str) -> dict[str, object]:
    match = SAMPLE_RE.fullmatch(sample_id)
    if not match:
        raise AuditError(f"Unrecognized sample ID: {sample_id}")
    row: dict[str, object] = match.groupdict()
    for key in set(row) - {"tile"}:
        row[key] = int(row[key])
    row["date"] = f"{row['year']:04d}-{row['month']:02d}-{row['day']:02d}"
    row["subtile_id"] = (
        f"{row['tile']}_X{row['subtile_x']:04d}_Y{row['subtile_y']:04d}_"
        f"S{row['subtile_size']:03d}"
    )
    row["patch_position_candidate"] = (
        f"{row['subtile_id']}_x{row['patch_row']}_y{row['patch_col']}_"
        f"{row['height']}x{row['width']}"
    )
    return row


@dataclass(frozen=True)
class Rectangle:
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    crs: str

    def __post_init__(self) -> None:
        if not self.crs or self.crs == UNKNOWN:
            raise AuditError("A verified CRS is required for footprint comparison")
        if not self.xmin < self.xmax or not self.ymin < self.ymax:
            raise AuditError("Invalid rectangle bounds")


def rectangles_overlap(left: Rectangle, right: Rectangle) -> bool:
    if left.crs != right.crs:
        raise AuditError("Footprints in different CRS cannot be compared directly")
    return not (
        left.xmax <= right.xmin
        or right.xmax <= left.xmin
        or left.ymax <= right.ymin
        or right.ymax <= left.ymin
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: Sequence[Mapping[str, object]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=fieldnames, extrasaction="raise", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def validate_split_membership(rows: Sequence[Mapping[str, str]]) -> None:
    if not rows:
        raise AuditError("Split table is empty")
    sample_ids = [row["sample_id"] for row in rows]
    if len(sample_ids) != len(set(sample_ids)):
        raise AuditError("Duplicate sample IDs")
    if set(row["split"] for row in rows) != set(SPLITS):
        raise AuditError("Expected nonempty train/validation/test splits")
    owner: dict[tuple[str, str], str] = {}
    for row in rows:
        for key in ("spatial_group_id", "source_subtile"):
            identity = (key, row[key])
            split = row["split"]
            if identity in owner and owner[identity] != split:
                raise AuditError(f"Cross-split {key}: {row[key]}")
            owner[identity] = split


def overlap_count(rows: Sequence[Mapping[str, str]], key: str, left: str, right: str) -> tuple[int, list[str]]:
    left_values = {row[key] for row in rows if row["split"] == left and row.get(key)}
    right_values = {row[key] for row in rows if row["split"] == right and row.get(key)}
    values = sorted(left_values & right_values)
    return len(values), values


def high_support_by_selected_group(
    split_rows: Sequence[Mapping[str, str]], census: Mapping[str, Mapping[str, str]]
) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in split_rows:
        if row["sample_id"] not in census:
            raise AuditError(f"Missing census row: {row['sample_id']}")
        grouped[row["spatial_group_id"]].append(row)
    output: list[dict[str, object]] = []
    for group, rows in sorted(grouped.items()):
        supports = [census[row["sample_id"]] for row in rows]
        high_pixels = sum(int(row["high_pixels"]) for row in supports)
        valid_pixels = sum(int(row["valid_pixels"]) for row in supports)
        output.append(
            {
                "geographic_group_id": group,
                "split": rows[0]["split"],
                "selected_patches": len(rows),
                "high_patches": sum(int(row["high_pixels"]) > 0 for row in supports),
                "high_pixels": high_pixels,
                "valid_pixels": valid_pixels,
                "high_percent_valid": 100.0 * high_pixels / valid_pixels if valid_pixels else 0.0,
                "distinct_dates": len({row["date"] for row in rows}),
                "high_dates": len(
                    {
                        row["date"]
                        for row, support in zip(rows, supports)
                        if int(support["high_pixels"]) > 0
                    }
                ),
                "source_tiles": "|".join(sorted({parse_sample_id(row["sample_id"])["tile"] for row in rows})),
                "component_identity_status": "VERIFIED_AUTHOR_GRID_COMPONENT_ONLY",
                "lake_identity_status": UNKNOWN,
                "scene_identity_status": UNKNOWN,
                "bloom_event_identity_status": UNKNOWN,
            }
        )
    return output


@dataclass(frozen=True)
class QualificationThresholds:
    high_recall: float = 0.50
    high_f1: float = 0.50
    low_f1: float = 0.50
    moderate_f1: float = 0.40
    macro_f1: float = 0.50
    minimum_high_components: int = 3

    def __post_init__(self) -> None:
        numbers = (self.high_recall, self.high_f1, self.low_f1, self.moderate_f1, self.macro_f1)
        if any(not 0 <= value <= 1 for value in numbers):
            raise AuditError("Metric thresholds must lie in [0, 1]")
        if self.minimum_high_components < 1:
            raise AuditError("At least one High component is required")


def qualification_decision(
    metrics: Mapping[str, float | int | None],
    *,
    thresholds: QualificationThresholds = QualificationThresholds(),
) -> tuple[bool, list[str]]:
    """Apply the frozen exploratory qualification gate without ranking models."""
    required = {
        "high_recall": thresholds.high_recall,
        "high_f1": thresholds.high_f1,
        "low_f1": thresholds.low_f1,
        "moderate_f1": thresholds.moderate_f1,
        "macro_f1": thresholds.macro_f1,
    }
    reasons: list[str] = []
    for name, floor in required.items():
        value = metrics.get(name)
        if value is None:
            reasons.append(f"{name}=UNDEFINED")
        elif not isinstance(value, (int, float)) or isinstance(value, bool):
            reasons.append(f"{name}=INVALID")
        elif value < floor:
            reasons.append(f"{name}<{floor:.2f}")
    components = metrics.get("high_components")
    if not isinstance(components, int) or isinstance(components, bool):
        reasons.append("high_components=INVALID")
    elif components < thresholds.minimum_high_components:
        reasons.append(f"high_components<{thresholds.minimum_high_components}")
    component_recalls = metrics.get("component_high_recalls")
    if not isinstance(component_recalls, Sequence) or isinstance(component_recalls, (str, bytes)):
        reasons.append("component_high_recalls=MISSING")
    else:
        if len(component_recalls) != components:
            reasons.append("component_high_recalls=COUNT_MISMATCH")
        elif any(value is None for value in component_recalls):
            reasons.append("component_high_recall=UNDEFINED")
        elif any(not isinstance(value, (int, float)) or isinstance(value, bool) for value in component_recalls):
            reasons.append("component_high_recall=INVALID")
        elif any(value <= 0 for value in component_recalls):
            reasons.append("component_high_recall=ZERO")
    return not reasons, reasons


def verify_expected_file(root: Path, path: str, expected_sha256: str) -> dict[str, object]:
    candidate = root / path
    if not candidate.is_file():
        return {
            "path": path,
            "expected_sha256": expected_sha256,
            "status": "MISSING_LOCAL",
            "actual_sha256": None,
            "bytes": None,
        }
    actual = sha256_file(candidate)
    return {
        "path": path,
        "expected_sha256": expected_sha256,
        "status": "VERIFIED" if actual == expected_sha256 else "HASH_MISMATCH",
        "actual_sha256": actual,
        "bytes": candidate.stat().st_size,
    }


def build_identity_table(
    split_rows: Sequence[Mapping[str, str]], census: Mapping[str, Mapping[str, str]]
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in sorted(split_rows, key=lambda item: item["sample_id"]):
        parsed = parse_sample_id(row["sample_id"])
        support = census.get(row["sample_id"])
        if support is None:
            raise AuditError(f"Missing reference census row: {row['sample_id']}")
        if parsed["date"] != row["date"] or parsed["subtile_id"] != row["source_subtile"]:
            raise AuditError(f"Filename/manifest identity conflict: {row['sample_id']}")
        valid = int(support["valid_pixels"])
        high = int(support["high_pixels"])
        output.append(
            {
                "sample_id": row["sample_id"],
                "split": row["split"],
                "geographic_component_id": row["spatial_group_id"],
                "component_evidence": "AUTHOR_GRID_CONNECTED_COMPONENT",
                "source_cyan_tile": parsed["tile"],
                "source_subtile": row["source_subtile"],
                "acquisition_date": row["date"],
                "acquisition_time": UNKNOWN,
                "sentinel_product_id": UNKNOWN,
                "sentinel_scene_id": UNKNOWN,
                "lake_waterbody_id": UNKNOWN,
                "footprint_geometry": UNKNOWN,
                "crs": UNKNOWN,
                "bloom_event_id": UNKNOWN,
                "patch_row": parsed["patch_row"],
                "patch_col": parsed["patch_col"],
                "patch_height": parsed["height"],
                "patch_width": parsed["width"],
                "patch_sequence": parsed["sequence"],
                "patch_position_candidate": parsed["patch_position_candidate"],
                "valid_reference_pixels": valid,
                "high_reference_pixels": high,
                "high_percent_valid": 100.0 * high / valid if valid else 0.0,
                "cyan_sha256": row["cyan_sha256"],
                "sentinel2_sha256": row["sen2_sha256"],
                "label_source": "PROCESSED_RESAMPLED_CYAN_DN_PROXY",
                "label_mapping": "DN_0_99_LOW;100_199_MODERATE;200_253_HIGH;254_255_IGNORE",
                "field_measurement_link": "NONE_IN_RELEASED_DATASET",
                "identity_evidence_level": "PARTIAL_FILENAME_AND_HASH_ONLY",
            }
        )
    return output


def build_overlap_audit(split_rows: Sequence[Mapping[str, str]]) -> list[dict[str, object]]:
    enriched = []
    for row in split_rows:
        parsed = parse_sample_id(row["sample_id"])
        enriched.append({**row, "patch_position_candidate": str(parsed["patch_position_candidate"])})
    definitions = [
        ("sample_id", "sample_id", "VERIFIED", "Exact saved sample identity"),
        ("geographic_component", "spatial_group_id", "CANDIDATE", "Author-grid connected component, not a lake"),
        ("source_subtile", "source_subtile", "CANDIDATE", "Author fixed-grid parent"),
        ("patch_position", "patch_position_candidate", "CANDIDATE", "Filename grid position; no physical CRS"),
        ("sentinel_array_hash", "sen2_sha256", "VERIFIED_CONTENT", "Exact saved Sentinel-array hash"),
        ("cyan_array_hash", "cyan_sha256", "VERIFIED_CONTENT", "Exact saved processed-reference hash"),
        ("acquisition_date", "date", "DATE_ONLY", "Same date is not proof of same scene"),
    ]
    output: list[dict[str, object]] = []
    for left, right in (("train", "validation"), ("train", "test"), ("validation", "test")):
        for label, key, level, note in definitions:
            count, values = overlap_count(enriched, key, left, right)
            output.append(
                {
                    "left_split": left,
                    "right_split": right,
                    "identity_type": label,
                    "evidence_level": level,
                    "overlap_count": count,
                    "overlap_values": "|".join(values),
                    "status": "NO_OVERLAP" if count == 0 else "OVERLAP_OBSERVED",
                    "interpretation": note,
                }
            )
        for label in ("lake_waterbody_id", "sentinel_scene_id", "footprint_geometry", "physical_footprint_overlap", "bloom_event_id"):
            output.append(
                {
                    "left_split": left,
                    "right_split": right,
                    "identity_type": label,
                    "evidence_level": UNKNOWN,
                    "overlap_count": "",
                    "overlap_values": "",
                    "status": UNKNOWN,
                    "interpretation": "Required source identity/geometry is absent; overlap cannot be tested",
                }
            )
    return output


def summary_counts(records: Iterable[Mapping[str, object]]) -> dict[str, int]:
    return dict(sorted(Counter(str(record["status"]) for record in records).items()))


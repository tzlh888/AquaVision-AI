"""Fail-closed geospatial evidence helpers for AquaVision Phase 3A-1."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping, Sequence


CONFIRMED = "CONFIRMED"
CANDIDATE = "CANDIDATE"
UNVERIFIED = "UNVERIFIED"
EVIDENCE_LEVELS = {CONFIRMED, CANDIDATE, UNVERIFIED}


class EvidenceError(ValueError):
    """Raised when evidence is incomplete or internally inconsistent."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_file(path: Path, expected_sha256: str) -> str:
    if not path.is_file():
        return "MISSING"
    return "VERIFIED" if sha256_file(path) == expected_sha256 else "HASH_MISMATCH"


def require_evidence_level(value: str) -> str:
    if value not in EVIDENCE_LEVELS:
        raise EvidenceError(f"Unknown evidence level: {value}")
    return value


def scene_identity_status(
    *, stored_product_id: str | None, stac_candidates: Sequence[str]
) -> tuple[str, str | None]:
    """STAC candidates cannot replace a discarded historical product ID."""
    if stored_product_id:
        return CONFIRMED, stored_product_id
    if stac_candidates:
        return CANDIDATE, stac_candidates[0] if len(stac_candidates) == 1 else None
    return UNVERIFIED, None


@dataclass(frozen=True)
class AffineTransform:
    a: float
    b: float
    c: float
    d: float
    e: float
    f: float
    crs: str

    def xy(self, row: float, col: float) -> tuple[float, float]:
        if not self.crs or self.crs == UNVERIFIED:
            raise EvidenceError("Verified CRS is required")
        return (
            self.a * col + self.b * row + self.c,
            self.d * col + self.e * row + self.f,
        )


def patch_polygon(
    transform: AffineTransform | None,
    row: int | None,
    col: int | None,
    size: int | None,
) -> list[tuple[float, float]]:
    if transform is None or row is None or col is None or size is None:
        raise EvidenceError("Transform, crop offsets, and patch size are all required")
    if row < 0 or col < 0 or size <= 0:
        raise EvidenceError("Invalid pixel window")
    corners = [
        transform.xy(row, col),
        transform.xy(row, col + size),
        transform.xy(row + size, col + size),
        transform.xy(row + size, col),
    ]
    return corners + [corners[0]]


def polygon_bounds(polygon: Sequence[tuple[float, float]]) -> tuple[float, float, float, float]:
    if len(polygon) < 4:
        raise EvidenceError("Polygon requires at least four points")
    xs = [point[0] for point in polygon]
    ys = [point[1] for point in polygon]
    return min(xs), min(ys), max(xs), max(ys)


def footprints_overlap(
    left: Sequence[tuple[float, float]],
    right: Sequence[tuple[float, float]],
    *,
    left_crs: str,
    right_crs: str,
) -> bool:
    if not left_crs or left_crs != right_crs or left_crs == UNVERIFIED:
        raise EvidenceError("Footprint overlap requires one verified common CRS")
    lx0, ly0, lx1, ly1 = polygon_bounds(left)
    rx0, ry0, rx1, ry1 = polygon_bounds(right)
    return lx0 < rx1 and rx0 < lx1 and ly0 < ry1 and ry0 < ly1


def conservative_group_identity(
    *, waterbody_id: str | None, scene_id: str | None, footprint_id: str | None
) -> str:
    if not waterbody_id or not scene_id or not footprint_id:
        raise EvidenceError("Conservative group identity requires waterbody, scene, and footprint")
    return f"{waterbody_id}|{scene_id}|{footprint_id}"


def near_temporal_duplicate(
    left_date: str,
    right_date: str,
    *,
    same_waterbody: bool,
    tolerance_days: int,
) -> bool:
    if tolerance_days < 0:
        raise EvidenceError("Negative temporal tolerance")
    if not same_waterbody:
        return False
    delta = abs((date.fromisoformat(left_date) - date.fromisoformat(right_date)).days)
    return delta <= tolerance_days


def confirmed_overlap_decision(rows: Iterable[Mapping[str, str]]) -> str:
    rows = list(rows)
    if not rows or any(row.get("footprint_status") != CONFIRMED for row in rows):
        return UNVERIFIED
    return "CHECKABLE"


def candidate_qualification(row: Mapping[str, str]) -> tuple[bool, list[str]]:
    required = {
        "waterbody_status": CONFIRMED,
        "scene_status": CONFIRMED,
        "footprint_status": CONFIRMED,
        "cyan_version_status": CONFIRMED,
        "historical_overlap_status": "NO_OVERLAP_CONFIRMED",
    }
    reasons = [f"{key}!={expected}" for key, expected in required.items() if row.get(key) != expected]
    try:
        high_pixels = int(row.get("high_pixels", "0"))
        high_patches = int(row.get("high_patches", "0"))
    except ValueError as error:
        raise EvidenceError("Non-integer High support") from error
    if high_pixels < 100:
        reasons.append("high_pixels<100")
    if high_patches < 3:
        reasons.append("high_patches<3")
    return not reasons, reasons

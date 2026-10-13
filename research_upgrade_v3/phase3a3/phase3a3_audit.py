"""Fail-closed geometry, native-pixel, qualification, and split helpers."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

import numpy as np
from PIL import Image, ImageDraw


LOW_MAX = 99
MODERATE_MAX = 199
HIGH_MIN = 200
VALID_MAX = 253


@dataclass(frozen=True)
class Grid:
    width: int
    height: int
    origin_x: float
    origin_y: float
    pixel_size: float


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def require_fields(record: dict[str, Any], fields: Sequence[str]) -> None:
    missing = [field for field in fields if record.get(field) in (None, "", [])]
    if missing:
        raise ValueError(f"Missing required evidence: {', '.join(missing)}")


def classify(values: np.ndarray) -> np.ndarray:
    source = np.asarray(values)
    result = np.full(source.shape, -1, dtype=np.int8)
    result[(source >= 0) & (source <= LOW_MAX)] = 0
    result[(source > LOW_MAX) & (source <= MODERATE_MAX)] = 1
    result[(source >= HIGH_MIN) & (source <= VALID_MAX)] = 2
    return result


def native_identity(product_id: str, row: int, col: int) -> str:
    if not product_id or row < 0 or col < 0:
        raise ValueError("Invalid native-pixel identity")
    return f"{product_id}|r{row}|c{col}"


def deduplicate_native_identities(
    identities: Iterable[tuple[str, int, int]],
) -> set[tuple[str, int, int]]:
    result: set[tuple[str, int, int]] = set()
    for product_id, row, col in identities:
        native_identity(product_id, row, col)
        result.add((product_id, row, col))
    return result


def _polygon_parts(geometry: dict[str, Any]) -> Iterator[list[list[list[float]]]]:
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if geometry_type == "Polygon" and coordinates:
        yield coordinates
    elif geometry_type == "MultiPolygon" and coordinates:
        yield from coordinates
    else:
        raise ValueError(f"Unsupported or empty geometry: {geometry_type}")


def geometry_bounds(geometries: Sequence[dict[str, Any]]) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for geometry in geometries:
        for polygon in _polygon_parts(geometry):
            for ring in polygon:
                for x, y in ring:
                    if not (math.isfinite(x) and math.isfinite(y)):
                        raise ValueError("Non-finite geometry coordinate")
                    xs.append(float(x))
                    ys.append(float(y))
    if not xs:
        raise ValueError("No geometry coordinates")
    return min(xs), min(ys), max(xs), max(ys)


def rasterize_center_mask(
    geometries: Sequence[dict[str, Any]], grid: Grid
) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """Rasterize polygons at native pixel-center coordinates with holes removed."""
    min_x, min_y, max_x, max_y = geometry_bounds(geometries)
    col0 = max(0, math.floor((min_x - grid.origin_x) / grid.pixel_size - 0.5) - 1)
    col1 = min(grid.width, math.ceil((max_x - grid.origin_x) / grid.pixel_size - 0.5) + 2)
    row0 = max(0, math.floor((grid.origin_y - max_y) / grid.pixel_size - 0.5) - 1)
    row1 = min(grid.height, math.ceil((grid.origin_y - min_y) / grid.pixel_size - 0.5) + 2)
    if row0 >= row1 or col0 >= col1:
        raise ValueError("Geometry falls outside the CyAN grid")
    image = Image.new("1", (col1 - col0, row1 - row0), 0)
    drawer = ImageDraw.Draw(image)

    def local_point(point: Sequence[float]) -> tuple[float, float]:
        x, y = point
        col = (x - grid.origin_x) / grid.pixel_size - 0.5 - col0
        row = (grid.origin_y - y) / grid.pixel_size - 0.5 - row0
        return col, row

    for geometry in geometries:
        for polygon in _polygon_parts(geometry):
            if not polygon:
                continue
            drawer.polygon([local_point(point) for point in polygon[0]], fill=1)
            for hole in polygon[1:]:
                drawer.polygon([local_point(point) for point in hole], fill=0)
    return np.asarray(image, dtype=bool), (row0, row1, col0, col1)


def class_counts(values: np.ndarray, mask: np.ndarray) -> dict[str, int]:
    if values.shape != mask.shape:
        raise ValueError("Value and mask shapes differ")
    classes = classify(values)
    selected = classes[mask]
    return {
        "low": int(np.sum(selected == 0)),
        "moderate": int(np.sum(selected == 1)),
        "high": int(np.sum(selected == 2)),
        "valid": int(np.sum(selected >= 0)),
        "invalid": int(np.sum(selected < 0)),
        "waterbody_mask_pixels": int(np.sum(mask)),
    }


def qualifies_high_unit(
    dates: Sequence[str],
    high_patch_count: int,
    unique_dated_native_high_pixels: int,
    evidence_complete: bool,
    minimum_dates: int = 2,
    minimum_separation_days: int = 30,
    minimum_high_patches: int = 3,
    minimum_native_high: int = 100,
) -> tuple[bool, list[str]]:
    failures: list[str] = []
    parsed = sorted({date.fromisoformat(value) for value in dates})
    if len(parsed) < minimum_dates:
        failures.append("insufficient_high_dates")
    elif (parsed[-1] - parsed[0]).days < minimum_separation_days:
        failures.append("insufficient_date_separation")
    if high_patch_count < minimum_high_patches:
        failures.append("insufficient_high_patches")
    if unique_dated_native_high_pixels < minimum_native_high:
        failures.append("insufficient_unique_dated_native_high_pixels")
    if not evidence_complete:
        failures.append("incomplete_provenance_or_independence_evidence")
    return not failures, failures


def deterministic_split(waterbody_ids: Sequence[str]) -> dict[str, str]:
    ordered = sorted(
        set(waterbody_ids),
        key=lambda value: hashlib.sha256(
            f"phase3a3-split-v1|{value}".encode("utf-8")
        ).hexdigest(),
    )
    names = ("Training", "Validation", "Confirmation")
    return {waterbody_id: names[index % 3] for index, waterbody_id in enumerate(ordered)}


def validate_split_isolation(split_members: dict[str, Sequence[str]]) -> None:
    seen: dict[str, str] = {}
    for split_name, members in split_members.items():
        for member in members:
            if member in seen:
                raise ValueError(
                    f"Waterbody {member} occurs in both {seen[member]} and {split_name}"
                )
            seen[member] = split_name


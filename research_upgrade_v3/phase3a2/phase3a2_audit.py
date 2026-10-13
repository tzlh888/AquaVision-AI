"""Fail-closed geospatial and provenance checks for the Phase 3A-2 pilot.

The module has no model-training code. Synthetic geometries are permitted only in
unit tests; real evidence is obtained from the official services recorded in the
pilot manifest.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Iterable, Mapping, Sequence


SCENE_ID = re.compile(
    r"^S2[ABC]_MSIL2A_\d{8}T\d{6}_N\d{4}_R\d{3}_T[A-Z0-9]{5}_\d{8}T\d{6}$"
)
EPSG_CODE = re.compile(r"^EPSG:(\d{4,6})$")


class EvidenceLevel(StrEnum):
    CONFIRMED = "CONFIRMED"
    CANDIDATE = "CANDIDATE"
    UNVERIFIED = "UNVERIFIED"


@dataclass(frozen=True)
class GridSpec:
    crs: str
    transform: tuple[float, float, float, float, float, float]
    shape: tuple[int, int]


@dataclass(frozen=True)
class PatchWindow:
    row_offset: int
    col_offset: int
    height: int
    width: int
    crs: str
    transform: tuple[float, float, float, float, float, float]
    bbox: tuple[float, float, float, float]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def canonical_json_sha256(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def map_cyan_dn(value: int) -> str:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("CyAN DN must be an integer")
    if 0 <= value <= 99:
        return "LOW"
    if 100 <= value <= 199:
        return "MODERATE"
    if 200 <= value <= 253:
        return "HIGH"
    if value in (254, 255):
        return "IGNORE"
    raise ValueError("CyAN DN must be in [0, 255]")


def _closed_ring(ring: Sequence[Sequence[float]]) -> list[tuple[float, float]]:
    points = [(float(point[0]), float(point[1])) for point in ring]
    if len(points) < 4:
        raise ValueError("Polygon ring needs at least four coordinates")
    if points[0] != points[-1]:
        points.append(points[0])
    return points


def polygon_parts(geometry: Mapping[str, Any]) -> list[list[list[tuple[float, float]]]]:
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if geometry_type == "Polygon":
        raw_parts = [coordinates]
    elif geometry_type == "MultiPolygon":
        raw_parts = coordinates
    else:
        raise ValueError("Only Polygon and MultiPolygon geometries are supported")
    if not raw_parts:
        raise ValueError("Geometry has no polygon parts")
    return [[_closed_ring(ring) for ring in part] for part in raw_parts]


def ring_area(ring: Sequence[tuple[float, float]]) -> float:
    return 0.5 * sum(
        x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(ring, ring[1:])
    )


def ring_centroid(ring: Sequence[tuple[float, float]]) -> tuple[float, float]:
    twice_area = sum(
        x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(ring, ring[1:])
    )
    if math.isclose(twice_area, 0.0, abs_tol=1e-12):
        return ring[0]
    x = sum(
        (x0 + x1) * (x0 * y1 - x1 * y0)
        for (x0, y0), (x1, y1) in zip(ring, ring[1:])
    ) / (3.0 * twice_area)
    y = sum(
        (y0 + y1) * (x0 * y1 - x1 * y0)
        for (x0, y0), (x1, y1) in zip(ring, ring[1:])
    ) / (3.0 * twice_area)
    return x, y


def point_in_ring(point: tuple[float, float], ring: Sequence[tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
        cross = (x - x0) * (y1 - y0) - (y - y0) * (x1 - x0)
        if math.isclose(cross, 0.0, abs_tol=1e-9):
            if min(x0, x1) - 1e-9 <= x <= max(x0, x1) + 1e-9 and min(
                y0, y1
            ) - 1e-9 <= y <= max(y0, y1) + 1e-9:
                return True
        if (y0 > y) != (y1 > y):
            x_intersection = (x1 - x0) * (y - y0) / (y1 - y0) + x0
            if x < x_intersection:
                inside = not inside
    return inside


def point_in_geometry(point: tuple[float, float], geometry: Mapping[str, Any]) -> bool:
    for part in polygon_parts(geometry):
        if point_in_ring(point, part[0]) and not any(
            point_in_ring(point, hole) for hole in part[1:]
        ):
            return True
    return False


def representative_point(geometry: Mapping[str, Any]) -> tuple[float, float]:
    parts = polygon_parts(geometry)
    outer_rings = [part[0] for part in parts]
    primary = max(outer_rings, key=lambda ring: abs(ring_area(ring)))
    candidate = ring_centroid(primary)
    if point_in_geometry(candidate, geometry):
        return candidate
    xs = [point[0] for point in primary]
    ys = [point[1] for point in primary]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    for denominator in (8, 16, 32, 64):
        for row in range(1, denominator):
            for col in range(1, denominator):
                candidate = (
                    min_x + (max_x - min_x) * col / denominator,
                    min_y + (max_y - min_y) * row / denominator,
                )
                if point_in_geometry(candidate, geometry):
                    return candidate
    raise ValueError("Could not find a deterministic point inside geometry")


def validate_waterbody_feature(
    feature: Mapping[str, Any], expected: Mapping[str, Any]
) -> None:
    properties = feature.get("properties", {})
    checks = {
        "OBJECTID": int(expected["object_id"]),
        "permanent_identifier": str(expected["permanent_identifier"]),
        "gnis_id": str(expected["gnis_id"]),
        "gnis_name": str(expected["gnis_name"]),
        "nhdplusid": int(expected["nhdplus_id"]),
    }
    for key, value in checks.items():
        if properties.get(key) != value:
            raise ValueError(f"Waterbody identity mismatch for {key}")
    polygon_parts(feature.get("geometry", {}))


def grid_from_stac_item(item: Mapping[str, Any], asset_name: str) -> GridSpec:
    item_id = item.get("id", "")
    if not SCENE_ID.fullmatch(item_id):
        raise ValueError("Invalid Sentinel-2 L2A item ID")
    properties = item.get("properties", {})
    parse_utc(properties["datetime"])
    if properties.get("processing:level") != "L2":
        raise ValueError("Expected a Level-2 item")
    asset = item.get("assets", {}).get(asset_name)
    if not isinstance(asset, Mapping):
        raise ValueError(f"Missing STAC asset {asset_name}")
    crs = asset.get("proj:code")
    if not isinstance(crs, str) or not EPSG_CODE.fullmatch(crs):
        raise ValueError("Missing or invalid projected CRS")
    transform = asset.get("proj:transform")
    shape = asset.get("proj:shape")
    if not isinstance(transform, list) or len(transform) != 6:
        raise ValueError("Missing six-term affine transform")
    if not isinstance(shape, list) or len(shape) != 2:
        raise ValueError("Missing raster shape")
    numeric_transform = tuple(float(value) for value in transform)
    if numeric_transform[1] != 0 or numeric_transform[3] != 0:
        raise ValueError("Rotated grids are not supported by this pilot")
    if numeric_transform[0] <= 0 or numeric_transform[4] >= 0:
        raise ValueError("Unexpected north-up grid transform")
    grid = GridSpec(
        crs=crs,
        transform=numeric_transform,
        shape=(int(shape[0]), int(shape[1])),
    )
    if not asset.get("file:checksum"):
        raise ValueError("STAC asset checksum is missing")
    return grid


def derive_patch_window(
    grid: GridSpec,
    center: tuple[float, float],
    patch_size_pixels: int,
) -> PatchWindow:
    if patch_size_pixels <= 0 or patch_size_pixels % 2:
        raise ValueError("Patch size must be a positive even integer")
    pixel_x, _, origin_x, _, pixel_y, origin_y = grid.transform
    center_col = math.floor((center[0] - origin_x) / pixel_x)
    center_row = math.floor((center[1] - origin_y) / pixel_y)
    col = center_col - patch_size_pixels // 2
    row = center_row - patch_size_pixels // 2
    if row < 0 or col < 0 or row + patch_size_pixels > grid.shape[0] or col + patch_size_pixels > grid.shape[1]:
        raise ValueError("Patch falls outside the Sentinel asset grid")
    left = origin_x + col * pixel_x
    top = origin_y + row * pixel_y
    right = left + patch_size_pixels * pixel_x
    bottom = top + patch_size_pixels * pixel_y
    return PatchWindow(
        row_offset=row,
        col_offset=col,
        height=patch_size_pixels,
        width=patch_size_pixels,
        crs=grid.crs,
        transform=(pixel_x, 0.0, left, 0.0, pixel_y, top),
        bbox=(left, bottom, right, top),
    )


def patch_corners(patch: PatchWindow) -> tuple[tuple[float, float], ...]:
    left, bottom, right, top = patch.bbox
    return ((left, bottom), (left, top), (right, top), (right, bottom))


def patch_within_waterbody(patch: PatchWindow, geometry: Mapping[str, Any]) -> bool:
    return all(point_in_geometry(point, geometry) for point in patch_corners(patch))


def derive_contained_patch(
    grid: GridSpec,
    waterbody_geometry: Mapping[str, Any],
    patch_size_pixels: int,
) -> PatchWindow:
    """Choose a deterministic grid-aligned patch wholly inside a waterbody."""
    initial = representative_point(waterbody_geometry)
    try:
        patch = derive_patch_window(grid, initial, patch_size_pixels)
        if patch_within_waterbody(patch, waterbody_geometry):
            return patch
    except ValueError:
        pass
    parts = polygon_parts(waterbody_geometry)
    primary = max((part[0] for part in parts), key=lambda ring: abs(ring_area(ring)))
    xs = [point[0] for point in primary]
    ys = [point[1] for point in primary]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    for denominator in (8, 16, 32, 64):
        for row in range(1, denominator):
            for col in range(1, denominator):
                candidate = (
                    min_x + (max_x - min_x) * col / denominator,
                    min_y + (max_y - min_y) * row / denominator,
                )
                if not point_in_geometry(candidate, waterbody_geometry):
                    continue
                try:
                    patch = derive_patch_window(grid, candidate, patch_size_pixels)
                except ValueError:
                    continue
                if patch_within_waterbody(patch, waterbody_geometry):
                    return patch
    raise ValueError("No full grid-aligned patch fits inside the waterbody")


def bboxes_overlap(
    first: Sequence[float], second: Sequence[float], *, first_crs: str, second_crs: str
) -> bool:
    if first_crs != second_crs:
        raise ValueError("Overlap requires a common verified CRS")
    if len(first) != 4 or len(second) != 4:
        raise ValueError("Bounding boxes need four coordinates")
    return not (
        first[2] <= second[0]
        or second[2] <= first[0]
        or first[3] <= second[1]
        or second[3] <= first[1]
    )


def cyan_filename_for_date(observed_at: str) -> str:
    date = parse_utc(observed_at)
    return (
        f"L{date.year}{date.timetuple().tm_yday:03d}."
        "L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif"
    )


def temporal_match_days(scene_datetime: str, cyan_filename: str) -> int:
    scene = parse_utc(scene_datetime)
    match = re.match(r"^L(\d{4})(\d{3})\.", cyan_filename)
    if not match:
        raise ValueError("Unrecognized CyAN filename")
    cyan_date = datetime.strptime("".join(match.groups()), "%Y%j").replace(
        tzinfo=timezone.utc
    )
    return abs((scene.date() - cyan_date.date()).days)


def assert_unique(values: Iterable[str], label: str) -> None:
    materialized = list(values)
    if len(materialized) != len(set(materialized)):
        raise ValueError(f"Duplicate {label}")


def validate_partition_isolation(rows: Sequence[Mapping[str, str]]) -> None:
    protected = ("waterbody_id", "scene_id", "patch_identity")
    for index, left in enumerate(rows):
        for right in rows[index + 1 :]:
            if left["split_membership"] == right["split_membership"]:
                continue
            for field in protected:
                if left[field] and left[field] == right[field]:
                    raise ValueError(f"Cross-partition overlap in {field}")
    confirmation = [row for row in rows if row["split_membership"] == "CONFIRMATION"]
    if any(row.get("label_accessed", "false").lower() == "true" for row in confirmation):
        raise ValueError("Confirmation labels must remain inaccessible before sealing")


def qualifies_high_unit(row: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    required = {
        "waterbody_status": EvidenceLevel.CONFIRMED,
        "scene_status": EvidenceLevel.CONFIRMED,
        "patch_geometry_status": EvidenceLevel.CONFIRMED,
        "cyan_product_status": EvidenceLevel.CONFIRMED,
        "cyan_version_status": EvidenceLevel.CONFIRMED,
        "source_label_hash_status": EvidenceLevel.CONFIRMED,
        "high_support_status": EvidenceLevel.CONFIRMED,
    }
    failures = tuple(
        key for key, expected in required.items() if row.get(key) != expected
    )
    return not failures, failures


def validate_file_hash(payload: bytes, expected_sha256: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise ValueError("Expected hash must be lowercase SHA-256")
    if sha256_bytes(payload) != expected_sha256:
        raise ValueError("SHA-256 mismatch")

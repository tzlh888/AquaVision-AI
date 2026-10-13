"""Auditable CyAN v6 GeoTIFF integration without model code or credentials."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import hashlib
import math
from pathlib import Path
import re
from typing import Iterable, Sequence

import numpy as np
from PIL import Image


Image.MAX_IMAGE_PIXELS = None

VALID_MIN = 0
VALID_MAX = 253
LAND_VALUE = 254
NODATA_VALUE = 255
LOW_MAX = 99
MODERATE_MAX = 199
HIGH_MIN = 200


@dataclass(frozen=True)
class RasterGrid:
    width: int
    height: int
    origin_x: float
    origin_y: float
    pixel_size_x: float
    pixel_size_y: float


@dataclass(frozen=True)
class PatchSpec:
    crs: str
    transform: tuple[float, float, float, float, float, float]
    width: int
    height: int


@dataclass(frozen=True)
class CyanMetadata:
    product_id: str
    acquisition_date: str
    processing_version: str
    width: int
    height: int
    dtype: str
    samples_per_pixel: int
    bits_per_sample: int
    photometric: int
    compression: int
    grid: RasterGrid
    crs_name: str
    crs_equivalent: str
    geokey_directory: tuple[int, ...]
    albers_parameters: tuple[float, ...]
    sha256: str
    byte_size: int


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()


def product_date(product_id: str) -> date:
    match = re.fullmatch(
        r"L(?P<year>\d{4})(?P<doy>\d{3})\.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m\.tif",
        product_id,
    )
    if match is None:
        raise ValueError(f"Unexpected frozen CyAN product ID: {product_id}")
    year = int(match.group("year"))
    day_of_year = int(match.group("doy"))
    if day_of_year < 1 or day_of_year > (366 if _is_leap(year) else 365):
        raise ValueError(f"Invalid day of year in {product_id}")
    return date(year, 1, 1) + timedelta(days=day_of_year - 1)


def _is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def class_name(value: float | int) -> str:
    if not math.isfinite(float(value)):
        return "Invalid"
    if value < VALID_MIN or value > VALID_MAX:
        return "Invalid"
    if value < LOW_MAX + 1:
        return "Low"
    if value < MODERATE_MAX + 1:
        return "Moderate"
    return "High"


def class_code(value: float | int) -> int:
    return {"Invalid": -1, "Low": 0, "Moderate": 1, "High": 2}[class_name(value)]


def classify_array(values: np.ndarray) -> np.ndarray:
    values_f = np.asarray(values, dtype=np.float64)
    result = np.full(values_f.shape, -1, dtype=np.int8)
    finite = np.isfinite(values_f)
    result[finite & (values_f >= 0) & (values_f < LOW_MAX + 1)] = 0
    result[finite & (values_f >= LOW_MAX + 1) & (values_f < MODERATE_MAX + 1)] = 1
    result[finite & (values_f >= HIGH_MIN) & (values_f <= VALID_MAX)] = 2
    return result


def read_cyan_metadata(path: Path) -> CyanMetadata:
    with Image.open(path) as image:
        tags = image.tag_v2
        bits = tuple(int(value) for value in tags.get(258, ()))
        if image.mode != "P" or bits != (8,):
            raise ValueError(f"Expected one-band 8-bit palette GeoTIFF: {path.name}")
        samples = int(tags.get(277, 1))
        if samples != 1:
            raise ValueError(f"Expected one sample per pixel: {path.name}")
        scale = tuple(float(value) for value in tags.get(33550, ()))
        tie = tuple(float(value) for value in tags.get(33922, ()))
        geokeys = tuple(int(value) for value in tags.get(34735, ()))
        doubles = tuple(float(value) for value in tags.get(34736, ()))
        metadata_xml = str(tags.get(42112, ""))
        version_match = re.search(r'Item name="OBPG_version">([^<]+)<', metadata_xml)
        if version_match is None:
            raise ValueError(f"Missing embedded OBPG_version: {path.name}")
        if len(scale) < 2 or len(tie) < 6:
            raise ValueError(f"Missing GeoTIFF scale/tiepoint: {path.name}")
        _verify_conus_albers(geokeys, doubles)
        grid = RasterGrid(
            width=image.width,
            height=image.height,
            origin_x=tie[3] - tie[0] * scale[0],
            origin_y=tie[4] + tie[1] * scale[1],
            pixel_size_x=scale[0],
            pixel_size_y=-scale[1],
        )
        return CyanMetadata(
            product_id=path.name,
            acquisition_date=product_date(path.name).isoformat(),
            processing_version=version_match.group(1),
            width=image.width,
            height=image.height,
            dtype="uint8",
            samples_per_pixel=samples,
            bits_per_sample=bits[0],
            photometric=int(tags.get(262, -1)),
            compression=int(tags.get(259, -1)),
            grid=grid,
            crs_name="NAD83 / Conus Albers",
            crs_equivalent="EPSG:5070",
            geokey_directory=geokeys,
            albers_parameters=doubles,
            sha256=sha256_file(path),
            byte_size=path.stat().st_size,
        )


def _geokey_values(directory: Sequence[int]) -> dict[int, int]:
    if len(directory) < 4 or (len(directory) - 4) % 4:
        raise ValueError("Malformed GeoKeyDirectory")
    count = directory[3]
    if len(directory) != 4 + 4 * count:
        raise ValueError("GeoKeyDirectory entry count mismatch")
    result: dict[int, int] = {}
    for offset in range(4, len(directory), 4):
        key, tag_location, value_count, value_offset = directory[offset : offset + 4]
        if tag_location == 0 and value_count == 1:
            result[key] = value_offset
    return result


def _verify_conus_albers(geokeys: Sequence[int], doubles: Sequence[float]) -> None:
    keys = _geokey_values(geokeys)
    expected = {
        1024: 1,  # projected model
        1025: 1,  # pixel is area
        2048: 4269,  # NAD83
        3075: 11,  # Albers equal area
        3076: 9001,  # metres
    }
    for key, value in expected.items():
        if keys.get(key) != value:
            raise ValueError(f"GeoKey {key} expected {value}, got {keys.get(key)}")
    expected_doubles = (29.5, 45.5, 23.0, -96.0, 0.0, 0.0)
    if len(doubles) < 6 or any(
        not math.isclose(actual, expected_value, abs_tol=1e-10)
        for actual, expected_value in zip(doubles[:6], expected_doubles)
    ):
        raise ValueError(f"Unexpected CONUS Albers parameters: {doubles}")


def parse_utm_epsg(crs: str) -> tuple[int, bool]:
    match = re.fullmatch(r"EPSG:(326|327)(\d{2})", crs)
    if match is None:
        raise ValueError(f"Expected WGS84 UTM CRS, got {crs}")
    zone = int(match.group(2))
    if not 1 <= zone <= 60:
        raise ValueError(f"Invalid UTM zone: {zone}")
    return zone, match.group(1) == "326"


def utm_to_lonlat(
    easting: float, northing: float, zone: int, northern: bool = True
) -> tuple[float, float]:
    """Inverse WGS84 UTM, sufficient for deterministic patch geolocation."""
    a = 6378137.0
    ecc_sq = 0.0066943799901413165
    ecc_prime_sq = ecc_sq / (1.0 - ecc_sq)
    k0 = 0.9996
    x = easting - 500000.0
    y = northing if northern else northing - 10000000.0
    m = y / k0
    mu = m / (
        a
        * (
            1.0
            - ecc_sq / 4.0
            - 3.0 * ecc_sq**2 / 64.0
            - 5.0 * ecc_sq**3 / 256.0
        )
    )
    e1 = (1.0 - math.sqrt(1.0 - ecc_sq)) / (1.0 + math.sqrt(1.0 - ecc_sq))
    phi1 = (
        mu
        + (3.0 * e1 / 2.0 - 27.0 * e1**3 / 32.0) * math.sin(2.0 * mu)
        + (21.0 * e1**2 / 16.0 - 55.0 * e1**4 / 32.0) * math.sin(4.0 * mu)
        + (151.0 * e1**3 / 96.0) * math.sin(6.0 * mu)
        + (1097.0 * e1**4 / 512.0) * math.sin(8.0 * mu)
    )
    n1 = a / math.sqrt(1.0 - ecc_sq * math.sin(phi1) ** 2)
    t1 = math.tan(phi1) ** 2
    c1 = ecc_prime_sq * math.cos(phi1) ** 2
    r1 = a * (1.0 - ecc_sq) / (1.0 - ecc_sq * math.sin(phi1) ** 2) ** 1.5
    d = x / (n1 * k0)
    latitude = phi1 - (n1 * math.tan(phi1) / r1) * (
        d**2 / 2.0
        - (5.0 + 3.0 * t1 + 10.0 * c1 - 4.0 * c1**2 - 9.0 * ecc_prime_sq)
        * d**4
        / 24.0
        + (
            61.0
            + 90.0 * t1
            + 298.0 * c1
            + 45.0 * t1**2
            - 252.0 * ecc_prime_sq
            - 3.0 * c1**2
        )
        * d**6
        / 720.0
    )
    longitude = (
        d
        - (1.0 + 2.0 * t1 + c1) * d**3 / 6.0
        + (
            5.0
            - 2.0 * c1
            + 28.0 * t1
            - 3.0 * c1**2
            + 8.0 * ecc_prime_sq
            + 24.0 * t1**2
        )
        * d**5
        / 120.0
    ) / math.cos(phi1)
    central_meridian = math.radians((zone - 1) * 6 - 180 + 3)
    return math.degrees(central_meridian + longitude), math.degrees(latitude)


def lonlat_to_conus_albers(lon: float, lat: float) -> tuple[float, float]:
    """Forward NAD83 / Conus Albers using the parameters embedded in the products."""
    a = 6378137.0
    inverse_flattening = 298.257222101
    f = 1.0 / inverse_flattening
    eccentricity_sq = 2.0 * f - f * f
    eccentricity = math.sqrt(eccentricity_sq)
    phi1, phi2, phi0 = map(math.radians, (29.5, 45.5, 23.0))
    lam0 = math.radians(-96.0)

    def m(phi: float) -> float:
        return math.cos(phi) / math.sqrt(1.0 - eccentricity_sq * math.sin(phi) ** 2)

    def q(phi: float) -> float:
        sine = math.sin(phi)
        return (1.0 - eccentricity_sq) * (
            sine / (1.0 - eccentricity_sq * sine * sine)
            - math.log((1.0 - eccentricity * sine) / (1.0 + eccentricity * sine))
            / (2.0 * eccentricity)
        )

    m1, m2 = m(phi1), m(phi2)
    q1, q2, q0 = q(phi1), q(phi2), q(phi0)
    n = (m1 * m1 - m2 * m2) / (q2 - q1)
    c = m1 * m1 + n * q1
    rho0 = a * math.sqrt(c - n * q0) / n
    phi = math.radians(lat)
    theta = n * (math.radians(lon) - lam0)
    rho = a * math.sqrt(c - n * q(phi)) / n
    return rho * math.sin(theta), rho0 - rho * math.cos(theta)


def transform_utm_to_albers(x: float, y: float, crs: str) -> tuple[float, float]:
    zone, northern = parse_utm_epsg(crs)
    lon, lat = utm_to_lonlat(x, y, zone, northern)
    return lonlat_to_conus_albers(lon, lat)


def pixel_center(transform: Sequence[float], row: int, col: int) -> tuple[float, float]:
    a, b, c, d, e, f = transform
    return (
        a * (col + 0.5) + b * (row + 0.5) + c,
        d * (col + 0.5) + e * (row + 0.5) + f,
    )


def patch_polygon_albers(patch: PatchSpec) -> list[tuple[float, float]]:
    a, b, c, d, e, f = patch.transform
    corners_px = ((0.0, 0.0), (patch.width, 0.0), (patch.width, patch.height), (0.0, patch.height))
    result = []
    for col, row in corners_px:
        x = a * col + b * row + c
        y = d * col + e * row + f
        result.append(transform_utm_to_albers(x, y, patch.crs))
    return result


def point_in_polygon(point: tuple[float, float], polygon: Sequence[tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    j = len(polygon) - 1
    for i, (xi, yi) in enumerate(polygon):
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / (yj - yi) + xi
        ):
            inside = not inside
        j = i
    return inside


def native_center_indices(
    grid: RasterGrid, polygon: Sequence[tuple[float, float]]
) -> list[tuple[int, int]]:
    min_x = min(x for x, _ in polygon)
    max_x = max(x for x, _ in polygon)
    min_y = min(y for _, y in polygon)
    max_y = max(y for _, y in polygon)
    min_col = max(0, math.floor((min_x - grid.origin_x) / grid.pixel_size_x - 0.5))
    max_col = min(grid.width - 1, math.ceil((max_x - grid.origin_x) / grid.pixel_size_x - 0.5))
    min_row = max(0, math.floor((grid.origin_y - max_y) / abs(grid.pixel_size_y) - 0.5))
    max_row = min(grid.height - 1, math.ceil((grid.origin_y - min_y) / abs(grid.pixel_size_y) - 0.5))
    indices = []
    for row in range(min_row, max_row + 1):
        y = grid.origin_y + (row + 0.5) * grid.pixel_size_y
        for col in range(min_col, max_col + 1):
            x = grid.origin_x + (col + 0.5) * grid.pixel_size_x
            if point_in_polygon((x, y), polygon):
                indices.append((row, col))
    return indices


def read_window(path: Path, rows: Iterable[int], cols: Iterable[int]) -> tuple[np.ndarray, int, int]:
    row_values = list(rows)
    col_values = list(cols)
    if not row_values or not col_values:
        raise ValueError("Empty raster window request")
    row_min, row_max = min(row_values), max(row_values)
    col_min, col_max = min(col_values), max(col_values)
    with Image.open(path) as image:
        cropped = image.crop((col_min, row_min, col_max + 1, row_max + 1))
        array = np.asarray(cropped, dtype=np.uint8)
    return array, row_min, col_min


def source_value(array: np.ndarray, row: int, col: int, row0: int, col0: int) -> int:
    return int(array[row - row0, col - col0])


def native_values_for_polygon(
    path: Path, grid: RasterGrid, polygon: Sequence[tuple[float, float]]
) -> tuple[list[tuple[int, int]], np.ndarray]:
    indices = native_center_indices(grid, polygon)
    if not indices:
        raise ValueError("Sentinel patch contains no CyAN native-cell centers")
    rows = [row for row, _ in indices]
    cols = [col for _, col in indices]
    window, row0, col0 = read_window(path, rows, cols)
    values = np.asarray(
        [source_value(window, row, col, row0, col0) for row, col in indices],
        dtype=np.uint8,
    )
    return indices, values


def bilinear_valid_dn(
    four_values: Sequence[float | int], row_weight: float, col_weight: float
) -> float:
    values = np.asarray(four_values, dtype=np.float64)
    if values.shape != (4,):
        raise ValueError("Bilinear interpolation requires four source values")
    if not 0.0 <= row_weight <= 1.0 or not 0.0 <= col_weight <= 1.0:
        raise ValueError("Bilinear weights must be within [0, 1]")
    if not np.all(np.isfinite(values)) or not np.all(
        (values >= VALID_MIN) & (values <= VALID_MAX)
    ):
        return math.nan
    top = values[0] * (1.0 - col_weight) + values[1] * col_weight
    bottom = values[2] * (1.0 - col_weight) + values[3] * col_weight
    return float(top * (1.0 - row_weight) + bottom * row_weight)


def integrate_patch(path: Path, patch: PatchSpec) -> dict[str, object]:
    metadata = read_cyan_metadata(path)
    polygon = patch_polygon_albers(patch)
    native_indices, native_values = native_values_for_polygon(path, metadata.grid, polygon)

    target_coords: list[tuple[float, float]] = []
    needed_rows = {row for row, _ in native_indices}
    needed_cols = {col for _, col in native_indices}
    nearest_indices: list[tuple[int, int]] = []
    bilinear_specs: list[tuple[int, int, float, float]] = []
    for row in range(patch.height):
        for col in range(patch.width):
            x_utm, y_utm = pixel_center(patch.transform, row, col)
            x, y = transform_utm_to_albers(x_utm, y_utm, patch.crs)
            target_coords.append((x, y))
            col_fraction = (x - metadata.grid.origin_x) / metadata.grid.pixel_size_x - 0.5
            row_fraction = (metadata.grid.origin_y - y) / abs(metadata.grid.pixel_size_y) - 0.5
            nearest_col = int(round(col_fraction))
            nearest_row = int(round(row_fraction))
            base_col = math.floor(col_fraction)
            base_row = math.floor(row_fraction)
            if not (0 <= nearest_row < metadata.height and 0 <= nearest_col < metadata.width):
                raise ValueError("Transformed Sentinel target is outside CyAN raster")
            if not (0 <= base_row < metadata.height - 1 and 0 <= base_col < metadata.width - 1):
                raise ValueError("Bilinear neighborhood is outside CyAN raster")
            nearest_indices.append((nearest_row, nearest_col))
            bilinear_specs.append(
                (base_row, base_col, row_fraction - base_row, col_fraction - base_col)
            )
            needed_rows.update((nearest_row, base_row, base_row + 1))
            needed_cols.update((nearest_col, base_col, base_col + 1))

    window, row0, col0 = read_window(path, needed_rows, needed_cols)
    nearest_values = np.asarray(
        [source_value(window, row, col, row0, col0) for row, col in nearest_indices],
        dtype=np.uint8,
    ).reshape((patch.height, patch.width))
    bilinear_values = np.full(patch.width * patch.height, np.nan, dtype=np.float32)
    for index, (base_row, base_col, row_weight, col_weight) in enumerate(bilinear_specs):
        four = np.asarray(
            [
                source_value(window, base_row, base_col, row0, col0),
                source_value(window, base_row, base_col + 1, row0, col0),
                source_value(window, base_row + 1, base_col, row0, col0),
                source_value(window, base_row + 1, base_col + 1, row0, col0),
            ],
            dtype=np.float64,
        )
        bilinear_values[index] = bilinear_valid_dn(
            four, row_weight=row_weight, col_weight=col_weight
        )
    bilinear_values = bilinear_values.reshape((patch.height, patch.width))
    nearest_classes = classify_array(nearest_values)
    bilinear_classes = classify_array(bilinear_values)
    both_valid = (nearest_classes >= 0) & (bilinear_classes >= 0)
    disagreement = int(np.sum(both_valid & (nearest_classes != bilinear_classes)))
    return {
        "metadata": metadata,
        "patch_polygon_albers": polygon,
        "native_indices": native_indices,
        "native_values": native_values,
        "nearest_values": nearest_values,
        "nearest_classes": nearest_classes,
        "bilinear_values": bilinear_values,
        "bilinear_classes": bilinear_classes,
        "bilinear_comparable_pixels": int(np.sum(both_valid)),
        "bilinear_class_disagreement_pixels": disagreement,
    }


def count_classes(values: np.ndarray) -> dict[str, int]:
    classes = classify_array(values)
    return {
        "low": int(np.sum(classes == 0)),
        "moderate": int(np.sum(classes == 1)),
        "high": int(np.sum(classes == 2)),
        "invalid": int(np.sum(classes == -1)),
    }


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image

from cyan_label_integration import (
    PatchSpec,
    RasterGrid,
    bilinear_valid_dn,
    class_code,
    classify_array,
    integrate_patch,
    lonlat_to_conus_albers,
    native_center_indices,
    parse_utm_epsg,
    point_in_polygon,
    product_date,
    read_cyan_metadata,
    sha256_file,
    utm_to_lonlat,
)


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[1]
RAW_DIR = REPOSITORY / "data" / "raw" / "final_label_pilot" / "cyan"
PROCESSED_DIR = REPOSITORY / "data" / "processed" / "final_label_pilot"
CATALOG = HERE.parent / "phase3a2" / "V3_METADATA_CATALOG.csv"
MANIFEST = HERE / "CYAN_PRODUCT_MANIFEST.json"
HIGH_SUPPORT = HERE / "HIGH_SUPPORT_PILOT.csv"

EXPECTED_HASHES = {
    "L2025193.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif": "ee9775ca7c1b7b12e64c68b3c24595e2991b3a73b513f5af47cad15441c39b40",
    "L2025206.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif": "0eed1b55b0fbdc8fbbb0bb8ccbfa70ad9b33d1451fa39b9ce1f0d927ffa4cd8f",
    "L2025209.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif": "5a778a76124f33ee48e03c2f6146a2c1dd1125ef37519dca446384d565bf530c",
    "L2025262.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif": "4624d8b25c0ab28dd9d37beb4abac00355642531e3d30d2dfaf22a2055874d30",
    "L2025266.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif": "e8aa9de2ca1a7dc8e465d58975383990d6a9adda18145f87ecf55804a35aae4e",
    "L2025268.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif": "18348a9b777cfd5b485e638b1bea1792615f9053915a8ee0e85363d9991b4c8f",
}


class SyntheticUnitTests(unittest.TestCase):
    """No real research claim is derived from these synthetic unit tests."""

    def test_product_date_and_rejection(self) -> None:
        self.assertEqual(
            product_date("L2025193.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif").isoformat(),
            "2025-07-12",
        )
        with self.assertRaises(ValueError):
            product_date("different-product.tif")

    def test_frozen_high_boundaries_and_invalid_values(self) -> None:
        values = np.asarray([-1, 0, 99, 99.9, 100, 199, 199.9, 200, 253, 254, 255, np.nan])
        self.assertEqual(
            classify_array(values).tolist(),
            [-1, 0, 0, 0, 1, 1, 1, 2, 2, -1, -1, -1],
        )
        self.assertEqual(class_code(200), 2)
        self.assertEqual(class_code(254), -1)

    def test_bilinear_nodata_rule_is_fail_closed(self) -> None:
        self.assertTrue(math.isnan(bilinear_valid_dn([10, 20, 30, 254], 0.5, 0.5)))
        self.assertTrue(math.isnan(bilinear_valid_dn([10, 20, 30, 255], 0.5, 0.5)))
        self.assertAlmostEqual(bilinear_valid_dn([0, 100, 200, 252], 0.5, 0.5), 138.0)

    def test_coordinate_reference_known_origins(self) -> None:
        lon, lat = utm_to_lonlat(500000.0, 0.0, zone=17, northern=True)
        self.assertAlmostEqual(lon, -81.0, places=7)
        self.assertAlmostEqual(lat, 0.0, places=7)
        x, y = lonlat_to_conus_albers(-96.0, 23.0)
        self.assertAlmostEqual(x, 0.0, places=6)
        self.assertAlmostEqual(y, 0.0, places=6)
        self.assertEqual(parse_utm_epsg("EPSG:32612"), (12, True))
        with self.assertRaises(ValueError):
            parse_utm_epsg("EPSG:4326")

    def test_spatial_intersection_uses_native_centers(self) -> None:
        grid = RasterGrid(4, 4, 0.0, 1200.0, 300.0, -300.0)
        polygon = [(0.0, 600.0), (600.0, 600.0), (600.0, 1200.0), (0.0, 1200.0)]
        indices = native_center_indices(grid, polygon)
        self.assertEqual(indices, [(0, 0), (0, 1), (1, 0), (1, 1)])
        self.assertTrue(point_in_polygon((150.0, 1050.0), polygon))
        self.assertFalse(point_in_polygon((750.0, 1050.0), polygon))

    def test_file_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.bin"
            path.write_bytes(b"synthetic-only")
            self.assertEqual(sha256_file(path), hashlib.sha256(b"synthetic-only").hexdigest())

    def test_missing_geospatial_metadata_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "L2025193.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif"
            Image.fromarray(np.zeros((2, 2), dtype=np.uint8), mode="P").save(path)
            with self.assertRaises(ValueError):
                read_cyan_metadata(path)


@unittest.skipUnless(MANIFEST.exists() and HIGH_SUPPORT.exists(), "saved real pilot outputs absent")
class SavedRealDataIntegrationTests(unittest.TestCase):
    """Tests the six downloaded official products and saved integration outputs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        with HIGH_SUPPORT.open(newline="", encoding="utf-8") as handle:
            cls.rows = list(csv.DictReader(handle))
        with CATALOG.open(newline="", encoding="utf-8") as handle:
            cls.catalog = {row["candidate_id"]: row for row in csv.DictReader(handle)}

    def test_exact_frozen_product_set_and_hashes(self) -> None:
        self.assertEqual({path.name for path in RAW_DIR.glob("*.tif")}, set(EXPECTED_HASHES))
        for name, expected_hash in EXPECTED_HASHES.items():
            self.assertEqual(sha256_file(RAW_DIR / name), expected_hash)

    def test_product_version_crs_affine_and_encoding(self) -> None:
        for name in EXPECTED_HASHES:
            metadata = read_cyan_metadata(RAW_DIR / name)
            self.assertEqual(metadata.processing_version, "6.0")
            self.assertEqual(metadata.crs_equivalent, "EPSG:5070")
            self.assertEqual((metadata.width, metadata.height), (26328, 15138))
            self.assertEqual(metadata.grid.pixel_size_x, 300.0)
            self.assertEqual(metadata.grid.pixel_size_y, -300.0)
            self.assertEqual(metadata.dtype, "uint8")
            self.assertEqual(metadata.samples_per_pixel, 1)

    def test_dates_match_frozen_sentinel_dates(self) -> None:
        self.assertEqual(len(self.rows), 6)
        for row in self.rows:
            self.assertEqual(
                product_date(row["cyan_product_id"]).isoformat(),
                row["sentinel_acquisition_timestamp"][:10],
            )
            self.assertEqual(row["temporal_match_days"], "0")

    def test_processed_traceability_and_resampling_consistency(self) -> None:
        for row in self.rows:
            output = REPOSITORY / row["processed_label_path"]
            self.assertEqual(sha256_file(output), row["processed_label_sha256"])
            with np.load(output, allow_pickle=False) as saved:
                nearest_dn = saved["source_dn_nearest"]
                nearest_class = saved["class_nearest"]
                bilinear_dn = saved["source_dn_bilinear"]
                bilinear_class = saved["class_bilinear"]
                trace = json.loads(str(saved["traceability_json"]))
            self.assertEqual(nearest_dn.shape, (64, 64))
            self.assertTrue(np.array_equal(nearest_class, classify_array(nearest_dn)))
            self.assertTrue(np.array_equal(bilinear_class, classify_array(bilinear_dn)))
            self.assertEqual(trace["scene_id"], row["scene_id"])
            self.assertEqual(trace["cyan_source_sha256"], row["cyan_sha256"])

    def test_real_bilinear_diagnostic_has_contiguous_classes(self) -> None:
        klamath = next(row for row in self.rows if row["candidate_id"] == "upper_klamath__2025_07")
        with np.load(REPOSITORY / klamath["processed_label_path"], allow_pickle=False) as saved:
            bilinear_dn = saved["source_dn_bilinear"]
            bilinear_class = saved["class_bilinear"]
        self.assertTrue(np.all(bilinear_class[np.isfinite(bilinear_dn)] >= 0))
        self.assertTrue(np.array_equal(bilinear_class, classify_array(bilinear_dn)))

    def test_real_patch_footprints_intersect_source_grid(self) -> None:
        for row in self.rows:
            candidate = self.catalog[row["candidate_id"]]
            patch = PatchSpec(
                candidate["scene_crs"],
                tuple(json.loads(candidate["patch_affine"])),
                int(candidate["patch_width"]),
                int(candidate["patch_height"]),
            )
            result = integrate_patch(RAW_DIR / row["cyan_product_id"], patch)
            self.assertEqual(len(result["native_indices"]), 19)
            self.assertEqual(result["nearest_values"].shape, (64, 64))

    def test_independent_group_census_is_not_scene_count(self) -> None:
        groups = self.manifest["group_support"]
        self.assertEqual(len(groups), 3)
        self.assertEqual(sum(group["candidate_scenes"] for group in groups), 6)
        self.assertEqual(sum(bool(group["waterbody_contains_high"]) for group in groups), 2)
        self.assertEqual(sum(bool(group["qualified_independent_high_unit"]) for group in groups), 0)
        self.assertEqual(
            {group["waterbody_name"]: group["date_span_days"] for group in groups},
            {"Lake Okeechobee": 53, "Utah Lake": 62, "Upper Klamath Lake": 73},
        )

    def test_manifest_provenance_hashes(self) -> None:
        self.assertFalse(self.manifest["model_training_performed"])
        self.assertFalse(self.manifest["target_product_set_changed"])
        self.assertFalse(self.manifest["credentials_stored"])
        for product in self.manifest["products"]:
            self.assertEqual(product["sha256"], EXPECTED_HASHES[product["product_id"]])
            self.assertEqual(product["processing_version"], "6.0")
            self.assertEqual(product["valid_data_range"], [0, 253])
            self.assertEqual(product["land_value"], 254)
            self.assertEqual(product["nodata_value"], 255)


if __name__ == "__main__":
    unittest.main()

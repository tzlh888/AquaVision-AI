import csv
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np

from phase3a1_audit import (
    CANDIDATE,
    CONFIRMED,
    UNVERIFIED,
    AffineTransform,
    EvidenceError,
    candidate_qualification,
    confirmed_overlap_decision,
    conservative_group_identity,
    footprints_overlap,
    near_temporal_duplicate,
    patch_polygon,
    scene_identity_status,
    verify_file,
)
from recover_v2_sentinel_arrays import local_entry


REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


class Phase3A1AuditTests(unittest.TestCase):
    def test_scene_candidate_is_not_confirmed_identity(self):
        self.assertEqual(scene_identity_status(stored_product_id=None, stac_candidates=[]), (UNVERIFIED, None))
        self.assertEqual(
            scene_identity_status(stored_product_id=None, stac_candidates=["candidate"]),
            (CANDIDATE, "candidate"),
        )
        self.assertEqual(
            scene_identity_status(stored_product_id="stored", stac_candidates=["other"]),
            (CONFIRMED, "stored"),
        )

    def test_patch_footprint_requires_transform_offsets_and_crs(self):
        with self.assertRaises(EvidenceError):
            patch_polygon(None, 0, 0, 64)
        with self.assertRaises(EvidenceError):
            patch_polygon(AffineTransform(1, 0, 0, 0, -1, 0, UNVERIFIED), 0, 0, 64)
        with self.assertRaises(EvidenceError):
            patch_polygon(AffineTransform(1, 0, 0, 0, -1, 0, "EPSG:4326"), -1, 0, 64)

    def test_synthetic_affine_patch_polygon(self):
        polygon = patch_polygon(AffineTransform(20, 0, 100, 0, -20, 500, "EPSG:32616"), 2, 3, 64)
        self.assertEqual(polygon[0], (160, 460))
        self.assertEqual(polygon[2], (1440, -820))
        self.assertEqual(polygon[0], polygon[-1])

    def test_spatial_intersection_requires_common_verified_crs(self):
        left = [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)]
        overlap = [(1, 1), (3, 1), (3, 3), (1, 3), (1, 1)]
        separate = [(2, 0), (4, 0), (4, 2), (2, 2), (2, 0)]
        self.assertTrue(footprints_overlap(left, overlap, left_crs="EPSG:4326", right_crs="EPSG:4326"))
        self.assertFalse(footprints_overlap(left, separate, left_crs="EPSG:4326", right_crs="EPSG:4326"))
        with self.assertRaises(EvidenceError):
            footprints_overlap(left, overlap, left_crs="EPSG:4326", right_crs="EPSG:3857")

    def test_conservative_group_and_temporal_duplicate(self):
        with self.assertRaises(EvidenceError):
            conservative_group_identity(waterbody_id="lake", scene_id=None, footprint_id="p")
        self.assertEqual(
            conservative_group_identity(waterbody_id="lake", scene_id="scene", footprint_id="p"),
            "lake|scene|p",
        )
        self.assertTrue(
            near_temporal_duplicate("2020-01-01", "2020-01-31", same_waterbody=True, tolerance_days=30)
        )
        self.assertFalse(
            near_temporal_duplicate("2020-01-01", "2020-01-02", same_waterbody=False, tolerance_days=30)
        )

    def test_overlap_and_candidate_qualification_fail_closed(self):
        self.assertEqual(confirmed_overlap_decision([{"footprint_status": UNVERIFIED}]), UNVERIFIED)
        row = {
            "waterbody_status": UNVERIFIED,
            "scene_status": UNVERIFIED,
            "footprint_status": UNVERIFIED,
            "cyan_version_status": UNVERIFIED,
            "historical_overlap_status": "LEGACY_SCREENED_NOT_BLIND",
            "high_pixels": "1000",
            "high_patches": "10",
        }
        qualified, reasons = candidate_qualification(row)
        self.assertFalse(qualified)
        self.assertIn("waterbody_status!=CONFIRMED", reasons)
        self.assertIn("historical_overlap_status!=NO_OVERLAP_CONFIRMED", reasons)

    def test_local_zip_header_identity(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
            archive.writestr("sample_sen2.npy", b"artifact")
        entry = local_entry(stream.getvalue(), "archive.zip")
        self.assertEqual(entry["member"], "sample_sen2.npy")
        self.assertEqual(entry["size_bytes"], 8)

    def test_hash_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "item"
            path.write_bytes(b"identity")
            expected = hashlib.sha256(b"identity").hexdigest()
            self.assertEqual(verify_file(path, expected), "VERIFIED")
            self.assertEqual(verify_file(path, "0" * 64), "HASH_MISMATCH")
            self.assertEqual(verify_file(path.parent / "missing", expected), "MISSING")

    def test_real_patch_catalog_has_no_fabricated_identity(self):
        with (OUT / "PATCH_IDENTITY_CATALOG.csv").open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 288)
        self.assertTrue(all(row["sentinel_artifact_status"] == "VERIFIED" for row in rows))
        self.assertTrue(all(row["cyan_artifact_status"] == "VERIFIED" for row in rows))
        for field in ("sentinel_product_id", "scene_id", "mgrs_tile_id", "original_crs", "patch_footprint_wkt", "waterbody_id"):
            self.assertTrue(all(not row[field] for row in rows), field)
        self.assertTrue(all(row["footprint_status"] == UNVERIFIED for row in rows))

    def test_real_recovered_sentinel_arrays_match_frozen_manifest(self):
        selection = json.loads((REPO / "data/metadata/phase3_5/geographic_split_v2.json").read_text())
        self.assertEqual(len(selection["samples"]), 288)
        for row in selection["samples"]:
            path = REPO / row["sen2_path"]
            self.assertTrue(path.is_file(), row["sample_id"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row["sen2_sha256"])
            array = np.load(path, allow_pickle=False)
            self.assertEqual(array.shape, (12, 64, 64))
            self.assertEqual(array.dtype, np.uint16)

    def test_real_cyan_boundary_counts_and_candidate_gate(self):
        selection = json.loads((REPO / "data/metadata/phase3_5/geographic_split_v2.json").read_text())
        counts = {99: 0, 100: 0, 199: 0, 200: 0, 254: 0, 255: 0}
        for row in selection["samples"]:
            array = np.load(REPO / row["cyan_path"], allow_pickle=False)
            for value in counts:
                counts[value] += int(np.count_nonzero(array == value))
        self.assertEqual(counts, {99: 1309, 100: 1087, 199: 1935, 200: 1912, 254: 0, 255: 338838})
        with (OUT / "INDEPENDENT_HIGH_CANDIDATES.csv").open(newline="") as stream:
            candidates = list(csv.DictReader(stream))
        self.assertEqual(len(candidates), 12)
        self.assertTrue(all(row["eligible_for_v3_validation"] == "NO" for row in candidates))
        self.assertTrue(all(row["eligible_for_confirmation"] == "NO" for row in candidates))


if __name__ == "__main__":
    unittest.main()

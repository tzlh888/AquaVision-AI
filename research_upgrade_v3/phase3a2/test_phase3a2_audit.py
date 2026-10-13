from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from phase3a2_audit import (
    EvidenceLevel,
    GridSpec,
    assert_unique,
    bboxes_overlap,
    cyan_filename_for_date,
    derive_contained_patch,
    derive_patch_window,
    grid_from_stac_item,
    map_cyan_dn,
    patch_corners,
    patch_within_waterbody,
    qualifies_high_unit,
    sha256_bytes,
    temporal_match_days,
    validate_file_hash,
    validate_partition_isolation,
    validate_waterbody_feature,
)


ROOT = Path(__file__).resolve().parent


def square(left: float, bottom: float, right: float, top: float) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [left, bottom],
                [left, top],
                [right, top],
                [right, bottom],
                [left, bottom],
            ]
        ],
    }


def synthetic_item() -> dict:
    return {
        "id": "S2A_MSIL2A_20250701T120000_N0511_R001_T10TEN_20250701T150000",
        "properties": {
            "datetime": "2025-07-01T12:00:00Z",
            "processing:level": "L2",
        },
        "assets": {
            "B05_20m": {
                "proj:code": "EPSG:32610",
                "proj:transform": [20, 0, 500000, 0, -20, 4700000],
                "proj:shape": [5490, 5490],
                "file:checksum": "1220" + "0" * 64,
            }
        },
    }


class SyntheticUnitTests(unittest.TestCase):
    """Small fabricated inputs test logic only; they are not research evidence."""

    def test_scene_grid_and_missing_metadata_rejection(self) -> None:
        grid = grid_from_stac_item(synthetic_item(), "B05_20m")
        self.assertEqual(grid.crs, "EPSG:32610")
        broken = synthetic_item()
        del broken["assets"]["B05_20m"]["proj:transform"]
        with self.assertRaises(ValueError):
            grid_from_stac_item(broken, "B05_20m")

    def test_crs_patch_and_spatial_containment(self) -> None:
        grid = GridSpec(
            "EPSG:32610", (20, 0, 500000, 0, -20, 4700000), (5490, 5490)
        )
        waterbody = square(510000, 4680000, 530000, 4695000)
        patch = derive_contained_patch(grid, waterbody, 64)
        self.assertEqual((patch.height, patch.width), (64, 64))
        self.assertTrue(patch_within_waterbody(patch, waterbody))
        self.assertEqual(len(patch_corners(patch)), 4)
        with self.assertRaises(ValueError):
            derive_patch_window(grid, (499000, 4710000), 64)

    def test_spatial_overlap_requires_same_crs(self) -> None:
        self.assertTrue(
            bboxes_overlap((0, 0, 2, 2), (1, 1, 3, 3), first_crs="A", second_crs="A")
        )
        self.assertFalse(
            bboxes_overlap((0, 0, 1, 1), (1, 0, 2, 1), first_crs="A", second_crs="A")
        )
        with self.assertRaises(ValueError):
            bboxes_overlap((0, 0, 2, 2), (1, 1, 3, 3), first_crs="A", second_crs="B")

    def test_temporal_matching_and_label_boundaries(self) -> None:
        filename = cyan_filename_for_date("2025-07-28T16:07:11Z")
        self.assertEqual(filename[:8], "L2025209")
        self.assertEqual(temporal_match_days("2025-07-28T16:07:11Z", filename), 0)
        expected = {
            0: "LOW",
            99: "LOW",
            100: "MODERATE",
            199: "MODERATE",
            200: "HIGH",
            253: "HIGH",
            254: "IGNORE",
            255: "IGNORE",
        }
        self.assertEqual({value: map_cyan_dn(value) for value in expected}, expected)

    def test_waterbody_identity_and_duplicate_detection(self) -> None:
        expected = {
            "object_id": 1,
            "permanent_identifier": "P1",
            "gnis_id": "G1",
            "gnis_name": "Test Lake",
            "nhdplus_id": "9",
        }
        feature = {
            "properties": {
                "OBJECTID": 1,
                "permanent_identifier": "P1",
                "gnis_id": "G1",
                "gnis_name": "Test Lake",
                "nhdplusid": 9,
            },
            "geometry": square(0, 0, 10, 10),
        }
        validate_waterbody_feature(feature, expected)
        assert_unique(["one", "two"], "scene ID")
        with self.assertRaises(ValueError):
            assert_unique(["one", "one"], "scene ID")

    def test_cross_split_and_confirmation_exclusion(self) -> None:
        rows = [
            {
                "split_membership": "TRAIN",
                "waterbody_id": "A",
                "scene_id": "S1",
                "patch_identity": "P1",
                "label_accessed": "true",
            },
            {
                "split_membership": "VALIDATION",
                "waterbody_id": "B",
                "scene_id": "S2",
                "patch_identity": "P2",
                "label_accessed": "true",
            },
            {
                "split_membership": "CONFIRMATION",
                "waterbody_id": "C",
                "scene_id": "S3",
                "patch_identity": "P3",
                "label_accessed": "false",
            },
        ]
        validate_partition_isolation(rows)
        rows[1]["waterbody_id"] = "A"
        with self.assertRaises(ValueError):
            validate_partition_isolation(rows)
        rows[1]["waterbody_id"] = "B"
        rows[2]["label_accessed"] = "true"
        with self.assertRaises(ValueError):
            validate_partition_isolation(rows)

    def test_fail_closed_high_qualification_and_hash(self) -> None:
        complete = {
            key: EvidenceLevel.CONFIRMED
            for key in (
                "waterbody_status",
                "scene_status",
                "patch_geometry_status",
                "cyan_product_status",
                "cyan_version_status",
                "source_label_hash_status",
                "high_support_status",
            )
        }
        self.assertEqual(qualifies_high_unit(complete), (True, ()))
        complete["cyan_version_status"] = EvidenceLevel.CANDIDATE
        qualified, failures = qualifies_high_unit(complete)
        self.assertFalse(qualified)
        self.assertIn("cyan_version_status", failures)
        payload = b"manifest"
        validate_file_hash(payload, sha256_bytes(payload))
        with self.assertRaises(ValueError):
            validate_file_hash(payload, "0" * 64)


class SavedOfficialEvidenceIntegrationTests(unittest.TestCase):
    """Checks saved official-source evidence; no synthetic rows count as findings."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(
            (ROOT / "V3_DATA_PROVENANCE_MANIFEST.json").read_text(encoding="utf-8")
        )
        with (ROOT / "V3_METADATA_CATALOG.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            cls.rows = list(csv.DictReader(handle))

    def test_real_catalog_identity_and_scene_uniqueness(self) -> None:
        self.assertEqual(len(self.rows), 6)
        self.assertEqual(len({row["waterbody_id"] for row in self.rows}), 3)
        self.assertEqual(len({row["scene_id"] for row in self.rows}), 6)
        assert_unique((row["scene_id"] for row in self.rows), "real scene ID")
        self.assertTrue(
            all(row["waterbody_status"] == EvidenceLevel.CONFIRMED for row in self.rows)
        )
        self.assertTrue(
            all(row["scene_status"] == EvidenceLevel.CONFIRMED for row in self.rows)
        )

    def test_real_crs_patch_geometry_and_temporal_match(self) -> None:
        scenes = self.manifest["normalized_evidence"]["scenes"]
        for row in self.rows:
            self.assertEqual(row["patch_geometry_status"], EvidenceLevel.CONFIRMED)
            self.assertTrue(row["scene_crs"].startswith("EPSG:326"))
            self.assertEqual(row["temporal_match_days"], "0")
            evidence = scenes[row["candidate_id"]]
            geometry = evidence["projected_waterbody_geometry"]
            patch = evidence["patch"]
            bbox = tuple(patch["bbox"])
            corners = ((bbox[0], bbox[1]), (bbox[0], bbox[3]), (bbox[2], bbox[3]), (bbox[2], bbox[1]))
            from phase3a2_audit import point_in_geometry

            self.assertTrue(all(point_in_geometry(point, geometry) for point in corners))

    def test_real_manifest_hashes_and_fail_closed_status(self) -> None:
        for name, expected in self.manifest["generated_artifact_sha256"].items():
            validate_file_hash((ROOT / name).read_bytes(), expected)
        self.assertEqual(self.manifest["qualified_high_units"], 0)
        self.assertEqual(self.manifest["confirmation_members"], 0)
        self.assertTrue(
            all(row["qualified_high_unit"] == "false" for row in self.rows)
        )
        self.assertTrue(
            all(row["high_support_status"] == EvidenceLevel.UNVERIFIED for row in self.rows)
        )

    def test_real_confirmation_is_unassigned_and_unaccessed(self) -> None:
        self.assertTrue(
            all(
                row["split_membership"] == "PILOT_CANDIDATE_UNASSIGNED"
                for row in self.rows
            )
        )
        self.assertTrue(all(row["label_accessed"] == "false" for row in self.rows))
        self.assertFalse(
            any(row["split_membership"] == "CONFIRMATION" for row in self.rows)
        )


if __name__ == "__main__":
    unittest.main()

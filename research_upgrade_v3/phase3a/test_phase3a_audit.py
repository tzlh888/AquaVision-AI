import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from phase3a_audit import (
    AuditError,
    QualificationThresholds,
    Rectangle,
    cyan_dn_class,
    parse_sample_id,
    qualification_decision,
    rectangles_overlap,
    validate_split_membership,
    verify_expected_file,
    read_csv,
)


REPO = Path(__file__).resolve().parents[2]


class Phase3AAuditTests(unittest.TestCase):
    def test_label_mapping_boundaries(self):
        expected = {
            0: "Low", 99: "Low", 100: "Moderate", 199: "Moderate",
            200: "High", 253: "High", 254: "IGNORE", 255: "IGNORE",
        }
        self.assertEqual({value: cyan_dn_class(value) for value in expected}, expected)
        with self.assertRaises(AuditError):
            cyan_dn_class(-1)

    def test_patch_and_scene_identity_are_not_conflated(self):
        parsed = parse_sample_id("6_2_X0500_Y1150_S050_2019_03_17_x256_y384_64x64_15")
        self.assertEqual(parsed["tile"], "6_2")
        self.assertEqual(parsed["subtile_id"], "6_2_X0500_Y1150_S050")
        self.assertEqual(parsed["date"], "2019-03-17")
        self.assertTrue(parsed["patch_position_candidate"].endswith("x256_y384_64x64"))
        self.assertNotIn("scene", parsed)

    def test_spatial_overlap_requires_common_verified_crs(self):
        first = Rectangle(0, 0, 10, 10, "EPSG:4326")
        self.assertTrue(rectangles_overlap(first, Rectangle(9, 9, 20, 20, "EPSG:4326")))
        self.assertFalse(rectangles_overlap(first, Rectangle(10, 0, 20, 10, "EPSG:4326")))
        with self.assertRaises(AuditError):
            rectangles_overlap(first, Rectangle(0, 0, 1, 1, "EPSG:3857"))
        with self.assertRaises(AuditError):
            Rectangle(0, 0, 1, 1, "UNVERIFIED")

    def test_component_isolation_and_split_membership(self):
        rows = [
            {"sample_id": "a", "split": "train", "spatial_group_id": "g1", "source_subtile": "s1"},
            {"sample_id": "b", "split": "validation", "spatial_group_id": "g2", "source_subtile": "s2"},
            {"sample_id": "c", "split": "test", "spatial_group_id": "g3", "source_subtile": "s3"},
        ]
        validate_split_membership(rows)
        rows[2]["spatial_group_id"] = "g1"
        with self.assertRaisesRegex(AuditError, "Cross-split spatial_group_id"):
            validate_split_membership(rows)

    def test_artifact_hash_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "artifact.bin"
            path.write_bytes(b"evidence")
            expected = "ee8250fb76e094b34b471f13a73dbbe51d1ae142e9df59d7c0d31ec20f0a0a8e"
            self.assertEqual(verify_expected_file(root, path.name, expected)["status"], "VERIFIED")
            self.assertEqual(verify_expected_file(root, path.name, "0" * 64)["status"], "HASH_MISMATCH")
            self.assertEqual(verify_expected_file(root, "missing.bin", "0" * 64)["status"], "MISSING_LOCAL")

    def test_unqualified_model_logic_and_missing_provenance(self):
        metrics = {
            "high_recall": 0.7, "high_f1": 0.6, "low_f1": 0.8,
            "moderate_f1": 0.6, "macro_f1": 0.65, "high_components": 3,
            "component_high_recalls": [0.6, 0.4, 0.2],
        }
        self.assertEqual(qualification_decision(metrics, thresholds=QualificationThresholds()), (True, []))
        metrics["high_components"] = 1
        metrics["component_high_recalls"] = [0.0]
        qualified, reasons = qualification_decision(metrics)
        self.assertFalse(qualified)
        self.assertIn("high_components<3", reasons)
        self.assertIn("component_high_recall=ZERO", reasons)
        metrics["high_recall"] = None
        self.assertIn("high_recall=UNDEFINED", qualification_decision(metrics)[1])

    def test_high_support_is_not_replaced_by_pixel_volume(self):
        metrics = {
            "high_recall": 0.99, "high_f1": 0.99, "low_f1": 0.99,
            "moderate_f1": 0.99, "macro_f1": 0.99, "high_components": 1,
            "component_high_recalls": [0.99],
        }
        qualified, reasons = qualification_decision(metrics)
        self.assertFalse(qualified)
        self.assertEqual(reasons, ["high_components<3"])

    def test_real_v2_split_membership_and_high_support(self):
        """Real-evidence integration check; unlike preceding synthetic unit tests."""
        rows = read_csv(REPO / "data/metadata/phase3_5/geographic_split_v2.csv")
        census = {
            row["sample_id"]: row
            for row in read_csv(REPO / "data/metadata/phase3_5/reference_census_round2.csv")
        }
        validate_split_membership(rows)
        expected = {
            "train": (96, 2, 6, 647),
            "validation": (48, 1, 4, 931),
            "test": (144, 3, 28, 37768),
        }
        for split, target in expected.items():
            part = [row for row in rows if row["split"] == split]
            observed = (
                len(part),
                len({row["spatial_group_id"] for row in part}),
                sum(int(census[row["sample_id"]]["high_pixels"]) > 0 for row in part),
                sum(int(census[row["sample_id"]]["high_pixels"]) for row in part),
            )
            self.assertEqual(observed, target)

    def test_real_v2_hash_identity_overlap(self):
        rows = read_csv(REPO / "data/metadata/phase3_5/geographic_split_v2.csv")
        by_split = {
            split: [row for row in rows if row["split"] == split]
            for split in ("train", "validation", "test")
        }
        for left, right in (("train", "validation"), ("train", "test"), ("validation", "test")):
            for key in ("sample_id", "spatial_group_id", "source_subtile", "sen2_sha256"):
                self.assertFalse({row[key] for row in by_split[left]} & {row[key] for row in by_split[right]})
            cyan_overlap = {row["cyan_sha256"] for row in by_split[left]} & {
                row["cyan_sha256"] for row in by_split[right]
            }
            self.assertEqual(cyan_overlap, {"06a9c033c64aca2820e3d6ba5f74dc3c188c14cead16e3fb236d27ba4baeeeed"})

    def test_real_recovered_cyan_arrays_match_frozen_hashes(self):
        """Real recovered-data integration check; no synthetic evidence."""
        selection = json.loads(
            (REPO / "data/metadata/phase3_5/geographic_split_v2.json").read_text()
        )
        self.assertEqual(len(selection["samples"]), 288)
        for row in selection["samples"]:
            path = REPO / row["cyan_path"]
            self.assertTrue(path.is_file(), row["sample_id"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row["cyan_sha256"])


if __name__ == "__main__":
    unittest.main()

import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("v4_audit", HERE / "v4_audit.py")
v4 = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(v4)


class V4AuditTests(unittest.TestCase):
    @staticmethod
    def positive_unit(**updates):
        record = {
            "origin": "synthetic_test_only",
            "waterbody_id": "test-waterbody-1",
            "waterbody_name": "Synthetic test waterbody",
            "identity_complete": True,
            "dates_with_high": 2,
            "high_date_span_days": 30,
            "verified_high_patches": 3,
            "distinct_native_high_support": 100,
            "provenance_complete_for_qualification": True,
            "registration_mask_product_checks_pass": True,
            "independence_resolved": True,
        }
        record.update(updates)
        return record

    def test_verified_scenes_keep_real_identity(self):
        audit = v4.geographic_identity_audit()
        pilot = [row for row in audit if row["evidence_stage"] == "v3_verified_label_pilot"]
        self.assertEqual(len(pilot), 6)
        self.assertTrue(all(str(row["scene_product_id"]).startswith("S2") for row in pilot))
        self.assertTrue(all("V6.0" in str(row["cyan_product_version"]) for row in pilot))

    def test_no_patch_is_promoted_to_independent_unit(self):
        audit = v4.independent_high_audit()
        self.assertEqual(len(audit), 15)
        self.assertEqual(sum(bool(row["qualified_independent_high_unit"]) for row in audit), 0)
        self.assertTrue(all(row["split_membership"] == "UNASSIGNED" for row in audit))

    def test_dynamic_gate_accepts_complete_test_only_positive(self):
        result = v4.evaluate_unit(self.positive_unit())
        self.assertTrue(result["qualified_independent_high_unit"])
        self.assertEqual(result["qualification_status"], "QUALIFIED")

    def test_each_frozen_gate_can_exclude(self):
        cases = {
            "identity_complete": False,
            "dates_with_high": 1,
            "high_date_span_days": 29,
            "verified_high_patches": 2,
            "distinct_native_high_support": 99,
            "provenance_complete_for_qualification": False,
            "registration_mask_product_checks_pass": False,
            "independence_resolved": False,
        }
        for field, failing_value in cases.items():
            with self.subTest(field=field):
                result = v4.evaluate_unit(self.positive_unit(**{field: failing_value}))
                self.assertFalse(result["qualified_independent_high_unit"])
                self.assertEqual(result["qualification_status"], "EXCLUDED_NOT_QUALIFIED")

    def test_missing_and_conflicting_evidence_fail_closed(self):
        missing = v4.evaluate_unit(self.positive_unit(independence_resolved=None))
        self.assertFalse(missing["qualified_independent_high_unit"])
        self.assertEqual(missing["qualification_status"], "BLOCKED_MISSING_EVIDENCE")
        conflict = v4.evaluate_unit(self.positive_unit(evidence_conflict=True))
        self.assertFalse(conflict["qualified_independent_high_unit"])
        self.assertEqual(conflict["qualification_status"], "BLOCKED_CONFLICTING_EVIDENCE")

    def test_duplicate_waterbody_identity_is_not_double_counted(self):
        first = self.positive_unit()
        duplicate = self.positive_unit(waterbody_name="Alternate spelling")
        audited = v4.audit_normalized_units([first, duplicate])
        self.assertEqual(len(audited), 1)
        self.assertEqual(audited[0]["duplicate_source_records"], 2)
        self.assertTrue(audited[0]["qualified_independent_high_unit"])

    def test_conflicting_duplicate_is_blocked(self):
        first = self.positive_unit()
        conflict = self.positive_unit(verified_high_patches=2)
        audited = v4.audit_normalized_units([first, conflict])
        self.assertEqual(len(audited), 1)
        self.assertFalse(audited[0]["qualified_independent_high_unit"])
        self.assertEqual(audited[0]["qualification_status"], "BLOCKED_CONFLICTING_EVIDENCE")

    def test_v4_output_is_isolated(self):
        self.assertEqual(v4.OUT.name, "research_upgrade_v4_candidate")

    def test_v4_artifact_manifest(self):
        manifest = json.loads((HERE / "V4_ARTIFACT_MANIFEST.json").read_text())
        for relative, expected in manifest["files"].items():
            self.assertEqual(v4.sha256(HERE / relative), expected, relative)

    def test_release_candidate_manifest(self):
        manifest = json.loads((HERE / "V4_RELEASE_CANDIDATE_MANIFEST.json").read_text())
        self.assertFalse(any(".egg-info/" in relative for relative in manifest["files"]))
        for relative, expected in manifest["files"].items():
            self.assertEqual(v4.sha256(v4.ROOT / relative), expected, relative)


if __name__ == "__main__":
    unittest.main()

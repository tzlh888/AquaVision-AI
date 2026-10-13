from __future__ import annotations

import unittest

import numpy as np

from phase3a3_audit import (
    Grid,
    classify,
    deduplicate_native_identities,
    deterministic_split,
    qualifies_high_unit,
    rasterize_center_mask,
    require_fields,
    validate_split_isolation,
)


class Phase3A3AuditTests(unittest.TestCase):
    def test_class_boundaries(self) -> None:
        values = np.array([0, 99, 100, 199, 200, 253, 254, 255])
        self.assertEqual(classify(values).tolist(), [0, 0, 1, 1, 2, 2, -1, -1])

    def test_native_identity_deduplication(self) -> None:
        identities = [("p1", 1, 2), ("p1", 1, 2), ("p2", 1, 2)]
        self.assertEqual(len(deduplicate_native_identities(identities)), 2)

    def test_invalid_native_identity_rejected(self) -> None:
        with self.assertRaises(ValueError):
            deduplicate_native_identities([("", 1, 2)])

    def test_high_qualification_pass(self) -> None:
        qualified, failures = qualifies_high_unit(
            ["2025-07-12", "2025-09-19"], 6, 100, True
        )
        self.assertTrue(qualified)
        self.assertEqual(failures, [])

    def test_high_qualification_fail_closed(self) -> None:
        qualified, failures = qualifies_high_unit(
            ["2025-07-12", "2025-07-25"], 2, 99, False
        )
        self.assertFalse(qualified)
        self.assertIn("insufficient_date_separation", failures)
        self.assertIn("insufficient_high_patches", failures)
        self.assertIn("insufficient_unique_dated_native_high_pixels", failures)
        self.assertIn("incomplete_provenance_or_independence_evidence", failures)

    def test_rasterize_polygon_and_hole(self) -> None:
        grid = Grid(width=10, height=10, origin_x=0, origin_y=10, pixel_size=1)
        geometry = {
            "type": "Polygon",
            "coordinates": [
                [[1, 9], [7, 9], [7, 3], [1, 3], [1, 9]],
                [[3, 7], [5, 7], [5, 5], [3, 5], [3, 7]],
            ],
        }
        mask, _ = rasterize_center_mask([geometry], grid)
        self.assertGreater(int(mask.sum()), 0)
        self.assertLess(int(mask.sum()), 49)

    def test_split_is_reproducible_and_isolated(self) -> None:
        ids = ["a", "b", "c", "d", "e", "f"]
        first = deterministic_split(ids)
        second = deterministic_split(list(reversed(ids)))
        self.assertEqual(first, second)
        self.assertEqual(set(first), set(ids))

    def test_cross_split_overlap_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_split_isolation(
                {"Training": ["lake-a"], "Validation": ["lake-a"], "Confirmation": []}
            )

    def test_confirmation_exclusion_passes(self) -> None:
        validate_split_isolation(
            {"Training": ["lake-a"], "Validation": ["lake-b"], "Confirmation": ["lake-c"]}
        )

    def test_missing_evidence_rejected(self) -> None:
        with self.assertRaises(ValueError):
            require_fields({"waterbody_id": "x", "scene_id": ""}, ["waterbody_id", "scene_id"])


if __name__ == "__main__":
    unittest.main()

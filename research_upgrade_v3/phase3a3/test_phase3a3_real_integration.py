from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "final_label_pilot"))

from cyan_label_integration import read_cyan_metadata  # noqa: E402
from phase3a3_audit import sha256_file  # noqa: E402


EXPECTED = {
    "L2025193.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif": "ee9775ca7c1b7b12e64c68b3c24595e2991b3a73b513f5af47cad15441c39b40",
    "L2025206.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif": "0eed1b55b0fbdc8fbbb0bb8ccbfa70ad9b33d1451fa39b9ce1f0d927ffa4cd8f",
    "L2025209.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif": "5a778a76124f33ee48e03c2f6146a2c1dd1125ef37519dca446384d565bf530c",
    "L2025262.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif": "4624d8b25c0ab28dd9d37beb4abac00355642531e3d30d2dfaf22a2055874d30",
    "L2025266.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif": "e8aa9de2ca1a7dc8e465d58975383990d6a9adda18145f87ecf55804a35aae4e",
    "L2025268.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif": "18348a9b777cfd5b485e638b1bea1792615f9053915a8ee0e85363d9991b4c8f",
}


class Phase3A3RealIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cyan_dir = ROOT / "data" / "raw" / "final_label_pilot" / "cyan"
        cls.screen_path = ROOT / "data" / "processed" / "phase3a3" / "candidate_native_screen.json"
        if not cls.cyan_dir.exists() or not cls.screen_path.exists():
            raise unittest.SkipTest("Real ignored Phase 3A-3 inputs are unavailable")

    def test_six_verified_raw_hashes_and_v6_grid(self) -> None:
        paths = sorted(self.cyan_dir.glob("*.tif"))
        self.assertEqual([path.name for path in paths], sorted(EXPECTED))
        grids = set()
        for path in paths:
            self.assertEqual(sha256_file(path), EXPECTED[path.name])
            metadata = read_cyan_metadata(path)
            self.assertEqual(metadata.processing_version, "6.0")
            self.assertEqual(metadata.crs_equivalent, "EPSG:5070")
            grids.add(metadata.grid)
        self.assertEqual(len(grids), 1)

    def test_real_screen_is_model_free_and_contains_full_frozen_pool(self) -> None:
        document = json.loads(self.screen_path.read_text(encoding="utf-8"))
        self.assertFalse(document["uses_model_predictions"])
        self.assertEqual(document["new_cyan_downloads"], 0)
        new_records = [
            record
            for record in document["records"]
            if record["candidate_origin"] == "phase3a3_new_pool"
        ]
        self.assertEqual(len(new_records), 12)
        self.assertEqual(sum(r["screening_status"] == "SCREENED" for r in new_records), 5)

    def test_missing_geometries_remain_fail_closed(self) -> None:
        document = json.loads(self.screen_path.read_text(encoding="utf-8"))
        failures = [
            record
            for record in document["records"]
            if record["screening_status"] == "IDENTITY_UNAVAILABLE"
        ]
        self.assertGreaterEqual(len(failures), 1)
        self.assertTrue(all("date_support" not in record for record in failures))


if __name__ == "__main__":
    unittest.main()

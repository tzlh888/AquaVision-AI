# Pilot Reproducibility

## Reproduction boundary

The label integration can be reproduced exactly from the six checksum-matching raw GeoTIFFs without Earthdata credentials. A fresh download requires interactive Earthdata authorization but must not store credentials in the repository.

Raw inputs are deliberately Git-ignored under `data/raw/final_label_pilot/cyan/`. Six derived `.npz` artifacts are deliberately Git-ignored under `data/processed/final_label_pilot/`. Their paths and SHA-256 values are registered in `CYAN_PRODUCT_MANIFEST.json`.

## Commands

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=research_upgrade_v3/final_label_pilot \
  python3 research_upgrade_v3/final_label_pilot/run_final_label_pilot.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=research_upgrade_v3/final_label_pilot \
  python3 -W error::ResourceWarning -m unittest -v \
  research_upgrade_v3/final_label_pilot/test_final_label_pilot.py
```

The integration runner fails closed if the raw product set differs from the six frozen IDs, a product date differs from the paired Sentinel date, `OBPG_version` is absent or not `6.0`, the source grid/CRS metadata differs, a transformed target lies outside the raster, or required metadata is missing.

## Software

- Python 3.14
- NumPy 2.5.3
- Pillow 12.3.0
- Python standard library only for coordinate equations, manifests, hashing, and CSV/JSON I/O

No model framework is imported or called. No model is fitted, evaluated, or selected.

## Automated tests

Final result: **15/15 PASS**.

Synthetic tests are explicitly separated from saved-real-data integration tests. They cover:

- product-ID date parsing and malformed-ID rejection;
- integer and interpolated class boundaries;
- invalid/land/no-data rejection;
- bilinear fail-closed behavior;
- WGS84 UTM and CONUS Albers reference origins;
- native-center polygon intersection;
- file SHA-256;
- missing GeoTIFF metadata rejection.

Real-data integration tests cover:

- exact six-product identity and SHA-256;
- embedded V6, CRS, affine, resolution, data type, and one-band encoding;
- zero-day calendar matching;
- 64×64 output shape and deterministic nearest/bilinear class calculation;
- source/scene traceability in every `.npz`;
- real footprint/source-grid intersection;
- three-group rather than six-scene independence accounting;
- product and processed-artifact manifest hashes.

One intermediate 14-test run failed because the diagnostic float classifier left 199.x values between integer bins. The bug did not affect nearest-neighbor integer labels. The diagnostic rule was corrected prospectively to continuous half-open intervals, a dedicated boundary test was added, all artifacts were regenerated, and the final 15-test suite passed. This failure and correction are retained here rather than hidden.

## Security and publication checks

- No credential or authentication file is present in the repository.
- No token, cookie, or authorization header is logged.
- Public artifacts contain relative paths only.
- Raw and processed rasters remain ignored by Git.
- Historical Phase 3A-2 files are not overwritten.
- Rebuilding changes only the new pilot CSV, manifest, and ignored processed artifacts.

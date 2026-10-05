# Phase 1 exploratory data inspection

Generated from `data/metadata/sample_manifest.json`. All observations below are from real downloaded data.
This is a deterministic file-access probe of **8 pairs**, not a representative research subset.

## Measured properties

- Sentinel-2 array: `[12, 64, 64]`, `uint16`; reference: `[1, 64, 64]`, `uint8`.
- Region IDs: `{'6_2': 4, '7_2': 4}`. These are CyAN tile IDs, not inferred states, watersheds, or water bodies.
- Acquisition years: `{'2019': 3, '2020': 5}`; months: `{'01': 1, '06': 1, '07': 1, '11': 1, '02': 2, '08': 1, '10': 1}` (from filenames, not sensing timestamps).
- 32,768 reference pixels; 25,062 native DN 0-253 pixels; 7,706 flag-255 pixels; 0 flag-254 pixels.
- 0 other invalid reference values; 0 nonfinite image values. Zeros are tabulated, not automatically marked missing.
- Paper-native bin pixel counts: `[24704, 358, 0]`. These are **not** image-level risk counts or cells/mL thresholds.
- Exact Sentinel-2 file duplicate groups: `[]`. This limited check cannot exclude broader archive duplicates.
- 8 pairs lack verified coordinates; 8 lack water-body IDs. No geographic map is fabricated.

## Figures and tables

`sample_images.png` shows RGB display stretches and unconverted reference DN. Display normalization does not modify stored data.
`sample_bands.png` shows stored digital numbers across all pixels; physical reflectance scaling remains unverified.
Region, year, month and native-bin plots describe only the access probe. Tables preserve sample IDs, original reference ranges,
flag counts, per-band distributions, and nonexclusive image counts per native bin. Pixels within a resampled reference are correlated.
No image-level class-distribution table can be justified until an aggregation rule is defined.

## Leakage investigation and limits

Each filename encodes a parent subtile, date, patch row/column and sequence. Repeated parent subtiles across dates and
neighboring patches are potential leakage routes. `*_pairs.csv` inventories expose these fields before image downloading.
See `archive_metadata_summary.json` for repeated-location and adjacent-subtile counts in indexed archives.
`sample_pair_distances.csv` lists raw-DN RMSE candidates; without registration, a threshold, or a larger sample it cannot
establish near-duplicate prevalence. Patch coordinates may shift between reprojected products even with matching indices.
Group all dates from a verified geographic unit together; check adjacent units and lakes crossing boundaries before splitting.

## Conclusions permitted

File access and decoding work. We can inspect raw reference masks and recover naming-based groups/dates.
This sample cannot estimate class balance, geographic representativeness, model performance, or usable research sample size.
No network was trained and no test split was constructed. Resolve the label and geographic provenance gates in DATASET_AUDIT.md first.

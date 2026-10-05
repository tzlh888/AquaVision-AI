# Phase 1 status — AquaVision AI

Date: **2026-10-04 (Europe/Budapest)**. **Phase 1 complete; training has not started.**

## Completed work

1. Inspected `<workspace>`: existing WaterSense-AI and other files were present; AquaVision-AI did not exist. Created a new independent Git repository at `.`. No existing project was modified, moved, overwritten or deleted. No remote repository was created or pushed.
2. Created the requested top-level research structure and a modular Phase 1 package. Later model/training/evaluation directories are explicitly reserved; there are no pretend model implementations or result notebooks.
3. Wrote the research README, licensing/attribution, data policy, configuration, pinned dependencies, and environment record. Python 3.12.14 in a local `.venv` isolates this project from the host Python 3.14 and other projects.
4. Verified the primary dataset via the deposit API, related author manuscript, pinned author code and NASA product documentation. Recorded hashes and source URLs. Visually reviewed manuscript methods pages 4-5 to verify the preprocessing/label statements.
5. Implemented bounded HTTP range access, remote ZIP inventory parsing, exact sample pairing, deterministic tiny-sample selection, CRC32/SHA-256 checks, safe NPY decoding and native-DN inspection. The code rejects unverified cells/mL conversion.
6. Retrieved **eight real Sentinel-2/CyAN pairs**, four each from archive regions `6_2` and `7_2`; indexed only those two archives. No full archive or bulk image dataset was downloaded.
7. Ran EDA: native reference bins, masks/invalids, region/year/month distributions, RGB/reference examples, all-band histograms, exact file duplicates, descriptive pair distances, repeated-date grid candidates and adjacent parent groups. Outputs are machine-readable and figures were visually inspected.
8. Added and ran the Phase 1 tests. Wrote the audit, provisional subset design, EDA, geographic-method and limitations reports.

## Exact dataset source

Hänsch, R.; Schloer, C. (2024), *Dataset for Increasing the Spatial Resolution of Harmful Cyanobacterial Bloom Detection using Deep Learning and Sentinel-2 Satellite Imagery*.
[Version DOI 10.5281/zenodo.14230064](https://doi.org/10.5281/zenodo.14230064), [record/API](https://zenodo.org/api/records/14230064). Dataset CC BY 4.0.
Associated [paper DOI 10.1109/JSTARS.2025.3629586](https://doi.org/10.1109/JSTARS.2025.3629586) and [author repository at inspected commit](https://github.com/cschloer/hab_detection_s2/tree/e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37).

The deposit lists six ZIP files totaling **23,402,209,757 bytes**. The paper's 938,607 pairs are a published claim, not our independently counted full-corpus result.

## Verified dataset properties

| Observation | Evidence |
|---|---|
| Sentinel-2 input `(12, 64, 64)`, uint16 | All eight downloaded pairs |
| Reference `(1, 64, 64)`, uint8, processed CyAN DN | All eight downloaded pairs |
| Twelve-band order B01-B09 including B8A, then B11/B12; B10 absent | Upstream saving code plus observed channel count; band names not embedded |
| Nominal 20 m processed grid, 300 m source reference | Primary-source documentation; exact final geotransform absent |
| Filename dates 2019-2020, tile/subtile/patch IDs | Both ZIP inventories and sample names |
| Two indexed archives: 6,343 + 18,175 = 24,518 pairs | Complete central directories of these two ZIPs only |
| 17 parent groups; all recur across dates | Cached metadata audit |
| No embedded georeferencing, water-body IDs or patch-level risk labels | Arrays, inspected inventories and pinned source tree |
| Eight-pair reference counts: 24,704 DN 0-99; 358 DN 100-199; 0 DN 200-253 | 25,062 native valid-bin pixels; 7,706 flag-255 pixels excluded |
| Three sample patches exceed 5% masked area; one has 90.53% masked | Direct decoded reference arrays |
| Zero exact Sentinel-2 file duplicates among eight files | SHA-256 comparison; no whole-corpus duplicate claim |

The sample's bin counts are **pixel counts, not sample risk labels**. No reference value was changed. The zero highest-bin count cannot estimate whole-dataset class prevalence. See DATASET_AUDIT.md for facts versus assumptions versus unresolved questions.

## Unresolved scientific questions and blockers

- **Target units:** The processed/resampled DN arrays have no verified exact conversion to the requested 20k/100k cells/mL categories. NASA's original-product DN-to-index equation alone is insufficient to validate this archive transformation. Conversion is blocked, not guessed.
- **Task definition:** The source task is segmentation. Image-level aggregation, valid-water area and mixed/uncertain-label rules must be justified before classification.
- **Geographic identity:** Exact footprints, water-body/basin IDs, cross-tile relationships and sensing times are absent from the inspected arrays. Group names alone cannot prove unseen water bodies; no geographic map is fabricated.
- **Source inconsistencies:** Zenodo reverses feature/reference prose; the paper and code differ on missing-pixel filtering and cloud/land masking. Observed high missing fractions contradict a universal 5% missing-area cutoff. Exact generation provenance remains unresolved.
- **Coverage:** Only two of six ZIP indices were inspected; remaining file counts, full duplicates, usable three-class support and physical input scaling are unverified.

**The dataset is accessible. There is no access blocker for the current phase.** The items above block scientifically valid label conversion, final subset selection and training. They do not invalidate the completed access/inspection work.

## Tests and validation

- `.venv/bin/python -m pytest -q --junitxml=research_outputs/reports/pytest_results.xml`: **37 passed, 0 failures, 0 errors, 0 skipped**.
- Coverage: native-DN threshold boundaries; preservation and invalid values; refused unit conversion; all-band loading/dtypes/shapes; object-pickle rejection; filename/date/path validation; reference pairing; deterministic bounded selection; selective HTTP/ZIP decoding; ignored Range rejection before body reading; malformed/truncated response handling; byte/decompression limits; gzip catalog regression; CRC corruption; existing-file protection; empty/tampered EDA inputs.
- `.venv/bin/python -m pip check`: passed (no broken requirements).
- `.venv/bin/python -m compileall -q src scripts tests`: passed.
- Real-data smoke run: `scripts/prepare_data.py --download-sample`, `scripts/inspect_metadata.py`, `scripts/inspect_sample.py` all completed. Sample hashes were revalidated during EDA.
- Visual QA: sample RGB/reference panels and twelve-band distribution figure are readable; source methods pages were inspected. No figure presents a model prediction.
- Split integrity, feature extraction, CNN forward, prediction metrics and calibration tests are **deferred with their unimplemented later-phase modules**. Phase 1 does not claim these were tested.

Machine-readable evidence: `pytest_results.xml`, `validation.json`, `data/metadata/environment.json`, `requirements.txt`, source/sample manifests, and `research_outputs/tables/`.

## Current storage usage

Snapshot UTC: `2026-10-03T23:00:00.888504+00:00`. Sizes below are measured local storage; the snapshot preceded writing this status file. See `storage_snapshot.json` for exact content-byte and filesystem-allocation accounting.

| Component | Measured size |
|---|---:|
| Raw eight-pair NPY data | 821,248 file-content bytes (0.783 MiB) |
| Cached indices and source documentation | 27,540,526 file-content bytes |
| Research reports/tables/figures at snapshot | 665,077 file-content bytes |
| Isolated environment allocated | 140,920 KiB |
| Whole repository including environment/cache/source PDF | 171,000 KiB allocated (approximately 167.0 MiB) |

Successful sample run: **6,841,460 bytes** of ZIP range bodies plus **5,586 bytes** of catalog JSON. Earlier selective probes read a 65,557-byte footer and 1,679,198 bytes for an exploratory index inspection; neither downloaded an image archive. Supporting sources include a 16,014,721-byte paper PDF. Package downloads and repeated catalog fetches were not cumulatively metered, so the sample-run byte count is not presented as all session network traffic.

## Files created

Full artifact list with sizes and SHA-256 hashes: `research_outputs/reports/FILE_INVENTORY.csv` (environment, Git internals, temporary PDF renders and caches excluded; the inventory/status/storage documents themselves excluded from self-hashing).

- Root: `README.md`, `LICENSE`, `pyproject.toml`, `requirements.txt`, `.gitignore`, `.env.example`, `.python-version`.
- Config/data guidance: `configs/data.yaml`, `data/README.md`, `notebooks/README.md`.
- Package: `src/aquavision/__init__.py`; `data/download.py`, `metadata.py`, `loader.py`, `labels.py`, `eda.py`; package initializers and reserved later-phase package directories.
- Commands: `scripts/prepare_data.py`, `inspect_metadata.py`, `inspect_sample.py`, `fetch_sources.py`.
- Tests: `tests/conftest.py`, `test_download.py`, `test_metadata.py`, `test_loader.py`, `test_labels.py`, `test_eda.py`.
- Data/evidence: eight raw pairs, `data/metadata/sample_manifest.json`, two member and two pair inventories, environment JSON, catalog, pinned author-code/documentation snapshots and source-hash manifest.
- Reports: `DATASET_AUDIT.md`, `SUBSET_DESIGN.md`, `EDA_REPORT.md`, `GEOGRAPHIC_SPLIT.md`, `LIMITATIONS.md`, this `PHASE_1_STATUS.md`, test XML, validation JSON, storage snapshot and file inventory.
- Figures: `sample_images.png`, `sample_bands.png`, `sample_reference_bins.png`, `sample_region.png`, `sample_year.png`, `sample_month.png`.
- Tables: sample metadata, native-reference bins, per-band statistics, region/year/month counts, pair distances, `sample_summary.json`, `archive_metadata_summary.json`.

Empty later-stage result reports/notebooks and training scripts were intentionally not manufactured. They will accompany actual implemented methods and measurements.

## Exact recommended next step

Perform a **bounded provenance-reconstruction pilot for an already downloaded pair**, beginning with `6_2_X0650_Y0900_S050_2019_01_04_x0_y320_64x64_1`:

1. Locate the original daily CyAN product and its encoding/version/CRS/geotransform metadata; recover the author `data.json` scene window or validate a reconstruction against the original products. Retain exact URLs, checksums and transformation steps.
2. Write a reviewed target-definition decision stating whether cells/mL categories are justified for the processed reference. If not, document the unsupported conversion and resolve the research target explicitly; do not relabel paper DN bins as cell-density classes.
3. Specify patch aggregation and minimum valid-reference coverage, validate geographic coordinates and water-body/basin grouping, then design a bounded label-aware screening pilot before selecting 10,000-50,000 usable samples.

**Do not train yet.** Once these gates are resolved, freeze a geographically defensible subset and split manifests, implement split-integrity tests, and start with interpretable baselines.

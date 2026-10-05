# Data policy and provenance

Only real public source data belongs here. Synthetic fixtures are confined to `tests/` and temporary pytest directories.

- `raw/inspection/`: eight unchanged NPY image/reference pairs from the pinned Zenodo record, ignored by Git. No reprojecting, scaling, label conversion or resampling is performed locally.
- `metadata/sample_manifest.json`: archive URLs, exact member names, source checksum declarations, selected sample IDs, byte-range logs, SHA-256 hashes, and local paths. Full archive MD5 validation is explicitly **not** claimed; downloaded members pass ZIP CRC32 checks.
- `metadata/*_members.csv`, `*_pairs.csv`: two remote ZIP inventories, including filename-derived date and grid fields. Ignored because they are readily regenerated. Inventory presence does not mean the imagery was downloaded or quality screened.
- `metadata/sources/`: Zenodo record, pinned GitHub tree and supporting documentation. `sources_manifest.json` records retrieval identity and hashes. Upstream Python is read as evidence only, never imported or executed.
- `interim/`, `processed/`: empty, reserved for later validated preprocessing. No fabricated observations.

CyAN references are processed digital-number images. They are not original laboratory measurements, physical cell counts, or an image-level target. Preserve `254`/`255` flags and below-detection `0` semantics. The EDA treats `0..253` as native data-bin values, retains zero as separately reported below-detection, and excludes flags from bin denominators. It does not assume zero cyanobacteria.

NASA defines original product 254 as land and 255 as no data; the author code remaps/masks land into 255, so these archive masks cannot be separated into cloud and land reliably. Arrays have no embedded CRS, geotransform, band names, timestamps, or lake IDs. Names and upstream code provide partial context only.

Dataset attribution: Hänsch and Schloer (2024), [10.5281/zenodo.14230064](https://doi.org/10.5281/zenodo.14230064), CC BY 4.0. Cite the related [paper](https://doi.org/10.1109/JSTARS.2025.3629586) when using this dataset. Generated RGB display stretches and DN summaries are derived representations, not changes to the original arrays.

## Phase 2 additions

`metadata/sample_metadata.csv` is the canonical eight-pair geography table. Blank coordinates/footprints/lake IDs are paired with explicit UNKNOWN/UNVERIFIED statuses. Candidate parent grids and within-tile connected components are separate from the unset final spatial group. A CyAN tile is not an S2/MGRS tile.

`research_outputs/tables/sample_label_audit.csv` preserves each original reference path/hash and exact DN histogram, diagnostic aggregation outputs, quality flags and uncertainty. No cells/mL estimate or final risk label is supplied. `metadata/splits/protocol.json` is a non-executable draft, not a real sample assignment.

`metadata/phase2_sources/` retains access logs, historical author-code ZIP indices, and literature snapshots. HTTP 200 login/redirect pages are explicitly recorded as failures to obtain the requested scientific object. Failed PDF/ZIP requests are saved under truthful HTML/error filenames. No additional image/reference pairs were fetched in Phase 2. Source snapshot hashes are recorded in `phase2_sources_manifest.json`.

## Phase 3 segmentation pilot (current)

`metadata/phase3/frozen_plan.json` is the immutable label-blind selection and split contract for 272 real pairs. `pilot_manifest.json` records local NPY paths and hashes. `pilot_*_split.csv` and `index_*_split.csv` are distinct readable exports; model training uses the pilot JSON assignments. `raw/phase3_pilot/` is ignored data, never synthesized. Source-grid IDs are verified fixed-region identifiers; scene UUIDs and waterbody identities remain unknown. The Phase 2 canonical table is retained as its historical eight-pair audit and does not define segmentation eligibility.

Targets remain H×W maps, with classes 0/1/2 and ignore index -100. No scalar patch label or physical cell-concentration estimate is produced. Both frozen pilot test sets have zero High reference pixels; see the Phase 3 reports before interpreting metrics.

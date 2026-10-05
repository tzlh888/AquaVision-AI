# Current Phase 2 decision after scientific reframing

**READY for bounded pixel-level segmentation training using published DN classes and verified author-grid region groups.** The completed Phase 3 pilot does not establish full three-class geographic generalization; see [initial results](PHASE_3_INITIAL_RESULTS.md).

The previous NOT READY decision below is preserved verbatim as historical audit evidence. Its mandatory cells/mL, image-label and coordinate gates are superseded by the explicitly revised task. Current decision details follow in **Scientific Reframing** at the end.

---

# Phase 2 — label and geographic validation

Audit date: 2026-10-04. Scope: AquaVision-AI only. Evidence comes from eight unchanged real pairs, two previously cached archive inventories, primary publications, official documentation and pinned author code.

## Executive conclusion

**NOT READY for model training.** The Phase 2 investigation and software safeguards are delivered, but the scientific completion criteria are not all satisfied. No predictive model was trained. No sample was assigned estimated cells/mL or a final Low/Moderate/High image label. No final train/validation/test split was created.

The stored references are masked, resampled CyAN digital numbers (DN), rather than cell counts. The released code explains much of the transformation, but original raster processing versions, exact georeferencing and original scene identifiers are missing. These gaps prevent a defensible physical target and verified unseen-waterbody evaluation. More patches alone would not resolve them.

## Verified scientific findings

- All eight Sentinel-2 arrays are `uint16`, shape `(12,64,64)`; references are `uint8`, shape `(1,64,64)`. SHA-256 checks confirm the original sample bytes were preserved.
- The source task is pixel-level segmentation. An image-level risk class is a new target requiring its own environmental definition.
- The eight references contain 24,704 / 358 / 0 valid pixels in native DN bins 0–99 / 100–199 / 200–253, plus 7,706 flag-255 pixels. This is not an estimate of full-corpus prevalence.
- One of eight patches changes diagnostic bin under different aggregation rules. Coverage requirements also alter which patches survive.
- The two cached inventories contain 24,518 pairs on 106 dates. Seventeen parent-grid identifiers form four within-tile adjacency components; these are unverified candidates, not four known lakes or independent regions.
- No audited sample has a verified coordinate, footprint or waterbody identity.

## Label provenance

The supported chain is daily CyAN `CI_cyano` encoded DN → reprojection → bilinear resampling to the warped Sentinel-2 resolution → common window crop → Sentinel-derived cloud/land masking → paired 64×64 NPY arrays. The daily reference lookup uses the Sentinel acquisition calendar date. Individual operations are verified in released code; that does not prove the exact binary-generation environment.

NASA describes original DN 0 as below detection, 1–253 as data, 254 as land and 255 as no data. Additional processing merges exclusion causes into 255, so retained-reference fraction is not a verified water-area fraction. The arrays retain no CRS, geotransform, physical-unit metadata or original scene UUID.

The manuscript's exclusion of patches with more than 5% missing pixels conflicts with a 95% code threshold and an observed patch with 90.53% masking. Cloud/land masking descriptions also differ. These discrepancies are preserved explicitly in the [transformation ledger](LABEL_PROVENANCE.md), with VERIFIED, LIKELY, UNKNOWN and CONFLICTING evidence labels.

## cells/mL conversion decision

**DISABLED.** The current NASA DN-to-index equation and a historical equation cited in primary literature have different coefficients. A further empirical factor relates index to approximate Microcystis-equivalent concentration; index itself is not cells/mL. Neither encoding has been pinned to the actual source rasters used for the deposit, and the released code performs no physical conversion.

Bilinear interpolation of encoded DN followed by exponentiation is generally different from interpolating physical concentration. Calibration transfer, flag treatment and historical integer rounding remain unresolved. The [conversion report](CELLS_PER_ML_VALIDATION.md) gives equations, sources, domains, limitations and analytical comparisons without producing sample abundance estimates. `to_cells_per_ml` continues to reject conversion.

## Image-level label decision

**No primary three-class risk target is finalized.** The strongest currently supported descriptor is the vector of native-bin fractions over retained reference pixels. A future fraction of verified water area above a validated abundance threshold could express bloom extent, but its denominator, threshold and image-class cutoffs are not established.

Median, mean, maximum, 90th percentile, majority bin, above-bin fractions and four-center-pixel consensus were compared. In the mixed patch, median DN is 12 and mean DN is 41.98634, while maximum is 153 and the 90th percentile is 124: median/mean/majority/center yield diagnostic bin 0, maximum/upper quantile bin 1. None is a validated risk class. See [image-label definition](IMAGE_LABEL_DEFINITION.md), [comparison table](../tables/image_aggregation_comparison.csv) and [figure](../figures/phase2_aggregation_sensitivity.png).

Retained-reference coverage scenarios of 5%, 50%, 80% and 95% retain 8, 6, 5 and 5 patches respectively. The mixed patch fails the 50% scenario. No coverage scenario is adopted as final eligibility.

## Risk threshold decision

The requested convention is recorded but disabled: Low <20,000; Moderate ≥20,000 and ≤100,000; High >100,000 cells/mL. The conversion-validity prerequisite failed, so these categories are not operationally validated or applied. The source paper's native DN cutoffs at 100 and 200 do not establish equivalence to these physical thresholds.

Configuration is in [phase2.yaml](../../configs/phase2.yaml). Tests at 19,999, 20,000, 20,001, 99,999, 100,000 and 100,001 verify refusal of unsupported conversion; they do not validate a numerical conversion or classify those concentrations. Native DN boundary tests are separate.

## Geographic grouping decision

Prefer verified basin units subject to whole-waterbody constraints, merging or excluding boundary-crossing units. Buffered spatial blocks with the same constraint are the fallback. Standalone lake grouping, Sentinel tile grouping and state grouping have progressively different contextual leakage limitations; see the [ranked decision table](GEOGRAPHIC_GROUPING_DECISION.md).

No final basin level, block size, group identity or allocation is selected. Filename parent X/Y and patch x/y have different axis conventions. Without the original transforms, generated crop windows and scene identities, these indices do not uniquely determine patch coordinates.

The [canonical metadata table](../../data/metadata/sample_metadata.csv) leaves physical geography UNKNOWN/UNVERIFIED and separates candidate identifiers from the unassigned final spatial group. No geographic maps were generated; [map status](../tables/phase2_map_status.json) records why.

## Spatial leakage analysis

Within the two indexed CyAN tiles, 23 adjacent parent pairs connect the 17 parent grids into four components containing 3,945, 2,398, 17,893 and 282 samples. Splitting by parent ID alone could separate neighboring patches. Even component grouping cannot exclude cross-tile lakes, links through unselected parents, or overlapping original scenes.

The split API requires verified targets, geographic evidence, footprint identities and all intersecting waterbody IDs. It rejects geographic group, footprint and waterbody overlap across partitions. These checks validate supplied metadata consistency, not the truth of a caller's VERIFIED flag; physical intersection and distance audits remain necessary.

## Temporal leakage analysis

Cached acquisitions span 2019-01-04 through 2020-12-10. All 17 parent groups occur on multiple dates. Of 1,391 patch-grid candidates, 1,386 recur across dates. There are 347 parent/date combinations and zero extra samples sharing the same patch-grid-candidate/date. Multiple patches within a parent/date are not duplicate images.

Actual repeated waterbody observations and identical physical footprints remain UNKNOWN. Candidate-component median date gaps are 10, 25, 12.5 and 30 days; these describe retained observations, not orbital revisit periods. All dates of any verified held-out waterbody must stay out of training. See the [spatiotemporal audit](SPATIOTEMPORAL_LEAKAGE_AUDIT.md).

## Proposed research subset

The requested 10,000–50,000 usable images remain a conditional planning range. The available evidence cannot establish an adequate number of independent units, three-class coverage, natural prevalence or training time. No main subset is selected or downloaded.

At the observed 102,656 bytes per stored pair, 10k–50k pairs would occupy approximately 0.956–4.780 GiB of raw file content, before filesystem overhead and derived artifacts. These are storage scenarios, not acquired data. The paper reports 938,607 pairs; only 24,518 have been independently indexed here.

Metadata-scale expansion was explicitly conditional on understanding labels and geography. That gate remains closed, so the remaining four image-archive inventories were not fetched. File lists alone do not expose class distributions; a later bounded reference-member pilot or an author manifest is needed. See the [conditional subset plan](RESEARCH_SUBSET_PLAN.md).

## Proposed train / validation / test splits

- **Random benchmark:** approved eligibility pool, deterministic seed 42, stratified approximately 80/10/10. Illustrative sizes are 8k/1k/1k for 10k eligible images or 40k/5k/5k for 50k. Report repeated-location leakage explicitly.
- **Geographic evaluation:** entire verified basin/block unions with whole-waterbody constraints and all dates kept together. Real group lists and sizes remain unassigned; forcing image percentages must not break groups.

[protocol.json](../../data/metadata/splits/protocol.json) persists the draft with final split creation disabled. No `random_split.csv` or `geographic_split.csv` exists. Future split persistence records the protocol and a source-metadata hash and refuses overwrite. Allocation must be fixed before fitting or score-based choices.

## Tests run

Run from the repository root:

```bash
.venv/bin/python scripts/validate_phase2.py
.venv/bin/python -m pytest -q --junitxml=research_outputs/reports/phase2_pytest_results.xml
.venv/bin/python -m pip check
.venv/bin/python -m compileall -q src scripts tests
```

Coverage includes prior bounded-download/decoding tests, native-label boundaries, blocked physical conversion, invalid/NaN handling, aggregation, filename/geography parsing, adjacency integrity, temporal repetition, deterministic splits, geographic/waterbody/footprint exclusion and frozen-file protection. Synthetic fixtures are restricted to software tests. The offline audit separately checks all eight real pairs and their original hashes.

## Test results

**70 passed, 0 failed, 0 errors, 0 skipped**, including all 37 Phase 1 tests. Dependency consistency and compilation checks passed. The real-data audit completed without producing physical abundance estimates, final risk classes, final partitions or fitted models. See [validation record](phase2_validation.json) and [JUnit results](phase2_pytest_results.xml).

Passing tests establish the implemented behavior and safeguards; they do not resolve the scientific evidence gaps.

## Storage impact

At the [recorded snapshot](phase2_storage_snapshot.json), repository allocated storage was 176,068 KiB (171.94 MiB), including the local environment and ignored sources. This is 5,068 KiB (4.95 MiB) above the saved Phase 1 snapshot of 171,000 KiB. It precedes this final status report and is not an exact before/after Phase 2 measurement.

The same 16 raw NPY files total 821,248 content bytes; **new imagery: 0 bytes**. Phase 2 source files occupy 3,936 KiB allocated. A historical code ZIP was inspected through 26,682 bytes of range responses. This is not total network traffic: documentation retrieval and an aborted size-limited literature request also occurred, and total network usage was not metered. No complete image ZIP was fetched. Source hashes and access outcomes are indexed in [the source manifest](../../data/metadata/phase2_sources/phase2_sources_manifest.json).

## Remaining blockers

| Completion criterion | Answer and unresolved part |
|---|---|
| A. What exactly is the source label? | Processed CyAN DN is established; source-raster version and exact generation environment remain unresolved. |
| B. Can it be converted to cells/mL? | Not defensibly with current evidence; conversion disabled. This is not proof that all future calibration is impossible. |
| C. What is the valid image-level label? | Native-bin fractions are supported descriptors; a primary three-class environmental target is unresolved. |
| D. Are Low/Moderate/High justified? | Not for the stored references; requested physical thresholds remain disabled. |
| E. Which geographic identifier prevents leakage? | Verified basin/block unions with whole-waterbody constraints are proposed; no actual identifiers are verified. |
| F. Can a waterbody recur across dates? | Filename candidates clearly recur; actual same-waterbody observations cannot be measured without identities. |
| G. What spatial unit defines geographic holdout? | Basin preferred, buffered block fallback; level/size and real membership unresolved. |
| H. How many real samples are needed? | 10k–50k is a planning range; independent-unit and class-support requirements cannot yet be estimated. |
| I. What exact experiment will Phase 3 run? | Validation continuation below; model experiments remain conditional. |

Two original daily CyAN GeoTIFF requests returned Earthdata authentication HTML rather than rasters. NASA tile-shapefile requests returned 403. The current author tree, path history and selectively inspected historical code ZIP did not supply generated scene-window `data.json`; `sen2_uuid` is accepted by saving code but discarded. No accessible supplement was located. These are recorded access/evidence limitations, not evidence that missing metadata does not exist elsewhere.

## Exact Phase 3 recommendation

**Continue validation; do not begin predictive modeling.** The next concrete experiment is an eight-pair provenance and georeferencing reconstruction pilot:

1. Obtain authorized original CyAN product headers/rasters and the applicable processing-version documentation, plus the authors' generated geographic windows and Sentinel scene UUID records or equivalent authoritative metadata. Start with the already requested 2019-01-04 tile 6_2 and 2020-10-23 tile 7_2 source products. Do not infer credentials or replace authentication failures with guessed rasters.
2. Reconstruct the original crop/reprojection grids for the eight audited pairs. Compare source flags, alignment and DN distributions against the saved arrays; resolve code/manuscript discrepancies and document any inability to reproduce the deposit.
3. Validate an abundance interpretation and water-area denominator, or explicitly reformulate the task around native reference descriptors. Freeze the intended environmental image target before evaluating predictive models.
4. Intersect verified footprints with authoritative waterbody and basin geometry, assign every intersected waterbody, and audit adjacent/cross-tile/repeated-date connections. Fix the grouping scale and buffers independently of model scores.
5. Only after those gates pass, expand lightweight metadata and conduct a bounded reference-only pilot across independent units to estimate class support and natural prevalence. Then freeze the eligible subset and both split files before opening a modeling phase.

Acceptance requires traceable label interpretation, validated image aggregation and verified physical holdout units. If the missing source evidence remains unavailable, record the dataset as insufficient for the requested risk-generalization study rather than manufacturing labels or coordinates.

## Terminal summary

```text
AquaVision-AI Phase 2: NOT READY
Real pairs audited: 8; cached indexed pairs: 24,518; dates: 106
Parent grids: 17; adjacency candidates: 4; verified geographic groups: UNKNOWN
Tests: 70 passed; dependency/compile checks passed
New imagery: 0 bytes; models trained: 0
cells/mL conversion: DISABLED; image risk labels: UNKNOWN; final splits: NONE
Next: original-product + scene-window provenance/georeferencing pilot
```


## Scientific Reframing

Revision on 2026-10-04, following the user's explicit correction and a fresh reading of the primary manuscript, author preprocessing/inference code, historical repository inventory and dataset archive metadata.

The earlier Phase 2 framed the project as image-level classification and consequently required cells/mL conversion, a scalar patch label and physical footprint reconstruction. The original publication instead defines pixel-level semantic segmentation using DN intervals 0–99, 100–199 and 200–253. `labels.segmentation_target` now returns a spatial int64 label map with classes 0/1/2; 254/255 and invalid values are ignored using -100. Physical conversion remains uncertain but is optional interpretation, not required target generation. Descriptive patch aggregations do not enter learning.

The author's `get_scene_id` and window construction establish that CyAN tile plus parent X/Y/S refers to a fixed selected region. `find_and_update_bordering` recursively groups touching/diagonal selected parents within a tile. These source-grid identifiers are sufficient for the stated unseen-region comparison without latitude/longitude. They do not certify unseen water bodies or eliminate all cross-tile/scene dependence. Missing coordinates, scene UUIDs and lake identities remain documented limitations.

The original no-data filtering discrepancy and uncertainties in masking/resampling are retained. All corrections and pipeline properties are detailed in [ORIGINAL_PIPELINE_RECONSTRUCTION.md](ORIGINAL_PIPELINE_RECONSTRUCTION.md), distinguishing paper, code, both and unresolved evidence.

**Revised gate decision: READY for a bounded source-defined segmentation pilot.** A label-blind 272-pair pool and random/geographic memberships were frozen before downloading its labels. The pilot subsequently trained spectral, classical and neural baselines with saved metrics and checkpoints. No physical cell-concentration target was created.

**Final evaluation readiness: NOT READY for a definitive three-class geographic-generalization claim.** The current 24,518-pair inventory supplies only four selected components, and neither frozen pilot test contains High pixels. This is a new evidence-based evaluation limitation, not a reinstatement of the superseded classification gates. [TRAINING_SUBSET_DECISION.md](TRAINING_SUBSET_DECISION.md) recommends additional independent regions and a reference-support audit, preserving existing splits/results.

All original findings above remain historical records. The current task, pipeline, measured leakage and bounded results are summarized in [PHASE_3_INITIAL_RESULTS.md](PHASE_3_INITIAL_RESULTS.md).

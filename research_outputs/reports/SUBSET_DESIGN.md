# Subset design — provisional, not a selected training dataset

## Phase 1 access probe actually selected

Four pairs from each of the two smallest training ZIPs (`6_2`, `7_2`), eight pairs total. Pair IDs are sorted lexicographically, and four evenly spaced positions including the endpoints are chosen. The exact IDs, member paths and hashes are saved in `data/metadata/sample_manifest.json`.

This label-blind rule checks multiple filenames, dates, and parent grid IDs cheaply and reproducibly. It **does not** produce representative class or seasonal sampling. Selection by sorted name is biased, and endpoint observations are overrepresented. Eight samples are suitable for file/shape/flag verification only, not for model evaluation. No highest-DN-bin pixels were found; we did not cherry-pick extra examples to hide that outcome.

The two inventories cover 24,518 pairs and 17 parent grid candidates, but imagery for only eight pairs was downloaded. Do not call 24,518 the usable subset size. No data from the archive's original test ZIP was downloaded; later geographic test groups must be fixed before model choices.

## Research subset to design after the audit gates

The requested 10,000-50,000 **usable** pairs remains a target range, not a promise or measured selection. Final sample size depends on class support in independent water bodies/basins, valid reference coverage, season coverage and storage. Two coarse CyAN tiles cannot by themselves demonstrate the requested geographic diversity.

Proposed order, subject to evidence:

1. Verify the reference-to-target transformation and image aggregation. Freeze units, thresholds, invalid flags and valid-area rules; preserve original references.
2. Obtain verified geographic footprints and water-body/basin identifiers. Prefer whole basins; if unavailable, use large buffered spatial blocks checked for crossing lakes, then water-body groups. Use state holdout only if better grouping is unavailable and document its limitations.
3. Index remaining archives without downloading image arrays, reconcile the full corpus count, and check duplicate IDs/regions. Screen bounded reference-member batches to estimate valid-pixel and provisional class support.
4. Allocate complete geographic units to train/validation/test; require adequate independent groups for each class. Keep all repeated dates and overlapping/adjacent candidate patches together, and verify cross-tile leakage. Record group counts and nearest inter-split distances once coordinates are validated.
5. Within eligible groups, select dates across seasons/years and cap repeated observations of a location. Retain a geographically held-out distribution suitable for the scientific question; do not balance a test set covertly or tune it using performance.
6. Report class balance *after* quality screening, along with exclusions, confidence intervals respecting geographic clustering, and the resulting effective number of independent locations.

The random-split benchmark will be compared on the same eligibility pool with documented overlap and identical model-selection budgets. Train-only normalization, class weighting and feature transformations are necessary. No test-set-driven model selection or calibration.

## Storage and compute scenarios, not measured outcomes

Each observed pair occupies 98,432 bytes (Sentinel-2 NPY) + 4,224 bytes (reference NPY) = **102,656 bytes uncompressed on disk**, before filesystem overhead. Eight pairs occupy **821,248 bytes** of file content.

If future eligible samples have that same representation:

| Hypothetical count | Raw NPY bytes | Approximate GiB |
|---:|---:|---:|
| 10,000 | 1,026,560,000 | 0.956 |
| 50,000 | 5,132,800,000 | 4.780 |

These estimates exclude indices, derived arrays, environments and checkpoints. They do not guarantee the availability of that many eligible samples or all classes. Avoid duplicating float32 imagery on disk initially; decode batches when later training is justified. Full-sample GPU/CPU runtime cannot be estimated responsibly without timing the final preprocessing and architecture.

## Decision

No final research subset is selected. First resolve the audit's processed-label and geographic-footprint questions, then conduct a bounded metadata/reference screening pilot. This preserves the project's main question: generalization to genuinely unseen water bodies rather than performance on repeated neighboring observations.

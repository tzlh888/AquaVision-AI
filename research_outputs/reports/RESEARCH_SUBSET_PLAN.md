# Research subset plan — conditional; main download NOT authorized by data gates

## Current evidence and decision

Eight real pairs are audited; two cached archive inventories contain 24,518 pairs, 106 dates, 17 parent grids and four connected parent-grid candidates. None has a verified lake/footprint identity. Full training eligibility cannot be established for any sample yet; this is **not** a claim that all imagery is unusable.

Label and geography prerequisites remain unresolved, so the Phase 2 instruction to expand metadata-scale collection **only after they are understood is not satisfied**. The remaining four image-archive indices were not fetched. Investigation of a small historical *code* ZIP and public documentation was for provenance, not bulk imagery acquisition.

## What can and cannot be estimated

| Item | Evidence-based statement |
|---|---|
| Full corpus sample count | Paper reports 938,607; only 24,518 pairs independently indexed here; deposit/corpus total not reconciled |
| Geographic regions | Five training archive tile names in catalog; two indexed. Independent lake/basin/block counts UNKNOWN |
| Dates | 106 distinct dates in the two cached indices; full-corpus count UNKNOWN |
| Physical risk classes | UNKNOWN; cells/mL conversion and image target disabled |
| Native-bin balance | Eight-sample pixel totals: 24,704 / 358 / 0 valid reference pixels in paper bins; not representative prevalence or image-class counts |
| Metadata class availability | ZIP directories hold names/sizes/CRC, not abundance or class summaries. Label-aware screening requires reading reference NPY members or an author-supplied manifest |
| Research sample requirement | Target 10,000-50,000 usable images remains conditional. Minimum meaningful number of independent groups/class cannot be estimated from four unverified candidates and no high-bin example |
| Training time | UNKNOWN until methods, hardware and data pipeline are fixed; no model was benchmarked |

## Storage and hypothetical random split sizes

Observed stored pair size: 98,432 bytes S2 + 4,224 bytes reference = 102,656 bytes, excluding filesystem overhead. Storage arithmetic below assumes future samples have the same representation. It is a planning scenario, not generated or selected data.

| Hypothetical eligible images | Raw bytes | Raw GiB | Random train / validation / test |
|---:|---:|---:|---|
| 10,000 | 1,026,560,000 | 0.956 | Approximately 8,000 / 1,000 / 1,000 |
| 50,000 | 5,132,800,000 | 4.780 | Approximately 40,000 / 5,000 / 5,000 |

Geographic split sizes remain UNKNOWN: whole units determine sample counts, and 80/10/10 cannot be forced without breaking units. The current component imbalance (17,893 versus 282 samples in two components) shows why equal image counts do not imply geographic balance.

## Conditional selection procedure

1. Recover original product/scene provenance, verify the label transformation or explicitly settle the native-reference alternative, and freeze the image target/coverage definition.
2. Obtain verified footprints, all intersecting waterbody IDs and a chosen basin level, or defined buffered blocks with whole-waterbody unions. Audit cross-tile and repeated-scene relationships.
3. Then index remaining archives under a declared metadata budget, reconcile paired IDs/duplicates and enumerate dates/independent units.
4. Read only bounded reference-member batches, selected by fixed seed across units and seasons, to estimate eligibility and natural class prevalence. Keep screening logs and exclusion reasons. Do not select only unusually colorful or high-reference images.
5. Choose total count in the 10k-50k target range **after** class support in independent units is known. Additional repeated patches of one lake cannot replace independent test units. Stop if some class has inadequate held-out support.
6. Freeze the eligibility manifest and geographical group allocation before model fitting. Keep naturally occurring test prevalence; report any training-only sampling/weighting later. Class weighting or balanced training sampling might be useful after measurement; focal loss is not implemented and no balancing method is selected now.

## Proposed experiments

**Random benchmark:** same approved eligibility pool; fixed seed 42, class-stratified approximate 80/10/10. Explicitly report repeated-location leakage. Deterministic split generation is implemented but cannot accept the current UNKNOWN target/geography.

**Primary geographic evaluation:** train, validation and test are distinct verified basin/block unions constrained by whole water bodies and buffers. All dates of each group stay together. Group lists, distances, class distributions and actual sizes must be documented before creating the final split files. No groups are currently assigned to any split.

Persisted `data/metadata/splits/protocol.json` records these intentions with null geographic group assignments and `final_split_creation_allowed: false`. It is not a final split. When prerequisites are satisfied, split creation will hash the source metadata and refuse overwrite; no seed or group search based on scores is permitted.

## Phase 3 recommendation

Do **not** start predictive modeling. Continue the provenance and georeferencing validation gate using authenticated original-product metadata and/or author-generated scene-window/UUID records. After that, conduct a modest reference-only eligibility pilot, finalize the target and whole-waterbody split, and only then open a baseline-modeling phase.

# Executive conclusion

**THREE-CLASS EVIDENCE STILL INSUFFICIENT**

Outcome **B — Partial evidence**. The support-valid v2 benchmark and all existing model families have been evaluated, but limited region replication, support-enriched sampling and short training do not justify strong reliability conclusions.

# Dataset expansion

All six ZIP central directories were indexed without full archive downloads: **404,450 pairs, 156 subtiles, 38 connected selected regions**. The publication reports 938,607 pairs; that is not the measured inventory of this deposited version. The original 24,518-reference pool was completely decoded, and selected reference-only screening expanded the evidence to 38,002 masks. 366,448 references outside that screening remain uninspected.

Source: [Zenodo version 14230064](https://doi.org/10.5281/zenodo.14230064), with the fixed-grid naming/adjacency method verified in [the pinned author preprocessing code](https://github.com/cschloer/hab_detection_s2/blob/e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37/code/dataset/generate_tiles.py). Exact member URLs, sizes, hashes and acquisition reasons are recorded in `data/metadata/phase3_5/downloaded_file_manifest.csv`.

After the completed candidate audit, a new 288-pair support-enriched dataset was selectively assembled. Inputs were never downloaded wholesale. Every retained file has source membership, size/CRC evidence, local SHA-256 and an inclusion reason. The original pilot remains unchanged.

# High-risk support audit

Original pool: **123 High-bearing pairs**, **99,620 High pixels**, **0.116374%** of 85,603,357 valid pixels, in **3 components**, 7 subtiles, 7 dates and 2 source tiles.

All screened masks: 187 High-bearing pairs, 149,720 High pixels, 12 High-containing components and 35 dates. These selected-screening proportions are not full-corpus prevalence. See [complete support audit](HIGH_RISK_SUPPORT_AUDIT.md) and machine-readable candidate/date/patch tables under `research_outputs/phase3_5/`.

# Geographic independence

The verified unit is the fixed author subtile and its connected selected-region component, recomputed using the complete indexed grid. All dates and adjoining selected parents stay together. Components are not certified independent lakes or bloom events. Scene UUIDs and exact physical footprints remain UNKNOWN. Repeated grid locations, adjacent High patches, date clustering, shared source tiles and equal reference-mask hashes are enumerated in [the independence audit](HIGH_RISK_INDEPENDENCE_AUDIT.md).

# Frozen evaluation criteria

The original [support criteria](EVALUATION_SUPPORT_CRITERIA.md) and their hashed contract were saved before screening/evaluation: three qualifying High test components across two CyAN tiles, one validation component, two training components; each qualifying component needs two High dates spanning ≥30 days, two grid positions and ≥100 High pixels. All splits need all three classes. These are operational adequacy floors, not a statistical power calculation or proof of independent bloom episodes.

Acquisition amendment A changed only the mask-count ceiling after a multipart transport probe, keeping the 64 MiB reference response budget, request cap and all scientific criteria unchanged. No model scores affected screening, ranking, selection or splitting.

# New split

`data/metadata/phase3_5/geographic_split_v2.json` and `.csv` persist the exact new membership. The selected dataset intentionally anchors High/date support and adds fixed-hash coverage patches; evaluation prevalence is conditional on that enrichment.

# Split integrity

All reference/input shapes and IDs align, hashes/CRC pass, no sample IDs repeat, no source subtile or full-context connected component crosses partitions, and no exact Sentinel input file hash crosses partitions. This is not independent validation of historical physical co-registration.

# Class distribution

| Split | Groups | Patches | Valid pixels | Low | Moderate | High | Qualified High groups | High % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| train | 2 | 96 | 267,862 | 205,627 | 61,588 | 647 | 2 | 0.2415 |
| validation | 1 | 48 | 144,289 | 117,518 | 25,840 | 931 | 1 | 0.6452 |
| test | 3 | 144 | 428,659 | 302,384 | 88,507 | 37,768 | 3 | 8.8107 |

Per-class percentages, not only High percentages, are saved in `split_support.csv` when a split is approved. High pixel count and qualifying component count are separate measures. Pooled interpolated pixels are not independent experimental replicates.

# Model results

| Model | Accuracy | Macro F1 | Weighted F1 | High precision | High recall | High F1 |
|---|---:|---:|---:|---:|---:|---:|
| NDCI | 0.8070 | 0.5185 | 0.7808 | 0.0081 | 0.0003 | 0.0006 |
| NDVI | 0.6780 | 0.4141 | 0.6682 | 0.0000 | 0.0000 | 0.0000 |
| FAI | 0.3008 | 0.3089 | 0.2955 | 0.2292 | 0.6771 | 0.3425 |
| B8AB4 | 0.6540 | 0.3653 | 0.6270 | 0.0391 | 0.0013 | 0.0025 |
| B3B2 | 0.7079 | 0.4212 | 0.6830 | 0.0000 | 0.0000 | 0.0000 |
| LogisticRegression | 0.8135 | 0.6983 | 0.8188 | 0.6071 | 0.5557 | 0.5803 |
| RandomForest | 0.7477 | 0.4794 | 0.7324 | 0.6970 | 0.0006 | 0.0012 |
| SmallSegCNN | 0.0918 | 0.0632 | 0.0234 | 0.0887 | 0.9886 | 0.1627 |
| DeepLabV3_ResNet18 | 0.6413 | 0.3627 | 0.5867 | 0.2183 | 0.3538 | 0.2700 |

All five spectral baselines, logistic regression, random forest, SmallSegCNN and 12-band DeepLabV3/ResNet18 use the Phase 3 definitions. Neural models remain randomly initialized, unweighted and trained for the same three/two epochs; no tuning or architecture search was performed. Normalization, sampled pixels and thresholds use training only; checkpoints use validation only.

The unchanged bounded classical pixel sampler retained Low/Moderate/High counts [18260, 6224, 56]. Thus classical training has only 56 High pixels, despite the larger total support in training masks. This constraint is exposed rather than corrected by post-test resampling.

# High-risk performance

High precision, recall and F1 are reported explicitly above. Undefined precision means the model predicted no High pixels; it is not hidden as a successful result. A model with zero High recall fails High detection even if Low-dominated accuracy is high.

Logistic regression provides genuine but partial High-detection evidence: pooled High precision 0.6071, recall 0.5557, F1 0.5803; its region-specific High recall ranges from 0.2793 to 0.5900, and F1 from 0.4006 to 0.5964. The equal-region mean High recall is 0.4767, below the pooled recall. One test component contributes 73.74% of High pixels, so pooled metrics overweight that geography.

Random forest reaches 0.7477 accuracy but High recall is only 0.000609: it effectively misses High. SmallSegCNN's High recall 0.9886 comes with precision 0.0887; widespread High predictions do not constitute useful detection. DeepLab's pooled High F1 is 0.2700, with zero High recall in 1 of the three held-out regions. Short unweighted training prevents attributing these failures to inherent architectural limits.

**Why B, not A:** all three classes and the preregistered regional support are now present, but High performance varies materially by region/model, only three test components were assessed, and evaluation prevalence is deliberately enriched. The benchmark passes its operational support gate; strong reliability evidence remains insufficient.

# Per-geographic-group performance

| Model / geographic group | Valid pixels | High support | Macro F1 | High recall | High precision | High F1 |
|---|---:|---:|---:|---:|---:|---:|
| NDCI / author_grid_component:6_2_X0500_Y1150_S050 | 165,722 | 6,345 | 0.5270 | 0.0000 | 0.0000 | 0.0000 |
| NDCI / author_grid_component:6_2_X0650_Y0900_S050 | 151,986 | 3,573 | 0.5056 | 0.0000 | 0.0000 | 0.0000 |
| NDCI / author_grid_component:7_5_X1800_Y1700_S050 | 110,951 | 27,850 | 0.4845 | 0.0004 | 0.0091 | 0.0008 |
| NDVI / author_grid_component:6_2_X0500_Y1150_S050 | 165,722 | 6,345 | 0.3837 | 0.0000 | 0.0000 | 0.0000 |
| NDVI / author_grid_component:6_2_X0650_Y0900_S050 | 151,986 | 3,573 | 0.3796 | 0.0000 | N/A | 0.0000 |
| NDVI / author_grid_component:7_5_X1800_Y1700_S050 | 110,951 | 27,850 | 0.4859 | 0.0000 | 0.0000 | 0.0000 |
| FAI / author_grid_component:6_2_X0500_Y1150_S050 | 165,722 | 6,345 | 0.3849 | 0.8367 | 0.1054 | 0.1872 |
| FAI / author_grid_component:6_2_X0650_Y0900_S050 | 151,986 | 3,573 | 0.1399 | 0.9415 | 0.1171 | 0.2082 |
| FAI / author_grid_component:7_5_X1800_Y1700_S050 | 110,951 | 27,850 | 0.3683 | 0.6068 | 0.5205 | 0.5603 |
| B8AB4 / author_grid_component:6_2_X0500_Y1150_S050 | 165,722 | 6,345 | 0.3151 | 0.0000 | 0.0000 | 0.0000 |
| B8AB4 / author_grid_component:6_2_X0650_Y0900_S050 | 151,986 | 3,573 | 0.3559 | 0.0000 | N/A | 0.0000 |
| B8AB4 / author_grid_component:7_5_X1800_Y1700_S050 | 110,951 | 27,850 | 0.4239 | 0.0017 | 0.0402 | 0.0033 |
| B3B2 / author_grid_component:6_2_X0500_Y1150_S050 | 165,722 | 6,345 | 0.4291 | 0.0000 | 0.0000 | 0.0000 |
| B3B2 / author_grid_component:6_2_X0650_Y0900_S050 | 151,986 | 3,573 | 0.3384 | 0.0000 | 0.0000 | 0.0000 |
| B3B2 / author_grid_component:7_5_X1800_Y1700_S050 | 110,951 | 27,850 | 0.4116 | 0.0000 | N/A | 0.0000 |
| LogisticRegression / author_grid_component:6_2_X0500_Y1150_S050 | 165,722 | 6,345 | 0.7299 | 0.5608 | 0.6025 | 0.5809 |
| LogisticRegression / author_grid_component:6_2_X0650_Y0900_S050 | 151,986 | 3,573 | 0.6400 | 0.2793 | 0.7078 | 0.4006 |
| LogisticRegression / author_grid_component:7_5_X1800_Y1700_S050 | 110,951 | 27,850 | 0.5906 | 0.5900 | 0.6029 | 0.5964 |
| RandomForest / author_grid_component:6_2_X0500_Y1150_S050 | 165,722 | 6,345 | 0.4699 | 0.0000 | N/A | 0.0000 |
| RandomForest / author_grid_component:6_2_X0650_Y0900_S050 | 151,986 | 3,573 | 0.4321 | 0.0000 | N/A | 0.0000 |
| RandomForest / author_grid_component:7_5_X1800_Y1700_S050 | 110,951 | 27,850 | 0.4879 | 0.0008 | 0.6970 | 0.0016 |
| SmallSegCNN / author_grid_component:6_2_X0500_Y1150_S050 | 165,722 | 6,345 | 0.0295 | 0.9989 | 0.0390 | 0.0750 |
| SmallSegCNN / author_grid_component:6_2_X0650_Y0900_S050 | 151,986 | 3,573 | 0.0219 | 0.9978 | 0.0240 | 0.0468 |
| SmallSegCNN / author_grid_component:7_5_X1800_Y1700_S050 | 110,951 | 27,850 | 0.1534 | 0.9851 | 0.2502 | 0.3991 |
| DeepLabV3_ResNet18 / author_grid_component:6_2_X0500_Y1150_S050 | 165,722 | 6,345 | 0.2174 | 0.0000 | 0.0000 | 0.0000 |
| DeepLabV3_ResNet18 / author_grid_component:6_2_X0650_Y0900_S050 | 151,986 | 3,573 | 0.3703 | 0.4352 | 0.1093 | 0.1747 |
| DeepLabV3_ResNet18 / author_grid_component:7_5_X1800_Y1700_S050 | 110,951 | 27,850 | 0.4433 | 0.4240 | 0.4846 | 0.4523 |

All confusion matrices use rows=true and columns=predicted. When evaluated, group matrices are checked to sum exactly to the pooled test matrix. Full Low/Moderate/High precision, recall, F1, support, accuracy, macro F1 and weighted F1 are in `model_metrics.csv` and the JSON results; `per_geographic_group_metrics.csv` exposes geographic variation.

# Pilot vs expanded comparison

| Model | Pilot geographic macro F1* | v2 macro F1 | Pilot High F1 | v2 High F1 |
|---|---:|---:|---|---:|
| NDCI | 0.4185 | 0.5185 | N/A (no support) | 0.0006 |
| NDVI | 0.2599 | 0.4141 | N/A (no support) | 0.0000 |
| FAI | 0.2781 | 0.3089 | N/A (no support) | 0.3425 |
| B8AB4 | 0.2891 | 0.3653 | N/A (no support) | 0.0025 |
| B3B2 | 0.4503 | 0.4212 | N/A (no support) | 0.0000 |
| LogisticRegression | 0.3266 | 0.6983 | N/A (no support) | 0.5803 |
| RandomForest | 0.3768 | 0.4794 | N/A (no support) | 0.0012 |
| SmallSegCNN | 0.2676 | 0.0632 | N/A (no support) | 0.1627 |
| DeepLabV3_ResNet18 | 0.3222 | 0.3627 | N/A (no support) | 0.2700 |

*Pilot macro averaged three slots with undefined-class score set to zero; its test contained no High pixels. The numbers are not like-for-like estimates of the same three-class distribution. Model families/configuration are unchanged, but training observations, independent regions and test prevalence differ. Each model was refitted on v2 training only; old checkpoints were not overwritten.

See [comparison report](PILOT_VS_EXPANDED_EVALUATION.md). Weaker scores are retained. No A/B outcome is manufactured by swapping regions or hiding failed classes. This is partial evidence, not readiness for later reliability modules.

# Tests

**103 tests passed**, including all original 94 tests. Added tests cover strict multipart framing and binary payloads, bounded member CRC/NPY decoding, no-gap range coalescing, support criteria, minimum independent groups, date/position diversity, deterministic allocation, missing High, duplicated IDs, group/subtile leakage and full-context adjacency identity. The original 42 pilot artifacts pass the preservation hash audit.

All 36 saved pooled/per-region test confusion matrices (nine models × pooled plus three regions) reproduce exactly after reloading the saved artifacts. The reproduction check also confirms immutable criteria, deterministic group allocation, source/artifact hashes, training-only normalization and pixel selection, and actual mask class counts.

# Storage impact

Metadata range acquisition charged 106,709,170 bytes; reference requests charged 48,696,346 bytes over 593 requests, including conservative envelope reservations and failed attempts. These are bounded charged-byte totals, not exact wire traffic. Full archives were not downloaded. Selective paired-input acquisition charged 21,763,564 bytes.

Allocated repository storage at reporting time: 1,978,100 KiB. Phase 3.5 metadata: 300,760 KiB; reference cache: 301,776 KiB; Phase 3.5 results: 70,828 KiB. The repository total includes the previously installed runtime. Detailed storage and validation are saved separately.

# Remaining limitations

- Outside the original 24,518-pair pool, reference screening is incomplete and enriched by compressed-mask complexity. Unscreened content is not assumed negative.
- v2 has deliberately enriched High support, with different class proportions across train, validation and test. Reported precision and accuracy are conditional on this design, not estimates under natural whole-deposit or field prevalence.
- Selected connected author-grid regions are the highest-confidence grouping; exact scenes, water bodies and cross-tile physical overlap remain unknown.
- Thirty-day-separated observations may still be one bloom episode; numerous interpolated pixels cannot establish independent biological evidence.
- Only three test components, one seed, support-enriched class prevalence and two/three neural epochs constrain interpretation. Model performance is not a converged benchmark, and geographic variation matters.
- Source masking/no-data discrepancies and remote-sensing label uncertainty persist; no direct laboratory or cells/mL claims are made.

# Exact next recommendation

Keep v2 fixed. First examine per-region errors and extend the same baseline training to a predeclared convergence budget, without changing architecture or consulting test scores for selection. Separately expand independent-region and episode support for a later untouched evaluation version, with a prevalence-preserving sampling design. Do not yet start calibration, Grad-CAM, robustness, frontend or architecture searches.

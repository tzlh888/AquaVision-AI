# AquaVision AI — One-Page Research Summary

## Research objective

AquaVision AI investigates whether Sentinel-2 multispectral imagery can identify NASA CyAN-derived bloom-proxy classes at geographically unseen waterbodies. The project’s most important result is not a new classifier. It is a scientific audit showing when a geographically convincing model claim cannot be supported, followed by a metadata-first attempt to build the missing evidence correctly.

## Historical evidence audit

The historical v2 benchmark contains 288 paired Sentinel and processed CyAN arrays: 96 training, 48 validation, and 144 test samples. All 576 arrays were exactly recovered and verified by hash. The modelling target is a processed satellite proxy: CyAN digital numbers 0–99, 100–199, and 200–253 map to Low, Moderate, and High. It is not field-measured toxin concentration or laboratory ground truth.

The audit found that the historical public artifacts do not retain the Sentinel product UUID, original CRS and affine transform, actual patch footprint, real waterbody identity, or confirmed historical CyAN processing version. The split’s author-grid components therefore cannot be assumed to be independent lakes. Historical High pixel counts are real array counts, but not verified independent geographic evidence.

Under the frozen historical rule, NDCI was validation-selected even though validation High F1 was 0; its test High F1 was 0.0006. Logistic Regression later showed test High F1 0.5803, but it was not validation-selected and cannot be chosen retrospectively. No CNN passed the predefined class guard. These metrics describe behavior on the legacy split, not reliable cross-waterbody generalization.

## Prospective v3 pilot

The project then built a traceable geospatial label-integration workflow. Six preselected Sentinel scenes across three named waterbodies were matched to six official NASA Ocean Color CyAN daily GeoTIFFs. All six products were obtained, hash-verified, confirmed as OBPG version 6.0, aligned by date and footprint, and transformed from the native 300 m grid to 64 × 64 Sentinel patch support. Discrete labels use nearest-neighbor source values; bilinear processing is diagnostic only and occurs before class mapping.

This bounded pilot succeeded technically. Two of three waterbodies contained High proxy support, totaling three High scenes and 48 distinct native High pixels. However, none met the frozen independent-unit requirement.

## Bounded expansion and stopping decision

Twelve additional waterbody candidates were frozen before screening. Five obtained authoritative identities and geometry; three contained at least one High native pixel. Only Lake Winnebago showed strong multi-date label-side potential, but no new Sentinel payload or complete patch provenance was acquired. The candidate universe could supply at most eight independent waterbodies, below the minimum nine needed for training/validation/confirmation partitions of 3/3/3. The study stopped instead of weakening its standards.

The final counts are **0 qualified independent High units** and **0/0/0 training, validation, and confirmation members**. No confirmation set was sealed, and Phase 3B model training did not begin.

## Scientific contribution

AquaVision demonstrates that pixel volume is not sample independence. A 300 m CyAN cell repeated across many 20 m pixels is still one coarse proxy observation. Same-scene crops and repeated dates also do not become independent simply because there are many patches. The project preserves negative results, distinguishes technical pipeline success from model success, and records a defensible stop condition.

## Final conclusion

The final status is **LIMITED**. The historical benchmark supports exploratory evidence of spectral signal but not verified geographic generalization. The v3 work proves that an end-to-end, identity-rich label pipeline is technically feasible, but it did not produce the independent High-class support required for a credible new modelling study. This is a strong undergraduate research narrative about data provenance, spatial dependence, failed validation gates, and scientific judgment—not a claim of operational algal-bloom detection.

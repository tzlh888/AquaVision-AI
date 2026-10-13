# AquaVision V3-only bounded expansion protocol

Status: **FROZEN BEFORE NEW PHASE 3A-3 LABEL SCREENING OR DOWNLOAD**  
Freeze date: 2026-10-12 (Europe/Budapest)  
Scope: metadata-first, High-enriched, v3-only dataset construction. No model training or model-based sample selection is permitted.

## 1. Scientific purpose and limits

This phase tests whether a geographically identified, provenance-complete v3-only dataset can satisfy the already-frozen High-unit qualification gate. It does not estimate natural class prevalence and it does not establish external model generalization.

Hard engineering limits are:

- no more than 12 newly retained real waterbodies;
- no more than 24 new Sentinel-2 scene/date combinations;
- no more than 24 newly downloaded unique CyAN source products;
- no automatic expansion when a limit is exhausted;
- no training, hyperparameter selection, threshold tuning, or use of model predictions.

The six verified CyAN V6 products and three pilot waterbodies remain admissible provenance evidence, but every unit is re-evaluated under this protocol. Reuse of an existing raw product does not count as a new download.

## 2. Frozen candidate-pool construction

### Amendment 1 — infrastructure fallback (2026-10-12, before any new CyAN value was inspected)

The nationwide `returnIdsOnly` query defined below returned HTTP 504 on all three bounded attempts and yielded no candidate metadata or label values. To distinguish an oversized-service-query failure from absence of data, the following fallback pool is frozen before any Phase 3A-3 CyAN screening: Lake Erie, Lake Champlain, Lake Winnebago, Mille Lacs Lake, Lake Pontchartrain, Clear Lake (California), Pyramid Lake (Nevada), Lake Texoma, Fort Peck Lake, Lake Sakakawea, Lake Eufaula (Oklahoma), and Saginaw Bay. Approximate point coordinates are used only to constrain the authoritative USGS identity query; they are not accepted as geometry or proof of identity. The selection is a deliberately bounded, geographically dispersed, large-waterbody/HAB-relevant engineering pool and is not a probability sample. Every listed candidate, including every failure or rejection, remains in the catalog. At most one bounded USGS identity query is made for each pre-listed candidate. No further substitution is permitted after label inspection begins.

This amendment changes only the candidate-pool retrieval mechanism. The High mapping, qualification gate, resource limits, and all stopping rules remain frozen.

The candidate universe is defined independently of model output:

1. Query the official USGS NHDPlus HR Waterbody service for named CONUS features with `AREASQKM >= 50`.
2. Preserve the returned object identifiers, attributes, query URL, retrieval time, response hash, and every accept/reject decision.
3. Intersect the resulting waterbody geometries with the six already downloaded, verified 2025 CyAN V6 daily products from the Final Label Pilot.
4. Use CyAN values only for label-enriched screening. This makes the retained sample explicitly **High-enriched**; it must never be described as an estimate of natural Low/Moderate/High occurrence.
5. Exclude a feature only for missing required identity/geometry, no valid CyAN coverage, insufficient label/date support, unavailable Sentinel match, duplicate/overlapping waterbody identity, or a hard resource limit. Rejections remain in the catalog.

If the official service cannot return reproducible identities for the pre-listed fallback pool, dataset expansion stops rather than substituting guessed identities.

## 3. Frozen label and temporal rules

- CyAN source: official NASA OBPG daily CONUS GeoTIFF, processing version V6 only.
- Values 0--99: Low; 100--199: Moderate; 200--253: High; 254: land; 255: no-data/invalid.
- Class mapping occurs on native CyAN values before any display-grid resampling.
- Sentinel and CyAN calendar dates must match exactly for this phase.
- A candidate High unit must contain at least two qualifying dates separated by at least 30 days.
- If more than two dates qualify, choose the two dates with greatest reproducible native High support; ties are resolved by earliest date and then lexicographic product ID.
- No unverified product version or inferred version is accepted.

## 4. Native-pixel identity and patch construction

The native CyAN identity is `(cyan_product_id, native_row, native_col)`. Within one product/date, repeated sampling of the same native cell counts once. The same geographic cell observed on another date is reported as a temporal repeat and as a separate dated label observation, while an additional undated spatial-identity count is also reported.

For each retained waterbody/date:

1. query an official Copernicus Data Space Sentinel-2 L2A item covering the candidate area and exact date;
2. select the item that covers the largest reproducible set of eligible High centers, then lower reported cloud cover, then lexicographic item ID;
3. anchor 64 x 64 patches to the Sentinel 20 m raster grid (1.28 km x 1.28 km footprint);
4. enumerate deterministic candidate windows containing native High-cell centers inside the waterbody;
5. greedily retain spatially non-overlapping windows that add the largest number of previously uncovered native High identities; ties use top-left raster row/column;
6. retain at most eight patches per scene/date and at most sixteen patches per waterbody unit.

Nearest-neighbour is the only permitted resampling method for discrete class labels. Bilinear interpolation may be recorded only as a continuous-value sensitivity diagnostic and may not determine class membership.

## 5. Frozen High-unit qualification gate

The Phase 3A-1 gate is unchanged. A waterbody is a qualified independent High unit only if all conditions hold:

- verified real waterbody identity and geometry;
- complete Sentinel and CyAN provenance for every retained sample;
- at least two qualifying dates separated by at least 30 days;
- at least three non-overlapping High patches;
- at least 100 unique dated native High identities after within-product deduplication;
- spatial registration, mask, and product-version checks pass;
- no unresolved identity or cross-split/event dependence.

The geometry audit must report that a single 64 x 64 patch covers only about 19 native 300 m pixel centers in the existing pilot geometry. Consequently, three patches alone can contribute at most about 57 non-duplicated centers; satisfying the 100-pixel condition normally requires at least six suitably placed, low-overlap patches. This observation does not alter the frozen gate.

## 6. Split assignment and independence

The independent unit is the conservatively grouped real waterbody/event history, not a patch, pixel, or scene.

- A waterbody and all of its scenes, dates, overlapping footprints, and strongly related observations belong to exactly one split.
- Duplicate or overlapping USGS features are merged into one conservative group or rejected.
- Split allocation occurs only after qualification and before any model result exists.
- Deterministic allocation order is SHA-256 of `phase3a3-split-v1|waterbody_id`; eligible units are assigned round-robin to Training, Validation, Confirmation while targeting at least three qualified High units in each.
- Confirmation membership, qualification evidence, member hashes, and the aggregate manifest hash must be sealed before any model training.
- Confirmation data cannot be used for architecture selection, hyperparameter selection, threshold optimization, or stopping decisions.

If fewer than nine qualified independent High units exist, the minimum 3/3/3 design cannot be sealed and the result is **NOT READY**. Empty or incomplete confirmation files are not represented as a successful seal.

## 7. Provenance and fail-closed rules

Every accepted sample requires: Waterbody ID, Sentinel scene/item ID, provider product identity/UUID when available, acquisition time, CRS, affine transform, patch footprint, CyAN source ID, OBPG version, native CyAN identities, raw hashes or provider asset identity plus downloaded-window hash, derived-label hash, mask/resampling configuration, source licence, and conservative group identity.

Missing required evidence causes rejection. A matching row count, similar image, approximate location, file date, or author-grid component is not enough to establish identity. Historical v2 samples with unknown geography are excluded from v3-only training, validation, and confirmation.

## 8. Download and processing budget

Before the first new payload download, the run records an estimate of unique products, expected bytes, local free space, request count, and processing footprint. Metadata requests are not payload downloads. Existing full-CONUS CyAN files are reused first. Any new CyAN download must be one of the pre-recorded selected dates and must remain within the 24-product limit.

Sentinel acquisition is limited to the minimum official assets/windows needed to establish an end-to-end reproducible sample. Partial/range downloads must record source asset URL, byte-range or window specification, response identity, and SHA-256. If a source cannot provide stable, attributable assets, the sample is rejected.

## 9. Stop conditions

Stop without relaxing standards when any of the following occurs:

- authoritative waterbody identity/geometry cannot be reproduced;
- product version or source cannot be verified;
- the 12-waterbody, 24-scene/date, or 24-new-CyAN limit is reached without nine qualified units;
- label geometry makes the frozen gate unattainable for the retained candidates;
- Sentinel/CyAN matching or required raw evidence cannot be obtained within the bounded run;
- cross-split independence cannot be established;
- a complete three-unit Confirmation split cannot be sealed.

The truthful terminal decision is READY, CONDITIONALLY READY, or NOT READY. READY only means the frozen prerequisites for a later Phase 3B have been met; it does not imply model reliability.

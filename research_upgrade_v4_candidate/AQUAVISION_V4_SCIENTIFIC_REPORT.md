# AquaVision AI — Research Upgrade V4 Candidate

## Evidence status

- **HISTORICAL:** 288 Sentinel/CyAN patch pairs, not 288 independent waterbodies; validation-selected NDCI; Logistic Regression geographic-Test High F1 0.5803 is post-hoc and not selection evidence.
- **REPRODUCED:** 124 current public tests passed with one documented complete-frozen-environment skip; all 60 research-upgrade tests passed.
- **NEW METHOD VALIDATION + DATA INTEGRATION:** V4 normalized the frozen V3 scene/product/footprint and waterbody-unit evidence into two reviewable audit tables and applied a dynamic fail-closed readiness gate. No new external records were added.
- **CONFIRMED:** no model-performance claim.
- **NOT READY:** 0 qualified independent High units; 0/0/0 Training/Validation/Confirmation members.

## Geographic evidence recovery

The project has strong traceability for six prospective pilot scene pairs: named waterbody, Sentinel product, date, patch CRS/affine/footprint, same-day CyAN V6 product and hash, native-grid overlap, and reference support. This is engineering and provenance evidence. It does not make six independent waterbodies: the scenes collapse to three waterbody histories.

The historical 288-pair benchmark remains geographically unresolved. Its author-grid components cannot be promoted to verified lakes, and 64×64 pixels cannot be counted as 4,096 independent labels. Resampling a roughly 300 m CyAN cell to a 20 m grid does not add independent evidence.

## Conditional model experiment

Not run. The frozen A2 gate failed before training. Consequently no new NDCI, Logistic Regression, Random Forest, or CNN comparison exists in V4, no Confirmation labels were accessed for model choice, and the final scientific status remains **LIMITED / NOT READY**.

## Scientific improvement

V4 makes the negative readiness decision machine-readable and separates three claims that are often conflated: exact array reproducibility, scene/label provenance, and independent cross-waterbody evidence. Only the first two are demonstrated for bounded portions of the project. This is **METHOD VALIDATION + DATA INTEGRATION**, not independent model confirmation.

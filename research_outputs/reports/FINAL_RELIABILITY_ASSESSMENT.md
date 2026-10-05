# Final reliability assessment

**Final scientific claim: LIMITED evidence for reliable three-class geographic generalization.**

**Ability:** Sentinel-2 multispectral features contain useful predictive information about the released CyAN-derived classes in this selected sample. The unchanged LR reaches Test Macro F1=0.6983 and High F1=0.5803, with High F1=0.4006–0.5964 across the three regions. All 12 outperforms RGB in the controlled diagnostic CNN run. These are evidence of association and partial discrimination, not a direct field validation of bloom risk, toxicity or cell concentration.

**Reliability:** The prospective selection rule chooses NDCI, whose High F1 is 0 on Validation and 0.0006 on Test; it fails High in two held-out regions. No CNN passes both validation class guards. LR's apparent Test advantage was already known and does not justify selecting it after viewing Test; it also misses all sampled training High pixels and all validation High pixels. Its high-confidence High precision varies sharply by region. RF misses almost all High and weighting/sampling does not fix it. The diagnostic CNN has 510 high-confidence High false positives and no true positives at that threshold. These results do not support dependable geographic three-class risk decisions.

The preregistered validation winner is `baseline_NDCI` (validation Macro F1 0.5751; validation High F1 0.0000). It fails to demonstrate High detection on Validation. `deep_weighted` is the highest-ranked CNN (validation Macro F1 0.3676; Low/Moderate/High F1 0.8507/0.1895/0.0625). **No CNN meets both preregistered Low>=0.50 and Moderate>=0.25 floors.** This CNN is a diagnostic fallback, not an eligible deployment choice. Ablations are excluded from winner selection by registration.

## Geographic uncertainty

| Model | Regional High F1 min | Regional High F1 max | LOO pooled High F1 min | LOO pooled High F1 max |
| --- | --- | --- | --- | --- |
| baseline_NDCI | 0.0000 | 0.0008 | 0.0000 | 0.0007 |
| baseline_LogisticRegression | 0.4006 | 0.5964 | 0.5288 | 0.5936 |
| baseline_RandomForest | 0.0000 | 0.0016 | 0.0000 | 0.0015 |
| deep_weighted | 0.1616 | 0.4546 | 0.1740 | 0.4138 |

These are observed geographic ranges and leave-one-region-out sensitivity, **not confidence intervals**. Each leave-one-out estimate sums confusion counts over the other2 whole regions before scoring; no individual-pixel bootstrap is used. Only 3 selected connected components cannot supply a reliable population-level interval. 7_5_X1800_Y1700 contributes 27,850 of 37,768 High Test pixels (73.74%); pooled metrics are heavily influenced by that region. Report all 3 regions rather than attaching pseudo-precise confidence to 428,659 correlated pixels.

[`leave_one_region_out.csv`](../phase4/leave_one_region_out.csv); [central reliability matrix](MODEL_RELIABILITY_MATRIX.md).

## What Phase4 resolves

The LR/RF difference is reproducible, the minority class is not missing from RF trees, and reweighting is insufficient. Larger aggregate spectral shift does not identify the worst High region. Temporal composition is also shifted, but the three-region evidence cannot identify causation. Temperature scaling can improve one calibration metric and worsen another without changing any classification. Mild synthetic perturbation stability coexists with poor baseline reliability. Integrated gradients supplies approximate exploratory model sensitivity, not causal explanation.

## Limitations and Phase5

The v2 subset is label-enriched: High prevalence is 0.242% in Train, 0.645% in Validation, and 8.811% in Test. Precision and calibration are conditional on that composition. There are two training components, one validation component and only three held-out connected geographic components; component separation does not certify separate lakes or independent bloom episodes. References are processed/resampled CyAN DN classes, not in-situ cell counts, toxin measurements, or verified 20 m biological ground truth. Neural budgets remain only 3 epochs (SmallSegCNN) / 2 epochs (DeepLab), random initialization, one seed. These are controlled short-budget experiments, not converged architecture comparisons.

Phase5 should prioritize additional independently held-out geographic components and independent validation regions with substantial, diverse High support; preserve v2 as an already-used benchmark and create a new external holdout before further optimization. Recover lake/scene/footprint metadata and validate temporal/event independence. Establish longer, train/validation-only convergence schedules and repeated seeds within a fixed budget, then reassess imbalance and band effects on the new holdout. Validate against independent in-situ biological/toxin measurements before any operational risk interpretation. Predefine per-class and worst-region operating requirements and calibration/abstention evaluation using validation data. Do not build a frontend or present these models as deployment-ready.

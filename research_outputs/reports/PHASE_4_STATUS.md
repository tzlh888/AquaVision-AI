# Executive conclusion

**Phase4 complete. Final scientific claim: LIMITED evidence for reliable three-class geographic generalization.** The project demonstrates partial predictive ability on CyAN-derived reference classes, but validation selection, minority behavior and confidence reliability do not support dependable unseen-region operation. 11 new model fits were evaluated: 8 imbalance variants and 3 band ablations, alongside 9 frozen baselines. No frontend was built.

# Best validation-selected model

The preregistered validation winner is `baseline_NDCI` (validation Macro F1 0.5751; validation High F1 0.0000). It fails to demonstrate High detection on Validation. `deep_weighted` is the highest-ranked CNN (validation Macro F1 0.3676; Low/Moderate/High F1 0.8507/0.1895/0.0625). **No CNN meets both preregistered Low>=0.50 and Moderate>=0.25 floors.** This CNN is a diagnostic fallback, not an eligible deployment choice. Ablations are excluded from winner selection by registration.

[Registered selection protocol](MODEL_SELECTION_PROTOCOL.md). The original LR has the highest observed Test Macro F1, but it is not the validation-selected winner.

# Geographic generalization

| Model | Region | Macro F1 | High P | High R | High F1 |
| --- | --- | --- | --- | --- | --- |
| baseline_NDCI | 6_2_X0500_Y1150 | 0.5270 | 0.0000 | 0.0000 | 0.0000 |
| baseline_NDCI | 6_2_X0650_Y0900 | 0.5056 | 0.0000 | 0.0000 | 0.0000 |
| baseline_NDCI | 7_5_X1800_Y1700 | 0.4845 | 0.0091 | 0.0004 | 0.0008 |
| baseline_LogisticRegression | 6_2_X0500_Y1150 | 0.7299 | 0.6025 | 0.5608 | 0.5809 |
| baseline_LogisticRegression | 6_2_X0650_Y0900 | 0.6400 | 0.7078 | 0.2793 | 0.4006 |
| baseline_LogisticRegression | 7_5_X1800_Y1700 | 0.5906 | 0.6029 | 0.5900 | 0.5964 |
| baseline_RandomForest | 6_2_X0500_Y1150 | 0.4699 | N/A | 0.0000 | 0.0000 |
| baseline_RandomForest | 6_2_X0650_Y0900 | 0.4321 | N/A | 0.0000 | 0.0000 |
| baseline_RandomForest | 7_5_X1800_Y1700 | 0.4879 | 0.6970 | 0.0008 | 0.0016 |
| deep_weighted | 6_2_X0500_Y1150 | 0.2973 | 0.1140 | 0.4145 | 0.1788 |
| deep_weighted | 6_2_X0650_Y0900 | 0.4093 | 0.1171 | 0.2606 | 0.1616 |
| deep_weighted | 7_5_X1800_Y1700 | 0.5493 | 0.3731 | 0.5814 | 0.4546 |


The validation-selected NDCI has Test Macro F1=0.5185, High F1=0.0006. The original LR has 0.6983/0.5803. The diagnostic weighted DeepLab has 0.4407/0.3522. [Model reliability matrix](MODEL_RELIABILITY_MATRIX.md) separates the old matched random/geographic pilot from v2; v2 has no matched Random result.

# High-risk performance

37,768 High Test pixels are present, so failure is now measurable. RF predicts High only 33 times (23 correct); weighted and balanced RF each predict one false High pixel and detect no true High pixels. LR detects 20,987 High pixels while missing 16,781. The selected NDCI misses 37,756. High recall by itself is insufficient: SmallSegCNN's near-universal High output has very poor precision.

# Regional variability

The hardest region depends on model and metric. LR High F1 spans 0.4006–0.5964; diagnostic CNN spans 0.1616–0.4546. One region contributes 73.74% of High Test support. [Regional failure analysis](REGIONAL_FAILURE_ANALYSIS.md) and machine-readable TP/FP/FN/proportions cover every 20 model×3 region×3 class combination.

# Class-imbalance experiments

Same-pixel LR/RF weighted fits, same-pool balanced sampling, and loss-only weighted/focal CNN variants are complete. Repeated sampling reuses 56 unique High training pixels. RF High failure persists; weighted DeepLab improves but does not pass the validation guard. [Full controlled comparison](CLASS_IMBALANCE_EXPERIMENTS.md).

# Distribution shift

The region with the largest average 12-band shift has the best LR/CNN High F1; the worst High region has the smallest spectral mean shift and largest monthly composition difference. Neither observation establishes causation with 3 regions. [Spectral analysis](REGIONAL_DISTRIBUTION_SHIFT.md); [temporal analysis](TEMPORAL_SHIFT_ANALYSIS.md).

# Calibration

LR High predictions at confidence>=0.8 are correct 60.96% pooled and 46.55% in its worst High region. The diagnostic CNN's 510 high-confidence High predictions are all false. Validation-only temperature scaling preserves every argmax; for that CNN NLL improves while ECE and Brier worsen. [Calibration analysis](CALIBRATION_ANALYSIS.md).

# Robustness

12 registered multispectral perturbations were evaluated. Worst pooled Macro decrease −0.0064; worst High-F1 decrease −0.0278. Low baseline reliability prevents a robustness claim from these small deltas. Clipping and synthetic-mask limitations are explicit. [Robustness analysis](ROBUSTNESS_ANALYSIS.md).

# Multispectral ablation

All 12 versus RGB increases Test Macro F1 by 0.0512 and High F1 by 0.0584. The 8-band visible/red-edge/NIR model has higher Macro but lower High F1 than All 12. This single-seed short-budget experiment is suggestive, not a stable superiority claim. [Band ablation](BAND_ABLATION.md).

# Explainability

21 deterministic region/category examples show RGB/reference/prediction/error/confidence. Segmentation-targeted integrated gradients covers one fixed High mask per region; numerical residuals and baseline limitations are disclosed. It is sensitivity analysis, not causal proof. [Explainability and error panels](EXPLAINABILITY_ANALYSIS.md).

# Statistical uncertainty

| Model | Regional High F1 min | Regional High F1 max | LOO pooled High F1 min | LOO pooled High F1 max |
| --- | --- | --- | --- | --- |
| baseline_NDCI | 0.0000 | 0.0008 | 0.0000 | 0.0007 |
| baseline_LogisticRegression | 0.4006 | 0.5964 | 0.5288 | 0.5936 |
| baseline_RandomForest | 0.0000 | 0.0016 | 0.0000 | 0.0015 |
| deep_weighted | 0.1616 | 0.4546 | 0.1740 | 0.4138 |


Observed ranges and leave-one-region-out sensitivity are descriptive only. No pixel bootstrap or misleading population confidence interval was produced with only 3 selected geographic components.

# Tests

**123 tests pass: all 103 original tests plus 20 new tests.** Original expected outputs were not changed. [Test results](../phase4/pytest_results.xml).

# Reproducibility

**100 confusion matrices and 40 class-prediction caches reproduce exactly; 177 prior files remain unchanged.** Nine validation-fitted temperatures reproduce and 18 argmax checks pass. Parallel RF probabilities differ only by up to 2.22e-16, explicitly logged without changing classes. [Reproduction report](PHASE_4_REPRODUCTION.md).

# Remaining limitations

The v2 subset is label-enriched: High prevalence is 0.242% in Train, 0.645% in Validation, and 8.811% in Test. Precision and calibration are conditional on that composition. There are two training components, one validation component and only three held-out connected geographic components; component separation does not certify separate lakes or independent bloom episodes. References are processed/resampled CyAN DN classes, not in-situ cell counts, toxin measurements, or verified 20 m biological ground truth. Neural budgets remain only 3 epochs (SmallSegCNN) / 2 epochs (DeepLab), random initialization, one seed. These are controlled short-budget experiments, not converged architecture comparisons. Validation is one region; labels, acquisition timing and selection enrichment can confound apparent geographic transfer. We do not claim independent biological episodes, toxin prediction, calibrated natural-population risk, or model convergence.

# Final scientific claim

**LIMITED.** Sentinel-2 contains predictive information for the released CyAN-derived classes, but current models and selection procedures do not establish reliable three-class discrimination across unseen geography. [Final research answer](FINAL_RELIABILITY_ASSESSMENT.md).

# Recommendation for Phase 5

Expand independent training/validation/held-out geography and real High events, recover source geospatial metadata, validate against independent biological references, and predefine convergence/multiple-seed studies and a new external Test set. Keep v2 frozen as an already-inspected benchmark. Defer deployment and frontend work.

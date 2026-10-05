# Confidence reliability and validation-only temperature scaling

**Model confidence is not generally trustworthy under this geographic shift.** LR's pooled High predictions with confidence>=0.8 are correct only 60.96% of the time (27,846 predictions); in 6_2_X0650_Y0900 they are correct 46.55% of the time (449 predictions). The diagnostic CNN makes 510 such High predictions and none is correct. These are correlated pixel counts, not 510 independent failure events. RF makes no High predictions at that confidence: N/A precision is not zero or perfect calibration.

## Uncalibrated geographic Test

| Model | ECE | NLL | Brier | High ECE | High predictions ≥0.8 | Precision of those High predictions |
| --- | --- | --- | --- | --- | --- | --- |
| ablation_compact_hab | 0.1268 | 1.0055 | 0.5174 | 0.2046 | 47 | 0.0000 |
| ablation_rgb | 0.1428 | 1.2128 | 0.6111 | 0.2120 | 7 | 0.0000 |
| ablation_visible_rededge_nir | 0.0979 | 1.0414 | 0.5059 | 0.1845 | 462 | 0.0000 |
| baseline_DeepLabV3_ResNet18 | 0.1579 | 1.0018 | 0.5551 | 0.2038 | 761 | 0.0000 |
| baseline_LogisticRegression | 0.0787 | 0.6635 | 0.2945 | 0.0512 | 27846 | 0.6096 |
| baseline_RandomForest | 0.0442 | 1.0179 | 0.3591 | 0.0726 | 0 | N/A |
| baseline_SmallSegCNN | 0.2690 | 1.1760 | 0.7166 | 0.2725 | 0 | N/A |
| deep_focal | 0.2426 | 1.0223 | 0.6033 | 0.2372 | 1543 | 0.0000 |
| deep_weighted | 0.1131 | 1.1237 | 0.5536 | 0.2165 | 510 | 0.0000 |
| lr_balanced | 0.1242 | 1.6889 | 0.4071 | 0.0880 | 38254 | 0.5351 |
| lr_weighted | 0.1201 | 1.6927 | 0.4031 | 0.0869 | 35630 | 0.5435 |
| rf_balanced | 0.0314 | 1.9066 | 0.3865 | 0.0820 | 0 | N/A |
| rf_weighted | 0.0330 | 2.1838 | 0.3915 | 0.0839 | 0 | N/A |
| small_focal | 0.2673 | 1.1752 | 0.7162 | 0.2729 | 0 | N/A |
| small_weighted | 0.2758 | 1.1950 | 0.7284 | 0.2765 | 0 | N/A |

Top-label ECE uses 15 equal-width bins of maximum probability and correctness. High ECE uses P(High) against the one-v-rest binary label on all valid pixels. Multiclass Brier is the mean sum of 3 squared probability errors (range 0–2); High Brier is binary. Multiclass and binary High NLL use log probabilities clipped at 1e-12. Confidence quantiles, bin populations and all corresponding region-specific metrics are in [`calibration.json`](../phase4/calibration.json) and [`calibration_metrics.csv`](../phase4/calibration_metrics.csv). Every probabilistic model has an overall +3 region reliability figure, for both top-label and High. Five thresholded spectral indices have no learned probabilities; calibration is N/A.

Pooled ECE can conceal class failure: RF has lower top-label ECE than LR while missing nearly all High pixels. ECE binning, prevalence and pooling matter; ECE alone is not a reliability score. High one-v-rest metrics are also dominated numerically by non-High pixels, so inspect High-prediction precision and support alongside them.

## Neural temperature scaling

| Neural model | Validation-fitted T | ECE before | ECE after | NLL before | NLL after | Brier before | Brier after |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ablation_compact_hab | 0.7578 | 0.1268 | 0.0921 | 1.0055 | 1.0391 | 0.5174 | 0.5010 |
| ablation_rgb | 0.9337 | 0.1428 | 0.1301 | 1.2128 | 1.2301 | 0.6111 | 0.6082 |
| ablation_visible_rededge_nir | 0.8840 | 0.0979 | 0.0793 | 1.0414 | 1.0651 | 0.5059 | 0.4995 |
| baseline_DeepLabV3_ResNet18 | 0.5466 | 0.1579 | 0.0620 | 1.0018 | 1.0374 | 0.5551 | 0.5180 |
| baseline_SmallSegCNN | 20.0000 | 0.2690 | 0.2429 | 1.1760 | 1.1023 | 0.7166 | 0.6691 |
| deep_focal | 0.3022 | 0.2426 | 0.0850 | 1.0223 | 1.0368 | 0.6033 | 0.5306 |
| deep_weighted | 1.0638 | 0.1131 | 0.1231 | 1.1237 | 1.1124 | 0.5536 | 0.5572 |
| small_focal | 20.0000 | 0.2673 | 0.2409 | 1.1752 | 1.1022 | 0.7162 | 0.6691 |
| small_weighted | 20.0000 | 0.2758 | 0.2459 | 1.1950 | 1.1031 | 0.7284 | 0.6697 |

A positive scalar T minimizes validation NLL only, bounded [0.05,20]. Temperatures and their validation objectives were frozen before new Test evaluation. All 9 neural checkpoints including ablations were calibrated; all 18 validation/Test argmax comparisons remain exactly unchanged, hence accuracy and every confusion matrix are unchanged. SmallSegCNN variants reach the upper bound 20, reflecting near-uniformization of a poor classifier; the bound is disclosed rather than expanded after Test inspection.

For the diagnostic CNN, T=1.0638 lowers Test NLL1.1237→1.1124 but increases ECE0.1131→0.1231 and Brier0.5536→0.5572. Temperature scaling is not a guaranteed simultaneous improvement under shift. The original DeepLab lowers pooled ECE but worsens NLL; pooled changes can also differ by region. Calibration does not repair discrimination, geography or missing minority support.

[Temperature-scaling method: Guo et al.2017](https://proceedings.mlr.press/v70/guo17a.html). [`temperatures.json`](../phase4/temperatures.json); [diagnostic CNN reliability diagrams](../phase4/plots/calibration_deep_weighted.png); [LR reliability diagrams](../phase4/plots/calibration_baseline_LogisticRegression.png).

## Fair random-versus-geographic comparison

| Pilot model | Random ECE | Geographic ECE | Random NLL | Geographic NLL |
| --- | --- | --- | --- | --- |
| LogisticRegression | 0.0284 | 0.0465 | 0.1009 | 0.1661 |
| RandomForest | 0.0364 | 0.0296 | 0.0877 | 0.1408 |
| SmallSegCNN | 0.0447 | 0.2537 | 1.0500 | 0.9857 |
| DeepLabV3_ResNet18 | 0.1880 | 0.2934 | 0.3347 | 0.6296 |

Only these reloaded original models share the same 272-pair pilot pool and original protocol. Both pilot Test partitions have zero High support, so High sensitivity/calibration claims cannot be evaluated there (binary High false-positive scoring still exists). [`matched_pilot_calibration.json`](../phase4/matched_pilot_calibration.json) preserves exact pilot confusion reproduction. Do not compare pilot Random Test directly to v2 Geographic Test: data pool, training data and class support differ.

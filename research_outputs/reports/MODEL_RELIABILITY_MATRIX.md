# Model reliability matrix

The preregistered validation winner is `baseline_NDCI` (validation Macro F1 0.5751; validation High F1 0.0000). It fails to demonstrate High detection on Validation. `deep_weighted` is the highest-ranked CNN (validation Macro F1 0.3676; Low/Moderate/High F1 0.8507/0.1895/0.0625). **No CNN meets both preregistered Low>=0.50 and Moderate>=0.25 floors.** This CNN is a diagnostic fallback, not an eligible deployment choice. Ablations are excluded from winner selection by registration.

## Frozen v2, 288 pairs

| Model | Random Macro F1 | Geographic Macro F1 | High F1 | Worst-region High F1 | ECE | Worst robustness ΔMacro F1 |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_NDCI | N/A | 0.5185 | 0.0006 | 0.0000 | N/A | N/A |
| baseline_NDVI | N/A | 0.4141 | 0.0000 | 0.0000 | N/A | N/A |
| baseline_FAI | N/A | 0.3089 | 0.3425 | 0.1872 | N/A | N/A |
| baseline_B8AB4 | N/A | 0.3653 | 0.0025 | 0.0000 | N/A | N/A |
| baseline_B3B2 | N/A | 0.4212 | 0.0000 | 0.0000 | N/A | N/A |
| baseline_LogisticRegression | N/A | 0.6983 | 0.5803 | 0.4006 | 0.0787 | N/A |
| baseline_RandomForest | N/A | 0.4794 | 0.0012 | 0.0000 | 0.0442 | N/A |
| baseline_SmallSegCNN | N/A | 0.0632 | 0.1627 | 0.0468 | 0.2690 | N/A |
| baseline_DeepLabV3_ResNet18 | N/A | 0.3627 | 0.2700 | 0.0000 | 0.1579 | N/A |
| lr_weighted | N/A | 0.6214 | 0.4886 | 0.0048 | 0.1201 | N/A |
| lr_balanced | N/A | 0.6216 | 0.5003 | 0.0061 | 0.1242 | N/A |
| rf_weighted | N/A | 0.4840 | 0.0000 | 0.0000 | 0.0330 | N/A |
| rf_balanced | N/A | 0.4842 | 0.0000 | 0.0000 | 0.0314 | N/A |
| small_weighted | N/A | 0.0665 | 0.1589 | 0.0466 | 0.2758 | N/A |
| small_focal | N/A | 0.0642 | 0.1626 | 0.0466 | 0.2673 | N/A |
| deep_weighted | N/A | 0.4407 | 0.3522 | 0.1616 | 0.1131 | -0.0064 |
| deep_focal | N/A | 0.3583 | 0.2600 | 0.0000 | 0.2426 | N/A |
| ablation_rgb | N/A | 0.3896 | 0.2938 | 0.0355 | 0.1428 | N/A |
| ablation_visible_rededge_nir | N/A | 0.4706 | 0.3279 | 0.2297 | 0.0979 | N/A |
| ablation_compact_hab | N/A | 0.4095 | 0.2741 | 0.0985 | 0.1268 | N/A |

## Matched original pilot, 272 pairs

| Model | Random Macro F1 | Geographic Macro F1 | High F1 | Worst-region High F1 | ECE | Worst robustness ΔMacro F1 |
| --- | --- | --- | --- | --- | --- | --- |
| NDCI | 0.3762 | 0.4185 | N/A | N/A | N/A | N/A |
| NDVI | 0.3141 | 0.2599 | N/A | N/A | N/A | N/A |
| FAI | 0.3211 | 0.2781 | N/A | N/A | N/A | N/A |
| B8AB4 | 0.3207 | 0.2891 | N/A | N/A | N/A | N/A |
| B3B2 | 0.3302 | 0.4503 | N/A | N/A | N/A | N/A |
| LogisticRegression | 0.3279 | 0.3266 | N/A | N/A | 0.0465 | N/A |
| RandomForest | 0.5166 | 0.3768 | N/A | N/A | 0.0296 | N/A |
| SmallSegCNN | 0.1979 | 0.2676 | N/A | N/A | 0.2537 | N/A |
| DeepLabV3_ResNet18 | 0.3261 | 0.3222 | N/A | N/A | 0.2934 | N/A |

N/A means unmeasured or undefined, never zero. v2 models have no matched Random Test fit. The old pilot has no High Test pixels, so its High F1 is undefined. Fixed-three-class Macro F1 assigns zero contribution to an unsupported class; do not compare these two tables as a causal random/geographic split effect. ECE is uncalibrated top-label ECE; temperature variants are in CALIBRATION_ANALYSIS.md. Robustness was measured only for the registered diagnostic CNN; value is the worst of 12 fixed perturbations. Predictive ranking, calibration and reliability can disagree.

[`model_reliability_matrix.csv`](../phase4/model_reliability_matrix.csv)

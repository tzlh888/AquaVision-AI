# Regional failure analysis

There is no model-independent hardest region. For LR the lowest Macro F1 is 7_5_X1800_Y1700 (0.5906), but the lowest High F1 is 6_2_X0650_Y0900 (0.4006). For the diagnostic CNN the lowest Macro F1 is 6_2_X0500_Y1150 (0.2973), and its lowest High F1 is 6_2_X0650_Y0900 (0.1616). The validation-selected NDCI fails High in both 6_2 regions.

| Region | Valid pixels | True Low fraction | True Moderate fraction | True High fraction | High support |
| --- | --- | --- | --- | --- | --- |
| 6_2_X0500_Y1150 | 165722 | 0.5955 | 0.3662 | 0.0383 | 6345 |
| 6_2_X0650_Y0900 | 151986 | 0.9094 | 0.0671 | 0.0235 | 3573 |
| 7_5_X1800_Y1700 | 110951 | 0.5902 | 0.1588 | 0.2510 | 27850 |

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

## Answers across every model

“Most FN” counts erroneous pixels by true class, so each wrong prediction counts once. It is not an FP+FN double count. Low dominates absolute errors for LR/RF because Low is common; Moderate has a larger conditional error burden than Low in several models. See per-class recall for prevalence-independent interpretation.

| Model | Lowest-Macro region | Macro F1 | Most FN (absolute) | High→Moderate | High→Low | Predicted High fraction | Lowest-High region | High F1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_NDCI | 7_5_X1800_Y1700 | 0.4845 | High | 35318 | 2438 | 0.0034 | 6_2_X0500_Y1150 | 0.0000 |
| baseline_NDVI | 6_2_X0650_Y0900 | 0.3796 | Low | 35440 | 2328 | 0.0001 | 6_2_X0500_Y1150 | 0.0000 |
| baseline_FAI | 6_2_X0650_Y0900 | 0.1399 | Low | 10716 | 1481 | 0.2603 | 6_2_X0500_Y1150 | 0.1872 |
| baseline_B8AB4 | 6_2_X0500_Y1150 | 0.3151 | Moderate | 24772 | 12948 | 0.0029 | 6_2_X0500_Y1150 | 0.0000 |
| baseline_B3B2 | 6_2_X0650_Y0900 | 0.3384 | Moderate | 29984 | 7784 | 0.0002 | 6_2_X0500_Y1150 | 0.0000 |
| baseline_LogisticRegression | 7_5_X1800_Y1700 | 0.5906 | Low | 15114 | 1667 | 0.0806 | 6_2_X0650_Y0900 | 0.4006 |
| baseline_RandomForest | 6_2_X0650_Y0900 | 0.4321 | Low | 34649 | 3096 | 0.0001 | 6_2_X0500_Y1150 | 0.0000 |
| baseline_SmallSegCNN | 6_2_X0650_Y0900 | 0.0219 | Low | 430 | 0 | 0.9824 | 6_2_X0650_Y0900 | 0.0468 |
| baseline_DeepLabV3_ResNet18 | 6_2_X0500_Y1150 | 0.2174 | Moderate | 2355 | 22049 | 0.1428 | 6_2_X0500_Y1150 | 0.0000 |
| lr_weighted | 6_2_X0500_Y1150 | 0.4952 | Low | 16483 | 918 | 0.1064 | 6_2_X0500_Y1150 | 0.0048 |
| lr_balanced | 6_2_X0500_Y1150 | 0.4929 | Low | 15231 | 924 | 0.1135 | 6_2_X0500_Y1150 | 0.0061 |
| rf_weighted | 6_2_X0650_Y0900 | 0.4268 | Low | 34915 | 2853 | 0.0000 | 6_2_X0500_Y1150 | 0.0000 |
| rf_balanced | 6_2_X0650_Y0900 | 0.4199 | Low | 33482 | 4286 | 0.0000 | 6_2_X0500_Y1150 | 0.0000 |
| small_weighted | 6_2_X0650_Y0900 | 0.0180 | Low | 1630 | 0 | 0.9733 | 6_2_X0650_Y0900 | 0.0466 |
| small_focal | 6_2_X0650_Y0900 | 0.0259 | Low | 309 | 0 | 0.9868 | 6_2_X0650_Y0900 | 0.0466 |
| deep_weighted | 6_2_X0500_Y1150 | 0.2973 | Moderate | 13124 | 4890 | 0.1736 | 6_2_X0650_Y0900 | 0.1616 |
| deep_focal | 6_2_X0500_Y1150 | 0.2146 | Moderate | 2137 | 22591 | 0.1459 | 6_2_X0500_Y1150 | 0.0000 |
| ablation_rgb | 6_2_X0500_Y1150 | 0.2416 | Moderate | 7112 | 16806 | 0.1319 | 6_2_X0500_Y1150 | 0.0355 |
| ablation_visible_rededge_nir | 6_2_X0500_Y1150 | 0.3524 | Moderate | 18017 | 1174 | 0.1762 | 6_2_X0500_Y1150 | 0.2297 |
| ablation_compact_hab | 6_2_X0500_Y1150 | 0.2744 | Moderate | 9789 | 14903 | 0.1345 | 6_2_X0500_Y1150 | 0.0985 |

High is mainly confused with Moderate for the frozen LR/RF/NDCI: LR has 15,114 High→Moderate versus 1,667 High→Low; RF has 34,649 versus 3,096. Pooled RF predicts just 33 High pixels versus 37,768 true High pixels; each modified RF predicts one High pixel, and it is false. LR predicts 34,568 High pixels, below support, but still misses 16,781 High pixels while introducing 13,581 false High predictions. The diagnostic CNN predicts 74,414 High pixels: overprediction and substantial misses coexist. Underprediction is not universal—SmallSegCNN predicts High almost everywhere.

LR/RF pixel prediction agreement is 0.7798; wrong-pixel Jaccard is 0.3459, and High-miss Jaccard is 0.4446. Shared confusion with Moderate does not mean equal geographic behavior. All pairwise comparisons are in [`error_similarity.csv`](../phase4/error_similarity.csv).

[`regional_failure_metrics.csv`](../phase4/regional_failure_metrics.csv) contains TP/FP/FN, precision/recall/F1, class support, predicted counts, true/predicted proportions and Macro F1 for all 20 models × 3 regions × 3 classes. [`results.json`](../phase4/results.json) stores every confusion matrix. [All-model confusion figures](../phase4/plots/all_confusion_matrices.png).

The v2 subset is label-enriched: High prevalence is 0.242% in Train, 0.645% in Validation, and 8.811% in Test. Precision and calibration are conditional on that composition. There are two training components, one validation component and only three held-out connected geographic components; component separation does not certify separate lakes or independent bloom episodes. References are processed/resampled CyAN DN classes, not in-situ cell counts, toxin measurements, or verified 20 m biological ground truth. Neural budgets remain only 3 epochs (SmallSegCNN) / 2 epochs (DeepLab), random initialization, one seed. These are controlled short-budget experiments, not converged architecture comparisons.

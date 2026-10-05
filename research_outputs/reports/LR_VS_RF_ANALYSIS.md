# Why LR and RF differ on High

The discrepancy reproduces from the frozen checkpoints and identical 24,540 sampled training pixels: 18,260 Low, 6,224 Moderate, only 56 High (0.2282%). Both original models have class_weight=None. Both use the same 22 features (12 reflectance bands, five verified indices, five missing-index indicators). LR standardizes features using the training sample; RF uses raw feature scales, which is appropriate for tree splits. There is no evidence that a bad RF implementation explains the result.

| Model | Pool | High support | High recall | High F1 | Mean P(High) on true High |
| --- | --- | --- | --- | --- | --- |
| LogisticRegression | training_resubstitution | 56 | 0.0000 | 0.0000 | 0.1178 |
| LogisticRegression | geographic_test | 37768 | 0.5557 | 0.5803 | 0.5483 |
| RandomForest | training_resubstitution | 56 | 0.4107 | 0.5750 | 0.4801 |
| RandomForest | geographic_test | 37768 | 0.0006 | 0.0012 | 0.0566 |

A critical caution: LR recalls **none of the 56 sampled training High pixels**, yet recalls 55.57% of High Test pixels. RF recalls 41.07% on those training pixels but only 0.0609% on geographic Test. Training resubstitution is not validation. LR's better Test score therefore cannot be described as robustly learned High discrimination across pools: shifted feature/label composition can put more Test pixels on the High side of its fitted global decision surface. This is a plausible mechanism, not a causal identification or evidence of leakage; the frozen split/data hashes and exact shared training sample were checked.

## Probability and ranking evidence

True High Test pixels have mean P(High)=0.5483 under LR versus 0.0566 under RF; medians are 0.6739 versus 0.0324. RF's High ROC AUC=0.7978 and AP=0.2801 show nonzero ranking information even while the argmax almost never selects High. LR High AUC=0.9022 and AP=0.5233 are higher on this selected Test pool. No Test threshold was fitted. ROC/PR are one-v-rest and AP depends on the enriched prevalence.

[Probability histograms](../phase4/plots/lr_rf_high_probability_histograms.png), [per-class ROC/PR](../phase4/plots/lr_rf_roc_pr.png), [confusion matrices](../phase4/plots/all_confusion_matrices.png), [`lr_rf_probability_summary.csv`](../phase4/lr_rf_probability_summary.csv), [`lr_rf_roc_pr_metrics.csv`](../phase4/lr_rf_roc_pr_metrics.csv).

## Tree depth, leaves and minority representation

All 64 trees reach the fixed depth cap 12; min_samples_leaf=2, max_features=sqrt. Across 29,728 leaves, only 377 (1.27%) have High as the majority class. Per-tree bootstrap High counts range 41–77; the minority is present, not silently dropped. Leaf files record original High occupancy, in-bag unique sample counts, bootstrap-weighted counts and all three class fractions. Sparse minority leaves, depth-limited partitions, local support and averaging are consistent with RF's low High probabilities under shift, but this analysis does not isolate their individual causal contributions. Weighted/sampled RF still has zero High Test recall, so “class imbalance alone” is not an established explanation.

[`rf_tree_diagnostics.csv`](../phase4/rf_tree_diagnostics.csv); [`rf_leaf_composition.csv`](../phase4/rf_leaf_composition.csv).

## Feature interpretation

Largest absolute LR High-minus-Moderate standardized logit coefficients:

| Feature | Coefficient per training SD |
| --- | --- |
| B06 | 5.0368 |
| B03 | 4.0903 |
| B02 | -3.8674 |
| B11 | -2.8253 |
| B09 | -2.2411 |
| B07 | -1.4879 |

Largest RF impurity importances:

| Feature | Impurity importance |
| --- | --- |
| NDCI | 0.2092 |
| B05 | 0.1121 |
| FAI | 0.0893 |
| B03 | 0.0770 |
| B04 | 0.0676 |
| B01 | 0.0635 |

LR coefficients are in standardized feature units; High-minus-Moderate is a pairwise log-odds contrast, not a causal effect. Correlated bands/derived indices can redistribute coefficients. RF impurity importance has split-opportunity and correlation biases and is not on the same numerical scale as LR coefficients. Do not rank models by coefficient magnitude.

[High versus Moderate training distributions](../phase4/plots/high_moderate_feature_distributions.png); [feature effects](../phase4/plots/lr_rf_feature_effects.png); [`feature_importance_coefficients.csv`](../phase4/feature_importance_coefficients.csv); [`training_feature_distributions.csv`](../phase4/training_feature_distributions.csv); [`class_conditional_spectral_shift.csv`](../phase4/class_conditional_spectral_shift.csv).

The supported explanation is a combination of very sparse minority support, differing decision geometry and geographic/class-conditional distribution changes. The experiment does not prove one cause, and the LR Test advantage is not a validation-selected deployment result.

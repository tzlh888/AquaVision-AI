# Regional spectral distribution shift

| Region | Mean absolute 12-band SMD | LR High F1 | CNN High F1 |
| --- | --- | --- | --- |
| 6_2_X0500_Y1150 | 0.3487 | 0.5809 | 0.1788 |
| 6_2_X0650_Y0900 | 0.1665 | 0.4006 | 0.1616 |
| 7_5_X1800_Y1700 | 0.4101 | 0.5964 | 0.4546 |

**No: the region with the largest aggregate spectral shift does not have the worst High performance.** 7_5_X1800_Y1700 has the largest mean absolute band SMD (0.4101), yet LR and the diagnostic CNN have their highest regional High F1 there. 6_2_X0650_Y0900 has the smallest shift (0.1665), but their lowest High F1. The three-region Spearman rank association is +1 for these two models; with n=3 this is only a description, not evidence of a general positive relationship or a causal mechanism.

For all 12 bands and all five previously verified indices (NDCI, NDVI, FAI, B8AB4, B3B2), every finite valid-reference pixel contributes to mean, median, SD and 5/25/75/95 percentiles. Undefined indices are counted and excluded feature-wise. Reflectance is the author's DN/10000 transform. SMD=(region mean −Train mean)/Train SD; Wasserstein distance is also divided by Train SD. This training-SD convention is explicit, not a pooled-SD effect size. No distributional p-values or additional divergence searches are used. Train is the frozen two-component training pool.

Pooled spectral changes mix class prevalence and within-class changes. [`class_conditional_spectral_shift.csv`](../phase4/class_conditional_spectral_shift.csv) provides matching per-class comparisons; the train High class has only 647 pixels and these are spatially correlated. Low aggregate shift can hide localized/class-specific shift, and high pooled shift can reflect the intentional High enrichment. Geography, date and class prevalence are confounded here.

[`spectral_summaries.csv`](../phase4/spectral_summaries.csv); [`spectral_shift.csv`](../phase4/spectral_shift.csv); [`shift_association.json`](../phase4/shift_association.json); [shift heatmap](../phase4/plots/spectral_shift.png).

The v2 subset is label-enriched: High prevalence is 0.242% in Train, 0.645% in Validation, and 8.811% in Test. Precision and calibration are conditional on that composition. There are two training components, one validation component and only three held-out connected geographic components; component separation does not certify separate lakes or independent bloom episodes. References are processed/resampled CyAN DN classes, not in-situ cell counts, toxin measurements, or verified 20 m biological ground truth. Neural budgets remain only 3 epochs (SmallSegCNN) / 2 epochs (DeepLab), random initialization, one seed. These are controlled short-budget experiments, not converged architecture comparisons.

# Core figure index

Ten figures form the final portfolio set. Each has a high-resolution PNG and editable vector SVG. Older figures remain as historical artifacts, not additional core selections. No plots imply independent-pixel confidence intervals. Data-derived images are attributed to Hänsch and Schloer, Zenodo version14230064, CC BY4.0.

## 1. Research overview

[PNG](../figures/project_overview.png) · [SVG](../figures/project_overview.svg)

Paired observations feed segmentation; CyAN is a separate reference source, not a laboratory target. The matched pilot and v2 are distinct experiments, not comparable Test pools.

## 2. Geographic split

[PNG](../figures/final_geographic_split.png) · [SVG](../figures/final_geographic_split.svg)

Native CyAN author-grid positions. Gray parents are not selected into v2. Exact lake boundaries and cross-tile nonoverlap remain unverified.

## 3. Class distribution

[PNG](../figures/final_class_distribution.png) · [SVG](../figures/final_class_distribution.svg)

All valid pixels, not independent observations. Deliberate Test enrichment prevents natural-population precision or calibration claims.

## 4. Central model comparison

[PNG](../figures/final_model_comparison.png) · [SVG](../figures/final_model_comparison.svg)

Fixed model order, not ranked by Test. NDCI is selected despite zero validation High F1; the weighted CNN fails the class guard.

## 5. Per-region High F1

[PNG](../figures/final_regional_high_f1.png) · [SVG](../figures/final_regional_high_f1.svg)

Three observed component scores; no pixel bootstrap and no population confidence intervals.

## 6. Segmentation and attribution

[PNG](../figures/final_segmentation_attribution.png) · [SVG](../figures/final_segmentation_attribution.svg)

Phase4 maximum-High-support attribution case in the LR/CNN worst-High-F1 region: 6_2_X0650_Y0950_S050_2020_07_17_x320_y384_64x64_58. It was not selected for visual success. Target is fixed true-High-region mean High logit.

## 7. High-class calibration

[PNG](../figures/final_calibration.png) · [SVG](../figures/final_calibration.svg)

Fifteen equal-width bins; bottom panels show uncalibrated bin populations. Temperature uses Validation only and does not alter argmax. Pixel counts are correlated.

## 8. Robustness

[PNG](../figures/final_robustness.png) · [SVG](../figures/final_robustness.svg)

Twelve registered perturbations. Partial masking is artifact stress, not a cloud-physics model. Small deltas do not repair weak baseline performance.

## 9. Band ablation

[PNG](../figures/final_band_ablation.png) · [SVG](../figures/final_band_ablation.svg)

All12 exceeds RGB in this run, but the 8-band variant has higher Macro F1. Single-seed two-epoch results do not establish a stable spectral advantage.

## 10. Failure examples

[PNG](../figures/final_failure_examples.png) · [SVG](../figures/final_failure_examples.svg)

Three existing Phase4 extreme diagnostic cases in the worst High-F1 region. The whole patch need not belong to the named category.

The exact source list and chosen sample IDs are in [figure_manifest.json](../phase5/figure_manifest.json). Selection reuses Phase4 deterministic cases. Figures can be regenerated with `scripts/build_phase5_figures.py` when the required local arrays and prediction caches are available.

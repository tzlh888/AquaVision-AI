# Segmentation attribution and deterministic error examples

The single primary method is integrated gradients of the **mean High logit over a fixed valid true-High pixel region**. This scalar is obtained from the segmentation output directly; it is not an image-classification Grad-CAM target. Per region, choose the patch with maximum true-High pixel support, tie by ascending sample_id. Fix the target mask throughout the integration path. Baseline is normalized zero (training per-band means); integrate from it to the observed12-band patch using trapezoidal32 and 64 steps in eval mode. Report the 64-step attribution, both completeness checks and their L1 change.

| Region | Target High pixels | 32-step relative residual | 64-step relative residual | Attribution L1 change32→64 |
| --- | --- | --- | --- | --- |
| 6_2_X0500_Y1150 | 2441 | 0.0014 | 0.0175 | 0.0588 |
| 6_2_X0650_Y0900 | 1890 | 0.2328 | 0.0949 | 0.0610 |
| 7_5_X1800_Y1700 | 3271 | 0.0192 | 0.0249 | 0.1146 |

The 64-step completeness residual is 1.75%,9.49%,2.49% of the target-logit change, respectively. The 6_2_X0650 case is numerically less reliable (9.49%, improved from 23.28% at 32 steps); the 7_5 case also changes 11.46% in attribution L1 between resolutions. These are approximate exploratory maps, not fully converged quantitative band rankings. Small logit changes and cancellation make relative residuals sensitive; absolute residuals and target changes are saved.

The maps measure model-output sensitivity along a particular baseline-to-image path. Attribution can occur outside the target mask or on ignored context because the CNN uses a spatial receptive field. Absolute band attribution aggregates both positive and negative effects and is not directly a causal importance estimate. Correlated bands, standardized coordinates and an artificial mean-spectrum baseline influence the result; the interpolation path need not represent physically realizable water. B05 is prominent in two examples and B03 in the third, consistent with sensitivity to visible/red-edge inputs, but this does not prove cyanobacteria-specific reasoning or explain geographic failure causally. No claim of toxin or concentration reasoning is made.

[Integrated-gradients method: Sundararajan et al.2017](https://proceedings.mlr.press/v70/sundararajan17a.html). [`integrated_gradients.json`](../phase4/integrated_gradients.json) and per-region`ig_*.npz` retain signed per-band maps and target masks.

## Deterministic error panels

For each region and each of 7 categories—correct Low, correct Moderate, correct High, High→Moderate, High→Low, false High, and error at confidence>=0.8—select the patch with highest mean confidence over qualifying pixels, tie by sample_id. This intentionally selects extreme diagnostic examples and is not a representative sample of frequency. “Correct Low example” means qualifying Low pixels exist, not that its whole patch is correct. The same patch may appear in multiple categories. All valid-region pixels remain visible in the panels. RGB uses the fixed B04/B03/B02 stretch0–0.2 reflectance and gamma 1/2.2; display scaling does not enter model inference.

Missing categories: none; all 21 region/category combinations have qualifying pixels.

Each row displays RGB, reference classes, prediction, error and uncalibrated confidence, with qualifying count and confidence. [`error_examples.json`](../phase4/error_examples.json) records sample IDs, scores and categories, enabling exact reproduction.

- [6_2_X0500_Y1150 error panel](../phase4/plots/errors_6_2_X0500_Y1150.png); [IG panel](../phase4/plots/ig_6_2_X0500_Y1150.png)
- [6_2_X0650_Y0900 error panel](../phase4/plots/errors_6_2_X0650_Y0900.png); [IG panel](../phase4/plots/ig_6_2_X0650_Y0900.png)
- [7_5_X1800_Y1700 error panel](../phase4/plots/errors_7_5_X1800_Y1700.png); [IG panel](../phase4/plots/ig_7_5_X1800_Y1700.png)

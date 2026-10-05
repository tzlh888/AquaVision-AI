# Controlled multispectral robustness

The registered diagnostic CNN is `deep_weighted`; it failed the validation Moderate guard. Original Test Macro F1=0.4407; High F1=0.3522. All 12 severity settings were registered before Test evaluation.

| Transform | Severity | Macro F1 | ΔMacro F1 | High F1 | ΔHigh F1 | Values clipped fraction |
| --- | --- | --- | --- | --- | --- | --- |
| brightness | mild | 0.4396 | -0.0011 | 0.3445 | -0.0077 | 0.0003 |
| brightness | moderate | 0.4372 | -0.0035 | 0.3244 | -0.0278 | 0.0004 |
| contrast | mild | 0.4375 | -0.0032 | 0.3462 | -0.0059 | 0.0290 |
| contrast | moderate | 0.4343 | -0.0064 | 0.3363 | -0.0158 | 0.0596 |
| noise | mild | 0.4408 | 0.0001 | 0.3524 | 0.0003 | 0.0287 |
| noise | moderate | 0.4420 | 0.0013 | 0.3559 | 0.0037 | 0.0475 |
| blur | mild | 0.4474 | 0.0067 | 0.3660 | 0.0139 | 0.0002 |
| blur | moderate | 0.4456 | 0.0049 | 0.3573 | 0.0052 | 0.0002 |
| resolution | mild | 0.4462 | 0.0055 | 0.3615 | 0.0093 | 0.0002 |
| resolution | moderate | 0.4400 | -0.0007 | 0.3437 | -0.0084 | 0.0002 |
| mask | mild | 0.4364 | -0.0043 | 0.3403 | -0.0118 | 0.0002 |
| mask | moderate | 0.4357 | -0.0050 | 0.3461 | -0.0061 | 0.0002 |

Brightness/contrast use common gain1.05/1.15 across bands. Contrast is about each band's image mean. Noise is one shared spatial Gaussian field across bands (reflectance sigma0.002/0.005), deliberately a correlated perturbation rather than an asserted MSI sensor-noise model. Blur uses the same spatial Gaussian kernel per band, sigma0.5/1 pixel; resolution is 64→48/32→64 with antialiased bilinear interpolation. Center masks are14×14 and 25×25 pixels (4.79%/15.26% area), filled with training band means. This masking is **obstruction artifact stress**, not a physical cloud or radiative-transfer simulation. Labels and valid-pixel eligibility remain unchanged, including occluded reference pixels.

Transforms operate on all 12 reflectance bands before fixed Train normalization, with shared parameters and fixed per-sample seeds. Outputs clip to[0,1.5]; clipping is part of the intervention. Contrast-moderate clips5.96% of channel values and noise-moderate4.75%, so those results combine the nominal perturbation and nonnegativity clipping; they must not be called pure gain/noise effects. Even the mild settings are synthetic approximations. No band-independent RGB augmentation was used. Zero/ignored-context pixels can change and influence model context, while only valid reference pixels are scored.

Worst pooled Macro F1 decrease is −0.0064 (contrast-moderate); worst High F1 decrease is −0.0278 (brightness-moderate). Blur can improve the score in this short-budget model. A small perturbation delta does not demonstrate reliability when baseline three-class performance is weak; it can reflect persistent errors. Regional changes can cancel when pooled. [`robustness_by_region.csv`](../phase4/robustness_by_region.csv) exposes those differences.

[`robustness_metrics.csv`](../phase4/robustness_metrics.csv); [robustness figure](../phase4/plots/robustness.png). No confidence interval or real-cloud generalization claim is warranted.

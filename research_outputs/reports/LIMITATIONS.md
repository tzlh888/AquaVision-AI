# Limitations — current evidence and planned safeguards

- **Reference validity:** CyAN-derived references are satellite estimates, not laboratory or in-situ ground truth. The project can eventually measure agreement with this reference; it cannot validate cell counts or toxicity without independent measurements.
- **Encoding and thresholds:** Stored DN is not cells/mL. Resampling in encoded space and integer quantization complicate conversion and boundary sensitivity. The requested abundance thresholds have not been applied.
- **Task mismatch:** Source data labels pixels. A patch may contain several levels, below-detection values and masked pixels. An image-level aggregation rule is a scientific choice still to be specified.
- **Atmosphere and masks:** Atmospheric correction, cloud contamination, shadows and land/water ambiguity may create spurious predictors. Released masking code and manuscript descriptions conflict. Flag 255 combines causes, and three of eight inspection patches exceed 5% masked pixels.
- **Spatial resolution:** A nominal 300 m reference resampled onto a finer grid does not become independent high-resolution truth. Upsampled pixels are spatially dependent. Final reprojection transforms are missing from NPYs.
- **Temporal mismatch:** A filename date does not establish simultaneous acquisitions; intraday bloom change and daily product construction may affect alignment.
- **Geographic sampling bias:** The source selection is bloom-enriched and region-limited. The eight access-probe pairs are not representative. No geographic generalization can be estimated from them.
- **Class imbalance:** There are no DN 200-253 pixels in this probe; this says nothing about their whole-dataset frequency. Adequate class support across independent held-out groups is unverified.
- **Spatial autocorrelation and leakage:** Repeated parent groups, adjacent subtiles, overlapping satellite scenes and lakes crossing region boundaries can leak information across splits. Grid IDs alone cannot establish unseen water bodies.
- **Seasonal differences:** Month/year coverage and geography can be confounded. Split reports must quantify this rather than interpreting all performance change as purely geographic.
- **Duplicate uncertainty:** Exact hashes exclude duplicates only within eight input files. Raw-DN distances without registration cannot establish near-duplicate prevalence.
- **Calibration and interpretability:** No calibration, robustness or Grad-CAM analysis has been performed. Future temperature scaling must use validation data; Grad-CAM cannot establish causality.
- **General scope:** Cyanobacterial abundance is not toxin concentration. Satellite-derived bloom indicators do not constitute complete water-quality assessment or health advice. Report negative results and uncertainty, including reference uncertainty.

No empirical predictive conclusion has been drawn in Phase 1. The strongest justified statement is that a small, traceable real sample can be selectively accessed, decoded and inspected, and that material label/geographic issues have been identified before modeling.

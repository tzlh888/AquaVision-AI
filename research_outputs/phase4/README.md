# Phase 4 reliability evidence

Start with [Phase 4 status](../reports/PHASE_4_STATUS.md), [final assessment](../reports/FINAL_RELIABILITY_ASSESSMENT.md), and [reliability matrix](../reports/MODEL_RELIABILITY_MATRIX.md).

Final claim: **LIMITED** evidence for reliable three-class geographic generalization. The validation-selected model is the frozen NDCI baseline, which fails High detection. No CNN passes the registered Low/Moderate guard. `deep_weighted` is the prespecified diagnostic fallback. The original LR's stronger Test result does not override validation selection.

- `results.json`: 20 model IDs, validation and pooled/three-region Test confusion matrices.
- `experiment_metrics.csv`, `regional_failure_metrics.csv`: class metrics and failure counts.
- `selection.json`, `test_evaluation_start.json`: sealed validation selection and evaluation ordering.
- `specifications.json`, `models/`: new experiment definitions and checkpoints; original checkpoints remain under Phase 3.5.
- `*_validation.npz`, `*_test.npz`, `prediction_order.json`: ordered reference/class maps and probabilities or logits.
- `calibration.json`, `temperatures.json`: raw/calibrated metrics and validation-only temperatures.
- `robustness_metrics.csv`, `robustness_by_region.csv`: fixed synthetic severity results.
- `spectral_summaries.csv`, `spectral_shift.csv`, `temporal_distributions.csv`: distribution evidence.
- `rf_*`, `lr_rf_*`, `train_test_minority_diagnostics.json`: LR/RF mechanism diagnostics.
- `error_examples.json`, `integrated_gradients.json`, `plots/`: deterministic examples and exploratory attribution.
- `leave_one_region_out.csv`: group-level sensitivity, not population confidence intervals.
- `pytest_results.xml`, `reproduction_check.json`, `preservation_check.json`: verification.
- `IMPLEMENTATION_NOTES.md`: disclosed RF floating-point summation tolerance correction.
- `delivery_manifest.json`: final SHA-256 inventory (excluding itself).

The training runner refuses to overwrite sealed results. See [reproduction instructions](../reports/PHASE_4_REPRODUCTION.md). Three selected regions and spatially correlated, resampled reference pixels do not justify precise independent-sample uncertainty claims.

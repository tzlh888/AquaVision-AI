# AquaVision Legacy Benchmark Registry

Every model-bearing evaluation below has been viewed, reported, or used in a decision. All are legacy as of 2026-10-12.

| Registry ID | Population / artifact | Historical exposure | Current status |
| --- | --- | --- | --- |
| AV-LB-01 | Phase 3 bounded-pilot random split | Baseline model validation/test metrics inspected; test has zero High support | Legacy exploratory benchmark; unsuitable for High-risk claims |
| AV-LB-02 | Phase 3 bounded-pilot geographic split | Baseline model validation/test metrics inspected; test has zero High support | Legacy geographic pilot; unsuitable for High-risk claims |
| AV-LB-03 | Phase 3.5 v2 train split: 96 patches, 2 connected groups | All training outcomes and class support known | Potential development data only; not evaluation evidence |
| AV-LB-04 | Phase 3.5/4 v2 validation: 48 patches, 1 connected group, 931 High pixels | Used for model selection, eligibility, calibration/temperature, checkpoint behavior and reporting | Legacy development benchmark; no independent claim |
| AV-LB-05 | Phase 3.5/4 v2 geographic test: 144 patches, 3 connected groups, 37,768 High pixels | All baseline and Phase 4 variant results viewed | Legacy test benchmark; prohibited for future selection |
| AV-LB-06 | Phase 4 per-region and leave-one-region-out test summaries | Regional failure and uncertainty analyses viewed | Legacy robustness evidence; only three test components |
| AV-LB-07 | Phase 4 calibration analyses on validation/test | Temperatures fitted on validation; all test calibration outcomes viewed | Legacy calibration evidence |
| AV-LB-08 | Phase 4 robustness suite | Brightness, contrast, noise, blur, resampling and masking outcomes viewed | Legacy diagnostic evidence; cannot motivate test-driven tuning |
| AV-LB-09 | Phase 4 band ablations | All12/RGB/visible-red-edge-NIR/compact-HAB results viewed | Legacy diagnostic evidence; cannot select a future band set |
| AV-LB-10 | Phase 4 attribution and deterministic failure examples | Integrated-gradient and failure outputs viewed | Exploratory diagnostic evidence, not causal or independent |
| AV-LB-11 | Phase 5 final tables/figures and complete local reload | Central claims and 100 confusion matrices reproduced | Historical reproduction evidence; no training performed |

## Governance rule

No AV-LB result may trigger a candidate, architecture, loss, threshold, calibration, epoch count, sampling policy, band set, or stopping-rule change. A future run may compare against a legacy entry only after all choices are frozen from eligible development data. Reusing validation/test content for training retires it permanently as evaluation evidence.

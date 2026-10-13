# AquaVision Research Protocol Freeze — Phase 2A

**Freeze date:** 2026-10-12  
**Upgrade branch:** `research-upgrade-v3`  
**Frozen baseline HEAD:** `bd11eceaa7efa7ca785d5e466cf807312ed70df0`  
**Scope:** registry and protocol freeze only; no model training, tuning, selection, result regeneration, commit, or push.

## 1. Frozen research state

AquaVision predicts three CyAN-derived reference classes from Sentinel-2 inputs. The labels are a satellite-derived proxy, not direct laboratory ground truth and not a validated physical cells/mL measurement. The current public conclusion remains **LIMITED**: useful signal is present, but reliable three-class generalisation to unseen geographic regions is not established.

The Phase 3.5 v2 split contains 288 image/reference pairs: 96 train patches in two connected geographic groups, 48 validation patches in one group, and 144 test patches in three groups. Pixel support is 647/931/37,768 High pixels in train/validation/test respectively. Pixel counts, patches, subtiles, dates, and connected components are distinct dependence units and must never be interchanged.

The original configs, run contracts, split-support table, results, selection record, and final audit are frozen by SHA-256 in `EVIDENCE_MANIFEST.csv`. Historical model outputs are not changed.

## 2. Data eligibility

| Evidence/data | Status after freeze | Permitted future use |
| --- | --- | --- |
| Phase 3.5 train split: 96 patches, two connected groups | Only eligible development population under the frozen v2 design, conditional on restoring/checking all underlying arrays and hashes | Training and training-internal resampling only |
| Phase 3.5/4 validation split: 48 patches, one connected group | Repeatedly inspected and used for model selection, thresholds, calibration, and eligibility | Legacy development evidence; never independent confirmation |
| Phase 3.5/4 geographic test split: 144 patches, three connected groups | Fully evaluated across baselines, variants, regions, robustness, calibration and ablations | Legacy benchmark only; prohibited for new selection |
| Phase 3 pilot random/geographic tests | Outcomes viewed; both have zero High test support | Historical exploratory evidence only |
| Saved prediction/model/calibration caches | Derived historical evidence; large local artifacts are not in the public checkout | Reproduction when verified, not new evidence |
| Future external lake/scene/event data | Not acquired or sealed | Only possible future confirmatory evidence after provenance and preregistration |

If train/validation/test rows are recombined for later development, every reused row loses evaluation status. A replacement confirmation set must be acquired and sealed before such reuse.

## 3. Independence and selection rules

- All existing outcomes are in `LEGACY_BENCHMARK_REGISTRY.md`; none can select a future model, loss, band set, threshold, calibration method, epoch, or robustness condition.
- Geographic connected components are the strongest preserved grouping unit. They do not prove independence by lake, Sentinel scene, footprint, or bloom event because those identifiers/transforms are missing.
- Multiple pixels from one patch and patches from one component are correlated support, not independent replicates. Pixel bootstrap is prohibited for population uncertainty.
- The validation-selected historical winner remains NDCI under the registered rule. Logistic Regression's stronger test High F1 is a post-hoc observation and cannot replace the winner.
- No CNN passed the registered validation Low/Moderate guard; the weighted DeepLab model remains diagnostic.

## 4. Provenance and reproducibility boundary

The saved Phase 4 selection SHA-256 is `22e009dd0814085fbeefac9639e85222e9c14f12f6fb9518471d0e91c1d8d7ee`; `test_evaluation_start.json` records that selection before test evaluation. The Phase 5 audit reports 123 passing tests, 100 exact confusion-matrix reconstructions, 40 exact cached prediction checks, 96 calibration-group checks, 18 temperature/argmax checks, and 288 verified input-pair hashes without training.

The current checkout intentionally omits raw imagery, checkpoints, and large caches. Therefore a fresh public clone cannot repeat inference or training; it can inspect configs, split metadata, source, metrics, reports, and hashes. The earlier complete local verification is historical evidence and is not silently rerun or overstated here.

## 5. Evidence gaps

1. Physical lake identity, Sentinel scene identity, exact footprint overlap, and bloom-event identity remain unknown.
2. Validation High support comes from one connected group and only 931 pixels; test High support is regionally concentrated.
3. The training split has only 647 High pixels and two connected groups, insufficient for strong population claims.
4. Labels remain a processed CyAN proxy without direct field-ground-truth validation.
5. Publicly absent raw arrays/checkpoints prevent fresh end-to-end reproduction in this checkout.
6. No untouched confirmatory dataset exists.

## 6. Change control

Future experiments require a dated decision-log entry before execution, a verified eligible-data manifest, group-isolated validation, fixed hypotheses/search spaces/qualification rules, and a new output directory. Legacy test metrics may be displayed only after configurations are frozen. Failed models and negative outcomes must remain available. No evidence may be described as external or independent beyond its verified grouping unit.

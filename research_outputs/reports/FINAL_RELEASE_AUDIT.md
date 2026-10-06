# AquaVision AI — Final Release Audit

**Audit date:** 6 October 2026
**Release conclusion:** **PASS**, with the scientific outcome retained as **LIMITED**.

This audit verifies the final research package without fitting, tuning, or selecting another model. The complete local audit reloaded the saved data, model checkpoints, prediction caches, and machine-readable metrics. A second metadata-only pass checks the public documents after packaging. The evidence is recorded in [`final_audit.json`](../phase5/final_audit.json), [`metadata_audit.json`](../phase5/metadata_audit.json), and the pytest XML report at [`pytest_results.xml`](../phase5/pytest_results.xml).

## 1. Scientific freeze and repository scope

- The frozen v2 split SHA-256 is `e96abb63318fdd3a57c87ee4bc9078a476c288156e32d1baf3d126533d884df2`.
- All **443** files covered by the Phase5 preservation manifest were present and accounted for during the complete audit. Of these, 436 retain their original recorded SHA-256 values. Seven text files match the explicit [public-release path-sanitization amendment](../../data/metadata/phase5/public_release_sanitization.json): machine-specific paths were replaced by repository-relative wording without changing source hashes, splits, models, predictions, metrics, or scientific conclusions.
- Historical reports were not rewritten. Their scope and relationship to the final report are documented in [`ARCHIVE_INDEX.md`](ARCHIVE_INDEX.md).
- The earlier root README is preserved as `data/metadata/phase5/README_before_phase5.md`; only the public-facing root README and new Phase5 packaging assets were intentionally written.
- No model was trained, tuned, or selected during Phase5. The geographic split and validation-selection protocol were not changed.
- Work was confined to the AquaVision-AI repository. The sibling WaterSense-AI repository was outside the audit and was not modified.

## 2. Test and numerical reproduction results

The final test run completed with **123 passed, 0 failed, 0 errors, and 0 skipped**. The complete read-only reload then verified:

| Check | Verified result |
| --- | ---: |
| Confusion-matrix metric reconstructions | 100 exact |
| Saved validation/Test class-prediction caches | 40 exact |
| Calibration group/mode reconstructions | 96 exact |
| Neural temperature/argmax invariance checks | 18 exact |
| Input pairs with recorded hashes | 288 verified |
| Random-Forest probability maximum round-off | `2.220446049250313e-16` |
| Training performed by the audit | No |

The Random-Forest probability difference is machine-precision floating-point round-off and falls below the audit tolerance of `1e-12`; predicted classes and every derived confusion matrix reproduce exactly. Regional matrices sum to their pooled Test matrices, registration order matches the recorded protocol, and the six-row final results table agrees with the frozen outputs.

## 3. Model-selection integrity

Reapplying the registered validation rule selects **NDCI**. Its validation Macro F1 is `0.5751`, while its validation High F1 is `0`. No CNN satisfies the registered Low/Moderate class guard. The weighted DeepLab variant therefore remains diagnostic rather than selected.

Logistic Regression has geographic-Test High F1 `0.5803`, but validation High F1 `0`. This is a post-hoc Test observation. Replacing the validation-selected model because of that Test value would use the Test set for selection and introduce selection bias. The README, canonical report, portfolio summary, results table, and figures all preserve this distinction.

## 4. Claim provenance and consistency

The public README has **49 claim-source records**. Each recorded snippet was found in the README, every linked machine-readable source exists, and every claim with a JSON locator matched its verified value. The canonical report contains all 19 requested numbered sections; its abstract is 188 words. The portfolio summary is 765 words, the application description is 197 words, and the CV one-line version is 29 words.

A repository-wide case-insensitive scan covered text, source code, configuration, metadata, cached source snapshots, reports, tables, logs, and SVG figures. It searched for wording concerning ground-truth status, pollution detection, accurate or reliable geographic generalization, physical cells-per-mL conversion, “best model,” and state-of-the-art claims. All 97 matched terms across 84 source lines were manually reviewed. Every matched location is recorded with file, line, term, bounded surrounding context, source-line hash, scope, and disposition in [`claim_occurrences.json`](../phase5/claim_occurrences.json).

The review found no unsupported positive claim in the current public materials. Current occurrences state limitations, pose the research question, or explain why a stronger claim is not supported. Other occurrences are in preserved historical reports, tests and refusal checks, saved provenance, or externally authored source snapshots. In particular:

- CyAN is consistently described in current materials as a **satellite-derived reference**, not direct laboratory ground truth.
- Physical cells/mL conversion is documented only as an earlier rejected framing or an unsupported interpretation; it is not the training target.
- No current material claims successful or reliable three-class geographic generalization.
- Source snapshots retain their authors' terminology but are explicitly excluded from AquaVision outcome claims.
- Earlier test counts, readiness states, and pilot findings remain in historical reports and are explicitly scoped in the archive index rather than silently edited.

## 5. Figures, tables, and publication package

The release includes ten core figures, each in 240-dpi PNG and editable SVG form. Their inputs, captions, and fixed example identifiers are recorded in [`figure_manifest.json`](../phase5/figure_manifest.json). The overview, geographic split, class distribution, model comparison, regional High F1, segmentation/attribution, calibration, robustness, band ablation, and deterministic failure examples were visually inspected after generation. They use frozen metrics and arrays only; figure generation performs no model inference or fitting.

The concise final table is available as [`final_results.csv`](../tables/final_results.csv) and [`final_results.md`](../tables/final_results.md). It uses a validation-neutral model order and labels NDCI as validation-selected, Logistic Regression as a non-selected comparator, and the weighted CNN as a diagnostic model that failed the guard.

## 6. Reproducibility boundary

The complete local environment reproduces the saved predictions, metrics, calibration summaries, split, and test suite. The public metadata audit can be run with:

```bash
python scripts/audit_final_release.py --metadata-only
```

The complete reload requires the locally retained raw arrays, model checkpoints, and prediction caches:

```bash
python scripts/audit_final_release.py --full
```

Those large regenerable artifacts are intentionally ignored by Git. A fresh public clone can inspect the reports, tables, figures, split metadata, claim provenance, and code, but cannot reproduce checkpoint inference without obtaining the original data and local artifacts described in the README. This audit records local scientific verification; publication history and hosting status are separate from that evidence.

## 7. Final assessment

The release package is internally consistent and suitable for technical review. Its central conclusion remains: Sentinel-2 contains useful predictive signal for CyAN-derived risk segmentation, but the experiments do not establish reliable three-class generalization to unseen geographic regions. High-risk behavior is region-dependent, the validation-selected NDCI model has zero validation High F1, and no CNN passed the predefined selection criterion. These negative results are retained as part of the research contribution.

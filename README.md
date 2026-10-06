# AquaVision AI

AquaVision AI is a research-oriented computer-vision project investigating whether Sentinel-2 multispectral imagery can identify cyanobacterial bloom risk and how reliably models generalize to geographically unseen regions.

**Final conclusion: LIMITED.** Predictive signal exists in the released CyAN-derived classes, but reliable three-class geographic generalization has not been demonstrated. The modeling phase is complete; this repository preserves the negative results and the evaluation decisions that produced them.

[Research report](research_outputs/reports/RESEARCH_RESULTS.md) · [Project summary](research_outputs/reports/PORTFOLIO_SUMMARY.md) · [Final results](research_outputs/tables/final_results.md) · [Core figures](research_outputs/reports/FIGURE_INDEX.md)

![AquaVision research overview](research_outputs/figures/project_overview.png)

## Research Question

**Can Sentinel-2 multispectral imagery identify cyanobacterial bloom risk, and how reliably do these predictions generalize to geographically unseen regions?**

“Risk” refers to the source-defined Low, Moderate, and High CyAN reference classes. It is not a direct measurement of toxin concentration or an operational health warning.

## Why This Matters

Nearby remote-sensing observations can share spatial and temporal structure. Random patch splitting may therefore overestimate performance at new locations. Geographic holdouts, class-specific metrics, and confidence analysis ask whether a useful prediction remains dependable when the location changes. The study's value includes identifying where that evidence is insufficient.

## Dataset

The source is [Zenodo version 14230064](https://doi.org/10.5281/zenodo.14230064), associated with [Schloer and Hänsch's study](https://doi.org/10.1109/JSTARS.2025.3629586). Input is a **12 × 64 × 64** Sentinel-2 patch; the target is a **64 × 64** processed CyAN mask. Channels are B01, B02, B03, B04, B05, B06, B07, B08, B8A, B09, B11, and B12.

Stored DN values 0–99, 100–199, and 200–253 map to Low, Moderate, and High. Flags 254/255 and invalid values use ignore index **−100**. CyAN provides satellite-derived reference labels, **not laboratory ground truth**. Cells/mL conversion is disabled and is not the training target. Coarse source-reference resampling limits the meaning and independence of fine-grid labels.

The final benchmark uses **288 real pairs**: **96 Train / 48 Validation / 144 Test**. Its **three geographic Test components** contain **37,768 High pixels**. Test is deliberately High-enriched, so precision and calibration do not estimate natural-population performance. [Support counts](research_outputs/phase3_5/split_support.csv).

## Methodology

Primary-source verification corrected the initial image-classification and concentration-conversion framing to pixel-level segmentation. Experiments use training-only preprocessing, explicit ignored pixels, fixed split membership, saved pixel identities, and versioned configurations. Controlled variants change weighting, sampling, loss, or available bands separately. [Scientific reframing](research_outputs/reports/RESEARCH_RESULTS.md#4-scientific-reframing).

## Models

- Spectral baselines: NDCI, NDVI, FAI, B8AB4, and B3B2 with training-fitted thresholds.
- Logistic Regression and Random Forest using the same sampled pixels and spectral features.
- SmallSegCNN and DeepLabV3/ResNet18 with twelve input channels and random initialization.
- Controlled imbalance variants and a small registered band-ablation set.

CNN training remains bounded to three SmallSegCNN epochs or two DeepLab epochs. Comparisons describe this protocol, not fully converged architecture rankings. All evaluated families and unsuccessful variants remain documented.

## Geographic Validation

Touching or diagonally adjacent source-grid parent windows form connected components. All dates within a component remain in one partition. This controls known within-tile adjacency; exact lake identities and cross-tile overlap remain unverified.

An initial **272-pair** matched random/geographic pilot had **no High test support** in either split. The corrected v2 benchmark is a separate pool and must not be compared with pilot Random Test as though only the split changed.

The Phase 4 rule ranked validation Macro F1, then High F1, subject to Low F1 ≥ 0.50 and Moderate F1 ≥ 0.25. It was registered before new variants were tested. Earlier baseline Test results were already known; the entire study was not blind. [Study protocol](research_outputs/reports/MODEL_SELECTION_PROTOCOL.md).

## Key Results

| Model | Validation Macro F1 | Validation High F1 | Test Macro F1 | Test High F1 | Status |
| --- | --- | --- | --- | --- | --- |
| NDCI | 0.5751 | 0.0000 | 0.5185 | 0.0006 | Validation-selected; High failure |
| Logistic Regression | 0.5437 | 0.0000 | 0.6983 | 0.5803 | Comparator; not selected |
| Random Forest | 0.4400 | 0.0000 | 0.4794 | 0.0012 | Comparator; not selected |
| SmallSegCNN | 0.0175 | 0.0123 | 0.0632 | 0.1627 | Comparator; not selected |
| DeepLabV3 / ResNet18 | 0.3343 | 0.0701 | 0.3627 | 0.2700 | Comparator; not selected |
| DeepLab + weighted CE | 0.3676 | 0.0625 | 0.4407 | 0.3522 | Diagnostic CNN; failed guard |

**NDCI was selected by the validation rule, despite validation High F1 = 0. No CNN passed the predefined class guard.** Weighted DeepLab is a diagnostic fallback. **LR's Test High F1 = 0.5803 is a descriptive observation, not permission to select it retrospectively.** Changing the rule after observing Test would introduce selection bias.

![Regional High performance](research_outputs/figures/final_regional_high_f1.png)

LR's regional High F1 spans **0.4006–0.5964**; the diagnostic CNN spans **0.1616–0.4546**. Only three selected test components are available, so regional ranges and leave-one-region-out sensitivity are reported without a population confidence interval. [Exact central CSV](research_outputs/tables/final_results.csv) · [All-model reliability matrix](research_outputs/reports/MODEL_RELIABILITY_MATRIX.md).

## Reliability Analysis

The project includes regional failures, class-imbalance controls, spectral and temporal shift analysis, confidence calibration, validation-only temperature scaling, multispectral perturbations, band ablation, and segmentation-targeted integrated gradients.

For the diagnostic CNN, **510 High predictions with confidence ≥ 0.8 were all false**. Temperature scaling preserved classifications but did not improve every calibration metric. All-band versus RGB results suggest useful spectral information in one short run, without establishing a stable advantage. Attribution is exploratory sensitivity and does not establish causal reasoning.

The [core figure index](research_outputs/reports/FIGURE_INDEX.md) contains ten selected PNG/SVG figures, including deterministic failure cases. Complete evidence remains in the [canonical report](research_outputs/reports/RESEARCH_RESULTS.md).

## Limitations

Satellite-derived references, coarse label resolution, severe imbalance, spatial autocorrelation, three test components, one validation component, possible within-day sensor mismatch, atmospheric/context effects, and short single-seed training constrain interpretation. Exact biological concentration and toxin measurements were not validated. These limits prevent deployment claims and leave three-class geographic performance unresolved.

## What I Learned

The project changed most when I verified what the dataset actually represented: that evidence shifted the task from image classification and concentration conversion to spatial segmentation. Geographic grouping and class-support checks mattered as much as model implementation, and the validation rule had to remain fixed even when a different model looked better on Test. The negative result clarified the difference between predictive signal and dependable behavior under distribution shift.

## Reproducibility

The repository retains the experiment configurations, exact split membership, analysis code, saved metrics, tables, and figures needed to inspect the study. Tests cover label mapping, data loading, geographic separation, leakage prevention, evaluation metrics, and the registered selection rule. Raw arrays and model checkpoints are not bundled into the lightweight public checkout, so full inference reproduction requires the original dataset artifacts.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-training.txt
.venv/bin/python -m pytest -q
```

<details>
<summary>Technical verification records</summary>

The final local audit passes **123 tests** and reproduces **100 confusion matrices** and **40 class-prediction caches** exactly. RF probability summation differs only at floating-point roundoff under its unchanged parallel setting; class predictions remain identical. Historical scientific outputs and the frozen split remain unchanged. See the [release audit](research_outputs/reports/FINAL_RELEASE_AUDIT.md), [preservation manifest](data/metadata/phase5/preservation_manifest.json), and [claim provenance](research_outputs/phase5/readme_claim_sources.json).

The earlier support-screening stage decoded **38,002 reference masks**; this screening volume is distinct from the 288-pair model benchmark.

The metadata-only check works with the public files:

```bash
.venv/bin/python scripts/audit_final_release.py --metadata-only
```

With the original local arrays, checkpoints, and caches available, the complete reload check is:

```bash
.venv/bin/python scripts/audit_final_release.py --full
```

The audit reads existing scientific artifacts and does not train or select models. Historical experiment runners can rewrite their original output directories, so they should be used only in a separate reproduction workspace. [Detailed reproduction scope](research_outputs/reports/FINAL_RELEASE_AUDIT.md).

</details>

## Repository Structure

```text
configs/                         Experiment settings
src/aquavision/                  Data, features, segmentation, reliability primitives
scripts/                        Data preparation, experiments, analysis, and release tools
tests/                          Data, split, evaluation, and selection checks
data/metadata/                  Provenance and fixed split membership
research_outputs/reports/       Canonical report, application materials, archive index
research_outputs/tables/        Final results and historical machine-readable tables
research_outputs/figures/       Ten selected core figures plus historical figures
research_outputs/phase4/        Final reliability-analysis evidence
research_outputs/phase5/        Technical release records
```

The historical folders record four stages in natural terms: dataset interpretation, a pilot study, class-support correction, and final reliability analysis. Their original directory names remain unchanged because reports and provenance records refer to them. The [archive index](research_outputs/reports/ARCHIVE_INDEX.md) explains which documents describe earlier or superseded states.

## Research Reports

| Material | Purpose |
| --- | --- |
| [Research Results](research_outputs/reports/RESEARCH_RESULTS.md) | Canonical final report |
| [Portfolio Summary](research_outputs/reports/PORTFOLIO_SUMMARY.md) | Self-contained admissions/technical-review summary |
| [CV Description](research_outputs/reports/CV_DESCRIPTION.md) | One line and two concise bullets |
| [Application Description](research_outputs/reports/APPLICATION_DESCRIPTION.md) | Reflective application-ready project account |
| [Final Results](research_outputs/tables/final_results.md) | Selected comparisons and metric definitions |
| [Figure Index](research_outputs/reports/FIGURE_INDEX.md) | Ten selected figures and their scientific captions |

Technical records are collected in the [archive index](research_outputs/reports/ARCHIVE_INDEX.md), [release audit](research_outputs/reports/FINAL_RELEASE_AUDIT.md), and [release status](research_outputs/reports/PHASE_5_STATUS.md).

## Repository Note

This repository was published after the main experimentation and documentation work had been completed, so the public Git history primarily reflects release preparation rather than the full development timeline.

## License

Original AquaVision code is [MIT licensed](LICENSE). The source dataset is CC BY 4.0; derived figures retain the required dataset attribution. The [pinned author repository](https://github.com/cschloer/hab_detection_s2/tree/e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37) is Apache 2.0. Publications and third-party dependencies retain their own licenses. This repository is a reimplementation and reliability investigation, not a claim to have reproduced the publication's full training experiment.

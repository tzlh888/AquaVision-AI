# AquaVision AI — Project Summary

## Problem

Can Sentinel-2 imagery identify cyanobacterial bloom risk, and how reliably do predictions transfer to geographically unseen regions? AquaVision investigates both predictive ability and reliability under distribution shift. Its final conclusion is **LIMITED**: the imagery contains useful signal for the released reference classes, but the experiments do not demonstrate stable three-class geographic generalization. The project is a research study, not a deployed environmental-warning application.

## Data

Inputs are twelve-band Sentinel-2 patches, each shaped 12 × 64 × 64. Paired 64 × 64 masks contain processed, satellite-derived CyAN digital numbers. The source-defined classes are Low (0–99), Moderate (100–199), and High (200–253); flags and invalid pixels are ignored. These references are not direct laboratory measurements, cell-count targets, or toxin measurements. Coarse CyAN data were resampled by the source pipeline, so fine output pixels do not represent independent biological observations.

The final frozen benchmark contains 288 real pairs: 96 training, 48 validation, and 144 geographic-test patches. Test spans three connected geographic components and includes 37,768 High pixels. A preceding audit decoded 38,002 reference masks, including complete coverage of the original 24,518-pair index. Screening volume and training volume are kept distinct. The benchmark deliberately enriches High support, making its precision and calibration conditional on the selected composition.

## Methods

I initially approached the task as image-level classification with physical concentration thresholds. Primary-source verification changed that design. The paper, author code, and stored arrays supported pixel-level semantic segmentation using discrete CyAN-derived classes; exact cells/mL conversion was not defensible for the processed references. I preserved spatial targets and disabled unsupported conversion rather than forcing the original framing.

Experiments compare five spectral-index baselines, standardized Logistic Regression, Random Forest, SmallSegCNN, and DeepLabV3/ResNet18. Controlled extensions test class weighting, balanced sampling, weighted cross-entropy, focal loss, and selected band subsets. Training-only preprocessing, saved pixel identities, fixed seeds, and versioned artifacts make the comparisons inspectable. Neural training remains deliberately short, so the study does not rank fully converged architectures.

## Geographic Validation

Random patch splitting can place spatially related observations on both sides of an evaluation boundary. AquaVision groups touching source-grid parent regions across all dates before assigning geographic partitions. This controls the verified adjacency structure, while acknowledging incomplete lake and footprint metadata.

The initial matched 272-pair random/geographic pilot contained no High pixels in either test partition. That prevented a three-class conclusion and prompted the support audit and frozen v2 benchmark. The two data pools are never treated as a clean random-versus-geographic comparison. Phase 4 selection rules were registered before new variants were tested; earlier baseline test results were already known.

## Main Findings

The rule prioritized validation Macro F1, then High F1, with minimum Low and Moderate performance. It selected NDCI, whose validation High F1 was zero despite available High references. No CNN satisfied both predefined class requirements. The strongest validation-ranked CNN was therefore used only as a diagnostic fallback.

Logistic Regression achieved geographic-test Macro F1 of 0.6983 and High F1 of 0.5803, with regional High F1 ranging from 0.4006 to 0.5964. Those test observations do not justify replacing the validation-selected model. Choosing after seeing Test would introduce selection bias. RF missed nearly all High pixels, and class weighting or balanced sampling did not restore true-High detection.

## Reliability Analysis

The analysis examines region-specific confusion, spectral and temporal composition, calibration, controlled multispectral perturbations, band ablation, and segmentation-targeted integrated gradients. LR predictions labeled High with confidence at least 0.8 were correct only 60.96% of the time overall. The diagnostic CNN made 510 such predictions with no true positives. Validation-only temperature scaling preserved classifications but improved some confidence metrics while worsening others.

All twelve bands exceeded RGB in one controlled CNN run, but the subset ordering and short training budget did not establish a reliable spectral advantage. Deterministic examples preserve High-to-Moderate, High-to-Low, and false-High failures. Attribution is exploratory sensitivity, not evidence of causal reasoning.

## Limitations

Only three test components and one validation component are available. High prevalence differs sharply across partitions. Pixels are spatially correlated, source references are uncertain and coarse, same-day pairing does not guarantee simultaneous acquisition, and geographic, seasonal, and class-composition changes are confounded. One seed and bounded training limit model comparisons. Geographic ranges and leave-one-region-out sensitivity are reported without misleading pixel-bootstrap confidence intervals.

## Takeaway

The project demonstrates how dataset interpretation, class support, and evaluation design can change a research conclusion. Negative results remain visible, including the selected model's High failure. The contribution is an auditable investigation of the gap between predictive performance and dependable behavior at new locations, supported by reproducible code, explicit protocols, and preserved historical evidence.

[Canonical report](RESEARCH_RESULTS.md) · [Final results](../tables/final_results.md) · [Release audit](FINAL_RELEASE_AUDIT.md)

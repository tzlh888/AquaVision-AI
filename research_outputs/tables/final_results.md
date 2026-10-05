# Final core results

| Model | Validation Macro F1 | Validation High F1 | Geographic Macro F1 | Geographic High F1 | ECE | Robustness delta Macro F1 | Selection Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NDCI | 0.5751 | 0.0000 | 0.5185 | 0.0006 | N/A | N/A | Validation-selected; High failure |
| Logistic Regression | 0.5437 | 0.0000 | 0.6983 | 0.5803 | 0.0787 | N/A | Comparator; not selected |
| Random Forest | 0.4400 | 0.0000 | 0.4794 | 0.0012 | 0.0442 | N/A | Comparator; not selected |
| SmallSegCNN | 0.0175 | 0.0123 | 0.0632 | 0.1627 | 0.2690 | N/A | Comparator; not selected |
| DeepLabV3 / ResNet18 | 0.3343 | 0.0701 | 0.3627 | 0.2700 | 0.1579 | N/A | Comparator; not selected |
| DeepLab + weighted CE | 0.3676 | 0.0625 | 0.4407 | 0.3522 | 0.1131 | -0.0064 | Diagnostic CNN; failed guard |

Values come from frozen Phase 4 results, calibration and robustness outputs. N/A (blank CSV field) means unavailable or unmeasured, never zero. ECE is uncalibrated top-label ECE with 15 bins. Robustness is the worst delta in Macro F1 over 12 registered perturbations, measured only for the diagnostic weighted CNN. Table order is fixed and is not a Test-based ranking. NDCI is the validation-selected model, despite zero validation High F1. No CNN passed the class guard. LR is a comparator, not a post-hoc selection. Full experiment IDs remain in the CSV.

Sources: [results](../phase4/results.json), [selection](../phase4/selection.json), [calibration](../phase4/calibration.json), [robustness](../phase4/robustness_metrics.csv).

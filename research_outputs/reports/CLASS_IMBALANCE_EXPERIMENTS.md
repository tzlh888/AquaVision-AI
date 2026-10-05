# Controlled class-imbalance experiments

Eight new imbalance experiment IDs were registered. Four original learned baselines remain unchanged. Weighted fits and sampling fits are separate; focal has gamma=2 without class weights. CNN architecture, epochs, seed, augmentation, optimizer and checkpoint rule are unchanged. The source of class counts differs appropriately: classical weights use the exact sampled training labels; CNN weights use all valid training-mask labels.

| Experiment | Validation Macro F1 | Test Macro F1 | High P | High R | High F1 | Moderate F1 | Low F1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_LogisticRegression | 0.5437 | 0.6983 | 0.6071 | 0.5557 | 0.5803 | 0.6029 | 0.9118 |
| baseline_RandomForest | 0.4400 | 0.4794 | 0.6970 | 0.0006 | 0.0012 | 0.5641 | 0.8729 |
| baseline_SmallSegCNN | 0.0175 | 0.0632 | 0.0887 | 0.9886 | 0.1627 | 0.0201 | 0.0069 |
| baseline_DeepLabV3_ResNet18 | 0.3343 | 0.3627 | 0.2183 | 0.3538 | 0.2700 | 0.0286 | 0.7897 |
| lr_weighted | 0.4154 | 0.6214 | 0.4467 | 0.5393 | 0.4886 | 0.5055 | 0.8702 |
| lr_balanced | 0.4219 | 0.6216 | 0.4444 | 0.5723 | 0.5003 | 0.4962 | 0.8683 |
| rf_weighted | 0.3804 | 0.4840 | 0.0000 | 0.0000 | 0.0000 | 0.5819 | 0.8702 |
| rf_balanced | 0.3854 | 0.4842 | 0.0000 | 0.0000 | 0.0000 | 0.5815 | 0.8710 |
| small_weighted | 0.0194 | 0.0665 | 0.0866 | 0.9568 | 0.1589 | 0.0407 | 0.0000 |
| small_focal | 0.0166 | 0.0642 | 0.0886 | 0.9918 | 0.1626 | 0.0171 | 0.0130 |
| deep_weighted | 0.3676 | 0.4407 | 0.2655 | 0.5230 | 0.3522 | 0.1908 | 0.7791 |
| deep_focal | 0.3330 | 0.3583 | 0.2085 | 0.3453 | 0.2600 | 0.0245 | 0.7905 |

Classical sampled counts: [18260, 6224, 56]. Inverse-frequency weights: [0.447973713033954, 1.31426735218509, 146.07142857142858]. Balanced draws: [8180, 8180, 8180]; effective unique counts: [8180, 4576, 56]. All 8,180 High draws repeat only 56 unique sampled pixels. Rebalancing does not create geographic or biological diversity. CNN counts are [205627,61588,647], with weights N/(3*n_c).

Weighted/balanced LR sacrifices some overall and High F1 relative to the original LR on Test. Neither weighted nor balanced RF detects a true High pixel. Weighted DeepLab improves Test Macro F1 from 0.3627 to 0.4407 and High F1 from 0.2700 to 0.3522, but validation Moderate F1 remains 0.1895, below the fixed 0.25 guard. Focal loss does not establish a useful improvement in this budget. SmallSegCNN remains collapsed. A high High recall alone is not useful.

Within-run checkpoint selection remains minimum unweighted validation CE, so changing loss is the only neural intervention. Across-run choice is by validation Macro F1 with the registered guard. All ablations preserve the chosen parent's weighted loss. No architecture/loss combination was added based on Test.

[`experiment_metrics.csv`](../phase4/experiment_metrics.csv) includes full validation and Test metrics. Model training JSON files record completed epochs, selected epochs, class weights and warnings. This is one seed and a short budget; differences are descriptive, with no significance claim.

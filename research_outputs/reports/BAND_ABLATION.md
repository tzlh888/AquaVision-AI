# Registered band ablation

| Band set | Validation Macro F1 | Test Macro F1 | Test High F1 | ΔTest Macro vs All 12 | Worst-region High F1 |
| --- | --- | --- | --- | --- | --- |
| All 12 | 0.3676 | 0.4407 | 0.3522 | 0.0000 | 0.1616 |
| RGB | 0.3707 | 0.3896 | 0.2938 | -0.0512 | 0.0355 |
| Visible + red-edge/NIR | 0.3737 | 0.4706 | 0.3279 | 0.0299 | 0.2297 |
| Compact HAB ingredients | 0.3789 | 0.4095 | 0.2741 | -0.0312 | 0.0985 |

All 12 versus RGB improves Test Macro F1 by 0.0512 and High F1 by 0.0584 in this one fixed run. The 8-band visible/red-edge/NIR variant has higher Macro F1 than All 12 but lower High F1. The compact4-band variant does not establish parity. These descriptive differences suggest spectral information beyond RGB can help in this protocol; they do not prove a stable multispectral advantage or an optimal band set. Validation ordering differs, all runs are short and single-seed, and no ablation replaces the previously locked winner.

| Set | Verified array bands |
| --- | --- |
| All 12 | B01,B02,B03,B04,B05,B06,B07,B08,B8A,B09,B11,B12 |
| RGB | B02,B03,B04 (display order B04/B03/B02) |
| Visible + red-edge/NIR | B02,B03,B04,B05,B06,B07,B08,B8A |
| Compact HAB ingredients | B04,B05,B8A,B11 |

The compact set supplies the previously verified NDCI red/red-edge ingredients and FAI red/narrow-NIR/SWIR ingredients. It is literature-informed, not a claim that this exact subset is a published optimum. Band mapping was checked against the pinned author data pipeline and [Copernicus MSI band documentation](https://sentiwiki.copernicus.eu/web/s2-mission). Prior project equations are from [Schloer and Hänsch,2025](https://doi.org/10.1109/JSTARS.2025.3629586). Nominal wavelengths used for FAI are approximations, not spacecraft-specific response integration.

All runs use DeepLabV3/ResNet18, weighted CE, same seed 42, batch 8, Adam and 2 epochs, no pretrained weights, same split and train-only normalization. They retain the 12-channel architecture and mask inactive normalized channels to 0 during training, validation and inference: this is train-mean imputation, not literal zero reflectance. Consequently the experiment controls architecture/parameter count while changing available information; it does not measure parameter efficiency of a native3-channel CNN. The All 12 result reuses the parent checkpoint without retraining.

[`experiment_metrics.csv`](../phase4/experiment_metrics.csv); [`specifications.json`](../phase4/specifications.json); validation epoch histories under`../phase4/models/ablation_*_training.json`. No exhaustive band search or Test-based subset tuning occurred.

# Phase 3 initial results — bounded pilot

**Verified segmentation pipeline and real pilot completed; full three-class geographic-generalization milestone remains incomplete.** No final model or publication-grade score is claimed.

## Scientific reframing

The project now asks: Can a multispectral computer-vision model identify pixel-level cyanobacterial bloom risk from Sentinel-2 imagery, and how reliably does it generalize to geographically unseen regions? The original Phase 2 required physical conversion, an image-level class and reconstructed coordinates; those requirements were unnecessarily restrictive for the published segmentation task. They are superseded, with historical findings preserved.

The [original pipeline reconstruction](ORIGINAL_PIPELINE_RECONSTRUCTION.md) records every correction with paper/code evidence. Primary references are [Schloer and Hänsch, DOI 10.1109/JSTARS.2025.3629586](https://doi.org/10.1109/JSTARS.2025.3629586), [pinned author code](https://github.com/cschloer/hab_detection_s2/tree/e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37), and [dataset version](https://zenodo.org/records/14230064).

## Verified label definition

Input X has 12×64×64 bands; output Y has 64×64 pixel labels. DN 0–99 maps to Low=0, 100–199 to Moderate=1, 200–253 to High=2. Ignore index is **-100** for 254, 255 and invalid numerical data. No mean, median, maximum or majority image target enters training. Cells/mL conversion stays disabled as optional scientific interpretation.

These are processed CyAN remote-sensing reference categories. They are not laboratory-measured cell concentrations, in-situ truth, toxin concentrations or independent 20 m field measurements. Training target code is not released; intervals are verified in the paper and the mask semantics in preprocessing/documentation.

## Verified spatial identifiers

The filename parent `{CyAN tile}_X{column}_Y{row}_S050` preserves a fixed author-selected spatial window; date and patch crop offsets also survive. Same-tile touching/diagonal parent cells are recursively connected. This defines verified author-grid regions without guessing coordinates. Scene UUIDs, physical footprints and waterbody IDs remain unavailable. “Unseen region” is the supported scope; “guaranteed unseen lake” is not.

## Split methodology

See [frozen protocol](PHASE_3_PROTOCOL.md). Membership and configuration were persisted before pilot labels were downloaded. Both model comparisons use the same 272-patch pool. Random sizes are 217/27/28; geographic sizes are 224/16/32 for train/validation/test. The geographic partition contains two training components and one component each for validation and test. Full-index CSV exports and pilot CSV exports are stored separately under `data/metadata/phase3/`.

Faithful author algorithm reproduction on these four components with seed 42 puts all 24,518 samples into train. This measured degeneracy is retained. Our three-way shuffle/reservation rule is an explicit extension, not an undisclosed reseeding or an assertion that we recovered the original paper's test set. Input means/stds and sampled pixels come from training only; checkpoint selection uses validation only.

## Leakage audit

| Pool / split | Shared subtile | Shared CyAN tile | Shared component | Repeated grid-position candidate | Same-date adjacent patch |
|---|---:|---:|---:|---:|---:|
| index / random | 2452/2452 | 2452/2452 | 2452/2452 | 2449/2452 | 2440/2452 |
| index / geographic | 0/3945 | 3945/3945 | 0/3945 | 0/3945 | 0/3945 |
| pilot / random | 28/28 | 28/28 | 28/28 | 5/28 | 2/28 |
| pilot / geographic | 0/32 | 32/32 | 0/32 | 0/32 | 0/32 |

See [detailed leakage report](RANDOM_SPLIT_LEAKAGE_AUDIT.md). The random full-index test has 100% same-subtile exposure to training. Geographic same-subtile/component exposure is zero. Scene and true footprint overlap are UNKNOWN; larger CyAN tiles still overlap. No exact pilot input hashes cross train/test.

## Dataset statistics

The indexed pool contains 24,518 pairs, 17 parents, four connected selected regions and 106 dates. It is not the downloaded training corpus. The pilot has 272 real pairs, 922,399 valid pixels and 191,713 ignored pixels. Exact full-pool pixel counts and Sentinel scene count remain UNKNOWN. Arrays are CRC/SHA-verified; no synthetic observations are used for training.

| Split | Patches | Valid pixels | Low | Moderate | High |
|---|---:|---:|---:|---:|---:|
| random / train | 217 | 734,682 | 678,778 | 54,968 | 936 |
| random / validation | 27 | 93,425 | 87,501 | 5,924 | 0 |
| random / test | 28 | 94,292 | 91,879 | 2,413 | 0 |
| geographic / train | 224 | 771,926 | 723,755 | 47,243 | 928 |
| geographic / validation | 16 | 37,638 | 27,907 | 9,723 | 8 |
| geographic / test | 32 | 112,835 | 106,496 | 6,339 | 0 |

## Class imbalance

Pilot valid pixels are 93.0354% Low, 6.8631% Moderate and 0.1015% High. High appears in training but **neither test set has High support**. Per-class recall/F1 for unsupported High is recorded as null. Pixel counts over interpolated fields must not be treated as independent sampling units.

Initial models are unweighted. Optional weighted cross entropy and focal loss are implemented and tested but not used in reported runs. Class-balanced sampling is discussed as a separate later experiment; the initial uniform bounded sampling is preserved. The author's per-DN frequency weighting is distinct from those alternatives. No test balancing or class-frequency fitting on held-out labels occurs.

## Spectral baselines

All five paper formulas were implemented: NDCI, NDVI, FAI, B8A/B4 normalized difference and B3/B2 normalized difference. FAI uses explicitly documented nominal band wavelengths. Training-only quantile-grid threshold fitting replaces the author's larger Bayesian search for this bounded pilot. Undefined ratios have explicit imputation/coverage handling. Validation/test confusion matrices and thresholds are saved in the results JSON.

## Classical ML baselines

Logistic regression and a 64-tree random forest use 12 spectral bands, five source-supported indices and five undefined-index indicators. Uniform valid-pixel sampling is capped at 256 per training patch and 32,768 total. Every sampled pixel ID is saved, and geographic test pixels cannot enter training. Scaling is fitted on training only. Models are saved locally as joblib artifacts.

- geographic: sampled training pixels Low/Moderate/High = [30820, 1917, 31].
- random: sampled training pixels Low/Moderate/High = [30052, 2668, 48].

## Small CNN results

SmallSegCNN explicitly exposes convolutions, ReLU, pooling, bilinear upsampling and three-channel pixel logits. Masked cross entropy, backward propagation and optimizer steps operate on spatial masks. Joint flips preserve image/target alignment. It is randomly initialized and intentionally small; three epochs establish an executable baseline, not a converged model.

## Deep segmentation results

DeepLabV3 with ResNet18 follows the author's available constructor: 12 input channels, three classes, **no pretrained weights**. The network has 15,927,683 parameters. Two CPU epochs provide an initial training/evaluation check. No RGB substitution, ImageNet download or architecture sweep was performed.

- geographic / SmallSegCNN: 3 epochs, 1.60 seconds, validation-selected checkpoint.
- geographic / DeepLabV3_ResNet18: 2 epochs, 7.11 seconds, validation-selected checkpoint.
- random / SmallSegCNN: 3 epochs, 1.35 seconds, validation-selected checkpoint.
- random / DeepLabV3_ResNet18: 2 epochs, 7.11 seconds, validation-selected checkpoint.

## Random vs Geographic generalization

| Model | Random macro F1* | Geographic macro F1* | Δ random−geo | Geo Low F1 | Geo Moderate F1 | Geo High F1 |
|---|---:|---:|---:|---:|---:|---:|
| NDCI | 0.3762 | 0.4185 | -0.0423 | 0.8995 | 0.3560 | N/A |
| NDVI | 0.3141 | 0.2599 | 0.0542 | 0.7718 | 0.0078 | N/A |
| FAI | 0.3211 | 0.2781 | 0.0430 | 0.8302 | 0.0041 | N/A |
| B8AB4 | 0.3207 | 0.2891 | 0.0316 | 0.8628 | 0.0046 | N/A |
| B3B2 | 0.3302 | 0.4503 | -0.1201 | 0.8773 | 0.4736 | N/A |
| LogisticRegression | 0.3279 | 0.3266 | 0.0013 | 0.9700 | 0.0097 | N/A |
| RandomForest | 0.5166 | 0.3768 | 0.1398 | 0.9733 | 0.1571 | N/A |
| SmallSegCNN | 0.1979 | 0.2676 | -0.0697 | 0.8029 | 0.0000 | N/A |
| DeepLabV3_ResNet18 | 0.3261 | 0.3222 | 0.0039 | 0.9462 | 0.0203 | N/A |

*Fixed three-class macro F1, undefined divisions scored zero. **Neither test set contains High reference pixels.** High recall/F1 is N/A, not measured zero. These scalars are pipeline diagnostics; they cannot establish three-class geographic generalization. Supported-class macro F1 and raw confusion matrices are in results JSON.

The same model definitions and declared optimizer settings are used across splits. Δ is random minus geographic macro F1. Test class mixtures, regions and training counts differ; the single-seed pilot cannot attribute the difference solely to leakage. Some geographic scores may exceed random scores. Low scores and reversals are retained. Deep learning superiority is not established by short training or unsupported High evaluation.

Machine-readable [central table](../tables/random_vs_geographic_pilot.csv), [per-class precision/recall/F1](../tables/phase3_per_class_metrics.csv), and [full metrics/confusion matrices](../phase3_pilot/results.json) contain the actual outputs. All confusion matrices use rows=true, columns=predicted.

## Limitations

- Four selected components in two author training archives are too few for broad independent-region claims. The original 183-parent/full-corpus partition is not reproduced.
- No High test pixels; high-risk performance cannot be estimated. Geographic validation has only eight High pixels. No reseeding is used to conceal this.
- A 272-patch, equally capped-per-subtile pilot is not representative of the full 24,518 pairs or the paper's 938,607 pairs. Full reference class counts remain unknown.
- Two or three epochs, one seed, different test prevalence and no confidence intervals preclude final generalization conclusions. Train/test pixel counts are not effective independent sample sizes.
- Code/paper no-data filtering and mask discrepancies remain. Bilinear interpolation transfers coarse remote-sensing labels, not new field observations.
- Nominal FAI wavelengths and pre-2022 /10000 scaling follow documented source conventions; spacecraft-specific calibration cannot be reconstructed.
- Exact coordinate, scene and lake overlap remain unverified. Region split correctness is a narrower guarantee.

## Tests

**94 tests passed**, including all 70 prior tests. Coverage includes all 256 byte labels, requested boundaries, ignored/invalid values, source-grid identity and transitive adjacency, deterministic author/three-way algorithms, ratio diagnostics, frozen-file protection, spectral formulas, missing denominators, absent-class metrics, full-coverage training batches, training-only normalization, small-CNN gradient masking, and 12-band DeepLab output shape. Software tests use synthetic fixtures; the separate pilot trains only on real deposited arrays.

Dependency consistency, compilation, original-sample hashes, new-pair hashes and frozen-plan integrity are checked. JUnit results are saved in `phase3_pytest_results.xml`. Reloading all saved models/thresholds reproduced **all 18 test confusion matrices exactly**, recorded in [the reproduction check](phase3_reproduction_check.json). Code hashes, plan hash, deterministic CPU settings and selection policy are in `research_outputs/phase3_pilot/run_contract.json`; artifact hashes cover saved results/checkpoints. `requirements-phase3.txt` records the original installed environment; `requirements-training.txt` provides the portable pinned install list.

## Remaining blockers

The mapping and author-grid region grouping gates are resolved for segmentation. Remaining blockers concern the final evaluation: independent-region diversity, High-class held-out support, missing full reference census, convergence and repeated-seed uncertainty. Cells/mL conversion and image-level aggregation are **not** reinstated as training requirements.

The conservative Phase 3 exception was used: build and verify the complete pipeline, then run a bounded pilot. The full ten-item milestone is not declared scientifically complete because the three-class comparison lacks High test support and adequate geographic replication.

Resource scope is also explicit: the pilot stores 27,922,432 raw bytes; the full indexed pool would store about 2.344 GiB before derived artifacts. The successful download attempt charged 46,808,601 range bytes, including rate-limit retry reservations; an earlier interrupted attempt and package downloads add traffic that is not included in that number. Current allocated repository storage is about 1.22 GiB, including roughly 1.01 GiB of runtime dependencies and 136 MiB of pilot outputs/checkpoints. The complete pool has about 90 times the pilot training patches. A simple linear extrapolation of the measured short DeepLab run suggests roughly ten minutes for just two epochs per full-pool split, exceeding this run's declared four-minute per-model pilot budget; this is a planning estimate, not a full-data benchmark. Convergence training is deferred until evaluation support is established. See [validation and storage record](phase3_validation.json).

## Recommended next experiment

**EXPAND SUBSET in independent regions**, as detailed in [subset decision](TRAINING_SUBSET_DECISION.md). First index remaining archives and audit bounded reference batches across additional components. Freeze a new experiment version with adequate held-out class support and multiple independent regions; preserve this pilot unchanged. Do not simply increase to 50,000 patches or substitute favorable groups after seeing scores. Once evaluation support is adequate, run the same model family with a justified convergence budget, then a single-factor unweighted-versus-training-weighted loss experiment. Grad-CAM, robustness, calibration and frontend work remain deferred.

Reproduction (from repository root):

```bash
.venv/bin/python -m pip install -r requirements-training.txt
.venv/bin/python scripts/prepare_phase3_pilot.py --download
.venv/bin/python scripts/audit_phase3.py
.venv/bin/python -m pytest -q --junitxml=research_outputs/reports/phase3_pytest_results.xml
.venv/bin/python scripts/run_phase3_pilot.py
.venv/bin/python scripts/verify_phase3.py
.venv/bin/python scripts/report_phase3.py
```

Frozen files reject changed membership/configuration. Source URL access may require retry; exact reported floating-point values are tied to the recorded package/platform environment. Existing model artifacts should be preserved before intentionally rerunning training.

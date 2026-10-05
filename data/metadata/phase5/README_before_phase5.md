# AquaVision-AI

**Multispectral semantic segmentation of cyanobacterial bloom risk from Sentinel-2 imagery, with emphasis on geographic generalization.**

Research question: Can a multispectral computer-vision model identify pixel-level cyanobacterial bloom risk from Sentinel-2 imagery, and how reliably does it generalize to geographically unseen regions?

**Current stage: verified segmentation pipeline and bounded Phase 3 pilot completed. A definitive three-class geographic-generalization result is not yet supported.** Work is confined to AquaVision-AI.

## What is verified

Input is twelve Sentinel-2 bands, `X=[12,64,64]`. The target is a spatial map, `Y=[64,64]`: stored CyAN DN 0–99 → Low (0), 100–199 → Moderate (1), 200–253 → High (2). Land/no-data flags 254/255 and invalid values use ignore index **-100**. No image-level label is constructed. Cells/mL conversion remains disabled as optional interpretation; it is not required for training.

These are published classes of a processed satellite reference, not in-situ laboratory cell counts or toxin measurements. Bilinear interpolation of the original coarse reference does not create independent 20 m ground truth.

The author filename's CyAN tile and parent X/Y/S identify fixed selected subregions. Touching/diagonally adjacent selected parents remain in one connected component. Coordinates are not required for this source-defined region holdout, although lake, scene and cross-tile overlap remain unverified.

The [pipeline reconstruction](research_outputs/reports/ORIGINAL_PIPELINE_RECONSTRUCTION.md) separates paper/code evidence and preserves discrepancies. [Phase 2 status](research_outputs/reports/PHASE_2_STATUS.md) retains the earlier audit and adds the explicit Scientific Reframing correction.

## Real pilot, not full-corpus results

- Cached metadata: **24,518 pairs**, 17 parent subtiles, four selected connected regions, 106 dates. Only two author training archives are indexed.
- Label-blind pilot: **272 real pairs**, selected before seeing their labels and used for both random and geographic comparisons.
- Valid pilot pixels: **922,399** — 858,158 Low, 63,305 Moderate and 936 High. Full-pool pixel counts remain unknown.
- Implemented and run: five spectral-index threshold baselines, pixel-level logistic regression, random forest, SmallSegCNN and DeepLabV3/ResNet18 with all 12 channels and random initialization.
- **Neither fixed test set has High reference pixels.** High recall/F1 is not estimable. Short neural training is a pipeline check, not a converged final model.
- **94 tests pass**, including all 70 prior tests. Reloading saved artifacts reproduces all 18 model/split test confusion matrices.

Read [Phase 3 initial results](research_outputs/reports/PHASE_3_INITIAL_RESULTS.md), [random split leakage audit](research_outputs/reports/RANDOM_SPLIT_LEAKAGE_AUDIT.md), [subset decision](research_outputs/reports/TRAINING_SUBSET_DECISION.md), and [frozen experiment protocol](research_outputs/reports/PHASE_3_PROTOCOL.md). [Central comparison CSV](research_outputs/tables/random_vs_geographic_pilot.csv) and [complete metrics](research_outputs/phase3_pilot/results.json) preserve poor scores and unsupported classes.

## Reproduce

Tested locally with Python 3.12.14 on macOS arm64, deterministic CPU execution. Use the existing `.venv`, or create one and install the portable pinned training requirements from the repository root:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-training.txt
.venv/bin/python scripts/prepare_phase3_pilot.py --download
.venv/bin/python scripts/audit_phase3.py
.venv/bin/python -m pytest -q --junitxml=research_outputs/reports/phase3_pytest_results.xml
.venv/bin/python scripts/run_phase3_pilot.py
.venv/bin/python scripts/verify_phase3.py
.venv/bin/python scripts/report_phase3.py
```

The preparation step requires the cached Phase 1 pair inventories and source catalog. On a fresh checkout, use `scripts/prepare_data.py` to reconstruct them; `scripts/fetch_sources.py` restores primary-source snapshots. Phase 1's original eight samples remain a separate audit set and can be retrieved with `scripts/prepare_data.py --download-sample`.

The immutable plan fixes selection, split membership and hyperparameters before label acquisition. No full ZIP fallback exists. Each archive attempt is bounded to 48 MiB; HTTP 429 responses trigger backoff. Existing cached members are checked against ZIP CRC before reuse. Training reads frozen membership and checks SHA-256. The recorded run contract includes source hashes and the original runtime snapshot; exact replay is tied to this environment. Preserve prior checkpoints/results before intentional training reruns. The environment snapshot `requirements-phase3.txt` includes its original local editable path; `requirements-training.txt` is the portable install list.

Training-only statistics normalize inputs; all sampled pixel identities are saved. Validation alone selects neural checkpoints. Test labels never tune thresholds, preprocessing, sampling or hyperparameters. Classical pixel sampling is bounded to 32,768 pixels; image datasets load patches lazily. No GPU or pretrained weights are required.

## Repository outputs

| Location | Purpose |
|---|---|
| `src/aquavision/data/labels.py` | Verified spatial target and historical descriptive diagnostics |
| `src/aquavision/data/geographic_split.py` | Author algorithm reproduction and region-based experiment splits |
| `src/aquavision/data/splits.py` | Preserved stricter waterbody/image-class infrastructure; not used by segmentation pilot |
| `src/aquavision/features/spectral.py` | Paper-supported spectral formulas |
| `src/aquavision/models/segmentation.py` | Small CNN, 12-band DeepLab, ignored/weighted/focal loss options |
| `data/metadata/phase3/` | Frozen plan, real-data manifest, split exports and access logs |
| `research_outputs/phase3_pilot/` | Results, normalization, pixel samples, code/artifact hashes and local checkpoints |
| `research_outputs/reports/` | Scientific reasoning, audit history, tests and initial results |

The earlier Phase 1 and Phase 2 reports describe historical states. Their raw findings remain valid; mandatory image-class/physical-conversion gates were superseded by the authorized segmentation framing. Running the historical Phase 2 script still reproduces its original diagnostic outputs; it does not define current model-stage readiness.

## Next research step

**Expand independent geographic coverage**, not automatically to 50,000 patches. Current data are adequate for a bounded implementation pilot but offer only one geographic test component and no High test support. Index additional regional archives, audit reference support by independent region, then freeze a new experiment version before convergence training. Keep both current splits and results unchanged. A later single-factor imbalance experiment can compare unweighted and training-only weighted loss; no balancing method is selected using test scores.

Grad-CAM, robustness, calibration, large hyperparameter sweeps and frontend work remain deferred.

## Sources and licensing

- Schloer and Hänsch, *Harmful Cyanobacterial Bloom Detection using Deep Learning and Sentinel-2 Imagery*, [DOI 10.1109/JSTARS.2025.3629586](https://doi.org/10.1109/JSTARS.2025.3629586).
- [Author code, pinned e24e311](https://github.com/cschloer/hab_detection_s2/tree/e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37), Apache 2.0. Algorithm behavior and formulas are reimplemented with source attribution; upstream code is not executed.
- [Dataset version 14230064](https://doi.org/10.5281/zenodo.14230064), CC BY 4.0. Six published ZIPs total 23,402,209,757 bytes; full archive checksums are not verified by partial downloads.
- [NASA CyAN documentation](https://oceancolor.gsfc.nasa.gov/about/projects/cyan/).

Original AquaVision code is MIT licensed. Third-party data, publications, runtime libraries and author code retain their own licenses.

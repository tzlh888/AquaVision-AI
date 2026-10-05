"""Build research reports strictly from saved observed pilot results."""
import csv
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from aquavision.data.metadata import write_csv

R=Path('research_outputs/reports')
T=Path('research_outputs/tables')

def fmt(x): return 'N/A' if x is None else f'{x:.4f}'

def main():
    stats=json.loads((T/'phase3_statistics.json').read_text())
    leaks=json.loads((T/'phase3_leakage.json').read_text())
    results=json.loads(Path('research_outputs/phase3_pilot/results.json').read_text())
    plan=json.loads(Path('data/metadata/phase3/frozen_plan.json').read_text())
    manifest=json.loads(Path('data/metadata/phase3/pilot_manifest.json').read_text())
    suite=ET.parse(R/'phase3_pytest_results.xml').getroot().find('testsuite')
    tests=int(suite.attrib['tests'])
    summary=[]; detailed=[]
    for model in results['random']['models']:
        a=results['random']['models'][model]['test']; b=results['geographic']['models'][model]['test']
        summary.append({'model':model,'random_macro_f1_fixed_three':a['macro_f1_fixed_three_zero_division'],
                        'geographic_macro_f1_fixed_three':b['macro_f1_fixed_three_zero_division'],
                        'delta_random_minus_geographic':a['macro_f1_fixed_three_zero_division']-b['macro_f1_fixed_three_zero_division'],
                        'random_low_f1':a['per_class'][0]['f1'],'geographic_low_f1':b['per_class'][0]['f1'],
                        'random_moderate_f1':a['per_class'][1]['f1'],'geographic_moderate_f1':b['per_class'][1]['f1'],
                        'random_high_f1':a['per_class'][2]['f1'],'geographic_high_f1':b['per_class'][2]['f1'],
                        'full_three_class_evaluation':False,'scope':'bounded_pilot'})
    for strategy,r in results.items():
        for model,m in r['models'].items():
            for partition in ('validation','test'):
                for c in m[partition]['per_class']:
                    detailed.append({'strategy':strategy,'model':model,'partition':partition,**c})
    write_csv(T/'random_vs_geographic_pilot.csv',summary)
    write_csv(T/'phase3_per_class_metrics.csv',detailed)
    table='| Model | Random macro F1* | Geographic macro F1* | Δ random−geo | Geo Low F1 | Geo Moderate F1 | Geo High F1 |\n|---|---:|---:|---:|---:|---:|---:|\n'
    for r in summary:
        table+='| '+r['model']+' | '+' | '.join(fmt(r[k]) for k in ('random_macro_f1_fixed_three','geographic_macro_f1_fixed_three','delta_random_minus_geographic','geographic_low_f1','geographic_moderate_f1','geographic_high_f1'))+' |\n'
    table+='\n*Fixed three-class macro F1, undefined divisions scored zero. **Neither test set contains High reference pixels.** High recall/F1 is N/A, not measured zero. These scalars are pipeline diagnostics; they cannot establish three-class geographic generalization. Supported-class macro F1 and raw confusion matrices are in results JSON.\n'
    leak_table='| Pool / split | Shared subtile | Shared CyAN tile | Shared component | Repeated grid-position candidate | Same-date adjacent patch |\n|---|---:|---:|---:|---:|---:|\n'
    for scope in ('index','pilot'):
        for strategy in ('random','geographic'):
            l=leaks[scope][strategy]
            leak_table+=f'| {scope} / {strategy} | '+' | '.join(f"{l[k]['exposed_test_patches']}/{l[k]['test_patches']}" for k in ('subtile_id','region','spatial_group_id','grid_position_candidate','neighboring_patch_same_parent_date'))+' |\n'
    (R/'RANDOM_SPLIT_LEAKAGE_AUDIT.md').write_text('''# Random split leakage audit

Counts are test patches whose identifier also occurs in training. Validation is not included in these exposure denominators. Both designs preserve the same eligible pool within each scope; the 272-patch pilot is separate from the 24,518-pair index audit.

'''+leak_table+'''
On the complete indexed pool, 100% of random test patches share a parent subtile and connected region with training; 99.88% share a patch-grid position candidate across dates, and 99.51% have a same-parent/date neighbor in training. The author-grid geographic split removes those measured overlaps. Sharing the larger CyAN tile is expected: this is unseen *subregion* evaluation, not an unseen-CyAN-tile experiment.

Sentinel-2 scene overlap remains UNKNOWN because `sen2_uuid` was discarded. The paper reports 1,789 products in its full experiment; this number is not assigned to our subset. Date/subtile combinations are not relabeled as scenes. Repeated physical footprints and cross-tile waterbody overlap remain UNKNOWN without original transforms and IDs.

All 17 parents recur over dates; 1,386 of 1,391 patch-position candidates recur. Parent assignment keeps all those dates together in the geographic design. Native crop offsets do not prove exact repeated physical footprints after reprojection.

In the pilot, no train/test input pair has the same complete-file SHA-256. A fixed appearance diagnostic compares 12-band 8×8 block means after /10000: one random test patch and zero geographic test patches have a nearest-training mean absolute difference ≤0.001. This is not a geographic-footprint test or proof of duplication. All distances are saved in `phase3_leakage.json`; no thresholds were selected using model scores.

No latitude/longitude is required for these verified author-grid constraints. This audit does not assert that the geographic split prevents all scene, lake, basin or cross-tile dependence. With four components and one held-out component, independence is limited.
''')
    pixel_table='| Split | Patches | Valid pixels | Low | Moderate | High |\n|---|---:|---:|---:|---:|---:|\n'
    for strategy in ('random','geographic'):
        for split in ('train','validation','test'):
            d=stats['pilot'][strategy][split]
            pixel_table+=f"| {strategy} / {split} | {d['patches']} | {d['valid_pixels']:,} | {d['counts'][0]:,} | {d['counts'][1]:,} | {d['counts'][2]:,} |\n"
    (R/'TRAINING_SUBSET_DECISION.md').write_text('''# Training subset decision

**EXPAND SUBSET — expand independent geographic coverage, not automatically the patch count to 50,000.** Keep the current pool as development data and retain this frozen pilot as historical evidence. No additional archive expansion is performed in this run.

The 24,518 indexed pairs span two CyAN tiles, 17 fixed parent subtiles, four selected adjacency components and 106 dates. Exact Sentinel scene count is UNKNOWN. Four components yield only two train components, one validation component and one test component under the declared three-way protocol. More repeated patches from these same components cannot establish broad regional reliability.

Only 272 label-blind pilot pairs were loaded for this phase. They contain **922,399 valid reference pixels: 858,158 Low (93.0354%), 63,305 Moderate (6.8631%), and 936 High (0.1015%)**, with 191,713 ignored pixels. These are exact pilot counts. Full 24,518-pair valid/class counts and percentages remain UNKNOWN; archive filenames cannot supply them. Equal sampling per subtile means even the pilot percentages are not an unbiased estimate of the indexed population.

'''+pixel_table+'''
Neither fixed test partition has a High pixel. Geographic validation has only eight High pixels, from correlated interpolated references. This cannot support an honest high-risk recall estimate. We did not change the seed, swap test groups or cherry-pick a high-risk test patch after observing this problem.

The current data are sufficient to validate loaders, losses, optimizer execution and leakage diagnostics. They are insufficient for the requested final three-class regional-generalization conclusion. This is not a claim that all 24,518 patches lack high-risk evaluation examples: the full reference distribution was not downloaded.

Next, index the remaining regional archives under a separate budget, build connected components over the enlarged selected grid, and perform a reference-only pilot across more independent components. Measure class support by region, season and date before freezing a new experiment version. Do not use existing test *scores* to choose its membership. Favor diverse independent units and natural evaluation prevalence; do not force image-level balancing. The missing full-pool reference census should be explicit until reference members or an authoritative class manifest are examined.

At 102,656 bytes per observed pair, the current 24,518-pair pool would require 2,516,919,808 raw content bytes (about 2.344 GiB). Downloading that whole pool is not necessary for the present bounded milestone. The 272-pair pilot occupies 27,922,432 raw content bytes; runtime libraries and model checkpoints are additional storage.
''')
    sampled='\n'.join(f"- {s}: sampled training pixels Low/Moderate/High = {r['sampled_train_class_counts']}." for s,r in results.items())
    epochs='\n'.join(f"- {s} / {m}: {r['models'][m]['completed_epochs']} epochs, {r['models'][m]['seconds']:.2f} seconds, validation-selected checkpoint." for s,r in results.items() for m in ('SmallSegCNN','DeepLabV3_ResNet18'))
    content='''# Phase 3 initial results — bounded pilot

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

'''+leak_table+'''
See [detailed leakage report](RANDOM_SPLIT_LEAKAGE_AUDIT.md). The random full-index test has 100% same-subtile exposure to training. Geographic same-subtile/component exposure is zero. Scene and true footprint overlap are UNKNOWN; larger CyAN tiles still overlap. No exact pilot input hashes cross train/test.

## Dataset statistics

The indexed pool contains 24,518 pairs, 17 parents, four connected selected regions and 106 dates. It is not the downloaded training corpus. The pilot has 272 real pairs, 922,399 valid pixels and 191,713 ignored pixels. Exact full-pool pixel counts and Sentinel scene count remain UNKNOWN. Arrays are CRC/SHA-verified; no synthetic observations are used for training.

'''+pixel_table+'''
## Class imbalance

Pilot valid pixels are 93.0354% Low, 6.8631% Moderate and 0.1015% High. High appears in training but **neither test set has High support**. Per-class recall/F1 for unsupported High is recorded as null. Pixel counts over interpolated fields must not be treated as independent sampling units.

Initial models are unweighted. Optional weighted cross entropy and focal loss are implemented and tested but not used in reported runs. Class-balanced sampling is discussed as a separate later experiment; the initial uniform bounded sampling is preserved. The author's per-DN frequency weighting is distinct from those alternatives. No test balancing or class-frequency fitting on held-out labels occurs.

## Spectral baselines

All five paper formulas were implemented: NDCI, NDVI, FAI, B8A/B4 normalized difference and B3/B2 normalized difference. FAI uses explicitly documented nominal band wavelengths. Training-only quantile-grid threshold fitting replaces the author's larger Bayesian search for this bounded pilot. Undefined ratios have explicit imputation/coverage handling. Validation/test confusion matrices and thresholds are saved in the results JSON.

## Classical ML baselines

Logistic regression and a 64-tree random forest use 12 spectral bands, five source-supported indices and five undefined-index indicators. Uniform valid-pixel sampling is capped at 256 per training patch and 32,768 total. Every sampled pixel ID is saved, and geographic test pixels cannot enter training. Scaling is fitted on training only. Models are saved locally as joblib artifacts.

'''+sampled+'''

## Small CNN results

SmallSegCNN explicitly exposes convolutions, ReLU, pooling, bilinear upsampling and three-channel pixel logits. Masked cross entropy, backward propagation and optimizer steps operate on spatial masks. Joint flips preserve image/target alignment. It is randomly initialized and intentionally small; three epochs establish an executable baseline, not a converged model.

## Deep segmentation results

DeepLabV3 with ResNet18 follows the author's available constructor: 12 input channels, three classes, **no pretrained weights**. The network has 15,927,683 parameters. Two CPU epochs provide an initial training/evaluation check. No RGB substitution, ImageNet download or architecture sweep was performed.

'''+epochs+'''

## Random vs Geographic generalization

'''+table+'''
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

'''+f'**{tests} tests passed**, including all 70 prior tests. '+'''Coverage includes all 256 byte labels, requested boundaries, ignored/invalid values, source-grid identity and transitive adjacency, deterministic author/three-way algorithms, ratio diagnostics, frozen-file protection, spectral formulas, missing denominators, absent-class metrics, full-coverage training batches, training-only normalization, small-CNN gradient masking, and 12-band DeepLab output shape. Software tests use synthetic fixtures; the separate pilot trains only on real deposited arrays.

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
'''
    (R/'PHASE_3_INITIAL_RESULTS.md').write_text(content)
    print(table)

if __name__=='__main__': main()

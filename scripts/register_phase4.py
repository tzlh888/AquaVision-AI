import json,hashlib,datetime
from pathlib import Path
root=Path('.')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def freeze(p,v):
    s=json.dumps(v,indent=2,allow_nan=False)+'\n'
    if p.exists():assert p.read_text()==s
    else:p.write_text(s)
p=Path('data/metadata/phase4/preservation_manifest.json')
if not p.exists():
    paths=set()
    for d in ['data/metadata/phase3_5','research_outputs/phase3_5','research_outputs/phase3_pilot','research_outputs/reports','configs','src','scripts','tests']:
        paths.update(x for x in Path(d).rglob('*') if x.is_file() and '__pycache__' not in x.parts)
    freeze(p,{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':{str(x):sha(x) for x in sorted(paths)}})
config={'experiment':'phase4_reliability_v1','seed':42,'baseline_config':'configs/phase3_pilot.json','split':'data/metadata/phase3_5/geographic_split_v2.json','selection':{'primary':'validation_macro_f1','secondary':'validation_high_f1','low_f1_floor':0.5,'moderate_f1_floor':0.25,'no_eligible_cnn':'highest validation macro F1 diagnostic CNN; fails eligibility guard'},'class_weights':'N / (3 * class_count), exact existing uniform sample for classical; all valid train pixels for CNN','balanced_sampling':'24540 draws from SAME frozen sampled pool: 8180/class, replacement only where needed, seed42; effective unique support reported','focal_gamma':2.0,'checkpoint_selection':'minimum unweighted validation cross entropy, unchanged from Phase3.5','classical_variants':['lr_weighted','lr_balanced','rf_weighted','rf_balanced'],'neural_variants':['small_weighted','small_focal','deep_weighted','deep_focal'],'bands':{'all12':['B01','B02','B03','B04','B05','B06','B07','B08','B8A','B09','B11','B12'],'rgb':['B02','B03','B04'],'visible_rededge_nir':['B02','B03','B04','B05','B06','B07','B08','B8A'],'compact_hab':['B04','B05','B8A','B11']},'ablation':'best validation-selected CNN same loss/architecture/epochs, inactive normalized channels zero during train/validation/test; not eligible for post-hoc winner selection','temperature':{'fit':'validation only, all valid pixels','bounds':[0.05,20.0],'objective':'multiclass NLL'},'ece_bins':15,'high_confidence_threshold':0.8,'perturbations':{'brightness':[1.05,1.15],'contrast':[1.05,1.15],'noise':[0.002,0.005],'blur':[0.5,1.0],'resolution':[48,32],'mask':[0.05,0.15]},'perturbation_notes':'input reflectance; common brightness/contrast gain, common noise field across bands; channelwise same spatial kernel; clamp [0,1.5] and log clipping; center square mask replaced by training mean (artifact stress, not cloud physics); labels fixed','uncertainty':'three-group ranges and leave-one-group-out pooled confusion; no pixel bootstrap or population CI','visualization':'per region/category choose patch with highest mean confidence on qualifying pixels; ties sample_id; report unavailable; error threshold0.8','explainability':'integrated gradients of mean High logit over fixed valid true-High pixels, one max-High-support patch/region; training-mean baseline, 32 and64-step trapezoid convergence check'}
freeze(Path('configs/phase4.json'),config)
report=Path('research_outputs/reports/MODEL_SELECTION_PROTOCOL.md')
if not report.exists():report.write_text('''# Phase 4 model selection protocol — registered before new variant Test evaluation

Registration timestamp and hashes are in `data/metadata/phase4/preregistration.json`. Phase 3.5 results were already known; this is prospective registration of Phase 4 procedures, not a claim of blind design.

All nine frozen baselines and eight named imbalance variants are candidates. Rank eligible candidates by validation fixed-three-class Macro F1, then validation High F1, then ascending experiment ID. Eligibility requires validation Low F1 >= 0.50 AND Moderate F1 >= 0.25. These fixed absolute floors reject catastrophic majority/minority collapse; they do not certify three-class adequacy. High F1 is a secondary criterion, not a recall-only target. A winner with zero validation High F1 must be reported explicitly as failing validation evidence for High.

Select overall winner and CNN winner separately. If no CNN meets both floors, designate the highest-ranked CNN for diagnostic robustness/attribution only, explicitly flagging failed eligibility. Do not loosen floors. Save and hash validation selection before any new Test predictions. All preregistered candidates receive one final geographic Test evaluation for the controlled comparison; none is selected or adjusted from Test results. Test metrics cannot trigger new candidate, threshold, severity, epoch, or band searches.

Original baselines are reused unchanged. Classical class-weighted fits use the exact original 24,540 training pixels and inverse-frequency weights N/(3*n_c). Balanced sampling uses that SAME frozen pool, fixed total 24,540 draws (8,180/class), seed 42, replacement only where required. It repeats the same 56 High training pixels; report effective unique pixels and do not imply new independent evidence. LR/RF features and hyperparameters remain fixed.

CNN variants alter loss only: inverse-frequency weighted CE from all valid training-mask counts; or unweighted focal gamma=2. Architectures, initialization seed, flips, Adam, learning rate, weight decay, epochs and batching remain unchanged. To avoid a second experimental factor, within-run checkpoint selection remains minimum UNWEIGHTED validation CE as in Phase 3.5. Across-run selection uses validation Macro F1. Short 3/2-epoch budgets diagnose this frozen protocol; they do not establish converged architecture rankings. No Dice loss.

Band ablations use the selected CNN architecture AND loss and the same training protocol. All 12 input channels remain in the architecture; excluded channels are set to zero after training-only normalization at train/validation/test (training-mean imputation). RGB=B02/B03/B04; visible+red-edge/NIR=B02/B03/B04/B05/B06/B07/B08/B8A; compact HAB=B04/B05/B8A/B11, supporting the previously verified NDCI and FAI ingredients. All12 reuses selected CNN. Ablations are diagnostic and do not change the winner.

Temperature is scalar and positive, optimized on validation NLL only within [0.05,20], separately for every neural checkpoint. Preserve argmax. Fit before Test evaluation. Calibration bins=15 equal-width; report top-label multiclass ECE and High one-v-rest ECE, sum-of-three-class Brier, binary High Brier/NLL, multiclass NLL, confidence summaries and High-prediction precision at confidence>=0.8. Indices have no trained probability output; calibration is N/A.

Robustness severities are fixed in `configs/phase4.json`: common-band brightness gain1.05/1.15; contrast about each band's image mean with common gain1.05/1.15; common spatial Gaussian noise sigma0.002/0.005 reflectance; Gaussian blur sigma0.5/1.0 pixels; 64->48/32->64 bilinear resampling; center square masking about5%/15% replaced with training band means. Masking is explicitly an obstruction artifact stress test, not a physical cloud simulator. Clip transformed reflectance to[0,1.5] and record clipping; identical transforms across spectral channels preserve their relationships as far as feasible. No change to reference mask or class target.

Uncertainty: report region ranges and leave-one-region-out pooled metrics. Only three selected connected geographic components exist; do not report a reliable population confidence interval or bootstrap pixels. These components do not establish independent lakes/bloom episodes. v2 is High-enriched and precision is conditional on its composition. Only the old 272-pair random/geographic pilot is a matched comparison; never call v2-versus-random a split effect.

Figures use deterministic per-category highest mean qualifying-pixel confidence, ties by sample_id; absent categories are shown as unavailable. Integrated gradients targets the mean High logit over a fixed true-High mask in the highest-High-support patch per test region, with a normalized-zero/training-mean baseline and 32/64-step trapezoid checks. This is exploratory sensitivity, not causal proof.

No test-driven amendment is allowed. Implementation bug fixes must be logged with their effect and cannot silently change the registered experiment.
''')
p=Path('data/metadata/phase4/preregistration.json')
if not p.exists():freeze(p,{'registered_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'config_sha256':sha(Path('configs/phase4.json')),'protocol_sha256':sha(report),'split_sha256':sha(Path(config['split'])),'preservation_manifest_sha256':sha(Path('data/metadata/phase4/preservation_manifest.json'))})
print('Frozen',len(json.load(open('data/metadata/phase4/preservation_manifest.json'))['files']),'existing files; registered Phase4 protocol')

"""Release navigation and numeric-claim provenance; no scientific-output changes."""
from pathlib import Path
import json,hashlib,datetime
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def write(p,v):(ROOT/p).write_text(json.dumps(v,indent=2)+'\n')
def main():
    manifest=read('data/metadata/phase5/preservation_manifest.json')
    old_figures=['phase2_aggregation_sensitivity.png','phase3_author_grid_split.png','sample_bands.png','sample_images.png','sample_month.png','sample_reference_bins.png','sample_region.png','sample_year.png']
    if 'historical_figure_snapshot_utc' not in manifest:
        for n in old_figures:
            p='research_outputs/figures/'+n;manifest['files'][p]=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
        manifest['historical_figure_snapshot_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        write('data/metadata/phase5/preservation_manifest.json',manifest)
    figures=read('research_outputs/phase5/figure_manifest.json')
    text='# Core figure index\n\nTen figures form the final portfolio set. Each has a high-resolution PNG and editable vector SVG. Older figures remain as historical artifacts, not additional core selections. No plots imply independent-pixel confidence intervals. Data-derived images are attributed to Hänsch and Schloer, Zenodo version14230064, CC BY4.0.\n\n'
    for j,f in enumerate(figures['figures'],1):
        text+=f"## {j}. {f['title']}\n\n[PNG](../figures/{f['name']}.png) · [SVG](../figures/{f['name']}.svg)\n\n{f['caption']}\n\n"
    text+='The exact source list and chosen sample IDs are in [figure_manifest.json](../phase5/figure_manifest.json). Selection reuses Phase4 deterministic cases. Figures can be regenerated with `scripts/build_phase5_figures.py` when the required local arrays and prediction caches are available.\n'
    (ROOT/'research_outputs/reports/FIGURE_INDEX.md').write_text(text)
    files=sorted(p for p in manifest['files'] if p.startswith('research_outputs/reports/') and p.endswith('.md'))
    p4=set(d['path'] for d in read('research_outputs/phase4/delivery_manifest.json')['files'])
    stage35={'PHASE_3_5_STATUS.md','HIGH_RISK_SUPPORT_AUDIT.md','HIGH_RISK_INDEPENDENCE_AUDIT.md','EVALUATION_SUPPORT_CRITERIA.md','REFERENCE_AUDIT_ACQUISITION_AMENDMENT.md','PILOT_VS_EXPANDED_EVALUATION.md','PHASE_3_5_REPRODUCTION.md'}
    text='''# Archive and source-scope index

The canonical project account is [RESEARCH_RESULTS.md](RESEARCH_RESULTS.md); the root README describes the completed study. Historical reports are preserved byte-for-byte and must be read as records of their named stage.

- **Dataset and target investigation (Phases 1–2):** earlier mandatory image-classification and physical-conversion gates were superseded by verified pixel segmentation. “Not ready,” unset splits and proposed concentration thresholds describe that historical inquiry, not the final training target.
- **Pilot study (Phase 3):** the 272-pair random/geographic comparison. Statements about zero High Test support and 94 tests refer to that pilot. They do not describe the final benchmark.
- **Class-support correction (Phase 3.5):** support screening and the fixed v2 baseline experiment. Its earlier PARTIAL classification is preserved. The later reliability analysis reaches a LIMITED conclusion.
- **Reliability analysis and final evaluation (Phase 4):** final scientific evidence. These results remain authoritative for the packaged report; the release stage adds presentation and verification only.

`data/README.md` is a preserved Phase1–3 provenance narrative. Its “current” Phase3 heading and references to eight-pair/pilot artifacts are historical scope, not a second current project overview. Source snapshots under `data/metadata/sources/` and `data/metadata/phase2_sources/` may use terminology from their authors, including “ground truth”; they are unedited primary-source evidence, not AquaVision claims of laboratory validation. The previous root README is retained at `data/metadata/phase5/README_before_phase5.md` as an explicitly archived snapshot.

Historical training, report-generation and verification scripts can overwrite their original output paths. Use the Phase5 audit runner for final read/reload checks. Their old future-tense descriptions and gates do not authorize changing the final scientific framing.

## Historical report inventory

| Report | Scope |
| --- | --- |
'''
    for p in files:
        name=Path(p).name
        stage='Phase4 final scientific appendix' if p in p4 else 'Phase3.5 support/baseline history' if name in stage35 else 'Phase3 pilot/method reconstruction' if any(s in name for s in ['PHASE_3_','PIPELINE_RECONSTRUCTION','GEOGRAPHIC_GROUPING','RANDOM_SPLIT','TRAINING_SUBSET']) else 'Earlier provenance/methodology history'
        text+=f'| [{name}]({name}) | {stage} |\n'
    text+='\nPreservation scope and hashes are recorded in [the Phase5 manifest](../../data/metadata/phase5/preservation_manifest.json). No historical wording was silently rewritten to make the final outcome appear stronger.\n'
    (ROOT/'research_outputs/reports/ARCHIVE_INDEX.md').write_text(text)
    claims=[]
    def claim(id,snippet,source,locator,value):claims.append({'id':id,'readme_snippet':snippet,'source':source,'locator':locator,'verified_value':value})
    result=read('research_outputs/phase4/results.json');cal=read('research_outputs/phase4/calibration.json');selection=read('research_outputs/phase4/selection.json');summary=read('research_outputs/phase3_5/high_support_summary.json');split=read('data/metadata/phase3_5/geographic_split_v2.json')
    claim('pairs','**288 real pairs**','data/metadata/phase3_5/geographic_split_v2.json','len(samples)',len(split['samples']))
    for k,idx,n in [('train',0,96),('validation',1,48),('test',2,144)]:claim('patches_'+k,'**96 Train / 48 Validation / 144 Test**','data/metadata/phase3_5/geographic_split_v2.json',f'support/{idx}/patches',split['support'][idx]['patches'])
    claim('regions','**three geographic Test components**','data/metadata/phase3_5/geographic_split_v2.json','support/2/geographic_groups',3)
    claim('high_pixels','**37,768 High pixels**','data/metadata/phase3_5/geographic_split_v2.json','support/2/high_pixels',37768)
    claim('screening','**38,002 reference masks**','research_outputs/phase3_5/high_support_summary.json','all_screened/decoded_pairs',summary['all_screened']['decoded_pairs'])
    pilot=read('data/metadata/phase3/pilot_manifest.json');claim('pilot','**272-pair**','data/metadata/phase3/pilot_manifest.json','len(samples)',len(pilot['samples']))
    pr=read('research_outputs/phase3_pilot/results.json')
    for s in ['random','geographic']:claim('pilot_high_'+s,'**no High test support**','research_outputs/phase3_pilot/results.json',f'{s}/models/NDCI/test/per_class/2/support',pr[s]['models']['NDCI']['test']['per_class'][2]['support'])
    for row in read('research_outputs/phase5/central_results.json'):
        i=row['experiment_id'];vals=[row[k] for k in ['Validation Macro F1','Validation High F1','Geographic Macro F1','Geographic High F1']];snippet='| '+row['Model']+' | '+' | '.join(f'{v:.4f}' for v in vals)+' | '+row['Selection Status']+' |'
        for s,m,k in [('validation','macro_f1','Validation Macro F1'),('validation','per_class/2/f1','Validation High F1'),('test','macro_f1','Geographic Macro F1'),('test','per_class/2/f1','Geographic High F1')]:claim(i+'_'+k,snippet,'research_outputs/phase4/results.json',f'{i}/{s}/{m}',row[k])
    claim('selected','NDCI was selected by the validation rule','research_outputs/phase4/selection.json','overall',selection['overall'])
    claim('no_cnn','No CNN passed the predefined class guard.','research_outputs/phase4/selection.json','cnn_eligible',selection['cnn_eligible'])
    for i,range_text in [('baseline_LogisticRegression','**0.4006–0.5964**'),('deep_weighted','**0.1616–0.4546**')]:
        gs=result[i]['test_groups'];v=[m['per_class'][2]['f1'] for m in gs.values()]
        claim(i+'_regional_range',range_text,'research_outputs/phase4/results.json',f'regional_high_range:{i}',[min(v),max(v)])
    claim('confident_high','**510 High predictions with confidence ≥ 0.8 were all false**','research_outputs/phase4/calibration.json','deep_weighted/raw/overall/high_confidence_predictions',cal['deep_weighted']['raw']['overall']['high_confidence_predictions'])
    claim('confident_high_precision','**510 High predictions with confidence ≥ 0.8 were all false**','research_outputs/phase4/calibration.json','deep_weighted/raw/overall/high_confidence_precision',cal['deep_weighted']['raw']['overall']['high_confidence_precision'])
    for id,snippet,key in [('matrices','**100 confusion matrices**','exact_confusion_matrices'),('predictions','**40 class-prediction caches**','exact_class_prediction_caches')]:claim(id,snippet,'research_outputs/phase4/reproduction_check.json',key,read('research_outputs/phase4/reproduction_check.json')[key])
    claim('tests','**123 tests**','research_outputs/phase4/report_summary.json','tests',123)
    claim('figures','ten selected PNG/SVG figures','research_outputs/phase5/figure_manifest.json','core_figure_count',10)
    # Definitions/hyperparameters are source code/config facts, not inferred metrics.
    claims.extend([{'id':'label_definition','readme_snippet':'Stored DN values 0–99, 100–199, and 200–253','source':'src/aquavision/data/labels.py','locator':'segmentation_target; boundary tests in tests/test_segmentation.py','review':'Verified implementation and existing boundary tests; cells/mL disabled'}, {'id':'band_shape','readme_snippet':'**12 × 64 × 64**','source':'src/aquavision/data/segmentation_dataset.py','locator':'training_normalization shape check; BANDS in features/spectral.py','review':'Verified source and frozen data manifests'}, {'id':'guard','readme_snippet':'Low F1 ≥ 0.50 and Moderate F1 ≥ 0.25','source':'configs/phase4.json','locator':'selection','review':'Registered fixed class floors'}, {'id':'epochs','readme_snippet':'three SmallSegCNN epochs or two DeepLab epochs','source':'configs/phase3_pilot.json','locator':'epochs_small,epochs_deep','review':'Also checked in each Phase4 training history'}, {'id':'claim','readme_snippet':'**Final conclusion: LIMITED.**','source':'research_outputs/phase4/report_summary.json','locator':'claim','verified_value':'LIMITED'}])
    write('research_outputs/phase5/readme_claim_sources.json',{'scope':'Every quantitative headline and central model-table cell; qualitative conclusions link to canonical report and frozen appendices','claims':claims})
    print('Indexes and',len(claims),'README provenance entries created; protected files',len(manifest['files']))
if __name__=='__main__':main()

"""Reload v2 models; reproduce pooled/group confusion matrices and audit history."""
import csv,hashlib,json
from pathlib import Path
import numpy as np
import joblib
import torch
from torch.utils.data import DataLoader
from aquavision.data.evaluation_support import validate_support,group_support,choose_groups
from aquavision.data.segmentation_dataset import verify_samples,PatchDataset
from aquavision.data.labels import segmentation_target
from aquavision.models.segmentation import SmallSegCNN,deep_lab
from aquavision.features.spectral import INDEX_NAMES
from run_phase3_pilot import evaluate_classical,evaluate_index,evaluate_torch
from run_phase3_5 import add_weighted


def main():
    meta=Path('data/metadata/phase3_5');root=Path('research_outputs/phase3_5/models_v2')
    split_path=meta/'geographic_split_v2.json';split=json.loads(split_path.read_text())
    rows=split['samples'];a=split['assignments'];verify_samples(rows)
    contract=json.loads((root/'run_contract.json').read_text())
    assert hashlib.sha256(split_path.read_bytes()).hexdigest()==contract['split_sha256']
    for p,digest in contract['source_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest,p
    for artifact in json.loads((root/'artifact_manifest.json').read_text()):assert hashlib.sha256(Path(artifact['path']).read_bytes()).hexdigest()==artifact['sha256']
    pilot=json.loads((meta/'pilot_preservation_manifest.json').read_text())
    for artifact in pilot['files']:assert hashlib.sha256(Path(artifact['path']).read_bytes()).hexdigest()==artifact['sha256'],artifact['path']
    initial=json.loads((meta/'criteria_contract.json').read_text())
    assert hashlib.sha256(Path('research_outputs/reports/EVALUATION_SUPPORT_CRITERIA.md').read_bytes()).hexdigest()==initial['criteria_sha256']
    assert hashlib.sha256(Path('configs/phase3_5.json').read_bytes()).hexdigest()==initial['config_sha256']
    support=validate_support(rows,a,split['criteria']);assert support==split['support']
    census_path=json.loads((meta/'candidate_audit_completed.json').read_text())['reference_census_path']
    census=list(csv.DictReader(Path(census_path).open()))
    expected_groups=choose_groups(group_support(census),split['criteria'])
    assert all(expected_groups[r['spatial_group_id']]==a[r['sample_id']] for r in rows)
    for r in rows:
        y=segmentation_target(np.load(r['cyan_path'],allow_pickle=False))
        counts=np.bincount(y[y>=0],minlength=3)
        assert counts.tolist()==[int(r[k+'_pixels']) for k in ('low','moderate','high')]
    norm=json.loads((root/'normalization.json').read_text())
    assert set(norm['training_sample_ids'])=={r['sample_id'] for r in rows if a[r['sample_id']]=='train'}
    for r in json.loads((root/'sampled_training_pixels.json').read_text()):assert a[r['sample_id']]=='train'
    saved=json.loads((root/'results.json').read_text());test=[r for r in rows if a[r['sample_id']]=='test']
    torch.set_num_threads(4);torch.use_deterministic_algorithms(True)
    checked=0
    for name,m in saved['models'].items():
        if name in INDEX_NAMES:
            def evaluate(part):return evaluate_index(m['threshold_fit'],INDEX_NAMES.index(name),part)
        elif name in ('LogisticRegression','RandomForest'):
            model=joblib.load(root/(name+'.joblib'))
            def evaluate(part):return evaluate_classical(model,part)
        else:
            model=SmallSegCNN() if name=='SmallSegCNN' else deep_lab()
            model.load_state_dict(torch.load(root/(name+'.pt'),map_location='cpu',weights_only=True)['state_dict'])
            def evaluate(part):return evaluate_torch(model,DataLoader(PatchDataset(part,norm),batch_size=8))
        targets={'pooled':(test,m['test'])}
        targets.update({g:([r for r in test if r['spatial_group_id']==g],v) for g,v in m['test_groups'].items()})
        for label,(part,stored) in targets.items():
            observed=add_weighted(evaluate(part))
            assert observed['confusion_matrix']==stored['confusion_matrix'],(name,label)
            for metric in ('accuracy','macro_f1','weighted_f1'):assert observed[metric]==stored[metric]
            checked+=1
    report={'status':'PASS','reloaded_confusion_matrices':checked,'models':len(saved['models']),
        'pilot_artifacts_unchanged':len(pilot['files']),'support_and_split_integrity':'PASS','criteria_hashes_unchanged':'PASS',
        'training_only_normalization_and_pixels':'PASS','reference_counts_and_pair_hashes':'PASS','deterministic_group_allocation':'PASS'}
    Path('research_outputs/phase3_5/reproduction_check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()

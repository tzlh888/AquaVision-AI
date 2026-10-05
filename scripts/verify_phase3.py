"""Reload saved artifacts and independently reproduce every pilot test confusion matrix."""
import hashlib
import json
from pathlib import Path
import numpy as np
import joblib
import torch
from torch.utils.data import DataLoader
from aquavision.data.geographic_split import validate_geographic
from aquavision.data.segmentation_dataset import verify_samples, PatchDataset
from aquavision.models.segmentation import SmallSegCNN, deep_lab
from aquavision.features.spectral import INDEX_NAMES
from run_phase3_pilot import evaluate_classical, evaluate_index, evaluate_torch


def main():
    root=Path('research_outputs/phase3_pilot')
    plan_path=Path('data/metadata/phase3/frozen_plan.json')
    plan=json.loads(plan_path.read_text())
    manifest=json.loads(Path('data/metadata/phase3/pilot_manifest.json').read_text())
    contract=json.loads((root/'run_contract.json').read_text())
    assert hashlib.sha256(plan_path.read_bytes()).hexdigest()==manifest['plan_sha256']==contract['plan_sha256']
    for p,digest in contract['source_sha256'].items():
        assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest, p
    for a in json.loads((root/'artifact_manifest.json').read_text()):
        assert hashlib.sha256(Path(a['path']).read_bytes()).hexdigest()==a['sha256'],a['path']
    rows=manifest['samples']; verify_samples(rows)
    verify_samples(json.loads(Path('data/metadata/sample_manifest.json').read_text())['samples'])
    validate_geographic(rows,plan['splits']['geographic'])
    saved=json.loads((root/'results.json').read_text()); checked=[]
    torch.set_num_threads(4); torch.use_deterministic_algorithms(True)
    for strategy,result in saved.items():
        assignment=plan['splits'][strategy]; folder=root/strategy
        test=[r for r in rows if assignment[r['sample_id']]=='test']
        norm=json.loads((folder/'normalization.json').read_text())
        assert set(norm['training_sample_ids'])=={r['sample_id'] for r in rows if assignment[r['sample_id']]=='train'}
        sampled=json.loads((folder/'sampled_training_pixels.json').read_text())
        assert all(assignment[r['sample_id']]=='train' for r in sampled)
        for name, m in result['models'].items():
            if name in INDEX_NAMES:
                observed=evaluate_index(m['threshold_fit'],INDEX_NAMES.index(name),test)
            elif name in ('LogisticRegression','RandomForest'):
                observed=evaluate_classical(joblib.load(folder/(name+'.joblib')),test)
            else:
                checkpoint=torch.load(folder/(name+'.pt'),map_location='cpu',weights_only=True)
                model=SmallSegCNN() if name=='SmallSegCNN' else deep_lab()
                model.load_state_dict(checkpoint['state_dict'])
                observed=evaluate_torch(model,DataLoader(PatchDataset(test,norm),batch_size=8))
            assert observed['confusion_matrix']==m['test']['confusion_matrix'],(strategy,name)
            assert observed['macro_f1_fixed_three_zero_division']==m['test']['macro_f1_fixed_three_zero_division']
            checked.append(strategy+'/'+name)
    report={'status':'PASS','reloaded_test_evaluations':len(checked),'models':checked,
            'plan_source_artifact_hashes':'PASS','original_and_pilot_array_hashes':'PASS',
            'training_only_normalization_and_pixel_ids':'PASS','geographic_adjacency_isolation':'PASS'}
    Path('research_outputs/reports/phase3_reproduction_check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()

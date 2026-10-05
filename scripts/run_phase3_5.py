"""Refit the existing model families on a support-validated v2 geographic split."""
import hashlib,json,time,warnings
from pathlib import Path
import numpy as np
import joblib
import torch
from torch.utils.data import DataLoader
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from threadpoolctl import threadpool_limits
from aquavision.data.geographic_split import freeze_json
from aquavision.data.evaluation_support import validate_support
from aquavision.data.segmentation_dataset import verify_samples,training_normalization,PatchDataset
from aquavision.features.spectral import INDEX_NAMES
from aquavision.models.segmentation import SmallSegCNN,deep_lab
from aquavision.data.metadata import write_csv
from run_phase3_pilot import training_pixels,fit_index,evaluate_index,evaluate_classical,train_neural,evaluate_torch

ROOT=Path('research_outputs/phase3_5/models_v2')


def add_weighted(m):
    cm=np.asarray(m['confusion_matrix'],dtype=np.int64);support=cm.sum(1);prediction=cm.sum(0)
    f1=np.divide(2*np.diag(cm),support+prediction,out=np.zeros(3,dtype=float),where=(support+prediction)>0)
    return {**m,'weighted_f1':float((f1*support).sum()/support.sum()) if support.sum() else None,
            'macro_f1':m['macro_f1_fixed_three_zero_division']}


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    path=Path('data/metadata/phase3_5/geographic_split_v2.json')
    split=json.loads(path.read_text())
    if not split['model_evaluation_allowed'] or split['integrity']!='PASS':raise ValueError('Support gate closed')
    if not Path('research_outputs/phase3_5/split_support.csv').exists():raise ValueError('Support table required before model fitting')
    rows=split['samples'];a=split['assignments'];verify_samples(rows)
    support=validate_support(rows,a,split['criteria'])
    if support!=split['support']:raise ValueError('Support changed')
    config=json.loads(Path('configs/phase3_pilot.json').read_text())
    torch.set_num_threads(config['torch_threads']);torch.use_deterministic_algorithms(True)
    contract={'split_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'model_config':config,
      'same_architectures_as_pilot':True,'new_fit_on_v2_train_only':True,
      'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path('src').rglob('*.py'))+[Path('scripts/run_phase3_pilot.py'),Path(__file__)]}}
    freeze_json(ROOT/'run_contract.json',contract)
    parts={s:[r for r in rows if a[r['sample_id']]==s] for s in ('train','validation','test')}
    norm=training_normalization(parts['train']);freeze_json(ROOT/'normalization.json',norm)
    x,y,sampled=training_pixels(parts['train'],config);freeze_json(ROOT/'sampled_training_pixels.json',sampled)
    if set(np.unique(y))!={0,1,2}:raise ValueError('Bounded training pixel sample lacks a class; no reseeding')
    result={'version':'geographic_split_v2','config':config,'training_pixel_counts':np.bincount(y,minlength=3).tolist(),'models':{}}
    test_groups=sorted({r['spatial_group_id'] for r in parts['test']})
    for col,name in enumerate(INDEX_NAMES):
        spec=fit_index(x,y,col)
        result['models'][name]={'threshold_fit':spec,
          **{s:add_weighted(evaluate_index(spec,col,parts[s])) for s in ('validation','test')},
          'test_groups':{g:add_weighted(evaluate_index(spec,col,[r for r in parts['test'] if r['spatial_group_id']==g])) for g in test_groups}}
    with threadpool_limits(limits=4):
        for name,model in [('LogisticRegression',make_pipeline(StandardScaler(),LogisticRegression(max_iter=400,random_state=config['seed']))),
                           ('RandomForest',RandomForestClassifier(n_estimators=64,max_depth=12,min_samples_leaf=2,n_jobs=2,random_state=config['seed']))]:
            start=time.monotonic()
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always');model.fit(x,y)
            joblib.dump(model,ROOT/(name+'.joblib'))
            result['models'][name]={'seconds':time.monotonic()-start,'warnings':[str(v.message) for v in w],
               **{s:add_weighted(evaluate_classical(model,parts[s])) for s in ('validation','test')},
               'test_groups':{g:add_weighted(evaluate_classical(model,[r for r in parts['test'] if r['spatial_group_id']==g])) for g in test_groups}}
            print(name,'fit; High metrics',result['models'][name]['test']['per_class'][2],flush=True)
    for name,factory in [('SmallSegCNN',SmallSegCNN),('DeepLabV3_ResNet18',deep_lab)]:
        fitted=train_neural(name,factory,parts,config,norm,ROOT)
        fitted['test']=add_weighted(fitted['test']);fitted['validation']=add_weighted(fitted['validation'])
        model=factory();model.load_state_dict(torch.load(ROOT/(name+'.pt'),map_location='cpu',weights_only=True)['state_dict'])
        fitted['test_groups']={g:add_weighted(evaluate_torch(model,DataLoader(PatchDataset([r for r in parts['test'] if r['spatial_group_id']==g],norm),batch_size=8))) for g in test_groups}
        result['models'][name]=fitted
    (ROOT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    pooled=[];per_group=[]
    for name,m in result['models'].items():
        for s in ('validation','test'):
            v=m[s];c=v['per_class']
            row={'model':name,'partition':s,'accuracy':v['accuracy'],'macro_f1':v['macro_f1'],'weighted_f1':v['weighted_f1'],'valid_pixels':v['valid_pixels']}
            for i,kind in enumerate(('low','moderate','high')):
                for metric in ('precision','recall','f1','support'):row[kind+'_'+metric]=c[i][metric]
            pooled.append(row)
        for g,v in m['test_groups'].items():
            high=v['per_class'][2]
            per_group.append({'model':name,'geographic_group':g,'valid_pixels':v['valid_pixels'],'high_support':high['support'],
               'macro_f1':v['macro_f1'],'weighted_f1':v['weighted_f1'],'high_recall':high['recall'],'high_precision':high['precision'],'high_f1':high['f1']})
        summed=np.sum([v['confusion_matrix'] for v in m['test_groups'].values()],axis=0)
        assert np.array_equal(summed,m['test']['confusion_matrix'])
    write_csv(Path('research_outputs/phase3_5/model_metrics.csv'),pooled)
    write_csv(Path('research_outputs/phase3_5/per_geographic_group_metrics.csv'),per_group)
    artifacts=[{'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='artifact_manifest.json']
    (ROOT/'artifact_manifest.json').write_text(json.dumps(artifacts,indent=2)+'\n')
    print('v2 evaluated using unchanged model families/configuration; no tuning.',flush=True)

if __name__=='__main__':main()

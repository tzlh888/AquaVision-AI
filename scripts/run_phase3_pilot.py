"""Bounded, reproducible real-data segmentation pilot; frozen splits only.

CPU deterministic execution, no pretrained weights, no test-based selection.
Every metric covers all retained reference pixels in its assigned partition.
"""
import copy
import hashlib
import json
import random
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import torch
from torch.utils.data import DataLoader
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from aquavision.data.labels import segmentation_target, IGNORE_INDEX
from aquavision.data.geographic_split import freeze_json, validate_geographic
from aquavision.data.segmentation_dataset import PatchDataset, training_normalization, verify_samples, merge_singleton_batches
from aquavision.features.spectral import pixel_features, spectral_indices, INDEX_NAMES
from aquavision.evaluation.segmentation import confusion, metrics
from aquavision.models.segmentation import SmallSegCNN, deep_lab, masked_loss

ROOT = Path('research_outputs/phase3_pilot')


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def training_pixels(rows, config):
    rng = np.random.default_rng(config['seed'])
    xx,yy, selected = [],[],[]
    for row in rows:
        raw = np.load(row['sen2_path'], allow_pickle=False)
        target = segmentation_target(np.load(row['cyan_path'], allow_pickle=False)).ravel()
        valid = np.flatnonzero(target != IGNORE_INDEX)
        ids = rng.choice(valid, min(len(valid), config['pixels_per_training_patch']), replace=False)
        xx.append(pixel_features(raw).reshape(22,-1).T[ids]); yy.append(target[ids])
        selected.extend({'sample_id':row['sample_id'],'pixel':int(i)} for i in ids)
    x,y = np.concatenate(xx),np.concatenate(yy)
    if len(y)>config['max_training_pixels']:
        ids=rng.choice(len(y),config['max_training_pixels'],replace=False)
        x,y=x[ids],y[ids]; selected=[selected[i] for i in ids]
    return x,y,selected


def evaluate_classical(model, rows):
    cm=np.zeros((3,3),dtype=np.int64)
    for row in rows:
        raw=np.load(row['sen2_path'],allow_pickle=False)
        y=segmentation_target(np.load(row['cyan_path'],allow_pickle=False))
        p=model.predict(pixel_features(raw).reshape(22,-1).T).reshape(y.shape)
        cm+=confusion(y,p)
    return metrics(cm)


def fit_index(x,y, column):
    # x[:,12:17] contains indices with undefined values replaced by zero.
    v=x[:,12+column]
    missing=x[:,17+column].astype(bool)
    median=float(np.median(v[~missing])) if (~missing).any() else 0.
    v=np.where(missing,median,v)
    candidates=np.unique(np.quantile(v,np.linspace(0,1,11)))
    best=None
    for a in candidates:
        for b in candidates:
            if b<a: continue
            for direction in (1,-1):
                pred=np.searchsorted([a,b],v,side='right')
                if direction==-1: pred=2-pred
                score=metrics(confusion(y,pred))['macro_f1_fixed_three_zero_division']
                if best is None or score>best['training_macro_f1']:
                    best={'thresholds':[float(a),float(b)],'direction':direction,'training_macro_f1':score,'invalid_imputation':median}
    return best


def evaluate_index(spec, column, rows):
    cm=np.zeros((3,3),dtype=np.int64); undefined=0
    for row in rows:
        raw=np.load(row['sen2_path'],allow_pickle=False)
        y=segmentation_target(np.load(row['cyan_path'],allow_pickle=False))
        v=spectral_indices(raw)[column]
        undefined+=int(((~np.isfinite(v)) & (y!=IGNORE_INDEX)).sum())
        v=np.nan_to_num(v,nan=spec['invalid_imputation'])
        p=np.searchsorted(spec['thresholds'],v,side='right')
        if spec['direction']==-1: p=2-p
        cm+=confusion(y,p)
    return {**metrics(cm),'undefined_index_valid_pixels':undefined}


def evaluate_torch(model, loader):
    cm=np.zeros((3,3),dtype=np.int64); loss_sum=0.; count=0
    model.eval()
    with torch.inference_mode():
        for x,y in loader:
            logits=model(x)
            n=int((y!=IGNORE_INDEX).sum())
            loss_sum+=float(masked_loss(logits,y))*n; count+=n
            cm+=confusion(y.numpy(),logits.argmax(1).numpy())
    return {**metrics(cm),'cross_entropy':loss_sum/count if count else None}


def train_neural(name, factory, partitions, config, norm, folder):
    random.seed(config['seed']); np.random.seed(config['seed']); torch.manual_seed(config['seed'])
    model=factory()
    optimizer=torch.optim.Adam(model.parameters(),lr=config['learning_rate'],weight_decay=config['weight_decay'])
    loaders={split:DataLoader(PatchDataset(rows,norm),batch_size=config['batch_size'],shuffle=split=='train',
                  num_workers=0,generator=torch.Generator().manual_seed(config['seed'])) for split,rows in partitions.items()}
    history=[]; best=None; best_loss=float('inf'); start=time.monotonic()
    max_epochs=config['epochs_small'] if name=='SmallSegCNN' else config['epochs_deep']
    for epoch in range(max_epochs):
        model.train(); numerator=0.; denominator=0
        training_loader = DataLoader(PatchDataset(partitions['train'],norm),
            batch_sampler=merge_singleton_batches(len(partitions['train']),config['batch_size'],seed=config['seed']+epoch))
        for x,y in training_loader:
            # Joint augmentation; masks undergo exactly the same flips as inputs.
            if torch.rand(()) < .5: x,y=x.flip(-1),y.flip(-1)
            if torch.rand(()) < .5: x,y=x.flip(-2),y.flip(-2)
            optimizer.zero_grad(set_to_none=True)
            logits=model(x)
            loss=masked_loss(logits,y)
            loss.backward(); optimizer.step()
            n=int((y!=IGNORE_INDEX).sum()); numerator+=float(loss.detach())*n; denominator+=n
        val=evaluate_torch(model,loaders['validation'])
        history.append({'epoch':epoch+1,'train_cross_entropy':numerator/denominator if denominator else None,'validation':val})
        value=val['cross_entropy']
        if value is not None and value<best_loss:
            best_loss=value; best=copy.deepcopy(model.state_dict())
        print(f'{folder.name} {name} epoch {epoch+1}: train CE={history[-1]["train_cross_entropy"]:.5f}; val CE={value}',flush=True)
        if time.monotonic()-start>config['max_runtime_seconds_per_model']:
            break
    if best is None:
        raise ValueError('No valid validation pixels; cannot select checkpoint')
    model.load_state_dict(best)
    torch.save({'state_dict':best,'normalization':norm,'config':config,'architecture':name},folder/(name+'.pt'))
    return {'parameter_count':sum(p.numel() for p in model.parameters()),'initialization':'random',
            'history':history,'completed_epochs':len(history),'seconds':time.monotonic()-start,
            'validation':evaluate_torch(model,loaders['validation']), 'test':evaluate_torch(model,loaders['test'])}


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    plan_path=Path('data/metadata/phase3/frozen_plan.json')
    plan=json.loads(plan_path.read_text()); config=plan['config']
    if config != json.loads(Path('configs/phase3_pilot.json').read_text()):
        raise ValueError('Config changed after frozen plan')
    manifest=json.loads(Path('data/metadata/phase3/pilot_manifest.json').read_text())
    if hashlib.sha256(plan_path.read_bytes()).hexdigest()!=manifest['plan_sha256']:
        raise ValueError('Plan hash mismatch')
    rows=manifest['samples']; verify_samples(rows)
    if {r['sample_id'] for r in rows} != set(plan['splits']['random']):
        raise ValueError('Incomplete downloaded pilot')
    validate_geographic(rows,plan['splits']['geographic'])
    sources = sorted(Path('src').rglob('*.py')) + [Path(__file__), Path('requirements-phase3.txt')]
    freeze_json(ROOT/'run_contract.json', {
        'plan_sha256':manifest['plan_sha256'], 'config':config,
        'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'device':'cpu', 'deterministic_algorithms':True,
        'batch_policy':'seeded full-coverage batches; final singleton merged into previous batch',
        'selection':'minimum validation pixel cross entropy within declared epoch budget',
        'loss':'unweighted; optional focal/weighted implementations not used in this pilot'})
    torch.set_num_threads(config['torch_threads']); torch.use_deterministic_algorithms(True)
    all_results={}
    for strategy,assignment in plan['splits'].items():
        folder=ROOT/strategy; folder.mkdir(exist_ok=True)
        partitions={s:[r for r in rows if assignment[r['sample_id']]==s] for s in ('train','validation','test')}
        norm=training_normalization(partitions['train'])
        freeze_json(folder/'normalization.json',norm)
        x,y,sampled=training_pixels(partitions['train'],config)
        if len(np.unique(y))<2:
            raise ValueError('Training pixel sample has fewer than two observed classes')
        freeze_json(folder/'sampled_training_pixels.json',sampled)
        result={'strategy':strategy,'plan_sha256':manifest['plan_sha256'],'scope':'bounded_pilot',
                'sampled_train_class_counts':np.bincount(y,minlength=3).tolist(),'models':{}}
        for col,name in enumerate(INDEX_NAMES):
            spec=fit_index(x,y,col)
            result['models'][name]={'fitted_on':'training pixels only','threshold_fit':spec,
                   **{s:evaluate_index(spec,col,partitions[s]) for s in ('validation','test')}}
        with threadpool_limits(limits=4):
            for name,model in [('LogisticRegression',make_pipeline(StandardScaler(),LogisticRegression(max_iter=400,random_state=config['seed']))),
                               ('RandomForest',RandomForestClassifier(n_estimators=64,max_depth=12,min_samples_leaf=2,n_jobs=2,random_state=config['seed']))]:
                start=time.monotonic()
                with warnings.catch_warnings(record=True) as recorded:
                    warnings.simplefilter('always'); model.fit(x,y)
                joblib.dump(model,folder/(name+'.joblib'))
                result['models'][name]={'seconds':time.monotonic()-start,'warnings':[str(w.message) for w in recorded],
                       **{s:evaluate_classical(model,partitions[s]) for s in ('validation','test')}}
                print(f'{strategy} {name} fitted using {len(y)} training pixels',flush=True)
        for name,factory in [('SmallSegCNN',SmallSegCNN),('DeepLabV3_ResNet18',deep_lab)]:
            result['models'][name]=train_neural(name,factory,partitions,config,norm,folder)
            write(folder/'results.json',result)
        all_results[strategy]=result
    write(ROOT/'results.json',all_results)
    artifacts=[]
    for p in sorted(ROOT.rglob('*')):
        if p.is_file() and p.name != 'artifact_manifest.json':
            artifacts.append({'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    write(ROOT/'artifact_manifest.json',artifacts)
    print('Bounded pilot finished; metrics saved. No full-corpus result is claimed.',flush=True)

if __name__=='__main__':
    main()

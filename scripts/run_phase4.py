"""Registered Phase4 fits: validation selection is sealed before new Test inference."""
import copy,datetime,hashlib,json,random,time,warnings
from pathlib import Path
import joblib,numpy as np,torch
from scipy.special import softmax
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from threadpoolctl import threadpool_limits
from torch.utils.data import DataLoader
from aquavision.data.geographic_split import freeze_json
from aquavision.data.labels import segmentation_target
from aquavision.data.segmentation_dataset import PatchDataset,merge_singleton_batches,verify_samples
from aquavision.features.spectral import pixel_features,spectral_indices,INDEX_NAMES,BANDS
from aquavision.models.segmentation import SmallSegCNN,deep_lab,masked_loss
from aquavision.evaluation.reliability import balanced_weights,balanced_sample_indices,region_metrics,fit_temperature,keep_bands,choose_models
from run_phase3_pilot import training_pixels,evaluate_torch

OUT=Path('research_outputs/phase4');OLD=Path('research_outputs/phase3_5/models_v2')
CFG=json.loads(Path('configs/phase4.json').read_text());BASE=json.loads(Path('configs/phase3_pilot.json').read_text())
NORM=json.loads((OLD/'normalization.json').read_text())

def write(p,v):
    Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def context():
    s=json.loads(Path(CFG['split']).read_text())
    return {p:[r for r in s['samples'] if s['assignments'][r['sample_id']]==p] for p in ('train','validation','test')}
def factory(family):return SmallSegCNN() if family=='SmallSegCNN' else deep_lab()
def neural(spec):return spec['family'] in ('SmallSegCNN','DeepLabV3_ResNet18')
def load_model(spec):
    if spec['family'] in INDEX_NAMES:return None
    if not neural(spec):return joblib.load(spec['path'])
    model=factory(spec['family']);model.load_state_dict(torch.load(spec['path'],map_location='cpu',weights_only=True)['state_dict']);return model.eval()
def predict(spec,rows,norm=NORM,model=None):
    model=load_model(spec) if model is None else model
    y=np.stack([segmentation_target(np.load(r['cyan_path'],allow_pickle=False)) for r in rows]).astype(np.int16)
    if spec['family'] in INDEX_NAMES:
        spec_fit=spec['threshold_fit'];pred=[]
        for r in rows:
            v=spectral_indices(np.load(r['sen2_path'],allow_pickle=False))[INDEX_NAMES.index(spec['family'])]
            v=np.nan_to_num(v,nan=spec_fit['invalid_imputation']);p=np.searchsorted(spec_fit['thresholds'],v,side='right')
            pred.append(2-p if spec_fit['direction']==-1 else p)
        return {'y':y,'pred':np.stack(pred).astype(np.int8)}
    if not neural(spec):
        probabilities=np.stack([model.predict_proba(pixel_features(np.load(r['sen2_path'],allow_pickle=False)).reshape(22,-1).T).reshape(64,64,3) for r in rows])
        return {'y':y,'prob':probabilities,'pred':probabilities.argmax(-1).astype(np.int8)}
    logits=[]
    with torch.inference_mode():
        for x,_ in DataLoader(PatchDataset(rows,norm),batch_size=8):
            z=model(keep_bands(x,spec.get('bands',BANDS)))
            logits.append(z.permute(0,2,3,1).numpy())
    logits=np.concatenate(logits)
    return {'y':y,'logits':logits,'pred':logits.argmax(-1).astype(np.int8)}
def probabilities(cache,temperature=1.):
    return softmax(cache['logits'].astype(np.float64)/temperature,axis=-1) if 'logits' in cache else cache['prob']
def summarize(cache,rows):
    m=region_metrics(cache['y'],cache['pred']);groups={}
    for g in sorted({r['spatial_group_id'] for r in rows}):
        ids=[i for i,r in enumerate(rows) if r['spatial_group_id']==g]
        groups[g]=region_metrics(cache['y'][ids],cache['pred'][ids])
    return m,groups

def train_cnn(spec,parts,counts):
    random.seed(42);np.random.seed(42);torch.manual_seed(42)
    model=factory(spec['family']);optimizer=torch.optim.Adam(model.parameters(),lr=BASE['learning_rate'],weight_decay=BASE['weight_decay'])
    val_loader=DataLoader(PatchDataset(parts['validation'],NORM),batch_size=8,shuffle=False,num_workers=0,generator=torch.Generator().manual_seed(42))
    weights=torch.tensor(balanced_weights(counts),dtype=torch.float32) if spec['loss']=='weighted' else None
    gamma=2. if spec['loss']=='focal' else None
    bands=spec.get('bands',BANDS);history=[];best=None;best_loss=float('inf');start=time.monotonic()
    epochs=BASE['epochs_small'] if spec['family']=='SmallSegCNN' else BASE['epochs_deep']
    for epoch in range(epochs):
        model.train();total=0.;n=0
        loader=DataLoader(PatchDataset(parts['train'],NORM),batch_sampler=merge_singleton_batches(len(parts['train']),8,seed=42+epoch))
        for x,y in loader:
            x=keep_bands(x,bands)
            if torch.rand(())<.5:x,y=x.flip(-1),y.flip(-1)
            if torch.rand(())<.5:x,y=x.flip(-2),y.flip(-2)
            optimizer.zero_grad(set_to_none=True);loss=masked_loss(model(x),y,class_weights=weights,focal_gamma=gamma)
            loss.backward();optimizer.step();count=int((y!=-100).sum());total+=float(loss.detach())*count;n+=count
        model.eval();cm=np.zeros((3,3),dtype=np.int64);ce=0.;valid_n=0
        from aquavision.evaluation.segmentation import confusion,metrics
        with torch.inference_mode():
            for x,y in val_loader:
                z=model(keep_bands(x,bands));count=int((y!=-100).sum());ce+=float(masked_loss(z,y))*count;valid_n+=count
                cm+=confusion(y.numpy(),z.argmax(1).numpy())
        val_ce=ce/valid_n
        history.append({'epoch':epoch+1,'train_loss':total/n,'validation_unweighted_ce':val_ce,'validation':metrics(cm)})
        if val_ce<best_loss:best_loss=val_ce;best=copy.deepcopy(model.state_dict());best_epoch=epoch+1
        print(spec['id'],'epoch',epoch+1,'validation CE',round(val_ce,6),flush=True)
        if time.monotonic()-start>BASE['max_runtime_seconds_per_model']:break
    torch.save({'state_dict':best,'normalization':NORM,'config':BASE,'architecture':spec['family'],'phase4_spec':spec},spec['path'])
    write(OUT/'models'/f"{spec['id']}_training.json",{'history':history,'selected_epoch':best_epoch,'seconds':time.monotonic()-start,'class_weights':weights.tolist() if weights is not None else None,'completed_epochs':len(history)})

def main():
    torch.set_num_threads(4);torch.use_deterministic_algorithms(True)
    reg=json.loads(Path('data/metadata/phase4/preregistration.json').read_text())
    assert reg['config_sha256']==sha('configs/phase4.json')
    assert reg['protocol_sha256']==sha('research_outputs/reports/MODEL_SELECTION_PROTOCOL.md')
    assert reg['split_sha256']==sha(CFG['split'])
    if (OUT/'selection.json').exists():raise RuntimeError('Run already selected; use saved artifacts, never silently retrain/reselect')
    parts=context();verify_samples(sum(parts.values(),[]))
    freeze_json(OUT/'run_contract.json',{'started_utc':now(),'preregistration_sha256':sha('data/metadata/phase4/preregistration.json'),'source_sha256':{str(p):sha(p) for p in [Path(__file__),Path('src/aquavision/evaluation/reliability.py'),Path('scripts/run_phase3_pilot.py')]},'split_sha256':sha(CFG['split']),'device':'cpu','deterministic_algorithms':True})
    write(OUT/'prediction_order.json',{p:[r['sample_id'] for r in rows] for p,rows in parts.items()})
    old=json.loads((OLD/'results.json').read_text());specs={};validation={};temperatures={}
    for family in old['models']:
        i='baseline_'+family;spec={'id':i,'family':family,'variant':'baseline','loss':'unweighted'}
        if family in INDEX_NAMES:spec['threshold_fit']=old['models'][family]['threshold_fit']
        else:spec['path']=str(OLD/(family+('.pt' if family in ('SmallSegCNN','DeepLabV3_ResNet18') else '.joblib')))
        specs[i]=spec
    x,y,sampled=training_pixels(parts['train'],BASE)
    assert sampled==json.loads((OLD/'sampled_training_pixels.json').read_text())
    ids=balanced_sample_indices(y);write(OUT/'balanced_sample_indices.json',ids.tolist())
    write(OUT/'sampling_audit.json',{'original_counts':np.bincount(y,minlength=3).tolist(),'balanced_counts':np.bincount(y[ids],minlength=3).tolist(),'balanced_unique_counts':[len(np.unique(ids[y[ids]==c])) for c in range(3)],'pool_sha256':sha(OLD/'sampled_training_pixels.json'),'weight_vector':balanced_weights(np.bincount(y,minlength=3)).tolist()})
    counts=np.sum([[int(r[k]) for k in ('low_pixels','moderate_pixels','high_pixels')] for r in parts['train']],axis=0)
    for family,prefix in [('LogisticRegression','lr'),('RandomForest','rf')]:
        for variant in ('weighted','balanced'):
            i=f'{prefix}_{variant}';spec={'id':i,'family':family,'variant':variant,'path':str(OUT/'models'/f'{i}.joblib')};specs[i]=spec
            cw='balanced' if variant=='weighted' else None
            model=make_pipeline(StandardScaler(),LogisticRegression(max_iter=400,random_state=42,class_weight=cw)) if prefix=='lr' else RandomForestClassifier(n_estimators=64,max_depth=12,min_samples_leaf=2,n_jobs=2,random_state=42,class_weight=cw)
            xx,yy=(x[ids],y[ids]) if variant=='balanced' else (x,y)
            with threadpool_limits(limits=4),warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always');model.fit(xx,yy)
            joblib.dump(model,spec['path']);write(OUT/'models'/f'{i}_training.json',{'warnings':[str(v.message) for v in w],'sample_counts':np.bincount(yy,minlength=3).tolist()});print(i,'fit',flush=True)
    for family,prefix in [('SmallSegCNN','small'),('DeepLabV3_ResNet18','deep')]:
        for loss in ('weighted','focal'):
            i=f'{prefix}_{loss}';spec={'id':i,'family':family,'variant':loss,'loss':loss,'path':str(OUT/'models'/f'{i}.pt')};specs[i]=spec;train_cnn(spec,parts,counts)
    for i,spec in specs.items():
        cache=predict(spec,parts['validation']);np.savez_compressed(OUT/f'{i}_validation.npz',**cache)
        validation[i]=summarize(cache,parts['validation'])[0]
        if neural(spec):
            valid=cache['y']!=-100;temperatures[i]=fit_temperature(cache['logits'][valid],cache['y'][valid])
        if spec['variant']=='baseline':assert validation[i]['confusion_matrix']==old['models'][spec['family']]['validation']['confusion_matrix']
    selection=choose_models(validation,{i for i,s in specs.items() if neural(s)})
    selection.update(selected_utc=now(),preregistration_sha256=sha('data/metadata/phase4/preregistration.json'),validation=validation)
    freeze_json(OUT/'selection.json',selection);print('SEALED VALIDATION SELECTION:',selection['overall'],selection['cnn'],'eligibleCNN',selection['cnn_eligible'],flush=True)
    for name,bands in CFG['bands'].items():
        if name=='all12':continue
        parent=specs[selection['cnn']];i=f'ablation_{name}'
        spec={**parent,'id':i,'variant':'band_ablation','bands':bands,'parent':parent['id'],'path':str(OUT/'models'/f'{i}.pt')};specs[i]=spec;train_cnn(spec,parts,counts)
        cache=predict(spec,parts['validation']);np.savez_compressed(OUT/f'{i}_validation.npz',**cache)
        validation[i]=summarize(cache,parts['validation'])[0];valid=cache['y']!=-100
        temperatures[i]=fit_temperature(cache['logits'][valid],cache['y'][valid])
    freeze_json(OUT/'specifications.json',specs);freeze_json(OUT/'temperatures.json',temperatures)
    freeze_json(OUT/'test_evaluation_start.json',{'started_utc':now(),'selection_sha256':sha(OUT/'selection.json'),'temperature_sha256':sha(OUT/'temperatures.json'),'specification_sha256':sha(OUT/'specifications.json')})
    results={}
    for i,spec in specs.items():
        cache=predict(spec,parts['test']);np.savez_compressed(OUT/f'{i}_test.npz',**cache);test,groups=summarize(cache,parts['test'])
        if spec['variant']=='baseline':
            assert test['confusion_matrix']==old['models'][spec['family']]['test']['confusion_matrix']
            for g,m in groups.items():assert m['confusion_matrix']==old['models'][spec['family']]['test_groups'][g]['confusion_matrix']
        results[i]={'validation':validation[i],'test':test,'test_groups':groups}
        print(i,'TEST macro',round(test['macro_f1'],4),'HighF1',round(test['per_class'][2]['f1'],4),flush=True)
    write(OUT/'results.json',results)
    print('All registered test evaluations complete.',flush=True)
if __name__=='__main__':main()

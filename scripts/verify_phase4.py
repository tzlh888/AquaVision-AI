"""Reload all Phase4/baseline checkpoints; verify frozen artifacts and inference."""
import json
from pathlib import Path
import numpy as np,torch
from aquavision.evaluation.reliability import choose_models,fit_temperature
from run_phase4 import OUT,CFG,context,predict,summarize,probabilities,neural,sha,write

def read(p):return json.loads(Path(p).read_text())
def main():
    torch.set_num_threads(4);torch.use_deterministic_algorithms(True)
    original=read('data/metadata/phase4/preservation_manifest.json')['files'];changed=[p for p,h in original.items() if not Path(p).exists() or sha(p)!=h]
    assert not changed,changed
    write(OUT/'preservation_check.json',{'checked':len(original),'changed':changed,'passed':True})
    contract=read(OUT/'run_contract.json')
    assert all(sha(p)==h for p,h in contract['source_sha256'].items())
    reg=read('data/metadata/phase4/preregistration.json');assert reg['config_sha256']==sha('configs/phase4.json');assert reg['protocol_sha256']==sha('research_outputs/reports/MODEL_SELECTION_PROTOCOL.md');assert reg['split_sha256']==sha(CFG['split'])
    start=read(OUT/'test_evaluation_start.json');selection=read(OUT/'selection.json');specs=read(OUT/'specifications.json');results=read(OUT/'results.json');temps=read(OUT/'temperatures.json')
    assert start['selection_sha256']==sha(OUT/'selection.json');assert start['temperature_sha256']==sha(OUT/'temperatures.json');assert start['specification_sha256']==sha(OUT/'specifications.json')
    assert reg['registered_utc']<selection['selected_utc']<start['started_utc']
    candidates={i:results[i]['validation'] for i,s in specs.items() if s['variant']!='band_ablation'}
    chosen=choose_models(candidates,{i for i,s in specs.items() if neural(s) and s['variant']!='band_ablation'})
    for k,v in chosen.items():assert selection[k]==v
    parts=context();count=0;predictions=0;temperature_checks=0;probability_differences=[]
    for i,spec in specs.items():
        for partition in ('validation','test'):
            cache=predict(spec,parts[partition]);saved=np.load(OUT/f'{i}_{partition}.npz')
            assert set(cache)==set(saved.files)
            for k,v in cache.items():
                if k=='prob' and spec['family']=='RandomForest':
                    difference=float(np.max(np.abs(v-saved[k])))
                    assert np.allclose(v,saved[k],rtol=0,atol=1e-12),(i,partition,k,difference)
                    probability_differences.append({'experiment_id':i,'partition':partition,'max_absolute_difference':difference})
                else:assert np.array_equal(v,saved[k]),(i,partition,k)
            pooled,groups=summarize(cache,parts[partition]);assert pooled==results[i][partition];count+=1;predictions+=1
            if partition=='test':
                for g,m in groups.items():assert m==results[i]['test_groups'][g];count+=1
            if neural(spec):
                p=probabilities(cache,temps[i]['temperature']);assert np.array_equal(p.argmax(-1),cache['pred']);temperature_checks+=1
                if partition=='validation':
                    valid=cache['y']!=-100;assert fit_temperature(cache['logits'][valid],cache['y'][valid])==temps[i]
        print('Reproduced',i,flush=True)
    write(OUT/'reproduction_check.json',{'passed':True,'exact_confusion_matrices':count,'exact_class_prediction_caches':predictions,'rf_probability_roundoff':probability_differences,'rf_probability_absolute_tolerance':1e-12,'unchanged_temperature_argmax_checks':temperature_checks,'models':len(specs),'validation_only_selection_reproduced':True,'validation_only_temperature_fits_reproduced':True,'registration_order_verified':True,'frozen_files_checked':len(original)})
if __name__=='__main__':main()

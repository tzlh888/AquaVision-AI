"""Additional descriptive train/test diagnostics, with no fitting or selection."""
import json
import joblib,numpy as np
from run_phase4 import OUT,OLD,BASE,context,write
from run_phase3_pilot import training_pixels
from aquavision.evaluation.reliability import region_metrics

def main():
    parts=context();x,y,sampled=training_pixels(parts['train'],BASE);out={}
    for family in ['LogisticRegression','RandomForest']:
        model=joblib.load(OLD/(family+'.joblib'));p=model.predict_proba(x)
        c=np.load(OUT/f'baseline_{family}_test.npz');valid=c['y']!=-100;yy=c['y'][valid];pp=c['prob'][valid]
        summary={}
        for name,probs,labels in [('training_resubstitution',p,y),('geographic_test',pp,yy)]:
            summary[name]={'metrics':region_metrics(labels,probs.argmax(1)), 'true_high_mean_probability':float(probs[labels==2,2].mean()),'true_high_quantiles':np.quantile(probs[labels==2,2],[.1,.5,.9]).tolist()}
        out[family]=summary
    write(OUT/'train_test_minority_diagnostics.json',out)
    print({k:{s:round(v['metrics']['per_class'][2]['recall'],4) for s,v in d.items()} for k,d in out.items()})
if __name__=='__main__':main()

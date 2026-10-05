"""Descriptive reliability analyses after sealed validation-only selection."""
import argparse,csv,itertools,json
from pathlib import Path
import joblib,numpy as np,torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from scipy.stats import wasserstein_distance,spearmanr
from sklearn.metrics import roc_curve,precision_recall_curve,roc_auc_score,average_precision_score
from aquavision.data.labels import segmentation_target
from aquavision.data.segmentation_dataset import PatchDataset
from aquavision.evaluation.segmentation import metrics
from aquavision.features.spectral import BANDS,INDEX_NAMES,pixel_features,spectral_indices
from aquavision.evaluation.reliability import calibration,region_metrics,perturb,sample_seed,keep_bands,select_example,integrated_gradients
from run_phase4 import OUT,OLD,BASE,CFG,NORM,context,predict,probabilities,load_model,neural,write,sha
from run_phase3_pilot import training_pixels

PLOTS=OUT/'plots';CLASSES=['Low','Moderate','High'];COLORS=['#277DA8','#E9B949','#CB3C33']

def read(p):return json.loads(Path(p).read_text())
def csvwrite(name,rows):
    if not rows:return
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def save(fig,name):fig.savefig(PLOTS/name,dpi=130,bbox_inches='tight');plt.close(fig)
def loadcache(i,partition='test'):
    with np.load(OUT/f'{i}_{partition}.npz') as f:return {k:f[k] for k in f.files}
def short(g):return g.split(':')[-1].replace('_S050','')

def regional(results):
    rows=[];pooled=[];loo=[]
    for i,r in results.items():
        for part in ('validation','test'):
            m=r[part];c=m['per_class'];pooled.append({'experiment_id':i,'partition':part,'macro_f1':m['macro_f1'],'high_precision':c[2]['precision'],'high_recall':c[2]['recall'],'high_f1':c[2]['f1'],'moderate_f1':c[1]['f1'],'low_f1':c[0]['f1']})
        for g,m in r['test_groups'].items():
            for c in m['per_class']:rows.append({'experiment_id':i,'region':g,'macro_f1':m['macro_f1'],**c})
            cm=np.asarray(r['test']['confusion_matrix'])-np.asarray(m['confusion_matrix']);v=metrics(cm)
            loo.append({'experiment_id':i,'omitted_region':g,'remaining_regions':2,'macro_f1':v['macro_f1_fixed_three_zero_division'],'high_f1':v['per_class'][2]['f1']})
    csvwrite('regional_failure_metrics.csv',rows);csvwrite('experiment_metrics.csv',pooled);csvwrite('leave_one_region_out.csv',loo)
    pred={i:loadcache(i)['pred'].ravel() for i in results};y=loadcache(next(iter(results)))['y'].ravel();valid=y!=-100;high=y==2
    similarities=[]
    for a,b in itertools.combinations(results,2):
        ea=(pred[a]!=y)&valid;eb=(pred[b]!=y)&valid;ha=(pred[a]!=2)&high;hb=(pred[b]!=2)&high
        similarities.append({'model_a':a,'model_b':b,'prediction_agreement':float((pred[a][valid]==pred[b][valid]).mean()),'error_jaccard':float((ea&eb).sum()/(ea|eb).sum()) if (ea|eb).any() else None,'high_miss_jaccard':float((ha&hb).sum()/(ha|hb).sum()) if (ha|hb).any() else None})
    csvwrite('error_similarity.csv',similarities)
    fig,axs=plt.subplots(5,4,figsize=(16,18))
    for ax,(i,r) in zip(axs.ravel(),results.items()):
        cm=np.asarray(r['test']['confusion_matrix']);norm=cm/cm.sum(1,keepdims=True)
        ax.imshow(norm,vmin=0,vmax=1,cmap='Blues')
        for a in range(3):
            for b in range(3):ax.text(b,a,f'{cm[a,b]:,}\n{norm[a,b]:.1%}',ha='center',va='center',fontsize=8,color='white' if norm[a,b]>.6 else 'black')
        ax.set_title(i,fontsize=10);ax.set_xticks(range(3),CLASSES);ax.set_yticks(range(3),CLASSES)
    fig.supxlabel('Predicted class');fig.supylabel('True class');fig.suptitle('Frozen v2 test confusion matrices (counts and row proportions)',y=1.01);fig.tight_layout();save(fig,'all_confusion_matrices.png')


def distributions(parts,results):
    pools={'Train':parts['train'],'Validation':parts['validation'],**{g:[r for r in parts['test'] if r['spatial_group_id']==g] for g in sorted({r['spatial_group_id'] for r in parts['test']})}}
    arrays={};labels={};names=list(BANDS)+list(INDEX_NAMES)
    for g,rows in pools.items():
        xx=[];yy=[]
        for r in rows:
            raw=np.load(r['sen2_path']);y=segmentation_target(np.load(r['cyan_path']));valid=y!=-100
            xx.append(np.concatenate([raw.astype(np.float32)/10000,spectral_indices(raw)])[...,valid].T);yy.append(y[valid])
        arrays[g]=np.concatenate(xx);labels[g]=np.concatenate(yy)
    rows=[];shifts=[];conditional=[]
    for g,x in arrays.items():
        for j,name in enumerate(names):
            v=x[:,j];v=v[np.isfinite(v)];q=np.quantile(v,[.05,.25,.5,.75,.95])
            rows.append({'pool':g,'feature':name,'n_finite':len(v),'n_undefined':len(x)-len(v),'mean':float(v.mean()),'std':float(v.std()),'q05':q[0],'q25':q[1],'median':q[2],'q75':q[3],'q95':q[4]})
            train=arrays['Train'][:,j];train=train[np.isfinite(train)];sd=max(float(train.std()),1e-8)
            if g not in ('Train','Validation'):
                shifts.append({'region':g,'feature':name,'standardized_mean_difference':float((v.mean()-train.mean())/sd),'wasserstein_train_sd':float(wasserstein_distance(train,v)/sd)})
                for c in range(3):
                    a=arrays['Train'][labels['Train']==c,j];b=x[labels[g]==c,j];a=a[np.isfinite(a)];b=b[np.isfinite(b)]
                    conditional.append({'region':g,'feature':name,'class':CLASSES[c],'train_n':len(a),'test_n':len(b),'standardized_mean_difference':float((b.mean()-a.mean())/max(a.std(),1e-8)) if len(a) and len(b) else None})
    csvwrite('spectral_summaries.csv',rows);csvwrite('spectral_shift.csv',shifts);csvwrite('class_conditional_spectral_shift.csv',conditional)
    gs=[g for g in pools if g not in ('Train','Validation')];scores={g:float(np.mean([abs(r['standardized_mean_difference']) for r in shifts if r['region']==g and r['feature'] in BANDS])) for g in gs}
    association={i:{'spearman_shift_vs_high_f1':float(spearmanr([scores[g] for g in gs],[r['test_groups'][g]['per_class'][2]['f1'] for g in gs]).statistic) if len(set(r['test_groups'][g]['per_class'][2]['f1'] for g in gs))>1 else None} for i,r in results.items()}
    write(OUT/'shift_association.json',{'mean_absolute_band_smd':scores,'model_associations':association,'n_regions':3,'inference':'descriptive ranks only; no p-values or causal claim'})
    fig,ax=plt.subplots(figsize=(13,4));matrix=np.array([[next(r['standardized_mean_difference'] for r in shifts if r['region']==g and r['feature']==n) for n in names] for g in gs]);im=ax.imshow(matrix,cmap='coolwarm',vmin=-2,vmax=2,aspect='auto');ax.set_xticks(range(17),names,rotation=45);ax.set_yticks(range(3),[short(g) for g in gs]);fig.colorbar(im,ax=ax,label='(Region mean - Train mean) / Train SD');ax.set_title('Spectral shift on valid reference pixels; color saturated at ±2 SD');save(fig,'spectral_shift.png')
    temporal=[];tvs={};months={};year_counts={}
    season={12:'DJF',1:'DJF',2:'DJF',3:'MAM',4:'MAM',5:'MAM',6:'JJA',7:'JJA',8:'JJA',9:'SON',10:'SON',11:'SON'}
    for g,rs in pools.items():
        months[g]=np.bincount([int(r['date'][5:7]) for r in rs],minlength=13)[1:];year_counts[g]={yr:sum(r['date'][:4]==yr for r in rs) for yr in ['2019','2020']}
        for unit,dates in [('patch',[r['date'] for r in rs]),('unique_date',sorted({r['date'] for r in rs}))]:
            for dim,keys,fn in [('month',list(range(1,13)),lambda d:int(d[5:7])),('season',['DJF','MAM','JJA','SON'],lambda d:season[int(d[5:7])]),('year',['2019','2020'],lambda d:d[:4])]:
                for key in keys:
                    count=sum(fn(d)==key for d in dates);temporal.append({'pool':g,'unit':unit,'dimension':dim,'value':key,'count':count,'proportion':count/len(dates),'total':len(dates)})
        if g not in ('Train','Validation'):
            tvs[g]={'patch_month_total_variation':float(np.abs(months[g]/months[g].sum()-months['Train']/months['Train'].sum()).sum()/2),'unique_dates':len({r['date'] for r in rs}),'years':year_counts[g],'months_observed':int((months[g]>0).sum())}
    csvwrite('temporal_distributions.csv',temporal);write(OUT/'temporal_shift.json',tvs)
    fig,ax=plt.subplots(figsize=(11,4))
    for g,v in months.items():ax.plot(range(1,13),v/v.sum(),marker='o',label=short(g))
    ax.set(xlabel='Acquisition month',ylabel='Fraction of patches',xticks=range(1,13),title='Temporal composition (patch-weighted; not independent observations)');ax.legend(fontsize=8);save(fig,'temporal_shift.png')


def calibrations(specs,parts):
    allcal={};rows=[];temps=read(OUT/'temperatures.json')
    for i,spec in specs.items():
        if spec['family'] in INDEX_NAMES:continue
        cache=loadcache(i);y=cache['y'];valid=y!=-100;allcal[i]={}
        selectors={'overall':np.ones(len(y),dtype=bool),**{g:np.array([r['spatial_group_id']==g for r in parts['test']]) for g in sorted({r['spatial_group_id'] for r in parts['test']})}}
        for mode,t in [('raw',1.)]+([('temperature',temps[i]['temperature'])] if neural(spec) else []):
            p=probabilities(cache,t);assert np.array_equal(p.argmax(-1),cache['pred'])
            allcal[i][mode]={}
            for g,sel in selectors.items():
                m=calibration(y[sel][valid[sel]],p[sel][valid[sel]]);allcal[i][mode][g]=m
                rows.append({'experiment_id':i,'mode':mode,'region':g,**{k:m[k] for k in ['n','accuracy','ece','nll','brier','high_ece','high_nll','high_brier','high_support','high_confidence_predictions','high_confidence_precision']}})
        fig,axes=plt.subplots(2,4,figsize=(15,7))
        for col,g in enumerate(selectors):
            for row,key in enumerate(['reliability_bins','high_reliability_bins']):
                ax=axes[row,col];ax.plot([0,1],[0,1],'--',c='gray')
                for mode,data in allcal[i].items():
                    bins=[v for v in data[g][key] if v['count']];ax.plot([v['confidence'] for v in bins],[v['frequency'] for v in bins],'.-',label=mode)
                ax.set(xlim=(0,1),ylim=(0,1),xlabel='Mean predicted probability',ylabel='Observed frequency',title=short(g)+(' — top label' if row==0 else ' — High one-v-rest'));ax.legend(fontsize=8)
        fig.suptitle(i+' | 15 equal-width bins; counts in calibration.json');fig.tight_layout();save(fig,f'calibration_{i}.png')
    write(OUT/'calibration.json',allcal);csvwrite('calibration_metrics.csv',rows)
    # Only this matched 272-pair pool supports random versus geographic comparison.
    plan=read('data/metadata/phase3/frozen_plan.json');samples=read('data/metadata/phase3/pilot_manifest.json')['samples'];matched={}
    for strategy in ('random','geographic'):
        rows=[r for r in samples if plan['splits'][strategy][r['sample_id']]=='test'];folder=Path('research_outputs/phase3_pilot')/strategy;norm=read(folder/'normalization.json');old=read(folder/'results.json');matched[strategy]={}
        for family in ('LogisticRegression','RandomForest','SmallSegCNN','DeepLabV3_ResNet18'):
            spec={'family':family,'path':str(folder/(family+('.pt' if family in ('SmallSegCNN','DeepLabV3_ResNet18') else '.joblib')))}
            cache=predict(spec,rows,norm);assert region_metrics(cache['y'],cache['pred'])['confusion_matrix']==old['models'][family]['test']['confusion_matrix']
            valid=cache['y']!=-100;matched[strategy][family]={'metrics':region_metrics(cache['y'],cache['pred']),'calibration':calibration(cache['y'][valid],probabilities(cache)[valid])}
    write(OUT/'matched_pilot_calibration.json',matched)


def lr_rf(parts):
    x,y,sampled=training_pixels(parts['train'],BASE);lr=joblib.load(OLD/'LogisticRegression.joblib');rf=joblib.load(OLD/'RandomForest.joblib');names=list(BANDS)+list(INDEX_NAMES)+[n+'_missing' for n in INDEX_NAMES]
    coefficients=lr.named_steps['logisticregression'].coef_;importance=rf.feature_importances_
    csvwrite('feature_importance_coefficients.csv',[{'feature':n,'rf_impurity_importance':importance[j],**{CLASSES[c]+'_standardized_logit_coefficient':coefficients[c,j] for c in range(3)},'high_minus_moderate_coefficient':coefficients[2,j]-coefficients[1,j]} for j,n in enumerate(names)])
    feature_rows=[]
    for pool,xx,yy in [('train_sample',x,y)]:
        for c in range(3):
            for j,n in enumerate(names):
                v=xx[yy==c,j];feature_rows.append({'pool':pool,'class':CLASSES[c],'feature':n,'n':len(v),'mean':float(v.mean()),'std':float(v.std()),'q10':float(np.quantile(v,.1)),'median':float(np.median(v)),'q90':float(np.quantile(v,.9))})
    csvwrite('training_feature_distributions.csv',feature_rows)
    tree_rows=[];leaf_rows=[];bootstrap=rf.estimators_samples_
    for k,tree in enumerate(rf.estimators_):
        t=tree.tree_;leaf=np.flatnonzero(t.children_left==-1);values=t.value[leaf,0];fraction=values/values.sum(1,keepdims=True);highleaf=np.argmax(fraction,axis=1)==2
        original_assignment=tree.apply(x);original_high_assignments=original_assignment[y==2]
        tree_rows.append({'tree':k,'depth':tree.get_depth(),'leaves':len(leaf),'high_majority_leaves':int(highleaf.sum()),'leaves_with_high_weight':int((fraction[:,2]>0).sum()),'bootstrap_high_count':int((y[bootstrap[k]]==2).sum()),'bootstrap_unique_high':int(len(np.unique(bootstrap[k][y[bootstrap[k]]==2]))),'maximum_leaf_high_fraction':float(fraction[:,2].max()),'original_high_in_high_majority_leaf':int(np.isin(original_high_assignments,leaf[highleaf]).sum())})
        for j,node in enumerate(leaf):leaf_rows.append({'tree':k,'node':int(node),'unique_in_bag_samples':int(t.n_node_samples[node]),'bootstrap_weighted_samples':float(t.weighted_n_node_samples[node]),'low_fraction':float(fraction[j,0]),'moderate_fraction':float(fraction[j,1]),'high_fraction':float(fraction[j,2]),'original_sample_high_in_leaf':int((original_high_assignments==node).sum())})
    csvwrite('rf_tree_diagnostics.csv',tree_rows);csvwrite('rf_leaf_composition.csv',leaf_rows)
    probsummary=[];curves=[];fig,axes=plt.subplots(2,3,figsize=(15,8));hist,ha=plt.subplots(2,3,figsize=(15,7))
    for family in ('LogisticRegression','RandomForest'):
        c=loadcache('baseline_'+family);valid=c['y']!=-100;yy=c['y'][valid];pp=c['prob'][valid]
        for cls in range(3):
            binary=yy==cls;fpr,tpr,_=roc_curve(binary,pp[:,cls]);pr,re,_=precision_recall_curve(binary,pp[:,cls]);auc=roc_auc_score(binary,pp[:,cls]);ap=average_precision_score(binary,pp[:,cls])
            axes[0,cls].plot(fpr,tpr,label=f'{family}: AUC={auc:.3f}');axes[1,cls].plot(re,pr,label=f'{family}: AP={ap:.3f}');axes[1,cls].axhline(binary.mean(),ls=':',c='gray')
            curves.append({'model':family,'class':CLASSES[cls],'roc_auc':float(auc),'average_precision':float(ap),'support':int(binary.sum())})
            q=pp[yy==cls,2];probsummary.append({'model':family,'true_class':CLASSES[cls],'n':len(q),'mean_high_probability':float(q.mean()),'q10':float(np.quantile(q,.1)),'median':float(np.median(q)),'q90':float(np.quantile(q,.9)),'fraction_high_argmax':float((pp[yy==cls].argmax(1)==2).mean())})
            row=0 if family=='LogisticRegression' else 1;ha[row,cls].hist(q,bins=np.linspace(0,1,31),weights=np.ones(len(q))/len(q),color=COLORS[cls]);ha[row,cls].set(title=f'{family} | true {CLASSES[cls]}',xlabel='P(High)',ylabel='Fraction of class pixels')
    for j in range(3):
        axes[0,j].plot([0,1],[0,1],':',c='gray');axes[0,j].set(title=CLASSES[j],xlabel='False positive rate',ylabel='True positive rate');axes[1,j].set(xlabel='Recall',ylabel='Precision')
        for a in axes[:,j]:a.legend(fontsize=8);a.set(xlim=(0,1),ylim=(0,1))
    fig.suptitle('LR versus RF: one-v-rest pooled v2 curves (descriptive, no threshold tuning)');fig.tight_layout();save(fig,'lr_rf_roc_pr.png');hist.tight_layout();save(hist,'lr_rf_high_probability_histograms.png');csvwrite('lr_rf_roc_pr_metrics.csv',curves);csvwrite('lr_rf_probability_summary.csv',probsummary)
    fig,axs=plt.subplots(1,2,figsize=(15,6));order=np.argsort(importance)[-12:];axs[0].barh(np.array(names)[order],importance[order]);axs[0].set_title('RF impurity importance (correlated-feature bias applies)');diff=coefficients[2]-coefficients[1];order=np.argsort(np.abs(diff))[-12:];axs[1].barh(np.array(names)[order],diff[order]);axs[1].set_title('LR High minus Moderate coefficients per training SD');fig.tight_layout();save(fig,'lr_rf_feature_effects.png')
    fig,axs=plt.subplots(2,4,figsize=(14,7))
    for ax,j in zip(axs.ravel(),[3,4,7,8,10,12,13,14]):
        ax.boxplot([x[y==c,j] for c in [1,2]],tick_labels=['Moderate','High'],showfliers=False);ax.set_title(names[j]);ax.set_ylabel('Scaled reflectance / index')
    fig.suptitle('Same training pixel pool: Moderate n=6224, High n=56; whiskers omit outliers');fig.tight_layout();save(fig,'high_moderate_feature_distributions.png')
    write(OUT/'lr_rf_diagnostics.json',{'same_training_pixels':sampled==read(OLD/'sampled_training_pixels.json'),'training_counts':np.bincount(y,minlength=3).tolist(),'tree_depth_range':[min(r['depth'] for r in tree_rows),max(r['depth'] for r in tree_rows)],'total_leaves':sum(r['leaves'] for r in tree_rows),'total_high_majority_leaves':sum(r['high_majority_leaves'] for r in tree_rows),'bootstrap_high_count_range':[min(r['bootstrap_high_count'] for r in tree_rows),max(r['bootstrap_high_count'] for r in tree_rows)],'rf_parameters':{k:rf.get_params()[k] for k in ['class_weight','max_depth','min_samples_leaf','n_estimators','max_features']},'lr_parameters':{k:lr.named_steps['logisticregression'].get_params()[k] for k in ['class_weight','C','max_iter','solver']}})


def robustness(specs,parts,results):
    selected=read(OUT/'selection.json')['cnn'];spec=specs[selected];model=load_model(spec);base=results[selected]['test'];ys=np.stack([segmentation_target(np.load(r['cyan_path'])) for r in parts['test']]);mean=np.asarray(NORM['mean'],np.float32)[:,None,None];std=np.asarray(NORM['std'],np.float32)[:,None,None];rows=[];regional_rows=[]
    for kind,levels in CFG['perturbations'].items():
        for level,severity in zip(('mild','moderate'),levels):
            pp=[];clipping=[];batch=[]
            with torch.inference_mode():
                for j,r in enumerate(parts['test']):
                    raw=np.load(r['sen2_path']).astype(np.float32)/10000;x,clip=perturb(raw,kind,severity,NORM['mean'],sample_seed(r['sample_id']));clipping.append(clip);batch.append((x-mean)/std)
                    if len(batch)==8 or j==len(parts['test'])-1:
                        pp.append(model(keep_bands(torch.from_numpy(np.stack(batch)),spec.get('bands',BANDS))).argmax(1).numpy());batch=[]
            pred=np.concatenate(pp);m=region_metrics(ys,pred)
            row={'experiment_id':selected,'kind':kind,'level':level,'parameter':severity,'original_macro_f1':base['macro_f1'],'perturbed_macro_f1':m['macro_f1'],'delta_macro_f1':m['macro_f1']-base['macro_f1'],'original_high_f1':base['per_class'][2]['f1'],'perturbed_high_f1':m['per_class'][2]['f1'],'delta_high_f1':m['per_class'][2]['f1']-base['per_class'][2]['f1'],'fraction_values_clipped':float(np.mean(clipping))};rows.append(row)
            for g,b in results[selected]['test_groups'].items():
                ids=[j for j,r in enumerate(parts['test']) if r['spatial_group_id']==g];v=region_metrics(ys[ids],pred[ids]);regional_rows.append({'experiment_id':selected,'region':g,'kind':kind,'level':level,'macro_f1':v['macro_f1'],'delta_macro_f1':v['macro_f1']-b['macro_f1'],'high_f1':v['per_class'][2]['f1'],'delta_high_f1':v['per_class'][2]['f1']-b['per_class'][2]['f1']})
            print('robustness',kind,level,round(m['macro_f1'],4),flush=True)
    csvwrite('robustness_metrics.csv',rows);csvwrite('robustness_by_region.csv',regional_rows)
    fig,ax=plt.subplots(figsize=(11,5));labels=[r['kind']+' '+r['level'] for r in rows];pos=np.arange(len(rows));ax.bar(pos-.2,[r['delta_macro_f1'] for r in rows],.4,label='Δ Macro F1');ax.bar(pos+.2,[r['delta_high_f1'] for r in rows],.4,label='Δ High F1');ax.axhline(0,c='black',lw=.6);ax.set_xticks(pos,labels,rotation=45,ha='right');ax.set_ylabel('Perturbed minus original F1');ax.set_title(selected+' | diagnostic CNN; failed selection guard');ax.legend();save(fig,'robustness.png')


def error_visualization(specs,parts):
    selected=read(OUT/'selection.json')['cnn'];cache=loadcache(selected);prob=probabilities(cache);y=cache['y'];pred=cache['pred'];confidence=prob.max(-1);records=[]
    categories=['correct_Low','correct_Moderate','correct_High','High_to_Moderate','High_to_Low','false_High','high_confidence_error'];cmap=ListedColormap(COLORS);cmap.set_bad('#D4D7DB');error_cmap=plt.get_cmap('Reds').copy();error_cmap.set_bad('#D4D7DB');confidence_cmap=plt.get_cmap('viridis').copy();confidence_cmap.set_bad('#D4D7DB')
    for g in sorted({r['spatial_group_id'] for r in parts['test']}):
        indices=[j for j,r in enumerate(parts['test']) if r['spatial_group_id']==g];fig,axes=plt.subplots(7,5,figsize=(15,23))
        for row,cat in enumerate(categories):
            candidates=[]
            for j in indices:
                masks=[(y[j]==c)&(pred[j]==c) for c in range(3)]+[(y[j]==2)&(pred[j]==1),(y[j]==2)&(pred[j]==0),(y[j]!=2)&(y[j]!=-100)&(pred[j]==2),(y[j]!=-100)&(y[j]!=pred[j])&(confidence[j]>=.8)]
                take=masks[row];candidates.append({'sample_id':parts['test'][j]['sample_id'],'index':j,'count':int(take.sum()),'confidence':float(confidence[j][take].mean()) if take.any() else 0.})
            chosen=select_example(candidates);records.append({'region':g,'category':cat,'selected':chosen})
            if chosen is None:
                for ax in axes[row]:ax.axis('off');ax.text(.5,.5,cat+'\nUNAVAILABLE',ha='center',va='center',fontsize=10,transform=ax.transAxes)
                continue
            j=chosen['index'];raw=np.load(parts['test'][j]['sen2_path']).astype(np.float32)/10000;rgb=np.moveaxis(np.clip(raw[[3,2,1]]/.2,0,1),0,-1)**(1/2.2);valid=y[j]!=-100
            axes[row,0].imshow(rgb);axes[row,1].imshow(np.ma.masked_where(~valid,y[j]),cmap=cmap,vmin=0,vmax=2,interpolation='nearest');axes[row,2].imshow(np.ma.masked_where(~valid,pred[j]),cmap=cmap,vmin=0,vmax=2,interpolation='nearest');axes[row,3].imshow(np.ma.masked_where(~valid,(pred[j]!=y[j]).astype(float)),cmap=error_cmap,vmin=0,vmax=1);axes[row,4].imshow(np.ma.masked_where(~valid,confidence[j]),cmap=confidence_cmap,vmin=0,vmax=1)
            axes[row,0].set_ylabel(cat.replace('_',' ')+'\n'+f"n={chosen['count']}, confidence={chosen['confidence']:.3f}",fontsize=9)
            for ax,title in zip(axes[row],['RGB (fixed 0–0.2 stretch)','Reference','Prediction','Error (red)','Confidence (0–1)']):ax.set_title(title,fontsize=9);ax.set_xticks([]);ax.set_yticks([])
        fig.suptitle(short(g)+' | '+selected+'\nLow=blue, Moderate=yellow, High=red, ignored=gray; IDs and selection scores in error_examples.json',fontsize=12);fig.tight_layout(rect=(0,0,1,.97));save(fig,'errors_'+short(g)+'.png')
    write(OUT/'error_examples.json',{'model':selected,'selection':'highest mean confidence on qualifying pixels, tie sample_id','records':records})


def explain(specs,parts):
    selected=read(OUT/'selection.json')['cnn'];spec=specs[selected];model=load_model(spec);records=[]
    for g in sorted({r['spatial_group_id'] for r in parts['test']}):
        rows=[r for r in parts['test'] if r['spatial_group_id']==g];r=min(rows,key=lambda r:(-int(r['high_pixels']),r['sample_id']));x,y=PatchDataset([r],NORM)[0];x=keep_bands(x[None],spec.get('bands',BANDS));mask=y.numpy()==2
        a32,m32=integrated_gradients(model,x,mask,steps=32);a,m=integrated_gradients(model,x,mask,steps=64);v=a[0].numpy();np.savez_compressed(OUT/f'ig_{short(g)}.npz',attribution=v,target_mask=mask)
        change=float((a-a32).abs().sum()/a.abs().sum().clamp_min(1e-8));channel=np.abs(v).sum((1,2));signed=v.sum((1,2));records.append({'region':g,'sample_id':r['sample_id'],'target_pixels':int(mask.sum()),'steps32':m32,'steps64':m,'relative_l1_change_32_to_64':change,'channel_absolute_sum':dict(zip(BANDS,channel.astype(float))),'channel_signed_sum':dict(zip(BANDS,signed.astype(float)))})
        raw=np.load(r['sen2_path']).astype(np.float32)/10000;rgb=np.moveaxis(np.clip(raw[[3,2,1]]/.2,0,1),0,-1)**(1/2.2);fig,axs=plt.subplots(1,4,figsize=(17,4));axs[0].imshow(rgb);axs[0].set_title('RGB');axs[1].imshow(mask,cmap='gray');axs[1].set_title('Fixed target: true High pixels');heat=v.sum(0);limit=max(float(np.abs(heat).max()),1e-8);im=axs[2].imshow(heat,cmap='coolwarm',vmin=-limit,vmax=limit);fig.colorbar(im,ax=axs[2],fraction=.046);axs[2].set_title('Signed IG, summed over bands');axs[3].bar(range(12),channel/channel.sum());axs[3].set_xticks(range(12),BANDS,rotation=90);axs[3].set_title('Absolute attribution share by band')
        for ax in axs[:3]:ax.set_xticks([]);ax.set_yticks([])
        fig.suptitle(short(g)+f' | mean High logit; relative completeness residual={m["relative_residual"]:.2%}');fig.tight_layout();save(fig,'ig_'+short(g)+'.png');print('IG',short(g),m['relative_residual'],flush=True)
    write(OUT/'integrated_gradients.json',{'model':selected,'target':'fixed true-High region mean High logit','baseline':'normalized zero = training per-band mean','records':records})


def main():
    torch.set_num_threads(4);torch.use_deterministic_algorithms(True);parts=context();specs=read(OUT/'specifications.json');results=read(OUT/'results.json')
    parser=argparse.ArgumentParser();parser.add_argument('--section',choices=['tables','calibration','visuals','all'],default='all');args=parser.parse_args()
    if args.section in ('tables','all'):regional(results);distributions(parts,results);lr_rf(parts);print('Regional/shift/LR-RF tables complete',flush=True)
    if args.section in ('calibration','all'):calibrations(specs,parts);print('Calibration complete',flush=True)
    if args.section in ('visuals','all'):robustness(specs,parts,results);error_visualization(specs,parts);explain(specs,parts)
if __name__=='__main__':main()

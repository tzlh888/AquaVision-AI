"""Publication assets derived only from frozen Phase4 arrays and metrics. No fitting."""
import csv,json,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch,Patch
from matplotlib.colors import ListedColormap

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research_outputs/figures';P4=ROOT/'research_outputs/phase4';P5=ROOT/'research_outputs/phase5'
MODELS=['baseline_NDCI','baseline_LogisticRegression','baseline_RandomForest','baseline_SmallSegCNN','baseline_DeepLabV3_ResNet18','deep_weighted']
LABELS=['NDCI','Logistic Regression','Random Forest','SmallSegCNN','DeepLabV3 / ResNet18','DeepLab + weighted CE']
C=['#247BA0','#E3AE3B','#B94640'];TRAIN='#306A93';TEST='#B56932';INK='#203348'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,'axes.labelsize':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','pdf.fonttype':42,'savefig.facecolor':'white','axes.axisbelow':True})
def read(p):return json.loads(Path(p).read_text())
def save(fig,name,title,source,caption):
    for ext in ('png','svg'):fig.savefig(OUT/f'{name}.{ext}',dpi=240,bbox_inches='tight',metadata={'Creator':'AquaVision AI: frozen-result packaging'})
    plt.close(fig);return {'name':name,'title':title,'source':source,'caption':caption,'png':f'research_outputs/figures/{name}.png','svg':f'research_outputs/figures/{name}.svg'}
def short(g):return g.split(':')[-1].replace('_S050','')
def tidy(ax):ax.grid(axis='y',color='#E5E9ED',lw=.7)
def main():
    OUT.mkdir(exist_ok=True,parents=True);P5.mkdir(exist_ok=True,parents=True)
    result=read(P4/'results.json');cal=read(P4/'calibration.json');split=read(ROOT/'data/metadata/phase3_5/geographic_split_v2.json');sel=read(P4/'selection.json');support=split['support'];records=[]
    testrows=[r for r in split['samples'] if split['assignments'][r['sample_id']]=='test'];groups=sorted({r['spatial_group_id'] for r in testrows})
    with (P4/'robustness_metrics.csv').open() as f:rob=list(csv.DictReader(f))
    # Selection-neutral main table, never sorted by Test score.
    table=[]
    for i,label in zip(MODELS,LABELS):
        v=result[i];status='Validation-selected; High failure' if i==sel['overall'] else ('Diagnostic CNN; failed guard' if i==sel['cnn'] else 'Comparator; not selected')
        table.append({'experiment_id':i,'Model':label,'Validation Macro F1':v['validation']['macro_f1'],'Validation High F1':v['validation']['per_class'][2]['f1'],'Geographic Macro F1':v['test']['macro_f1'],'Geographic High F1':v['test']['per_class'][2]['f1'],'ECE':cal.get(i,{}).get('raw',{}).get('overall',{}).get('ece'),'Robustness delta Macro F1':min(float(r['delta_macro_f1']) for r in rob) if i==sel['cnn'] else None,'Selection Status':status})
    (P5/'central_results.json').write_text(json.dumps(table,indent=2)+'\n')
    fig,ax=plt.subplots(figsize=(13.4,7.3));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    def box(x,y,w,h,title,body,fill='#F3F6F9',edge='#C5CFD9'):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.012,rounding_size=0.01',fc=fill,ec=edge,lw=1.0))
        ax.text(x+.018,y+h-.035,title,ha='left',va='top',fontsize=12,fontweight='bold',color=INK)
        ax.text(x+.018,y+h-.09,body,ha='left',va='top',fontsize=10,color='#344454',linespacing=1.5)
    def arrow(a,b):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=14,lw=1.4,color='#748493',connectionstyle='arc3'))
    ax.text(.02,.98,'AquaVision AI',fontsize=21,fontweight='bold',color=INK,va='top')
    ax.text(.02,.895,'Predictive ability and reliability across geographically unseen regions',fontsize=12,color='#52616F',va='top')
    box(.025,.63,.27,.20,'Paired satellite observations','Sentinel-2: 12 × 64 × 64 bands\nCyAN-derived mask: 64 × 64\nLow / Moderate / High; ignore flags')
    box(.36,.63,.27,.20,'Pixel-level segmentation','Spectral indices · LR · RF\nSmallSegCNN · DeepLabV3\nTrain-only preprocessing')
    box(.70,.63,.27,.20,'Evaluation discipline','Validation selection locked\nMacro F1 → High F1 + class guard\nNo Test-based model choice')
    arrow((.30,.73),(.35,.73));arrow((.64,.73),(.69,.73))
    box(.055,.35,.39,.21,'Random vs geographic pilot','Same 272-pair pool, two split strategies\nNeither Test partition contains High\nPilot cannot establish three-class transfer')
    box(.555,.35,.39,.21,'Frozen geographic benchmark v2','288 pairs: 96 Train / 48 Validation / 144 Test\n3 held-out regions · 37,768 High Test pixels\nClass support repaired before model comparison')
    arrow((.48,.62),(.26,.57));arrow((.53,.62),(.74,.57))
    box(.055,.055,.43,.19,'Reliability analysis','Regional failures · class imbalance · calibration\nMultispectral perturbations · band ablation\nSegmentation-targeted attribution')
    box(.555,.055,.39,.19,'LIMITED evidence','Predictive signal exists; stable three-class\ngeographic generalization is not established.\nSelected NDCI: validation High F1 = 0.',fill='#F9EFEB',edge='#C9826A')
    arrow((.25,.34),(.25,.26));arrow((.75,.34),(.44,.25));arrow((.50,.145),(.54,.145))
    records.append(save(fig,'project_overview','Research overview',['research_outputs/phase4/results.json','research_outputs/phase4/selection.json','data/metadata/phase3_5/split_support.csv'],'Paired observations feed segmentation; CyAN is a separate reference source, not a laboratory target. The matched pilot and v2 are distinct experiments, not comparable Test pools.'))
    # Native author-grid coordinates, explicitly not a basemap.
    plan=read(ROOT/'data/metadata/phase3_5/reference_screening_plan.json');selected={r['spatial_group_id']:split['assignments'][r['sample_id']] for r in split['samples']};colors={'train':TRAIN,'validation':'#AD7A27','test':'#AA443D','unselected':'#D9DFE5'}
    fig,axes=plt.subplots(1,5,figsize=(13,4.3),sharex=True,sharey=True)
    for ax,tile in zip(axes,['6_2','6_5','7_2','7_5','8_3']):
        for sid,g in plan['components'].items():
            if sid.startswith(tile+'_'):
                bits=sid.split('_');ax.scatter(int(bits[2][1:]),int(bits[3][1:]),marker='s',s=24,color=colors[selected.get(g,'unselected')],edgecolors='white',linewidths=.25)
        ax.set(title='CyAN tile '+tile,xlim=(-50,2050),ylim=(2050,-50),xlabel='Parent column');ax.set_aspect('equal')
    axes[0].set_ylabel('Parent row');fig.legend(handles=[Patch(color=colors[k],label=k.title()) for k in colors],loc='lower center',ncol=4,frameon=False,bbox_to_anchor=(.5,.055));fig.suptitle('Frozen v2 geographic grouping in the author grid',fontsize=15);fig.text(.5,.018,'Selected connected components stay in one partition across dates. This is not a latitude/longitude map.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.16,1,.95));records.append(save(fig,'final_geographic_split','Geographic split',['data/metadata/phase3_5/geographic_split_v2.json','data/metadata/phase3_5/reference_screening_plan.json'],'Native CyAN author-grid positions. Gray parents are not selected into v2. Exact lake boundaries and cross-tile nonoverlap remain unverified.'))
    fig,axes=plt.subplots(1,2,figsize=(10.7,4.1),gridspec_kw={'width_ratios':[1.5,1]});bottom=np.zeros(3)
    for c,key in enumerate(['low_pixels','moderate_pixels','high_pixels']):
        values=np.array([r[key]/r['valid_pixels'] for r in support])*100;axes[0].bar(range(3),values,bottom=bottom,color=C[c],label=['Low','Moderate','High'][c]);bottom+=values
    axes[0].set(xticks=range(3),xticklabels=['Train\n96 patches','Validation\n48 patches','Test\n144 patches'],ylabel='Valid reference pixels (%)',ylim=(0,100),title='Class composition');axes[0].legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,1.17),frameon=False)
    for j,r in enumerate(support):
        pct=100*r['high_pixels']/r['valid_pixels'];axes[1].bar(j,pct,color=C[2]);axes[1].text(j,pct+.2,f'{pct:.3f}%\nn={r["high_pixels"]:,}',ha='center',va='bottom',fontsize=9)
    axes[1].set(xticks=range(3),xticklabels=['Train','Validation','Test'],ylabel='High pixels (%)',ylim=(0,11),title='High support is deliberately enriched');tidy(axes[1]);fig.tight_layout();records.append(save(fig,'final_class_distribution','Class distribution',['data/metadata/phase3_5/split_support.csv'],'All valid pixels, not independent observations. Deliberate Test enrichment prevents natural-population precision or calibration claims.'))
    fig,axs=plt.subplots(1,2,figsize=(12,4.8),sharey=True);pos=np.arange(6)
    for ax,metric,title in zip(axs,['macro_f1','high'],'Macro F1|High F1'.split('|')):
        for offset,partition,color,label in [(-.18,'validation',TRAIN,'Validation'),(.18,'test',TEST,'Geographic Test')]:
            vals=[result[i][partition]['macro_f1'] if metric=='macro_f1' else result[i][partition]['per_class'][2]['f1'] for i in MODELS];bars=ax.barh(pos+offset,vals,.33,color=color,label=label)
            ax.bar_label(bars,fmt='%.3f',fontsize=8,padding=3)
        ax.set(yticks=pos,yticklabels=['NDCI [selected]','Logistic Regression','Random Forest','SmallSegCNN','DeepLabV3','DeepLab weighted [diagnostic]'],xlim=(0,.82),title=title);ax.grid(axis='x',color='#E5E9ED')
    axs[0].invert_yaxis();handles,labels=axs[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=2,frameon=False);fig.suptitle('Validation selection and Test observation are different claims',fontsize=14);fig.tight_layout(rect=(0,.07,1,.95));records.append(save(fig,'final_model_comparison','Central model comparison',['research_outputs/phase4/results.json','research_outputs/phase4/selection.json'],'Fixed model order, not ranked by Test. NDCI is selected despite zero validation High F1; the weighted CNN fails the class guard.'))
    fig,ax=plt.subplots(figsize=(10,4.4));ids=[MODELS[0],MODELS[1],MODELS[2],MODELS[5]];pos=np.arange(4)
    for j,g in enumerate(groups):
        vals=[result[i]['test_groups'][g]['per_class'][2]['f1'] for i in ids];bars=ax.bar(pos+(j-1)*.23,vals,.22,color=[TRAIN,'#83A9BA',TEST][j],label=short(g));ax.bar_label(bars,fmt='%.3f',padding=2,fontsize=8)
    ax.set(xticks=pos,xticklabels=['NDCI [selected]','Logistic Regression','Random Forest','DeepLab weighted\n[diagnostic]'],ylabel='High F1',ylim=(0,.72),title='High-class performance depends on the held-out region');tidy(ax);ax.legend(frameon=False,ncol=3,loc='upper center');fig.tight_layout();records.append(save(fig,'final_regional_high_f1','Per-region High F1',['research_outputs/phase4/results.json'],'Three observed component scores; no pixel bootstrap and no population confidence intervals.'))
    # One fixed-region attribution case selected in Phase4; do not cherry-pick anew.
    g=groups[1];ig=read(P4/'integrated_gradients.json');igrow=next(r for r in ig['records'] if r['region']==g);j=next(j for j,r in enumerate(testrows) if r['sample_id']==igrow['sample_id']);cache=np.load(P4/'deep_weighted_test.npz');y=cache['y'];pred=cache['pred'];z=cache['logits'].astype(float);z-=z.max(-1,keepdims=True);p=np.exp(z);p/=p.sum(-1,keepdims=True);conf=p.max(-1)
    cmap=ListedColormap(C);cmap.set_bad('#D5DADF');error=plt.get_cmap('Reds').copy();error.set_bad('#D5DADF');confidence=plt.get_cmap('viridis').copy();confidence.set_bad('#D5DADF')
    def maps(index):
        raw=np.load(ROOT/testrows[index]['sen2_path']).astype(float)/10000;valid=y[index]!=-100
        return [np.moveaxis(np.clip(raw[[3,2,1]]/.2,0,1),0,-1)**(1/2.2),np.ma.masked_where(~valid,y[index]),np.ma.masked_where(~valid,pred[index]),np.ma.masked_where(~valid,pred[index]!=y[index]),np.ma.masked_where(~valid,conf[index])]
    def draw(ax,v,k):
        kw={} if k==0 else {'cmap':cmap if k in [1,2] else error if k==3 else confidence,'vmin':0,'vmax':2 if k in [1,2] else 1}
        image=ax.imshow(v,interpolation='nearest',**kw);ax.set_xticks([]);ax.set_yticks([]);return image
    fig,axs=plt.subplots(2,3,figsize=(9.1,6.6));titles=['RGB composite','CyAN-derived reference','CNN prediction','Error on valid pixels','Uncalibrated confidence']
    for k,v in enumerate(maps(j)):
        im=draw(axs.ravel()[k],v,k);axs.ravel()[k].set_title(titles[k])
        if k==4:fig.colorbar(im,ax=axs.ravel()[k],fraction=.045,pad=.03)
    attr=np.load(P4/f'ig_{short(g)}.npz')['attribution'].sum(0);lim=np.abs(attr).max();im=axs[1,2].imshow(attr,cmap='coolwarm',vmin=-lim,vmax=lim);axs[1,2].set_title('Signed integrated gradients');axs[1,2].set_xticks([]);axs[1,2].set_yticks([]);fig.colorbar(im,ax=axs[1,2],fraction=.045,pad=.03)
    fig.suptitle('Diagnostic segmentation and attribution | '+short(g),fontsize=14);fig.text(.5,.012,'Low=blue · Moderate=gold · High=red · ignored=gray | IG completeness residual: 9.49%; not causal evidence',ha='center',fontsize=9);fig.tight_layout(rect=(0,.035,1,.96));records.append(save(fig,'final_segmentation_attribution','Segmentation and attribution',['research_outputs/phase4/integrated_gradients.json','research_outputs/phase4/deep_weighted_test.npz',testrows[j]['sen2_path']],f'Phase4 maximum-High-support attribution case in the LR/CNN worst-High-F1 region: {igrow["sample_id"]}. It was not selected for visual success. Target is fixed true-High-region mean High logit.'))
    fig,axs=plt.subplots(2,2,figsize=(9.6,6.4),gridspec_kw={'height_ratios':[2,1]},sharex=True)
    for col,i in enumerate(['baseline_LogisticRegression','deep_weighted']):
        for mode,color in [('raw',TRAIN),('temperature',TEST)]:
            if mode not in cal[i]:continue
            bins=cal[i][mode]['overall']['high_reliability_bins'];valid=[b for b in bins if b['count']];axs[0,col].plot([b['confidence'] for b in valid],[b['frequency'] for b in valid],'o-',ms=4,color=color,label=mode)
        bins=cal[i]['raw']['overall']['high_reliability_bins'];axs[1,col].bar([(b['lower']+b['upper'])/2 for b in bins],[b['count'] for b in bins],width=1/16,color='#A9BACA');axs[0,col].plot([0,1],[0,1],'--',c='gray',lw=1);axs[0,col].set(title='LR [not selected]' if col==0 else 'Weighted DeepLab [diagnostic]',ylim=(0,1));axs[0,col].legend(frameon=False);axs[1,col].set(xlabel='Predicted P(High)',xlim=(0,1));axs[1,col].ticklabel_format(axis='y',style='sci',scilimits=(3,3))
    axs[0,0].set_ylabel('Observed High frequency');axs[1,0].set_ylabel('Pixels per bin');fig.suptitle('High-class confidence reliability on the frozen geographic Test',fontsize=14);fig.tight_layout();records.append(save(fig,'final_calibration','High-class calibration',['research_outputs/phase4/calibration.json','research_outputs/phase4/temperatures.json'],'Fifteen equal-width bins; bottom panels show uncalibrated bin populations. Temperature uses Validation only and does not alter argmax. Pixel counts are correlated.'))
    fig,axs=plt.subplots(1,2,figsize=(11.5,4.1));kinds=list(dict.fromkeys(r['kind'] for r in rob));pos=np.arange(6)
    for ax,key,title in zip(axs,['delta_macro_f1','delta_high_f1'],['Change in Macro F1','Change in High F1']):
        for offset,level,color in [(-.18,'mild',TRAIN),(.18,'moderate',TEST)]:ax.bar(pos+offset,[float(next(r[key] for r in rob if r['kind']==k and r['level']==level)) for k in kinds],.34,color=color,label=level)
        ax.axhline(0,color='#566573',lw=.8);ax.set(xticks=pos,xticklabels=kinds,ylabel='Perturbed minus original',title=title);ax.tick_params(axis='x',rotation=30);tidy(ax)
    axs[0].legend(frameon=False);fig.suptitle('Fixed multispectral perturbations | diagnostic weighted DeepLab',fontsize=14);fig.tight_layout();records.append(save(fig,'final_robustness','Robustness',['research_outputs/phase4/robustness_metrics.csv'],'Twelve registered perturbations. Partial masking is artifact stress, not a cloud-physics model. Small deltas do not repair weak baseline performance.'))
    fig,ax=plt.subplots(figsize=(9.8,4.1));ids=['deep_weighted','ablation_rgb','ablation_visible_rededge_nir','ablation_compact_hab'];pos=np.arange(4)
    for offset,metric,color,label in [(-.18,'macro',TRAIN,'Test Macro F1'),(.18,'high',TEST,'Test High F1')]:
        vals=[result[i]['test']['macro_f1'] if metric=='macro' else result[i]['test']['per_class'][2]['f1'] for i in ids];bars=ax.bar(pos+offset,vals,.34,color=color,label=label);ax.bar_label(bars,fmt='%.3f',padding=3,fontsize=9)
    ax.set(xticks=pos,xticklabels=['All 12','RGB (3)','Visible + red-edge/NIR (8)','Compact HAB (4)'],ylim=(0,.61),ylabel='F1',title='Band ablation under the same short CNN training protocol');tidy(ax);ax.legend(frameon=False,ncol=2);fig.tight_layout();records.append(save(fig,'final_band_ablation','Band ablation',['research_outputs/phase4/results.json','research_outputs/phase4/specifications.json'],'All12 exceeds RGB in this run, but the 8-band variant has higher Macro F1. Single-seed two-epoch results do not establish a stable spectral advantage.'))
    examples=read(P4/'error_examples.json');cats=['High_to_Moderate','High_to_Low','false_High'];fig,axs=plt.subplots(3,5,figsize=(12,7.7));chosen=[]
    for row,cat in enumerate(cats):
        record=next(r for r in examples['records'] if r['region']==g and r['category']==cat);chosen.append(record);j=record['selected']['index']
        for k,v in enumerate(maps(j)):
            draw(axs[row,k],v,k)
            if row==0:axs[row,k].set_title(['RGB','Reference','Prediction','Error','Confidence (0–1)'][k])
        axs[row,0].set_ylabel(cat.replace('_',' ')+'\n'+f"qualifying n={record['selected']['count']}",fontsize=10)
    fig.suptitle('Deterministic failure examples | '+short(g),fontsize=14);fig.text(.5,.009,'Maximum mean confidence over qualifying pixels, selected in Phase4; examples do not estimate error frequency.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.025,1,.96));records.append(save(fig,'final_failure_examples','Failure examples',['research_outputs/phase4/error_examples.json','research_outputs/phase4/deep_weighted_test.npz'],'Three existing Phase4 extreme diagnostic cases in the worst High-F1 region. The whole patch need not belong to the named category.'))
    (P5/'figure_manifest.json').write_text(json.dumps({'core_figure_count':len(records),'figures':records,'attribution_sample_id':igrow['sample_id'],'failure_examples':chosen},indent=2)+'\n')
    assert len(records)==10
    print('Created 10 core figures, each PNG + SVG; no model inference or fitting.')
if __name__=='__main__':main()

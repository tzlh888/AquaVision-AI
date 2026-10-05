"""Phase 4 reliability primitives; prior evaluation modules remain immutable."""
import hashlib
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import logsumexp, softmax
from scipy.ndimage import gaussian_filter
import torch
import torch.nn.functional as F
from aquavision.evaluation.segmentation import metrics, confusion
from aquavision.features.spectral import BANDS


def balanced_weights(counts):
    counts=np.asarray(counts,dtype=float)
    if counts.shape!=(3,) or not np.isfinite(counts).all() or (counts<=0).any():
        raise ValueError('Three positive training counts required')
    return counts.sum()/(3*counts)


def balanced_sample_indices(y, seed=42):
    y=np.asarray(y)
    if len(y)%3 or set(np.unique(y))!={0,1,2}:raise ValueError('Three classes and total divisible by three required')
    rng=np.random.default_rng(seed); n=len(y)//3
    ids=np.concatenate([rng.choice(np.flatnonzero(y==c),n,replace=(y==c).sum()<n) for c in range(3)])
    return rng.permutation(ids)


def region_metrics(y,p):
    cm=confusion(y,p); m=metrics(cm); n=int(cm.sum())
    m['macro_f1']=m['macro_f1_fixed_three_zero_division']
    for i,c in enumerate(m['per_class']):
        c.update(tp=int(cm[i,i]),fp=int(cm[:,i].sum()-cm[i,i]),fn=int(cm[i].sum()-cm[i,i]),
                 true_proportion=float(cm[i].sum()/n) if n else None,
                 predicted_proportion=float(cm[:,i].sum()/n) if n else None)
    return m


def bins_summary(confidence, correct, bins=15):
    confidence=np.asarray(confidence,dtype=float); correct=np.asarray(correct,dtype=float)
    if confidence.shape!=correct.shape or not len(confidence):raise ValueError('Nonempty matching arrays required')
    ids=np.minimum((confidence*bins).astype(int),bins-1)
    out=[]; ece=0.
    for b in range(bins):
        take=ids==b; n=int(take.sum())
        avg=float(confidence[take].mean()) if n else None
        acc=float(correct[take].mean()) if n else None
        if n:ece+=n/len(ids)*abs(avg-acc)
        out.append({'lower':b/bins,'upper':(b+1)/bins,'count':n,'confidence':avg,'frequency':acc})
    return float(ece),out


def calibration(y, probabilities, bins=15):
    y=np.asarray(y,dtype=int); p=np.asarray(probabilities,dtype=float)
    if p.shape!=(len(y),3) or not np.isin(y,[0,1,2]).all() or not np.isfinite(p).all() or (p<0).any() or not np.allclose(p.sum(1),1,atol=1e-5):
        raise ValueError('Valid normalized probabilities and three-class labels required')
    if not len(y):raise ValueError('Empty calibration sample')
    pred=p.argmax(1); confidence=p.max(1); h=(y==2).astype(float)
    ece,rel=bins_summary(confidence,pred==y,bins); hece,hrel=bins_summary(p[:,2],h,bins)
    onehot=np.eye(3)[y]; clipped=np.clip(p,1e-12,1-1e-12)
    strong=(pred==2)&(confidence>=.8)
    return {'n':len(y),'accuracy':float((pred==y).mean()),'ece':ece,
      'brier':float(((p-onehot)**2).sum(1).mean()),'nll':float(-np.log(clipped[np.arange(len(y)),y]).mean()),
      'confidence_quantiles':np.quantile(confidence,[0,.1,.25,.5,.75,.9,1]).tolist(),
      'reliability_bins':rel,'high_ece':hece,'high_brier':float(((p[:,2]-h)**2).mean()),
      'high_nll':float(-(h*np.log(clipped[:,2])+(1-h)*np.log(1-clipped[:,2])).mean()),
      'high_reliability_bins':hrel,'high_support':int(h.sum()),'high_confidence_predictions':int(strong.sum()),
      'high_confidence_precision':float((y[strong]==2).mean()) if strong.any() else None}


def fit_temperature(logits,y,bounds=(.05,20.)):
    z=np.asarray(logits,dtype=np.float64); y=np.asarray(y,dtype=int)
    if z.shape!=(len(y),3) or not len(y) or not np.isfinite(z).all() or not np.isin(y,[0,1,2]).all():raise ValueError('Invalid logits/labels')
    def objective(log_t):
        scaled=z/np.exp(log_t)
        return float((logsumexp(scaled,axis=1)-scaled[np.arange(len(y)),y]).mean())
    result=minimize_scalar(objective,bounds=tuple(np.log(bounds)),method='bounded',options={'xatol':1e-7})
    candidates=[(objective(0.),1.),(objective(np.log(bounds[0])),bounds[0]),(objective(np.log(bounds[1])),bounds[1]),(float(result.fun),float(np.exp(result.x)))]
    loss,t=min(candidates)
    return {'temperature':t,'validation_nll_before':objective(0.),'validation_nll_after':loss,
            'at_bound':bool(np.isclose(t,bounds[0]) or np.isclose(t,bounds[1])),'fit_partition':'validation'}


def keep_bands(x,names):
    if not names or len(set(names))!=len(names) or any(n not in BANDS for n in names):raise ValueError('Unknown/duplicate/empty band selection')
    channel_axis=1 if x.ndim==4 else 0
    if x.shape[channel_axis]!=12:raise ValueError('Expected 12 channels')
    out=x.clone() if isinstance(x,torch.Tensor) else np.array(x,copy=True)
    missing=[i for i,n in enumerate(BANDS) if n not in names]
    if x.ndim==4:out[:,missing]=0
    else:out[missing]=0
    return out


def perturb(raw,kind,severity,training_mean,seed=42):
    """Reflectance C,H,W, shared spectral transforms; raw input is not mutated."""
    x=np.asarray(raw,dtype=np.float32)
    if x.ndim!=3 or x.shape[0]!=12 or not np.isfinite(x).all():raise ValueError('Expected finite 12-band reflectance')
    rng=np.random.default_rng(seed)
    if kind=='brightness':out=x*severity
    elif kind=='contrast':
        center=x.mean((1,2),keepdims=True);out=center+severity*(x-center)
    elif kind=='noise':out=x+rng.normal(0,severity,size=(1,*x.shape[1:])).astype(np.float32)
    elif kind=='blur':out=gaussian_filter(x,sigma=(0,severity,severity),mode='reflect')
    elif kind=='resolution':
        small=F.interpolate(torch.from_numpy(x)[None],size=(int(severity),int(severity)),mode='bilinear',align_corners=False,antialias=True)
        out=F.interpolate(small,size=x.shape[1:],mode='bilinear',align_corners=False,antialias=True)[0].numpy()
    elif kind=='mask':
        out=x.copy(); h,w=x.shape[1:];size=max(1,int(round(np.sqrt(severity*h*w))))
        top=(h-size)//2;left=(w-size)//2
        out[:,top:top+size,left:left+size]=np.asarray(training_mean)[:,None,None]
    else:raise ValueError('Unknown perturbation')
    fraction=float(((out<0)|(out>1.5)).mean())
    return np.clip(out,0,1.5).astype(np.float32),fraction


def sample_seed(sample_id):
    return int.from_bytes(hashlib.sha256(sample_id.encode()).digest()[:4],'big')^42


def choose_models(validation,neural_ids,low_floor=.5,moderate_floor=.25):
    def rank(k):
        m=validation[k];return (-m['macro_f1'],-(m['per_class'][2]['f1'] or 0),k)
    eligible=[k for k,m in validation.items() if (m['per_class'][0]['f1'] or 0)>=low_floor and (m['per_class'][1]['f1'] or 0)>=moderate_floor]
    neural=[k for k in eligible if k in neural_ids]
    return {'overall':min(eligible,key=rank) if eligible else None,
            'cnn':min(neural or list(neural_ids),key=rank),'cnn_eligible':bool(neural),
            'eligible':sorted(eligible),'ranking':sorted(validation,key=rank)}


def select_example(candidates):
    """Input records carry ID, qualifying pixel count, and mean confidence."""
    eligible=[c for c in candidates if c['count']>0]
    return min(eligible,key=lambda c:(-c['confidence'],c['sample_id'])) if eligible else None


def integrated_gradients(model,x,target_mask,target_class=2,steps=32):
    """Attribute fixed-region mean logit against normalized-zero baseline."""
    model.eval();mask=torch.as_tensor(target_mask,dtype=x.dtype,device=x.device)
    if not bool(mask.any()) or steps<1:raise ValueError('Nonempty fixed target region and positive steps required')
    total=torch.zeros_like(x)
    def scalar(z):return (model(z)[0,target_class]*mask).sum()/mask.sum()
    for k in range(steps+1):
        z=(x.detach()*(k/steps)).requires_grad_(True)
        g=torch.autograd.grad(scalar(z),z)[0]
        total+=g*(.5 if k in (0,steps) else 1.)
    attribution=x.detach()*total/steps
    with torch.no_grad():delta=float(scalar(x)-scalar(torch.zeros_like(x)))
    residual=float(attribution.sum())-delta
    return attribution.detach(),{'steps':steps,'target_logit_delta':delta,'attribution_sum':float(attribution.sum()),'completeness_residual':residual,'relative_residual':abs(residual)/max(abs(delta),1e-8)}

import numpy as np
import pytest
import torch
from aquavision.evaluation.reliability import (balanced_weights,balanced_sample_indices,calibration,fit_temperature,keep_bands,perturb,region_metrics,choose_models,select_example,integrated_gradients,sample_seed)
from aquavision.models.segmentation import masked_loss
from scipy.special import softmax


def test_inverse_frequency_weights():
    c=np.array([100,20,2]);w=balanced_weights(c)
    np.testing.assert_allclose(w*c,np.repeat(c.sum()/3,3))
    with pytest.raises(ValueError):balanced_weights([1,0,2])


def test_balancing_same_pool_reproducible():
    y=np.array([0]*20+[1]*8+[2]*2);i=balanced_sample_indices(y)
    np.testing.assert_array_equal(i,balanced_sample_indices(y))
    np.testing.assert_array_equal(np.bincount(y[i]),[10,10,10])
    assert len(np.unique(i[y[i]==2]))==2
    assert np.isin(i,np.arange(len(y))).all()


def test_weighted_ce_matches_torch_and_ignores():
    z=torch.tensor([[[[2.,1.]],[[0.,0.]],[[1.,2.]]]],requires_grad=True);y=torch.tensor([[[0,-100]]]);w=torch.tensor([.5,1.,3.])
    assert torch.allclose(masked_loss(z,y,class_weights=w),torch.nn.functional.cross_entropy(z,y,weight=w,ignore_index=-100))
    masked_loss(z,y,class_weights=w).backward();assert z.grad[:,:,:,1].abs().sum()==0


def test_focal_formula_and_gamma_zero():
    z=torch.tensor([[[[2.]],[[0.]],[[1.]]]]);y=torch.tensor([[[0]]])
    ce=masked_loss(z,y)
    assert torch.allclose(masked_loss(z,y,focal_gamma=0),ce)
    assert torch.allclose(masked_loss(z,y,focal_gamma=2),(1-torch.exp(-ce))**2*ce)
    assert masked_loss(z,torch.full_like(y,-100),focal_gamma=2)==0


def test_calibration_perfect_and_uniform():
    y=np.array([0,1,2]);perfect=calibration(y,np.eye(3));assert perfect['ece']==0 and perfect['brier']==0
    uniform=calibration(y,np.ones((3,3))/3)
    assert uniform['nll']==pytest.approx(np.log(3));assert uniform['brier']==pytest.approx(2/3)
    assert uniform['ece']==pytest.approx(0);assert uniform['high_confidence_precision'] is None
    assert sum(b['count'] for b in perfect['reliability_bins'])==3
    with pytest.raises(ValueError):calibration(y,np.ones((3,3)))


def test_temperature_validation_nll_and_argmax():
    z=np.array([[8,0,0],[8,0,0],[0,8,0],[0,0,8]],float);y=np.array([0,1,1,2])
    t=fit_temperature(z,y)
    assert t['fit_partition']=='validation' and t['validation_nll_after']<=t['validation_nll_before']
    np.testing.assert_array_equal(softmax(z/t['temperature'],axis=1).argmax(1),z.argmax(1))


def test_band_mapping_preserves_selected_and_input():
    x=torch.ones(2,12,4,4);out=keep_bands(x,['B02','B03','B04'])
    assert out[:,[1,2,3]].sum()==96 and out.sum()==96 and x.sum()==384
    with pytest.raises(ValueError):keep_bands(x,['B10'])


@pytest.mark.parametrize('kind,severity',[('brightness',1.05),('contrast',1.15),('noise',.005),('blur',1.),('resolution',32),('mask',.15)])
def test_perturbations_finite_bounded_reproducible(kind,severity):
    x=np.ones((12,64,64),np.float32)*.2;x[:,20:30,20:30]=.4
    before=x.copy();a,f=perturb(x,kind,severity,np.ones(12)*.1);b,_=perturb(x,kind,severity,np.ones(12)*.1)
    np.testing.assert_array_equal(x,before);np.testing.assert_array_equal(a,b)
    assert a.shape==x.shape and np.isfinite(a).all() and a.min()>=0 and a.max()<=1.5 and 0<=f<=1
    np.testing.assert_allclose(a[0],a[-1])


def test_regional_failure_counts():
    m=region_metrics([0,1,2,2,-100],[0,2,1,2,0]);h=m['per_class'][2]
    assert (h['tp'],h['fp'],h['fn'])==(1,1,1);assert h['true_proportion']==.5


def test_selection_guard_and_no_test_argument():
    good=region_metrics([0,1,2],[0,1,2]);bad=region_metrics([0,1,2],[2,2,2])
    s=choose_models({'good':good,'cnn':bad},{'cnn'})
    assert s['overall']=='good' and s['cnn']=='cnn' and not s['cnn_eligible']


def test_example_deterministic_and_missing():
    a={'sample_id':'a','count':3,'confidence':.9};b={'sample_id':'b','count':4,'confidence':.9}
    assert select_example([b,a])==a and select_example([]) is None
    assert sample_seed('a')==sample_seed('a')!=sample_seed('b')


def test_integrated_gradients_linear_completeness():
    model=torch.nn.Conv2d(12,3,1,bias=False);model.weight.data.fill_(.1)
    a,m=integrated_gradients(model,torch.ones(1,12,2,2),np.ones((2,2)),steps=4)
    assert abs(m['completeness_residual'])<1e-6
    assert float(a.sum())==pytest.approx(1.2)


def test_registered_phase4_no_test_selection_or_temperature_fit():
    import json
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    out=root/'research_outputs/phase4'
    if not (out/'results.json').exists():pytest.skip('Requires completed registered real-data experiment')
    results=json.loads((out/'results.json').read_text());specs=json.loads((out/'specifications.json').read_text());selection=json.loads((out/'selection.json').read_text())
    candidates={k:v['validation'] for k,v in results.items() if specs[k]['variant']!='band_ablation'}
    neural_ids={k for k in candidates if specs[k]['family'] in ['SmallSegCNN','DeepLabV3_ResNet18']}
    got=choose_models(candidates,neural_ids)
    assert all(selection[k]==v for k,v in got.items())
    assert all(t['fit_partition']=='validation' for t in json.loads((out/'temperatures.json').read_text()).values())
    assert selection['selected_utc']<json.loads((out/'test_evaluation_start.json').read_text())['started_utc']


def test_registration_and_frozen_files_unchanged():
    import hashlib,json
    from pathlib import Path
    root=Path(__file__).resolve().parents[1];path=root/'data/metadata/phase4/preservation_manifest.json'
    if not path.exists():pytest.skip('Requires local frozen benchmark')
    for p,h in json.loads(path.read_text())['files'].items():assert hashlib.sha256((root/p).read_bytes()).hexdigest()==h,p
    reg=json.loads((root/'data/metadata/phase4/preregistration.json').read_text())
    for key,p in [('config_sha256','configs/phase4.json'),('protocol_sha256','research_outputs/reports/MODEL_SELECTION_PROTOCOL.md'),('split_sha256','data/metadata/phase3_5/geographic_split_v2.json')]:
        assert hashlib.sha256((root/p).read_bytes()).hexdigest()==reg[key]


def test_region_sums_equal_pooled_results():
    import json
    from pathlib import Path
    path=Path(__file__).resolve().parents[1]/'research_outputs/phase4/results.json'
    if not path.exists():pytest.skip('Requires completed experiment')
    for m in json.loads(path.read_text()).values():
        np.testing.assert_array_equal(np.sum([v['confusion_matrix'] for v in m['test_groups'].values()],axis=0),m['test']['confusion_matrix'])

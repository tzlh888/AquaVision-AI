import numpy as np
import pytest
import torch
from aquavision.data.labels import segmentation_target, IGNORE_INDEX
from aquavision.features.spectral import spectral_indices
from aquavision.evaluation.segmentation import confusion, metrics
from aquavision.models.segmentation import SmallSegCNN, masked_loss, deep_lab


def test_exhaustive_byte_mapping():
    x=np.arange(256,dtype=np.uint8).reshape(16,16)
    expected=np.array([0]*100+[1]*100+[2]*54+[IGNORE_INDEX]*2).reshape(16,16)
    y=segmentation_target(x)
    np.testing.assert_array_equal(y,expected)
    np.testing.assert_array_equal(segmentation_target(x[None]),expected)
    assert y.dtype==np.int64 and x[15,15]==255

@pytest.mark.parametrize('dn,c',[(0,0),(1,0),(99,0),(100,1),(101,1),(199,1),(200,2),(201,2),(253,2),(254,-100),(255,-100)])
def test_boundaries(dn,c):
    assert segmentation_target([[dn]])[0,0]==c


def test_invalid_reference():
    assert (segmentation_target([[np.nan,np.inf,-1,256,1.5]])==IGNORE_INDEX).all()
    with pytest.raises(ValueError): segmentation_target(np.ones((2,4,4)))
    with pytest.raises(ValueError): segmentation_target([[1j]])


def test_indices_formula_and_no_integer_overflow():
    x=np.ones((12,2,2),dtype=np.uint16)*1000
    x[4]=3000; x[7]=5000; x[8]=4000; x[10]=6000
    y=spectral_indices(x)
    np.testing.assert_allclose(y[:,0,0],[.5,2/3,.4-(.1+.5*200/945),.6,0],atol=1e-6)
    assert np.isnan(spectral_indices(np.zeros((12,1,1)))[0,0,0])


def test_metrics_ignore_absent_class():
    cm=confusion(np.array([0,1,IGNORE_INDEX]),np.array([0,0,2]))
    assert cm.sum()==2
    m=metrics(cm)
    assert m['per_class'][2]['recall'] is None
    assert m['per_class'][2]['f1'] is None
    assert m['macro_f1_fixed_three_zero_division']==pytest.approx(2/9)


def test_small_segmentation_and_gradient_ignore():
    torch.set_num_threads(2)
    model=SmallSegCNN(); x=torch.ones(2,12,16,16)
    logits=model(x); assert logits.shape==(2,3,16,16)
    target=torch.zeros(2,16,16,dtype=torch.long); target[:,:,0]=IGNORE_INDEX
    logits.retain_grad(); loss=masked_loss(logits,target); loss.backward()
    assert (logits.grad[:,:,:,0]==0).all()
    assert any(p.grad is not None and p.grad.abs().sum()>0 for p in model.parameters())
    assert masked_loss(logits,torch.full_like(target,IGNORE_INDEX)).item()==0


def test_deep_multispectral_output():
    torch.set_num_threads(2)
    model=deep_lab().eval()
    assert model.encoder.conv1.in_channels==12
    with torch.inference_mode(): assert model(torch.zeros(2,12,64,64)).shape==(2,3,64,64)


def test_weighted_focal_are_optional_and_finite():
    logits=torch.tensor([[[[2.]],[[0.]],[[1.]]]],requires_grad=True)
    y=torch.tensor([[[0]]])
    plain=masked_loss(logits,y)
    assert torch.allclose(plain,masked_loss(logits,y,focal_gamma=0))
    assert masked_loss(logits,y,focal_gamma=2)<plain
    assert torch.isfinite(masked_loss(logits,y,class_weights=torch.ones(3)))


def test_training_batches_cover_every_patch_without_singletons():
    from aquavision.data.segmentation_dataset import merge_singleton_batches
    for n in (2,8,9,17,217):
        batches=merge_singleton_batches(n,8,seed=42)
        assert sorted(i for batch in batches for i in batch)==list(range(n))
        assert all(len(batch)>=2 for batch in batches)
        assert batches==merge_singleton_batches(n,8,seed=42)


def test_normalization_uses_only_supplied_training_rows(tmp_path):
    from aquavision.data.segmentation_dataset import training_normalization
    paths=[]
    for i,v in enumerate((1000,3000,60000)):
        p=tmp_path/f'{i}.npy'; np.save(p,np.full((12,64,64),v,dtype=np.uint16))
        paths.append({'sample_id':str(i),'sen2_path':str(p)})
    stats=training_normalization(paths[:2])
    np.testing.assert_allclose(stats['mean'],.2)
    np.testing.assert_allclose(stats['std'],.1)
    assert stats['training_sample_ids']==['0','1']

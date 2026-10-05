"""Explicit small CNN and source-supported DeepLabV3/ResNet18, all 12 bands."""
import torch
from torch import nn
import torch.nn.functional as F
from aquavision.data.labels import IGNORE_INDEX


class SmallSegCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(nn.Conv2d(12,16,3,padding=1), nn.ReLU(),
                                     nn.MaxPool2d(2), nn.Conv2d(16,32,3,padding=1), nn.ReLU())
        self.decoder = nn.Sequential(nn.Conv2d(32,16,3,padding=1), nn.ReLU(), nn.Conv2d(16,3,1))

    def forward(self,x):
        z = self.encoder(x)
        z = F.interpolate(z, size=x.shape[-2:], mode='bilinear', align_corners=False)
        return self.decoder(z)


def deep_lab():
    # Matches author functions.load_model; no downloaded pretrained RGB weights.
    import segmentation_models_pytorch as smp
    return smp.DeepLabV3(encoder_name='resnet18', encoder_weights=None, in_channels=12, classes=3)


def masked_loss(logits, target, *, class_weights=None, focal_gamma=None):
    valid = target != IGNORE_INDEX
    if not valid.any():
        return logits.sum()*0  # finite, differentiable zero for fully masked batches
    loss = F.cross_entropy(logits, target, ignore_index=IGNORE_INDEX, reduction='none')
    if focal_gamma is not None:
        if focal_gamma < 0:
            raise ValueError('Negative focal gamma')
        loss = loss*(1-torch.exp(-loss))**focal_gamma
    if class_weights is not None:
        weights = class_weights[target[valid]]
        return (loss[valid]*weights).sum()/weights.sum().clamp_min(1e-12)
    return loss[valid].mean()

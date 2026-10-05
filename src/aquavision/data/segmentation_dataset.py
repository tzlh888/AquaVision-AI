"""Lazy real patches; normalization derived exclusively from training inputs."""
import hashlib
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import Dataset
from .labels import segmentation_target
from .loader import load_pair


def verify_samples(rows):
    for row in rows:
        for kind in ('sen2','cyan'):
            if hashlib.sha256(Path(row[kind+'_path']).read_bytes()).hexdigest() != row[kind+'_sha256']:
                raise ValueError('Data hash mismatch: '+row['sample_id'])


def training_normalization(rows):
    if not rows:
        raise ValueError('No training rows')
    total = np.zeros(12, dtype=np.float64)
    total2 = total.copy()
    n = 0
    for row in rows:
        raw = np.load(row['sen2_path'], allow_pickle=False).astype(np.float64)/10000
        if raw.shape != (12,64,64) or not np.isfinite(raw).all():
            raise ValueError('Invalid input')
        total += raw.sum((1,2)); total2 += (raw*raw).sum((1,2)); n += 4096
    mean = total/n
    std = np.maximum(np.sqrt(np.maximum(total2/n-mean**2,0)),1e-6)
    return {'mean':mean.tolist(),'std':std.tolist(),'training_sample_ids':sorted(r['sample_id'] for r in rows)}


class PatchDataset(Dataset):
    def __init__(self,rows,normalization):
        self.rows = rows
        self.mean = np.asarray(normalization['mean'], dtype=np.float32)[:,None,None]
        self.std = np.asarray(normalization['std'], dtype=np.float32)[:,None,None]

    def __len__(self):
        return len(self.rows)

    def __getitem__(self,i):
        x,y = load_pair(Path(self.rows[i]['sen2_path']), Path(self.rows[i]['cyan_path']))
        return torch.from_numpy((x.astype(np.float32)/10000-self.mean)/self.std), torch.from_numpy(segmentation_target(y))


def merge_singleton_batches(length, batch_size, *, seed):
    """Deterministic full-coverage batches; DeepLab global-pool BN needs N>=2."""
    if length < 2 or batch_size < 2:
        raise ValueError('Training BatchNorm needs at least two samples')
    ids = np.random.default_rng(seed).permutation(length).tolist()
    batches = [ids[i:i+batch_size] for i in range(0, length, batch_size)]
    if len(batches)>1 and len(batches[-1])==1:
        batches[-2].extend(batches.pop())
    return batches

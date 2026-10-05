"""Paper equations (6)-(10), DOI 10.1109/JSTARS.2025.3629586.

Author band order excludes B10. Raw pre-2022 L2A DN is divided by 10,000 as
in author functions.handle_input_transform. Nominal wavelengths 665/865/1610
nm approximate MSI B4/B8A/B11; spacecraft-specific response is unavailable.
"""
import numpy as np

BANDS = ('B01','B02','B03','B04','B05','B06','B07','B08','B8A','B09','B11','B12')
INDEX_NAMES = ('NDCI','NDVI','FAI','B8AB4','B3B2')


def spectral_indices(raw):
    x = np.asarray(raw, dtype=np.float32)/10000
    if x.ndim != 3 or x.shape[0] != 12 or not np.isfinite(x).all():
        raise ValueError('Expected finite 12xHxW multispectral input')
    def nd(a,b):
        denominator = a+b
        return np.divide(a-b, denominator, out=np.full_like(a, np.nan), where=np.abs(denominator)>1e-8)
    blue, green, red, re, nir, nir_narrow, swir = x[1],x[2],x[3],x[4],x[7],x[8],x[10]
    return np.stack([nd(re,red), nd(nir,red),
                     nir_narrow-(red+(swir-red)*(865-665)/(1610-665)),
                     nd(nir_narrow,red), nd(green,blue)])


def pixel_features(raw):
    """Undefined indices become zero plus explicit missing indicators; 22 features."""
    indices = spectral_indices(raw)
    return np.concatenate([np.asarray(raw,dtype=np.float32)/10000,
                           np.nan_to_num(indices, nan=0.0), (~np.isfinite(indices)).astype(np.float32)])

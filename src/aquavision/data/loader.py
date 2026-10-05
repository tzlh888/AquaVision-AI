"""Decode stored NPY arrays without pickle, rescaling, reordering, or relabeling."""

from pathlib import Path

import numpy as np

BANDS = ("B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B11", "B12")


def load_pair(sen2_path: Path, cyan_path: Path) -> tuple[np.ndarray, np.ndarray]:
    if any(p.stat().st_size > 2_000_000 for p in (sen2_path, cyan_path)):
        raise ValueError("Unexpectedly large sample")
    # mmap inspects headers without allocating an arbitrary claimed array size.
    image = np.load(sen2_path, allow_pickle=False, mmap_mode="r")
    reference = np.load(cyan_path, allow_pickle=False, mmap_mode="r")
    if image.shape != (12, 64, 64):
        raise ValueError(f"Unexpected Sentinel-2 shape: {image.shape}")
    if reference.shape != (1, 64, 64):
        raise ValueError(f"Unexpected CyAN reference shape: {reference.shape}")
    if image.dtype != np.dtype("uint16") or reference.dtype != np.dtype("uint8"):
        raise ValueError(f"Unexpected stored dtypes: {image.dtype}, {reference.dtype}")
    return image, reference

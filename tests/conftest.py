"""Synthetic fixtures live only in tests; never use them as research observations."""

import io
import zipfile

import numpy as np
import pytest


@pytest.fixture
def synthetic_pair(tmp_path):
    image = np.arange(12 * 64 * 64, dtype=np.uint16).reshape(12, 64, 64)
    reference = np.zeros((1, 64, 64), dtype=np.uint8)
    reference[0, 0, :8] = [0, 99, 100, 199, 200, 253, 254, 255]
    image_path, reference_path = tmp_path / "synthetic_sen2.npy", tmp_path / "synthetic_cyan.npy"
    np.save(image_path, image)
    np.save(reference_path, reference)
    return image_path, reference_path


@pytest.fixture
def synthetic_zip(synthetic_pair):
    data = io.BytesIO()
    prefix = "6_2/6_2_X0650_Y0900_S050_2019_04_19_x0_y512_64x64_5"
    with zipfile.ZipFile(data, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for kind, path in zip(("sen2", "cyan"), synthetic_pair, strict=True):
            archive.writestr(f"{prefix}_{kind}.npy", path.read_bytes())
    return data.getvalue()

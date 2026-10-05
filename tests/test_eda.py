"""EDA failure gates use synthetic manifests in temporary test directories."""

import json

import pytest

from aquavision.data.eda import inspect_sample


def test_eda_rejects_empty_sample(tmp_path):
    manifest = tmp_path / "synthetic_manifest.json"
    manifest.write_text(json.dumps({"samples": []}))
    with pytest.raises(ValueError, match="No real samples"):
        inspect_sample(manifest, tmp_path, tmp_path / "output")


def test_eda_rejects_tampered_sample(tmp_path):
    image = tmp_path / "synthetic.npy"
    image.write_bytes(b"synthetic_corrupted_bytes")
    manifest = tmp_path / "synthetic_manifest.json"
    manifest.write_text(json.dumps({"samples": [{"sen2_path": "synthetic.npy", "sen2_sha256": "wrong"}],
        "config": {"reference": {"diagnostic_bin_edges": [100, 200], "units": "processed_cyan_digital_number"}}}))
    with pytest.raises(ValueError, match="hash mismatch"):
        inspect_sample(manifest, tmp_path, tmp_path / "output")

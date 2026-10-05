"""Restore bounded primary-source snapshots; never execute downloaded code."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

SHA = "e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37"
BASE = f"https://raw.githubusercontent.com/cschloer/hab_detection_s2/{SHA}/"


def source_urls():
    urls = {
        "zenodo_record.json": "https://zenodo.org/api/records/14230064",
        "github_tree.json": f"https://api.github.com/repos/cschloer/hab_detection_s2/git/trees/{SHA}?recursive=1",
        "paper.pdf": "https://elib.dlr.de/219745/1/Harmful_Cyanobacterial_Bloom_Detection_using_Deep_Learning_and_Sentinel-2_Imagery.pdf",
        "nasa_cyan.html": "https://oceancolor.gsfc.nasa.gov/about/projects/cyan/",
    }
    for name in ["code/README.md", "code/dataset/README.md", "code/constants.py", "code/dataset/create_dataset.py",
                 "code/dataset/download_and_process.py", "code/dataset/archive.py", "code/dataset/generate_tiles.py",
                 "code/dataset/helpers.py", "code/functions.py", "code/run_model.py", "LICENSE"]:
        urls["upstream_" + name.replace("/", "_")] = BASE + name
    return urls


def main():
    destination = Path("data/metadata/sources")
    destination.mkdir(parents=True, exist_ok=True)
    manifest_path = destination / "sources_manifest.json"
    expected = {}
    if manifest_path.exists():
        expected = {r["filename"]: r["sha256"] for r in json.loads(manifest_path.read_text())["sources"]}
    records = []
    for name, url in source_urls().items():
        cap = 20_000_000 if name.endswith(".pdf") else 2_000_000
        path = destination / name
        # Preserve the evidence inspected for this audit. No silent updates.
        cached = path.exists()
        if not cached:
            with requests.get(url, stream=True, timeout=(15, 60)) as response:
                response.raise_for_status()
                payload = response.raw.read(cap + 1, decode_content=True)
            if len(payload) > cap:
                raise RuntimeError(f"Source exceeds cap: {url}")
            if name in expected and hashlib.sha256(payload).hexdigest() != expected[name]:
                raise RuntimeError(f"Source changed since audit: {name}. Preserve the audit and review a new version explicitly.")
            path.write_bytes(payload)
        payload = path.read_bytes()
        if name in expected and hashlib.sha256(payload).hexdigest() != expected[name]:
            raise RuntimeError(f"Cached source hash mismatch: {name}")
        records.append({"filename": name, "url": url, "bytes": len(payload),
                        "sha256": hashlib.sha256(payload).hexdigest(),
                        "mode": "existing_snapshot_hashed" if cached else "fetched",
                        "verified_at_utc": datetime.now(timezone.utc).isoformat()})
        print(f"{name}: {len(payload):,} bytes", flush=True)
    manifest_path.write_text(json.dumps({"upstream_commit": SHA, "sources": records}, indent=2) + "\n")


if __name__ == "__main__":
    main()

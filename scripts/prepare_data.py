"""Inspect two remote ZIP indices and optionally retrieve a tiny real sample.

Run from repository root after `pip install -e .`. Default is metadata only.
"""

import argparse
import json
import platform
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

from aquavision.data.download import ByteBudget, HTTPRangeReader, RECORD_ID, fetch_record, read_member, save_member
from aquavision.data.metadata import build_inventory, select_inspection_pairs, write_csv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/data.yaml"))
    parser.add_argument("--download-sample", action="store_true", help="Download only the configured bounded inspection pairs")
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text())
    if config["record_id"] != RECORD_ID or config["record_url"] != f"https://zenodo.org/api/records/{RECORD_ID}":
        raise ValueError("This adapter is specific to the verified Zenodo record")
    if not 1 <= config["pairs_per_archive"] <= 8 or not 1 <= len(config["archives"]) <= 2:
        raise ValueError("Phase 1 permits at most two archives and eight pairs each")
    if not 0 < config["max_transfer_bytes"] <= 32 * 1024**2:
        raise ValueError("Phase 1 transfer budget must be <=32 MiB")
    if not 0 < config["max_member_bytes"] <= 2_000_000:
        raise ValueError("Phase 1 member cap must be <=2 MB")
    metadata = Path("data/metadata")
    record = fetch_record(metadata / "sources/zenodo_record.json")
    files = {f["key"]: f for f in record["files"]}
    budget = ByteBudget(config["max_transfer_bytes"])
    manifest = {"created_utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
                "record_id": RECORD_ID, "doi": record["doi"], "config": config,
                "selection_bias": "Deterministic access probe, not representative of regions or classes",
                "archives": [], "samples": []}
    for name in config["archives"]:
        item = files[name]
        with HTTPRangeReader(item["links"]["self"], item["size"], budget) as remote:
            with zipfile.ZipFile(remote) as archive:
                members, rows, summary = build_inventory(archive)
                stem = Path(name).stem
                write_csv(metadata / f"{stem}_members.csv", members)
                write_csv(metadata / f"{stem}_pairs.csv", rows)
                if summary["unpaired_sample_ids"] or summary["unrecognized_members"]:
                    raise ValueError(f"Unresolved archive members: {summary}")
                print(json.dumps({"archive": name, **summary}), flush=True)
                if args.download_sample:
                    for row in select_inspection_pairs(rows, config["pairs_per_archive"]):
                        sample = {**row, "archive": name}
                        for kind in ("sen2", "cyan"):
                            member = row[f"{kind}_member"]
                            payload = read_member(archive, member, max_bytes=config["max_member_bytes"])
                            # Use validated basename and record archive context; never extractall.
                            path = Path("data/raw/inspection") / stem / Path(member).name
                            sample[f"{kind}_sha256"] = save_member(path, payload)
                            sample[f"{kind}_path"] = path.as_posix()
                            sample[f"{kind}_bytes"] = len(payload)
                        manifest["samples"].append(sample)
            manifest["archives"].append({"name": name, "url": item["links"]["self"],
                "archive_size_bytes": item["size"], "published_checksum": item["checksum"],
                "full_archive_checksum_verified": False, "index_summary": summary,
                "requests": remote.requests_log})
    manifest["range_transfer_bytes"] = budget.used
    manifest["catalog_size_bytes"] = (metadata / "sources/zenodo_record.json").stat().st_size
    filename = "sample_manifest.json" if args.download_sample else "index_manifest.json"
    (metadata / filename).write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Saved {filename}; range transfer {budget.used:,} bytes; {len(manifest['samples'])} real pairs")


if __name__ == "__main__":
    main()

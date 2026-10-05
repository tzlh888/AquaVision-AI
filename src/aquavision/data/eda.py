"""Descriptive inspection of a small real sample; never model evaluation."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .labels import inspect_reference
from .loader import BANDS, load_pair
from .metadata import write_csv


def _json(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")


def _bar(counter, title, xlabel, path):
    fig, ax = plt.subplots(figsize=(7, 4), layout="constrained")
    keys = sorted(counter)
    ax.bar([str(k) for k in keys], [counter[k] for k in keys], color="#167b82")
    ax.set(xlabel=xlabel, ylabel="Inspection pairs", title=title)
    ax.text(0.99, 0.97, "Access probe only", transform=ax.transAxes, ha="right", va="top", fontsize=9)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def inspect_sample(manifest_path: Path, project_root: Path, output: Path) -> dict:
    manifest = json.loads(manifest_path.read_text())
    if not manifest.get("samples"):
        raise ValueError("No real samples in manifest; run prepare_data.py --download-sample")
    if len(manifest["samples"]) > 16:
        raise ValueError("This EDA is capped at 16 inspection pairs")
    for folder in ("figures", "tables", "reports"):
        (output / folder).mkdir(parents=True, exist_ok=True)
    images, refs, rows, bands = [], [], [], []
    grouped_hashes = defaultdict(list)
    counts = np.zeros(3, dtype=np.int64)
    images_with_bin = np.zeros(3, dtype=np.int64)
    class_ranges = [[], [], []]
    edges = manifest["config"]["reference"]["diagnostic_bin_edges"]
    units = manifest["config"]["reference"]["units"]
    for sample in manifest["samples"]:
        paths = []
        for kind in ("sen2", "cyan"):
            path = (project_root / sample[f"{kind}_path"]).resolve()
            if not path.is_relative_to(project_root.resolve()):
                raise ValueError("Sample path escapes project root")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != sample[f"{kind}_sha256"]:
                raise ValueError(f"Sample hash mismatch: {path}")
            paths.append(path)
        image, reference = load_pair(*paths)
        result = inspect_reference(reference, units=units, bin_edges=edges)
        images.append(image)
        refs.append(reference)
        grouped_hashes[sample["sen2_sha256"]].append(sample["sample_id"])
        valid = result["valid"]
        row = {"sample_id": sample["sample_id"], "region": sample["region"],
               "acquisition_date": sample["acquisition_date"],
               "spatial_group_candidate": sample["spatial_group_candidate"],
               "reference_min": int(reference.min()), "reference_max": int(reference.max()),
               "total_pixels": reference.size, "valid_reference_pixels": int(valid.sum()),
               "below_detection_pixels": int(result["no_detection"].sum()),
               "land_flag_pixels": int(result["land"].sum()),
               "masked_pixels": int(result["masked"].sum()),
               "invalid_reference_pixels": int(result["invalid"].sum()),
               "reference_excluded_fraction": float((~valid).mean()),
               "image_nonfinite_values": int((~np.isfinite(image)).sum()),
               "image_zero_values": int((image == 0).sum()),
               "latitude": sample["latitude"], "longitude": sample["longitude"],
               "water_body_id": sample["water_body_id"], "image_risk_class": None}
        for c in range(3):
            mask = result["bins"] == c
            n = int(mask.sum())
            counts[c] += n
            images_with_bin[c] += n > 0
            if n:
                class_ranges[c].extend([int(reference[mask].min()), int(reference[mask].max())])
            row[f"paper_bin_{c}_pixels"] = n
        rows.append(row)
        for band, values in zip(BANDS, image, strict=True):
            bands.append({"sample_id": sample["sample_id"], "band": band, "units": "stored_S2_DN",
                          "min": int(values.min()), "max": int(values.max()),
                          "mean": float(values.mean()), "std": float(values.std()),
                          "p05": float(np.percentile(values, 5)), "p50": float(np.median(values)),
                          "p95": float(np.percentile(values, 95)),
                          "zero_fraction": float((values == 0).mean())})
    total_valid = int(counts.sum())
    class_rows = []
    for c, (low, high) in enumerate(zip([0, *edges], [edges[0] - 1, edges[1] - 1, 253], strict=True)):
        class_rows.append({"class": f"Paper DN bin {low}-{high}", "pixel_count": int(counts[c]),
            "percentage_of_valid_pixels": float(100 * counts[c] / total_valid) if total_valid else None,
            "images_containing_bin_nonexclusive": int(images_with_bin[c]),
            "observed_reference_min": min(class_ranges[c], default=None),
            "observed_reference_max": max(class_ranges[c], default=None), "units": units})
    write_csv(output / "tables/sample_reference_bins.csv", class_rows)
    write_csv(output / "tables/sample_metadata.csv", rows)
    write_csv(output / "tables/sample_band_statistics.csv", bands)
    regions = Counter(r["region"] for r in rows)
    years = Counter(r["acquisition_date"][:4] for r in rows)
    months = Counter(r["acquisition_date"][5:7] for r in rows)
    for key, counter in (("region", regions), ("year", years), ("month", months)):
        write_csv(output / f"tables/sample_{key}_counts.csv", [{key: k, "pair_count": v} for k, v in sorted(counter.items())])
        _bar(counter, f"Inspection sample by {key}", key.title(), output / f"figures/sample_{key}.png")
    fig, ax = plt.subplots(figsize=(7, 4), layout="constrained")
    ax.bar([r["class"] for r in class_rows], counts, color="#167b82")
    ax.set(ylabel="Valid reference pixels", title="Reference DN bins: eight-pair access probe" if len(rows) == 8 else "Reference DN bins: access probe")
    fig.savefig(output / "figures/sample_reference_bins.png", dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(3, 4, figsize=(12, 8), layout="constrained")
    for i, (band, ax) in enumerate(zip(BANDS, axes.flat, strict=True)):
        values = np.concatenate([img[i].ravel() for img in images])
        ax.hist(values, bins=40, color="#167b82")
        ax.set(title=band, xlabel="Stored S2 DN", ylabel="Pixels")
    fig.suptitle("Band distributions across inspection patches (all pixels, masks not applied)")
    fig.savefig(output / "figures/sample_bands.png", dpi=150)
    plt.close(fig)
    fig, axes = plt.subplots(len(rows), 2, figsize=(10, 3 * len(rows)), squeeze=False, layout="constrained")
    for i, (image, ref, row) in enumerate(zip(images, refs, rows, strict=True)):
        rgb = np.moveaxis(np.asarray(image[[3, 2, 1]], dtype=float), 0, -1)
        low, high = np.percentile(rgb, [2, 98])
        rgb = np.clip((rgb - low) / max(high - low, 1), 0, 1)
        axes[i, 0].imshow(rgb)
        axes[i, 0].set_title(f"{row['region']} | {row['acquisition_date']}\nRGB: per-patch 2-98% display stretch", fontsize=10)
        masked_ref = np.ma.masked_where(ref[0] >= 254, ref[0])
        cmap = plt.get_cmap("viridis").copy()
        cmap.set_bad("#dedede")
        plot = axes[i, 1].imshow(masked_ref, vmin=0, vmax=253, cmap=cmap, interpolation="nearest")
        axes[i, 1].set_title(f"Processed CyAN DN | {row['reference_excluded_fraction']:.1%} excluded\nGrey: flags 254/255; no risk conversion", fontsize=10)
        fig.colorbar(plot, ax=axes[i, 1], label="Processed CyAN DN", fraction=0.04)
        for ax in axes[i]:
            ax.set_axis_off()
    fig.savefig(output / "figures/sample_images.png", dpi=120)
    plt.close(fig)
    # Distances are descriptive candidates only, not a claim of near-duplication.
    neighbors = []
    for i in range(len(images)):
        for j in range(i + 1, len(images)):
            delta = np.asarray(images[i], dtype=float) - images[j]
            neighbors.append({"sample_id_a": rows[i]["sample_id"], "sample_id_b": rows[j]["sample_id"],
                              "raw_DN_RMSE": float(np.sqrt(np.mean(delta**2))),
                              "interpretation": "unregistered raw-DN distance; no duplicate threshold"})
    write_csv(output / "tables/sample_pair_distances.csv", sorted(neighbors, key=lambda x: x["raw_DN_RMSE"]),
              fieldnames=["sample_id_a", "sample_id_b", "raw_DN_RMSE", "interpretation"])
    summary = {"scope": "Real access probe only; no training or evaluation", "pairs": len(rows),
               "image_shape": list(images[0].shape), "reference_shape": list(refs[0].shape),
               "image_dtype": str(images[0].dtype), "reference_dtype": str(refs[0].dtype),
               "band_order_source": "pinned upstream generate_all_bands; NPY itself has no band names",
               "band_order": list(BANDS), "regions": dict(regions), "years": dict(years), "months": dict(months),
               "total_reference_pixels": sum(r["total_pixels"] for r in rows),
               "valid_reference_pixels": total_valid, "paper_bin_pixel_counts": counts.tolist(),
               "masked_pixels": sum(r["masked_pixels"] for r in rows),
               "land_flag_pixels": sum(r["land_flag_pixels"] for r in rows),
               "invalid_reference_pixels": sum(r["invalid_reference_pixels"] for r in rows),
               "image_nonfinite_values": sum(r["image_nonfinite_values"] for r in rows),
               "missing_coordinate_pairs": sum(r["latitude"] is None or r["longitude"] is None for r in rows),
               "missing_water_body_id_pairs": sum(r["water_body_id"] is None for r in rows),
               "image_level_risk_labels": "not_defined", "cells_per_ml_conversion": "blocked",
               "exact_image_duplicate_groups": [ids for ids in grouped_hashes.values() if len(ids) > 1],
               "geographic_map": "not_generated_missing_verified_coordinates"}
    _json(output / "tables/sample_summary.json", summary)
    text = f"""# Phase 1 exploratory data inspection

Generated from `data/metadata/sample_manifest.json`. All observations below are from real downloaded data.
This is a deterministic file-access probe of **{len(rows)} pairs**, not a representative research subset.

## Measured properties

- Sentinel-2 array: `{summary['image_shape']}`, `{summary['image_dtype']}`; reference: `{summary['reference_shape']}`, `{summary['reference_dtype']}`.
- Region IDs: `{dict(regions)}`. These are CyAN tile IDs, not inferred states, watersheds, or water bodies.
- Acquisition years: `{dict(years)}`; months: `{dict(months)}` (from filenames, not sensing timestamps).
- {summary['total_reference_pixels']:,} reference pixels; {total_valid:,} native DN 0-253 pixels; {summary['masked_pixels']:,} flag-255 pixels; {summary['land_flag_pixels']:,} flag-254 pixels.
- {summary['invalid_reference_pixels']} other invalid reference values; {summary['image_nonfinite_values']} nonfinite image values. Zeros are tabulated, not automatically marked missing.
- Paper-native bin pixel counts: `{counts.tolist()}`. These are **not** image-level risk counts or cells/mL thresholds.
- Exact Sentinel-2 file duplicate groups: `{summary['exact_image_duplicate_groups']}`. This limited check cannot exclude broader archive duplicates.
- {summary['missing_coordinate_pairs']} pairs lack verified coordinates; {summary['missing_water_body_id_pairs']} lack water-body IDs. No geographic map is fabricated.

## Figures and tables

`sample_images.png` shows RGB display stretches and unconverted reference DN. Display normalization does not modify stored data.
`sample_bands.png` shows stored digital numbers across all pixels; physical reflectance scaling remains unverified.
Region, year, month and native-bin plots describe only the access probe. Tables preserve sample IDs, original reference ranges,
flag counts, per-band distributions, and nonexclusive image counts per native bin. Pixels within a resampled reference are correlated.
No image-level class-distribution table can be justified until an aggregation rule is defined.

## Leakage investigation and limits

Each filename encodes a parent subtile, date, patch row/column and sequence. Repeated parent subtiles across dates and
neighboring patches are potential leakage routes. `*_pairs.csv` inventories expose these fields before image downloading.
See `archive_metadata_summary.json` for repeated-location and adjacent-subtile counts in indexed archives.
`sample_pair_distances.csv` lists raw-DN RMSE candidates; without registration, a threshold, or a larger sample it cannot
establish near-duplicate prevalence. Patch coordinates may shift between reprojected products even with matching indices.
Group all dates from a verified geographic unit together; check adjacent units and lakes crossing boundaries before splitting.

## Conclusions permitted

File access and decoding work. We can inspect raw reference masks and recover naming-based groups/dates.
This sample cannot estimate class balance, geographic representativeness, model performance, or usable research sample size.
No network was trained and no test split was constructed. Resolve the label and geographic provenance gates in DATASET_AUDIT.md first.
"""
    (output / "reports/EDA_REPORT.md").write_text(text)
    return summary

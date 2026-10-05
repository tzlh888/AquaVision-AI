"""Regenerate real-sample label/geographic diagnostics without network or models."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml

from aquavision.data.geography import adjacent_components, temporal_summary
from aquavision.data.labels import aggregate_native_reference
from aquavision.data.loader import BANDS, load_pair
from aquavision.data.metadata import parse_member, write_csv


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def main():
    root = Path.cwd()
    config = yaml.safe_load(Path("configs/phase2.yaml").read_text())
    if config["training_allowed"] or config["final_splits_allowed"] or config["cells_per_ml_conversion"] != "DISABLED":
        raise ValueError("This audit cannot approve conversion, training or final splits")
    manifest_path = Path("data/metadata/sample_manifest.json")
    manifest = json.loads(manifest_path.read_text())
    if not manifest["samples"]:
        raise ValueError("No existing real pairs to audit")
    rows = []
    for path in sorted(Path("data/metadata").glob("*_pairs.csv")):
        with path.open() as f:
            rows.extend(csv.DictReader(f))
    if not rows:
        raise ValueError("Cached Phase 1 inventories are required")
    components = adjacent_components(rows)
    for row in rows:
        row["candidate_component_id"] = components[row["spatial_group_candidate"]]
    tables = Path("research_outputs/tables")
    figures = Path("research_outputs/figures")
    audits, metadata, aggregates, coverage = [], [], [], []
    for sample in manifest["samples"]:
        paths = []
        for kind in ("sen2", "cyan"):
            path = (root / sample[f"{kind}_path"]).resolve()
            if not path.is_relative_to(root):
                raise ValueError("Sample path escapes repository")
            if hashlib.sha256(path.read_bytes()).hexdigest() != sample[f"{kind}_sha256"]:
                raise ValueError("Sample SHA-256 mismatch")
            paths.append(path)
        image, reference = load_pair(*paths)
        d = aggregate_native_reference(reference, bin_edges=tuple(config["native_bin_edges"]), quantile=config["aggregation_quantile"])
        values, counts = np.unique(reference, return_counts=True)
        native_histogram = {str(int(v)):int(c) for v,c in zip(values, counts, strict=True)}
        sid = sample["sample_id"]
        parsed = parse_member(sample["sen2_member"])
        component = components[parsed["spatial_group_candidate"]]
        audits.append({"sample_id": sid, "acquisition_date": parsed["acquisition_date"],
            "sentinel_bands": ";".join(BANDS), "band_evidence": "12 channels observed; identities from upstream saving code",
            "reference_path": sample["cyan_path"], "reference_sha256": sample["cyan_sha256"],
            "raw_reference_units": "processed_cyan_digital_number",
            "raw_reference_histogram_dn_count": json.dumps(native_histogram),
            "transformed_reference_value": "NONE: stored values unchanged",
            "estimated_cells_per_ml": "UNKNOWN", "conversion_status": "DISABLED_VERSION_AND_PROCESSING_UNRESOLVED",
            "quality_flags": json.dumps({k:d[k] for k in ("below_detection_pixels","land_flag_pixels","masked_pixels","invalid_pixels")}),
            "valid_reference_fraction": d["valid_reference_fraction"],
            "candidate_native_bins": json.dumps({k:d[k] for k in ("median_dn_bin","mean_dn_bin","max_dn_bin","upper_quantile_dn_bin","majority_bin","center_consensus_bin")}),
            "candidate_risk_class": "UNKNOWN", "final_image_label": "UNKNOWN",
            "latitude": "UNKNOWN", "longitude": "UNKNOWN", "footprint": "UNKNOWN",
            "geographic_group": "UNKNOWN", "candidate_parent_grid": parsed["spatial_group_candidate"],
            "candidate_component": component,
            "uncertainty": "Encoding version; resampling; mask cause; water-area denominator; footprint; lake identity; image-target applicability"})
        metadata.append({"sample_id": sid, "date": parsed["acquisition_date"],
            "latitude": "", "longitude": "", "sentinel_tile": "", "mgrs_tile": "",
            "waterbody_id": "", "waterbody_ids": "[]", "basin_id": "", "huc_code": "", "state": "",
            "footprint_wkt": "", "footprint_id": "", "spatial_group_id": "",
            "cyan_tile_id": parsed["region"], "candidate_parent_grid": parsed["spatial_group_candidate"],
            "candidate_component_id": component, "patch_row": parsed["patch_row"], "patch_col": parsed["patch_col"],
            "coordinate_status": "UNKNOWN", "geography_status": "UNVERIFIED",
            "label_status": "UNVERIFIED", "class_id": "", "geography_evidence": "filename convention only; no CRS/transform"})
        aggregates.append({"sample_id":sid, **{k:(json.dumps(v) if isinstance(v,list) else v) for k,v in d.items()}})
        for minimum in config["coverage_scenarios"]:
            coverage.append({"sample_id":sid, "minimum_valid_reference_fraction": minimum,
                "passes_coverage_scenario": d["valid_reference_fraction"] >= minimum,
                "qualified_for_training": False, "note":"Scenario only; valid water-area coverage is UNKNOWN"})
    write_csv(tables / "sample_label_audit.csv", audits)
    write_csv(Path("data/metadata/sample_metadata.csv"), metadata)
    write_csv(tables / "image_aggregation_comparison.csv", aggregates)
    write_csv(tables / "coverage_sensitivity.csv", coverage)
    summaries = {}
    for key in ("spatial_group_candidate", "grid_position_candidate", "candidate_component_id"):
        result = temporal_summary(rows, key)
        write_csv(tables / f"temporal_{key}.csv", result)
        summaries[key] = {"groups":len(result), "groups_on_multiple_dates":sum(x["unique_dates"]>1 for x in result),
                          "group_date_extra_samples":sum(x["same_group_date_extra_samples"] for x in result)}
    group_rows = []
    for group, component in sorted(components.items()):
        subset = [r for r in rows if r["spatial_group_candidate"] == group]
        group_rows.append({"parent_group":group,"candidate_component":component,"samples":len(subset),
                           "unique_dates":len({r["acquisition_date"] for r in subset}),
                           "verified_waterbody":False,"usable_as_final_holdout_group":False})
    write_csv(tables / "geographic_candidate_groups.csv", group_rows)
    class_fields = ("median_dn_bin","mean_dn_bin","max_dn_bin","upper_quantile_dn_bin","majority_bin","center_consensus_bin")
    disagree = []
    for row in aggregates:
        observed = {row[k] for k in class_fields if row[k] is not None}
        if len(observed)>1:
            disagree.append(row["sample_id"])
    summary = {"readiness":"NOT READY", "real_pairs":len(audits), "cached_index_pairs":len(rows),
        "unique_dates_in_cached_indices":len({r["acquisition_date"] for r in rows}),
        "date_min":min(r["acquisition_date"] for r in rows),"date_max":max(r["acquisition_date"] for r in rows),
        "region_counts":dict(Counter(r["region"] for r in rows)),
        "temporal_summaries":summaries, "candidate_component_sample_counts":dict(Counter(r["candidate_component_id"] for r in rows)),
        "aggregation_disagreement_sample_ids":disagree,
        "coverage_scenario_pass_counts":{str(t):sum(r["valid_reference_fraction"]>=t for r in aggregates) for t in config["coverage_scenarios"]},
        "verified_coordinate_samples":0,"verified_waterbody_samples":0,"cells_per_ml_estimates_produced":0,
        "final_risk_labels_produced":0,"final_split_files_produced":0,"models_trained":0,
        "full_dataset_distribution":"UNKNOWN; expansion gated on labels/geography",
        "sample_manifest_sha256":hashlib.sha256(manifest_path.read_bytes()).hexdigest()}
    dump(tables/"phase2_summary.json",summary)
    protocol = {"status":"DRAFT_NOT_EXECUTABLE_ON_CURRENT_METADATA", "seed":config["seed"],
        "random_benchmark":{"fractions":[0.8,0.1,0.1],"stratified":True,"requires":"approved three-class labels and >=10 samples/class"},
        "geographic_experiment":{"preference":"verified basin units with complete intersecting waterbody constraints",
            "train_groups":None,"validation_groups":None,"test_groups":None,
            "requires":["verified footprints","all intersecting waterbody IDs","cross-unit lake checks","sufficient class support","spatial buffers"]},
        "do_not_optimize_on_test_scores":True, "same_eligibility_pool_for_comparisons":True,
        "final_split_creation_allowed":False,"current_sample_manifest_sha256":summary["sample_manifest_sha256"]}
    dump(Path("data/metadata/splits/protocol.json"),protocol)
    dump(tables/"phase2_map_status.json",{"all_samples":"NOT_GENERATED_NO_VERIFIED_COORDINATES",
        "geographic_groups":"NOT_GENERATED_NO_VERIFIED_FOOTPRINTS", "train_validation_test":"NOT_GENERATED_NO_VALID_FINAL_SPLIT"})
    # A diagnostic heatmap, not a geographical map or trained-model output.
    matrix = np.array([[float(r[k]) if r[k] is not None else np.nan for k in class_fields] for r in aggregates])
    fig, ax = plt.subplots(figsize=(11,5), layout="constrained")
    masked = np.ma.masked_invalid(matrix)
    cmap=plt.get_cmap("viridis",3).copy();cmap.set_bad("#dddddd")
    chart=ax.imshow(masked,vmin=-0.5,vmax=2.5,cmap=cmap,aspect="auto")
    ax.set_xticks(range(6),["Median DN","Mean DN","Maximum DN","90th percentile DN","Majority bin","Center consensus"],rotation=20,ha="right")
    ax.set_yticks(range(len(audits)),[f"{i+1}: {s['acquisition_date']} | {s['candidate_parent_grid']}" for i,s in enumerate(audits)],fontsize=8)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):ax.text(j,i,"?" if np.isnan(matrix[i,j]) else str(int(matrix[i,j])),ha="center",va="center",color="white" if matrix[i,j]==0 else "black")
    fig.colorbar(chart,ax=ax,ticks=[0,1,2],label="Paper-native DN bin ID; NOT a risk class")
    ax.set_title("Eight real pairs: diagnostic aggregation sensitivity\nGrey = unavailable; no cells/mL conversion or finalized image labels")
    fig.savefig(figures/"phase2_aggregation_sensitivity.png",dpi=160);plt.close(fig)
    print(json.dumps(summary,indent=2))
    print("PHASE 2: NOT READY | no models trained | no final risk labels or split assignments generated")


if __name__ == "__main__":
    main()

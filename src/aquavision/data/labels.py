"""Inspect and map native CyAN digital numbers. This is NOT a cells/mL conversion.

Paper bins support the published pixel-level segmentation task. They do not establish an
image-level risk target, toxin concentration, or clinical/public-health category.
The published resampling/masking history prevents treating these arrays as
unmodified original CyAN observations. Never overwrite the reference array.
"""

import numpy as np

IGNORE_INDEX = -100


def segmentation_target(values):
    """Return int64 HxW classes 0/1/2; mask flags/invalid data with -100.

    Schloer & Haensch, DOI 10.1109/JSTARS.2025.3629586, section III-B:
    DN 0..99 / 100..199 / 200..253. Paper excludes land/cloud pixels;
    generate_tiles.py identifies 254 as land, download_and_process.py writes
    255 for excluded pixels. Training-target source code is not released.
    Keeping residual 254 excluded is explicit defensive handling, not a claim
    to have inspected the unavailable training loss implementation.
    """
    data = np.asarray(values)
    if data.ndim == 3 and data.shape[0] == 1:
        data = data[0]
    if data.ndim != 2 or not data.size:
        raise ValueError("Expected HxW or 1xHxW reference")
    info = inspect_reference(data, units="processed_cyan_digital_number")
    target = np.full(data.shape, IGNORE_INDEX, dtype=np.int64)
    target[info["valid"]] = info["bins"][info["valid"]]
    return target


def inspect_reference(values, *, units: str, bin_edges=(100, 200)) -> dict:
    if units != "processed_cyan_digital_number":
        raise ValueError("Only processed_cyan_digital_number is verified; conversion is blocked")
    if len(bin_edges) != 2 or any(type(v) is not int for v in bin_edges) or not 0 < bin_edges[0] < bin_edges[1] < 254:
        raise ValueError("Require two increasing integer native-DN edges inside (0, 254)")
    data = np.asarray(values)
    if not (np.issubdtype(data.dtype, np.integer) or np.issubdtype(data.dtype, np.floating)):
        raise ValueError("Reference must be real numeric data")
    finite = np.isfinite(data)
    integral = np.zeros(data.shape, dtype=bool)
    integral[finite] = data[finite] == np.floor(data[finite])
    valid = finite & integral & (data >= 0) & (data <= 253)
    no_detection = valid & (data == 0)
    land = finite & (data == 254)
    masked = finite & (data == 255)
    invalid = ~(valid | land | masked)
    bins = np.full(data.shape, -1, dtype=np.int8)
    bins[valid] = np.searchsorted(bin_edges, data[valid], side="right")
    return {"bins": bins, "valid": valid, "no_detection": no_detection,
            "land": land, "masked": masked, "invalid": invalid,
            "units": units, "bin_edges": list(bin_edges)}


def to_cells_per_ml(*args, **kwargs):
    raise NotImplementedError(
        "Conversion of processed/resampled CyAN DN to cells/mL is not verified. "
        "See LABEL_PROVENANCE.md and CELLS_PER_ML_VALIDATION.md. "
        "No dataset-matched encoding version or calibrated transformation is established."
    )


def aggregate_native_reference(values, *, bin_edges=(100, 200), quantile=0.9):
    """Compare diagnostic aggregations of stored DN, never estimate cells/mL.

    Source paper DOI 10.1109/JSTARS.2025.3629586 defines pixel bins, not
    an image target. Quantiles use observed order statistics (inverted_cdf);
    means of logarithmically encoded DN have no cell-density interpretation.
    Denominator is valid *reference pixels*, not a verified water-area mask.
    """
    if not np.isfinite(quantile) or not 0 <= quantile <= 1:
        raise ValueError("Quantile must lie in [0, 1]")
    data = np.asarray(values)
    if data.ndim == 3 and data.shape[0] == 1:
        data = data[0]
    if data.ndim != 2 or not data.size:
        raise ValueError("Expected a nonempty 2D reference or one-channel reference")
    inspected = inspect_reference(data, units="processed_cyan_digital_number", bin_edges=bin_edges)
    valid = inspected["valid"]
    selected = data[valid].astype(float)
    counts = np.bincount(inspected["bins"][valid], minlength=3)
    result = {"valid_pixels": int(valid.sum()), "total_pixels": int(data.size),
              "valid_reference_fraction": float(valid.mean()),
              "below_detection_pixels": int(inspected["no_detection"].sum()),
              "land_flag_pixels": int(inspected["land"].sum()),
              "masked_pixels": int(inspected["masked"].sum()),
              "invalid_pixels": int(inspected["invalid"].sum()),
              "native_bin_counts": counts.tolist(), "quantile": quantile,
              "units": "processed_cyan_digital_number", "final_risk_class": "UNKNOWN"}
    stats = {"median_dn": None, "mean_dn": None, "max_dn": None, "upper_quantile_dn": None}
    if selected.size:
        stats = {"median_dn": float(np.quantile(selected, 0.5, method="inverted_cdf")),
                 "mean_dn": float(selected.mean()), "max_dn": float(selected.max()),
                 "upper_quantile_dn": float(np.quantile(selected, quantile, method="inverted_cdf"))}
    result.update(stats)
    for name, value in stats.items():
        result[name + "_bin"] = int(np.searchsorted(bin_edges, value, side="right")) if value is not None else None
    winners = np.flatnonzero(counts == counts.max())
    result["majority_bin"] = int(winners[0]) if selected.size and len(winners) == 1 else None
    result["majority_status"] = "unique" if result["majority_bin"] is not None else "tie_or_no_valid_data"
    for edge in bin_edges:
        result[f"fraction_valid_dn_ge_{edge}"] = float((selected >= edge).mean()) if selected.size else None
    # For even dimensions there are four central pixels, not a unique center.
    h, w = data.shape
    center = data[(h - 1)//2:h//2+1, (w - 1)//2:w//2+1]
    center_bins = inspected["bins"][(h - 1)//2:h//2+1, (w - 1)//2:w//2+1]
    result["center_raw_dn"] = [float(v) if np.isfinite(v) else None for v in center.ravel()]
    unique = np.unique(center_bins)
    result["center_consensus_bin"] = int(unique[0]) if len(unique) == 1 and unique[0] >= 0 else None
    return result

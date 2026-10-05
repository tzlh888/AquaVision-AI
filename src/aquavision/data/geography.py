"""Naming-based geography candidates; no invented real-world coordinates."""

from collections import defaultdict
from datetime import date
import math

from .metadata import parse_member


def adjacent_components(rows):
    """Connect touching parent grid cells within each CyAN tile, including diagonals.

    Mirrors the adjacency concept in the authors' generate_tiles.py. Components
    are minimum co-location constraints, NOT verified lake/basin groups.
    Cross-tile connections cannot be inferred without actual footprints.
    """
    groups = {}
    for row in rows:
        parsed = parse_member(row["sen2_member"])
        group = parsed["spatial_group_candidate"]
        identity = (parsed["region"], parsed["subtile_x"], parsed["subtile_y"], parsed["subtile_size"])
        if group in groups and groups[group] != identity:
            raise ValueError("Inconsistent parent grid metadata")
        groups[group] = identity
    parent = {key: key for key in groups}

    def find(key):
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    keys = sorted(groups)
    for i, a in enumerate(keys):
        ra, xa, ya, sa = groups[a]
        for b in keys[i+1:]:
            rb, xb, yb, sb = groups[b]
            if ra != rb:
                continue
            if sa != sb:
                raise ValueError("Mixed parent-grid sizes need explicit footprint geometry")
            if abs(xa-xb) <= sa and abs(ya-yb) <= sa:
                x, y = sorted([find(a), find(b)])
                parent[y] = x
    return {key: "candidate_component:" + find(key) for key in keys}


def temporal_summary(rows, group_key):
    grouped = defaultdict(list)
    for row in rows:
        group = row.get(group_key)
        if not group or group == "UNKNOWN":
            raise ValueError(f"Missing {group_key}; unknown IDs cannot be treated as a real location")
        grouped[group].append(date.fromisoformat(row["acquisition_date"]))
    result = []
    for group, dates in sorted(grouped.items()):
        unique = sorted(set(dates))
        gaps = sorted((b-a).days for a, b in zip(unique, unique[1:]))
        result.append({"group": group, "sample_count": len(dates), "unique_dates": len(unique),
                       "first_date": unique[0].isoformat(), "last_date": unique[-1].isoformat(),
                       "span_days": (unique[-1]-unique[0]).days,
                       "same_group_date_extra_samples": len(dates)-len(unique),
                       "min_gap_days": min(gaps) if gaps else None,
                       "median_gap_days": ((gaps[(len(gaps)-1)//2]+gaps[len(gaps)//2])/2) if gaps else None,
                       "observed_dates_per_30_days": 30*len(unique)/((unique[-1]-unique[0]).days+1)})
    return result


def require_verified_geography(row):
    """Reject incomplete identities before any actual geographic partition."""
    if row.get("geography_status") != "VERIFIED":
        raise ValueError("Geography is not VERIFIED")
    for key in ("spatial_group_id", "footprint_id", "geography_evidence"):
        value = row.get(key)
        if not isinstance(value, str) or not value.strip() or value == "UNKNOWN" or value.startswith("candidate_"):
            raise ValueError(f"Missing verified {key}")
    waterbodies = row.get("waterbody_ids")
    if not isinstance(waterbodies, list) or not waterbodies or any(not isinstance(x, str) or not x.strip() or x == "UNKNOWN" for x in waterbodies):
        raise ValueError("All intersecting waterbody_ids must be known")
    for key, low, high in (("latitude", -90, 90), ("longitude", -180, 180)):
        value = row.get(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"Invalid {key}")

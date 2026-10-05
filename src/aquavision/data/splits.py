"""Fail-closed split infrastructure. Phase 2 produces NO real final split.

Only metadata with approved target/geography can enter these functions. Tests
use explicitly synthetic records. A successful guard is not a substitute for
scientific validation of source footprints or cross-boundary water bodies.
"""

import hashlib
import json
import random
from pathlib import Path

from .geography import require_verified_geography

SPLITS = ("train", "validation", "test")


def _eligible(rows):
    if not rows:
        raise ValueError("No eligible samples")
    ids = [r["sample_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate sample IDs")
    for row in rows:
        if row.get("label_status") != "VERIFIED" or type(row.get("class_id")) is not int or row["class_id"] not in (0, 1, 2):
            raise ValueError("A verified three-class target is required")
        require_verified_geography(row)


def validate_partition(rows, assignments, *, geographic=True):
    _eligible(rows)
    if set(assignments) != {r["sample_id"] for r in rows}:
        raise ValueError("Split must account for every eligible sample exactly once")
    if set(assignments.values()) != set(SPLITS):
        raise ValueError("Require nonempty train, validation and test partitions")
    if geographic:
        for key in ("spatial_group_id", "footprint_id", "waterbody_ids"):
            membership = {}
            for row in rows:
                values = row[key] if key == "waterbody_ids" else [row[key]]
                for value in values:
                    split = assignments[row["sample_id"]]
                    if value in membership and membership[value] != split:
                        raise ValueError(f"Geographic leakage: {key} {value}")
                    membership[value] = split
    for split in SPLITS:
        observed = {r["class_id"] for r in rows if assignments[r["sample_id"]] == split}
        if observed != {0, 1, 2}:
            raise ValueError(f"Insufficient three-class support in {split}; do not search for a favorable seed")


def geographic_partition(rows, group_assignment):
    """Apply a predeclared group allocation; no optimization or hidden rebalancing."""
    _eligible(rows)
    groups = {r["spatial_group_id"] for r in rows}
    if set(group_assignment) != groups:
        raise ValueError("Explicit assignments required for exactly the eligible groups")
    assignments = {r["sample_id"]: group_assignment[r["spatial_group_id"]] for r in rows}
    validate_partition(rows, assignments, geographic=True)
    return assignments


def random_partition(rows, *, seed=42):
    """Conventional stratified 80/10/10 benchmark; geographic leakage is expected.

    Sorted input and fixed RNG make the result insensitive to table row order.
    Refuse classes with fewer than ten samples instead of producing empty strata.
    """
    _eligible(rows)
    result = {}
    rng = random.Random(seed)
    for c in (0, 1, 2):
        ids = sorted(r["sample_id"] for r in rows if r["class_id"] == c)
        if len(ids) < 10:
            raise ValueError("At least ten samples per class required for 80/10/10 stratification")
        rng.shuffle(ids)
        n_train, n_validation = int(0.8*len(ids)), int(0.1*len(ids))
        for i, sid in enumerate(ids):
            result[sid] = "train" if i < n_train else "validation" if i < n_train+n_validation else "test"
    validate_partition(rows, result, geographic=False)
    return result


def freeze_partition(path: Path, rows, assignments, *, protocol, geographic=True):
    """Exclusive creation; hash metadata and protocol so splits cannot be rewritten."""
    validate_partition(rows, assignments, geographic=geographic)
    if not protocol:
        raise ValueError("A declared protocol is required")
    canonical = json.dumps(sorted(rows, key=lambda r:r["sample_id"]), sort_keys=True, allow_nan=False)
    payload = {"metadata_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
               "protocol": protocol, "geographic": geographic, "assignments": dict(sorted(assignments.items()))}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(payload, stream, indent=2, allow_nan=False)
        stream.write("\n")

"""Inspect cached ZIP inventories for geographic/temporal leakage candidates."""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


def summarize(path: Path) -> dict:
    with path.open() as stream:
        rows = list(csv.DictReader(stream))
    dates_by_group, dates_by_grid = defaultdict(set), defaultdict(set)
    groups = {}
    for row in rows:
        dates_by_group[row["spatial_group_candidate"]].add(row["acquisition_date"])
        dates_by_grid[row["grid_position_candidate"]].add(row["acquisition_date"])
        groups[row["spatial_group_candidate"]] = row
    adjacent = []
    ids = sorted(groups)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            x, y = groups[a], groups[b]
            if x["region"] != y["region"] or x["subtile_size"] != y["subtile_size"]:
                continue
            dx = abs(int(x["subtile_x"]) - int(y["subtile_x"]))
            dy = abs(int(x["subtile_y"]) - int(y["subtile_y"]))
            if dx <= int(x["subtile_size"]) and dy <= int(x["subtile_size"]):
                adjacent.append([a, b])
    return {"index": path.name, "pairs": len(rows), "spatial_group_candidates": len(groups),
            "parent_groups_observed_on_multiple_dates": sum(len(v) > 1 for v in dates_by_group.values()),
            "grid_positions_observed_on_multiple_dates": sum(len(v) > 1 for v in dates_by_grid.values()),
            "same_tile_neighboring_parent_groups": adjacent,
            "region_counts": dict(Counter(r["region"] for r in rows)),
            "year_counts": dict(Counter(r["year"] for r in rows)),
            "month_counts": dict(Counter(r["month"] for r in rows)),
            "coordinate_status": "Grid offsets only; adjacency is not a watershed/lake identity or measured distance"}


if __name__ == "__main__":
    paths = sorted(Path("data/metadata").glob("*_pairs.csv"))
    if not paths:
        raise SystemExit("No cached inventories; run scripts/prepare_data.py first")
    result = [summarize(path) for path in paths]
    out = Path("research_outputs/tables/archive_metadata_summary.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

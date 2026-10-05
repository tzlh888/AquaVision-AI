"""Author-grid segmentation splits, distinct from stricter waterbody splits.

Evidence: cschloer/hab_detection_s2, commit e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37,
code/dataset/generate_tiles.py: get_scene_id, find_and_update_bordering.
Only selected parents in a supplied inventory define this graph. Unknown lake
boundaries and missing selected parents are limitations, not fabricated IDs.
"""
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

from .geography import adjacent_components
from .metadata import parse_member


def spatial_rows(rows):
    if not rows or len({r['sample_id'] for r in rows}) != len(rows):
        raise ValueError('Require nonempty unique samples')
    for row in rows:
        p = parse_member(row['sen2_member'])
        if p['sample_id'] != row['sample_id']:
            raise ValueError('Sample/member identity mismatch')
        if p['subtile_size'] != 50 or p['subtile_x'] % 50 or p['subtile_y'] % 50:
            raise ValueError('Not the verified 50-pixel author grid')
        if not (0 <= p['subtile_x'] < 2000 and 0 <= p['subtile_y'] < 2000):
            raise ValueError('Outside author tile grid')
    components = adjacent_components(rows)
    return [{**r, 'subtile_id': parse_member(r['sen2_member'])['spatial_group_candidate'],
             'spatial_group_id': components[parse_member(r['sen2_member'])['spatial_group_candidate']].replace('candidate_component:', 'author_grid_component:'),
             'spatial_identifier_status': 'VERIFIED_AUTHOR_GRID',
             'scene_id': None} for r in rows]


def author_partition(rows, seed=42, train_probability=0.7):
    """Faithful seeded component coin toss in sorted-parent traversal order.

    Equivalent to recursive region growing, without recursion-depth limits.
    Deliberately permits all-train outcomes; no favorable seed search.
    Reproduces algorithm on supplied nodes, not missing original 183-node split.
    """
    if not 0 <= train_probability <= 1:
        raise ValueError('Invalid train probability')
    enriched = spatial_rows(rows)
    rng = random.Random(seed)
    allocation = {g: 'train' if rng.random() <= train_probability else 'test'
                  for g in sorted({r['spatial_group_id'] for r in enriched})}
    return {r['sample_id']: allocation[r['spatial_group_id']] for r in enriched}


def experiment_partitions(rows, seed=42):
    """Predeclared 80/10/10 random and whole-component 3-way pilot design.

    Geographic: shuffle sorted components once; last is test, penultimate is
    validation, all others train. Counts are diagnostics, never optimized.
    """
    enriched = spatial_rows(rows)
    ids = sorted(r['sample_id'] for r in enriched)
    if len(ids) < 10:
        raise ValueError('Need at least ten patches')
    random.Random(seed).shuffle(ids)
    a, b = int(.8 * len(ids)), int(.9 * len(ids))
    rand = {sid: 'train' if i < a else 'validation' if i < b else 'test' for i, sid in enumerate(ids)}
    groups = sorted({r['spatial_group_id'] for r in enriched})
    if len(groups) < 3:
        raise ValueError('Need three independent selected components')
    random.Random(seed).shuffle(groups)
    ga = {g: 'test' if g == groups[-1] else 'validation' if g == groups[-2] else 'train' for g in groups}
    geo = {r['sample_id']: ga[r['spatial_group_id']] for r in enriched}
    validate_geographic(enriched, geo)
    return {'random': rand, 'geographic': geo}


def validate_geographic(rows, assignments):
    enriched = spatial_rows(rows)
    if set(assignments) != {r['sample_id'] for r in enriched}:
        raise ValueError('Incomplete or extra split assignments')
    if not set(assignments.values()) <= {'train', 'validation', 'test'}:
        raise ValueError('Invalid partition')
    seen = {}
    for r in enriched:
        g, part = r['spatial_group_id'], assignments[r['sample_id']]
        if g in seen and seen[g] != part:
            raise ValueError('Identical/adjacent connected region leakage')
        seen[g] = part


def ratio_diagnostics(rows, assignments):
    enriched = spatial_rows(rows)
    out = {}
    for split in ('train', 'validation', 'test'):
        subset = [r for r in enriched if assignments[r['sample_id']] == split]
        out[split] = {'patches': len(subset), 'fraction': len(subset)/len(rows),
                      'subtiles': len({r['subtile_id'] for r in subset}),
                      'components': len({r['spatial_group_id'] for r in subset})}
    return out


def freeze_json(path, payload):
    """Allow exact replay, reject changing a frozen protocol or membership."""
    path = Path(path)
    content = json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + '\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text() != content:
            raise FileExistsError(f'Frozen artifact differs: {path}')
    else:
        with path.open('x') as f:
            f.write(content)
    return hashlib.sha256(content.encode()).hexdigest()

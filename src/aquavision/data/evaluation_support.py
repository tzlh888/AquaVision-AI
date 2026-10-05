"""Phase 3.5 dataset-only support gates; no model scores enter allocation."""
from collections import defaultdict
from datetime import date
import hashlib
from .geographic_split import spatial_rows, validate_geographic


def group_support(rows):
    groups=defaultdict(list)
    for r in rows:groups[r['spatial_group_id']].append(r)
    result=[]
    for group,items in sorted(groups.items()):
        high=[r for r in items if int(r['high_pixels'])>0]
        dates=sorted({r['date'] for r in high})
        counts=[sum(int(r[k+'_pixels']) for r in items) for k in ('low','moderate','high')]
        valid=sum(counts)
        result.append({'geographic_group_id':group,'source_tiles':sorted({r['tile'] for r in items}),
          'subtiles':sorted({r['subtile_id'] for r in items}),'patches':len(items),'valid_pixels':valid,
          'low_pixels':counts[0],'moderate_pixels':counts[1],'high_pixels':counts[2],
          'high_percent':100*counts[2]/valid if valid else 0.,'high_patches':len(high),
          'high_subtiles':len({r['subtile_id'] for r in high}),'high_dates':dates,
          'high_date_count':len(dates),'high_date_span_days':(date.fromisoformat(dates[-1])-date.fromisoformat(dates[0])).days if dates else 0,
          'high_patch_positions':len({(r['subtile_id'],str(r['patch_row']),str(r['patch_col'])) for r in high}),
          'sentinel_scene_ids':None})
    return result


def qualifies(group,criteria):
    return (group['high_date_count']>=criteria['high_dates_per_component'] and
            group['high_date_span_days']>=criteria['minimum_date_span_days'] and
            group['high_patch_positions']>=criteria['high_patch_positions_per_component'] and
            group['high_pixels']>=criteria['minimum_high_pixels_per_component'])


def choose_groups(groups,criteria,seed=35042):
    """Metadata-only deterministic allocation; no favorable score/seed search.

    Highest usefulness = dates, spatial positions, high subtiles (not raw pixel
    count). Ties use fixed hash. Select test with tile diversity first, retain
    separate validation/train components. No claim these are independent lakes.
    """
    eligible=[g for g in groups if qualifies(g,criteria)]
    required=sum(criteria[k] for k in ('test_high_components','validation_high_components','train_high_components'))
    if len(eligible)<required:raise ValueError(f'Need {required} qualifying components; found {len(eligible)}')
    order=sorted(eligible,key=lambda g:(-g['high_date_count'],-g['high_patch_positions'],-g['high_subtiles'],
                  hashlib.sha256(f"{seed}:{g['geographic_group_id']}".encode()).hexdigest()))
    test=[];used_tiles=set()
    for g in order:
        if not set(g['source_tiles'])<=used_tiles:
            test.append(g);used_tiles.update(g['source_tiles'])
            if len(used_tiles)>=criteria['test_source_tiles']:break
    if len(used_tiles)<criteria['test_source_tiles']:raise ValueError('Insufficient source tile diversity')
    if len(test)>criteria['test_high_components']:raise ValueError('Tile diversity exceeds test group count')
    for g in order:
        if len(test)>=criteria['test_high_components']:break
        if g not in test:test.append(g)
    rest=[g for g in order if g not in test]
    val=rest[:criteria['validation_high_components']]
    train=rest[criteria['validation_high_components']:criteria['validation_high_components']+criteria['train_high_components']]
    return {g['geographic_group_id']:split for split,part in [('test',test),('validation',val),('train',train)] for g in part}


def validate_support(rows,assignments,criteria,*,grid_context=None):
    """Full selected-grid context prevents a sparse subset dropping graph bridges."""
    if len(rows)!=len({r['sample_id'] for r in rows}):raise ValueError('Duplicate sample IDs')
    if set(assignments)!={r['sample_id'] for r in rows}:raise ValueError('Incomplete assignments')
    if set(assignments.values())!={'train','validation','test'}:raise ValueError('Empty/invalid partition')
    if grid_context is not None:
        context={r['subtile_id']:r['spatial_group_id'] for r in spatial_rows(grid_context)}
        if any(context.get(r['subtile_id'])!=r['spatial_group_id'] for r in rows):raise ValueError('Global component identity mismatch')
    seen={}
    for row in rows:
        for key in ('spatial_group_id','subtile_id'):
            identity=(key,row[key]);part=assignments[row['sample_id']]
            if identity in seen and seen[identity]!=part:raise ValueError('Geographic/subtile leakage')
            seen[identity]=part
    # Additionally reconstruct adjacency among retained subtiles.
    normal=[{**r,'sen2_member':r.get('sen2_member',r['member'].replace('_cyan.npy','_sen2.npy'))} for r in rows]
    validate_geographic(normal,assignments)
    result=[]
    for split in ('train','validation','test'):
        part=[r for r in rows if assignments[r['sample_id']]==split]
        groups=group_support(part)
        high=sum(qualifies(g,criteria) for g in groups)
        needed=criteria[split+'_high_components']
        counts=[sum(int(r[k+'_pixels']) for r in part) for k in ('low','moderate','high')]
        if min(counts)<=0:raise ValueError('Missing target class in '+split)
        if high<needed:raise ValueError(f'Insufficient qualified High groups in {split}: {high} < {needed}')
        if split=='test' and len({t for g in groups if qualifies(g,criteria) for t in g['source_tiles']})<criteria['test_source_tiles']:
            raise ValueError('Test lacks source tile diversity')
        result.append({'split':split,'patches':len(part),'geographic_groups':len(groups),'qualified_high_groups':high,
                       'valid_pixels':sum(counts),'low_pixels':counts[0],'moderate_pixels':counts[1],'high_pixels':counts[2],
                       'low_percent':100*counts[0]/sum(counts),'moderate_percent':100*counts[1]/sum(counts),'high_percent':100*counts[2]/sum(counts)})
    return result

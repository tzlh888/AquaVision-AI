"""Dataset-only follow-up to resolve sparse dates/positions in observed High regions."""
import csv,json,hashlib
from pathlib import Path
from collections import defaultdict
from datetime import date
from aquavision.data.geographic_split import freeze_json
from aquavision.data.evaluation_support import group_support,qualifies

ROOT=Path('data/metadata/phase3_5')


def main():
    old=json.loads((ROOT/'reference_screening_plan.json').read_text())
    observed=list(csv.DictReader((ROOT/'reference_census.csv').open()))
    criteria=json.loads(Path('configs/phase3_5.json').read_text())['criteria']
    groups=group_support(observed)
    targets={g['geographic_group_id'] for g in groups if g['high_pixels'] and not qualifies(g,criteria)}
    positions=defaultdict(set);dates=defaultdict(set)
    for r in observed:
        if int(r['high_pixels'])>0:
            positions[r['spatial_group_id']].add((r['subtile_id'],int(r['patch_row']),int(r['patch_col'])))
            dates[r['spatial_group_id']].add(date.fromisoformat(r['date']))
    seen={r['sample_id'] for r in observed};candidates=defaultdict(list)
    for path in ROOT.glob('*_entries.csv'):
        for r in csv.DictReader(path.open()):
            if r['kind']!='cyan' or r['sample_id'] in seen:continue
            g=old['components'][r['subtile_id']]
            if g in targets:candidates[g].append({**r,'spatial_group_id':g})
    chosen=[]
    for g,rows in sorted(candidates.items()):
        def priority(r):
            pos=(r['subtile_id'],int(r['patch_row']),int(r['patch_col']))
            distance=0 if pos in positions[g] else 1 if any((pos[0],pos[1]+dx,pos[2]+dy) in positions[g] for dx in(-64,0,64) for dy in(-64,0,64)) else 2
            far=any(abs((date.fromisoformat(r['date'])-d).days)>=30 for d in dates[g])
            return (not far,distance,hashlib.sha256(('35042:'+r['date']).encode()).hexdigest(),hashlib.sha256(('35042:'+r['sample_id']).encode()).hexdigest())
        chosen.extend(sorted(rows,key=priority)[:1024])
    all_rows=old['screening_rows']+chosen
    if len(all_rows)>50000:raise ValueError('Mask cap')
    plan={**old,'round':2,'followup_targets':sorted(targets),'followup_added_masks':len(chosen),
          'followup_rule':'Observed High but insufficient support: prioritize >=30-day alternate dates and same/neighboring grid positions, then hash; max1024 per component; no model outputs',
          'screening_rows':sorted(all_rows,key=lambda r:(r['archive'],int(r['header_offset'])))}
    freeze_json(ROOT/'reference_screening_plan_round2.json',plan)
    print(json.dumps({'followup_targets':sorted(targets),'added_masks':len(chosen),'total_masks':len(all_rows),'support_criteria_unchanged':True},indent=2))

if __name__=='__main__':main()

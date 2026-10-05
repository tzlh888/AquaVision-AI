"""Summarize decoded reference evidence before any new paired imagery download."""
import csv,hashlib,json
from collections import defaultdict,Counter
from datetime import date
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from aquavision.data.evaluation_support import group_support,qualifies,choose_groups
from aquavision.data.metadata import write_csv

ROOT=Path('data/metadata/phase3_5');OUT=Path('research_outputs/phase3_5');REPORTS=Path('research_outputs/reports')


def summarize(rows):
    high=[r for r in rows if int(r['high_pixels'])>0]
    counts=[sum(int(r[k+'_pixels']) for r in rows) for k in ('low','moderate','high')]
    return {'decoded_pairs':len(rows),'valid_pixels':sum(counts),'low_pixels':counts[0],'moderate_pixels':counts[1],'high_pixels':counts[2],
            'high_percent_valid':100*counts[2]/sum(counts) if sum(counts) else None,
            'high_pairs':len(high),'high_components':len({r['spatial_group_id'] for r in high}),
            'high_subtiles':len({r['subtile_id'] for r in high}),'high_dates':len({r['date'] for r in high}),
            'high_source_tiles':sorted({r['tile'] for r in high})}


def main():
    suffix='_round2' if (ROOT/'reference_census_round2_completion.json').exists() else ''
    census_path=ROOT/f'reference_census{suffix}.csv'
    completion=json.loads((ROOT/f'reference_census{suffix}_completion.json').read_text())
    if not completion['complete']:raise ValueError('Screening not complete')
    rows=list(csv.DictReader(census_path.open()))
    plan=json.loads((ROOT/'reference_screening_plan.json').read_text())
    criteria=json.loads(Path('configs/phase3_5.json').read_text())['criteria']
    cached=[r for r in rows if r['archive'] in ('dataset_train_6_2.zip','dataset_train_7_2.zip')]
    if len(cached)!=24518:raise ValueError('Original pool census incomplete')
    summary={'cached_pool':summarize(cached),'all_screened':summarize(rows),'full_index_pairs':plan['all_pairs'],
             'full_index_subtiles':plan['subtiles'],'full_index_components':len(set(plan['components'].values())),
             'uninspected_references':plan['all_pairs']-len(rows),'full_corpus_pixel_counts':'UNKNOWN outside decoded references'}
    summary['reference_census_path']=str(census_path)
    summary['reference_completion_path']=str(ROOT/f'reference_census{suffix}_completion.json')
    summary['screening_round']=2 if suffix else 1
    groups=group_support(rows)
    for g in groups:g['qualifies']=qualifies(g,criteria)
    summary['qualifying_components']=[g['geographic_group_id'] for g in groups if g['qualifies']]
    try:
        allocation=choose_groups(groups,criteria)
        summary['candidate_gate']='PASS';summary['candidate_allocation']=allocation
    except ValueError as e:
        summary['candidate_gate']='BLOCKED';summary['reason']=str(e)
    by_date=defaultdict(list)
    for r in rows:by_date[(r['spatial_group_id'],r['tile'],r['subtile_id'],r['date'])].append(r)
    date_table=[]
    for (g,t,s,d),part in sorted(by_date.items()):
        a=summarize(part)
        date_table.append({'geographic_group_id':g,'source_tile':t,'subtile':s,'date':d,**a,'sentinel_scene_ids':'UNKNOWN'})
    independence=[]
    for g in groups:
        part=[r for r in rows if r['spatial_group_id']==g['geographic_group_id'] and int(r['high_pixels'])>0]
        lookup={(r['subtile_id'],r['date'],int(r['patch_row']),int(r['patch_col'])) for r in part}
        neighbors=sum(any((r['subtile_id'],r['date'],int(r['patch_row'])+dr,int(r['patch_col'])+dc) in lookup
                         for dr in (-64,0,64) for dc in (-64,0,64) if(dr,dc)!=(0,0)) for r in part)
        positions=defaultdict(set)
        for r in part:positions[(r['subtile_id'],r['patch_row'],r['patch_col'])].add(r['date'])
        close_dates=sum(any(0<(date.fromisoformat(b)-date.fromisoformat(a)).days<=30 for a,b in zip(sorted(ds),sorted(ds)[1:])) for ds in positions.values())
        exact=Counter(r['reference_sha256'] for r in part)
        independence.append({'geographic_group_id':g['geographic_group_id'],'high_patches':len(part),'high_patch_positions':len(positions),
            'positions_repeated_across_dates':sum(len(ds)>1 for ds in positions.values()),'positions_repeated_within_30_days':close_dates,
            'high_patches_with_same_date_neighbor':neighbors,'identical_high_mask_extra_patches':sum(n-1 for n in exact.values()),
            'scene_identity':'UNKNOWN','physical_overlap':'UNKNOWN','bloom_episode_identity':'UNKNOWN'})
    OUT.mkdir(exist_ok=True)
    (OUT/'high_support_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (OUT/'group_support.json').write_text(json.dumps(groups,indent=2)+'\n')
    write_csv(OUT/'high_group_candidates.csv',[{**g,'source_tiles':json.dumps(g['source_tiles']),'subtiles':json.dumps(g['subtiles']),'high_dates':json.dumps(g['high_dates'])} for g in groups])
    write_csv(OUT/'high_group_subtile_date.csv',date_table)
    write_csv(OUT/'high_independence.csv',independence)
    write_csv(OUT/'high_patch_candidates.csv',[r for r in rows if int(r['high_pixels'])>0])
    a,b=summary['cached_pool'],summary['all_screened']
    table='| Scope | Decoded pairs | High pairs | Valid pixels | High pixels | High % | High components | High dates | High source tiles |\n|---|---:|---:|---:|---:|---:|---:|---:|---|\n'
    for scope,r in [('Original cached pool — complete census',a),('All screened — selected outside pool',b)]:
        table+=f"| {scope} | {r['decoded_pairs']:,} | {r['high_pairs']:,} | {r['valid_pixels']:,} | {r['high_pixels']:,} | {r['high_percent_valid']:.6f} | {r['high_components']} | {r['high_dates']} | {', '.join(r['high_source_tiles'])} |\n"
    ranked=sorted(groups,key=lambda g:(-g['qualifies'],-g['high_date_count'],-g['high_patch_positions'],-g['high_subtiles'],g['geographic_group_id']))
    group_table='| Component | High pixels | High dates | Date span days | High grid positions | Qualified |\n|---|---:|---:|---:|---:|---|\n'
    for g in ranked:
        if g['high_patches']:
            group_table+=f"| {g['geographic_group_id']} | {g['high_pixels']:,} | {g['high_date_count']} | {g['high_date_span_days']} | {g['high_patch_positions']} | {g['qualifies']} |\n"
    (REPORTS/'HIGH_RISK_SUPPORT_AUDIT.md').write_text(f'''# High-risk support audit

The original 24,518-pair pool now has a **complete decoded reference census**, not a CRC-based inference. Every reference was read from its source or an already verified local pair; ZIP CRC, uncompressed size, NPY shape/dtype and SHA-256 were recorded. No Sentinel-2 member was downloaded for this census.

{table}
The full six-archive directory inventory contains **{plan['all_pairs']:,} paired IDs, {plan['subtiles']} selected subtiles and {len(set(plan['components'].values()))} connected selected regions**. The publication's 938,607-pair experiment is a different reported total; it must not replace the measured deposit inventory. All six central directories were read, but only {len(rows):,} reference masks were decoded. The other {summary['uninspected_references']:,} reference contents remain uninspected.

Outside the original pool, screening selected up to 16 hash-ranked dates per subtile and up to four high-compressed-size reference members per date. This metadata-only heuristic favors varied masks; it does not imply High until decoded. These selected counts are **not** full-deposit class prevalence. No model outputs were accessed for candidate selection.

{group_table}
Candidate usefulness depends on dates, distinct grid positions and subtiles within independently held-out components; raw High pixel count alone is insufficient. Allocation tie-breaking is fixed seed-35042 hashing, never model performance. Exact candidate rows and every component/date/subtile are in `research_outputs/phase3_5/high_group_candidates.csv`, `high_group_subtile_date.csv`, and `high_patch_candidates.csv`.

The preregistered candidate gate is **{summary['candidate_gate']}**; qualifying components: {len(summary['qualifying_components'])}. Passing this candidate gate does not yet freeze a split or authorize model evaluation: selected pairs must still meet support and integrity criteria after acquisition.

The original support-criteria contract is preserved. Acquisition amendment A was recorded after a two-range transport probe showed batching could make a full census practical. It changed only the mask-count limit; all scientific support criteria, 64 MiB reference byte budget and 1,200-request cap stayed fixed. Reference requests and charged bytes are logged under `data/metadata/phase3_5/`.
''')
    (REPORTS/'HIGH_RISK_INDEPENDENCE_AUDIT.md').write_text(f'''# High-risk independence audit

Pixel totals and numbers of independent geographic components are reported separately. The complete selected-grid graph contains {len(set(plan['components'].values()))} components across five CyAN tiles. Source subtiles inside a connected component are not counted as independent test regions. All dates inherit the same grouping.

Among decoded High-bearing references, there are {sum(r['high_patches_with_same_date_neighbor'] for r in independence):,} patches with another High-bearing adjacent patch on the same parent/date grid, {sum(r['positions_repeated_across_dates'] for r in independence):,} grid positions recurring across dates, and {sum(r['positions_repeated_within_30_days'] for r in independence):,} positions repeating within 30 days. These are correlated support, not independent geographic replicates. Exact tabulations are in `high_independence.csv`.

Identical label-mask hashes are also counted, but equal reference masks alone do not prove duplicate Sentinel inputs or identical geographic footprints. Input content hashes are checked after any selective paired-image acquisition. Final grid transforms and scene UUIDs were not preserved; exact source-scene sharing and physical overlap remain UNKNOWN. Dates are not renamed scene identifiers.

A 30-day span criterion reduces dependence on a single short observation window but cannot establish bloom-episode identity. Long events may span months, neighboring patches share interpolated coarse reference cells, and separate subtiles may share a lake or source scene. Same CyAN tile is reported as a shared larger source unit; multiple within-tile components are not assumed hydrologically independent.

The best-supported independence claim is **disjoint connected selected author-grid regions**, with test regions spanning multiple CyAN tiles when the gate permits. Unknown cross-tile lake/scene dependence remains a limitation. No latitude/longitude or bloom-event IDs are invented. Rankings use only source metadata and decoded references, never model scores.
''')
    # Grid schematic, explicitly not geographic coordinates.
    fig,axes=plt.subplots(1,5,figsize=(18,4))
    by_sub=defaultdict(int)
    for r in rows:by_sub[r['subtile_id']]+=int(r['high_pixels'])
    for ax,tile in zip(axes,('6_2','6_5','7_2','7_5','8_3')):
        for sid,group in plan['components'].items():
            if not sid.startswith(tile+'_'):continue
            bits=sid.split('_');x=int(bits[2][1:]);y=int(bits[3][1:])
            ax.scatter(x,y,c='#d73027' if by_sub[sid]>0 else '#bdbdbd',s=22,marker='s')
        ax.set(title=tile,xlim=(-50,2050),ylim=(2050,-50),xlabel='Parent column X');ax.set_aspect('equal')
    axes[0].set_ylabel('Parent row Y')
    fig.suptitle('Author-grid support: red = decoded High; grey = none observed in screened references (not proof of absence)')
    fig.tight_layout();fig.savefig(OUT/'high_support_grid.png',dpi=150);plt.close(fig)
    if suffix:
        with (REPORTS/'HIGH_RISK_SUPPORT_AUDIT.md').open('a') as stream:
            stream.write('\n## Targeted follow-up (round 2)\n\nThe first round identified five qualifying regions. Before any paired imagery or model evaluation, a frozen follow-up plan examined alternate dates (prioritizing spans ≥30 days) at known High grid positions, neighboring positions and then other positions in High-bearing but nonqualifying components. At most 1,024 additional masks per such component were selected. All criteria and the cumulative reference budget stayed unchanged. The original complete 24,518-mask census and round-1 audit are preserved; merged round-2 counts add targeted observations and remain unsuitable as full-corpus prevalence.\n')
    (ROOT/'candidate_audit_completed.json').write_text(json.dumps({'candidate_gate':summary['candidate_gate'],'reference_census_path':str(census_path),'reference_census_sha256':hashlib.sha256(census_path.read_bytes()).hexdigest(),'report_sha256':hashlib.sha256((REPORTS/'HIGH_RISK_SUPPORT_AUDIT.md').read_bytes()).hexdigest(),'criteria':criteria},indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()

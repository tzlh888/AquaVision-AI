"""Report exact pilot pixel counts and index-level split leakage; no model fitting."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from aquavision.data.labels import segmentation_target, IGNORE_INDEX
from aquavision.data.metadata import write_csv
from aquavision.data.segmentation_dataset import verify_samples


def overlap(rows, assignments, key):
    train=[r for r in rows if assignments[r['sample_id']]=='train']
    test=[r for r in rows if assignments[r['sample_id']]=='test']
    known={r[key] for r in train if r.get(key)}
    count=sum(r.get(key) in known for r in test if r.get(key))
    return {'test_patches':len(test),'exposed_test_patches':count,'fraction':count/len(test) if test else None,
            'shared_ids':len(known & {r[key] for r in test if r.get(key)})}


def leakage(rows,assignments):
    out={key:overlap(rows,assignments,key) for key in ('subtile_id','region','spatial_group_id','grid_position_candidate')}
    lookup={(r['subtile_id'],r['acquisition_date'],int(r['patch_row']),int(r['patch_col']))
            for r in rows if assignments[r['sample_id']]=='train'}
    tests=[r for r in rows if assignments[r['sample_id']]=='test']
    count=sum(any((r['subtile_id'],r['acquisition_date'],int(r['patch_row'])+dr,int(r['patch_col'])+dc) in lookup
                  for dr in (-64,0,64) for dc in (-64,0,64) if (dr,dc)!=(0,0)) for r in tests)
    out['neighboring_patch_same_parent_date']={'exposed_test_patches':count,'test_patches':len(tests),'fraction':count/len(tests)}
    out['sentinel_scene_overlap']='UNKNOWN: UUID not preserved; dates are not scene IDs'
    out['identical_physical_footprints']='UNKNOWN: grid offsets are candidates, no final transforms'
    return out


def main():
    plan=json.loads(Path('data/metadata/phase3/frozen_plan.json').read_text())
    manifest=json.loads(Path('data/metadata/phase3/pilot_manifest.json').read_text())
    rows=manifest['samples']; verify_samples(rows)
    index=[]
    from aquavision.data.geographic_split import spatial_rows
    for p in sorted(Path('data/metadata').glob('*_pairs.csv')): index.extend(csv.DictReader(p.open()))
    index=spatial_rows(index)
    audit=[]; summaries={}; thumbnails={}
    for r in rows:
        raw=np.load(r['cyan_path'],allow_pickle=False)
        y=segmentation_target(raw)
        count=np.bincount(y[y!=IGNORE_INDEX],minlength=3)
        audit.append({'sample_id':r['sample_id'],'subtile_id':r['subtile_id'],'spatial_group_id':r['spatial_group_id'],
                      'date':r['acquisition_date'],'low_pixels':int(count[0]),'moderate_pixels':int(count[1]),'high_pixels':int(count[2]),
                      'valid_pixels':int(count.sum()),'ignored_pixels':int((y==IGNORE_INDEX).sum()),
                      'raw_254':int((raw==254).sum()),'raw_255':int((raw==255).sum()),
                      'random_split':plan['splits']['random'][r['sample_id']],
                      'geographic_split':plan['splits']['geographic'][r['sample_id']]})
        x=np.load(r['sen2_path'],allow_pickle=False).astype(float)/10000
        thumbnails[r['sample_id']]=x.reshape(12,8,8,8,8).mean((2,4)).ravel()
    for strategy,assignment in plan['splits'].items():
        summaries[strategy]={}
        for split in ('train','validation','test','all'):
            part=[r for r in audit if split=='all' or r[strategy+'_split']==split]
            counts=[sum(r[k+'_pixels'] for r in part) for k in ('low','moderate','high')]
            total=sum(counts)
            summaries[strategy][split]={'patches':len(part),'counts':counts,'valid_pixels':total,
                                       'percent_valid_by_class':[100*c/total if total else None for c in counts],
                                       'ignored_pixels':sum(r['ignored_pixels'] for r in part)}
    leaks={'index':{s:leakage(index,a) for s,a in plan['index_splits'].items()},
           'pilot':{s:leakage(rows,a) for s,a in plan['splits'].items()}}
    for s,a in plan['splits'].items():
        leaks['pilot'][s]['exact_input_sha256']=overlap(rows,a,'sen2_sha256')
        train=[r for r in rows if a[r['sample_id']]=='train']; test=[r for r in rows if a[r['sample_id']]=='test']
        t=np.stack([thumbnails[r['sample_id']] for r in train])
        distances=[float(np.abs(t-thumbnails[r['sample_id']]).mean(1).min()) for r in test]
        leaks['pilot'][s]['appearance_similarity']={'definition':'nearest train mean absolute difference of 12-band 8x8 block means after /10000; <=0.001',
            'exposed_test_patches':sum(d<=.001 for d in distances),'test_patches':len(test),
            'minimum_distances':distances,'caveat':'appearance diagnostic, not verified near-identical geographic footprints'}
    stats={'index_pairs':len(index),'subtiles':len({r['subtile_id'] for r in index}),
           'components':len({r['spatial_group_id'] for r in index}),'dates':len({r['acquisition_date'] for r in index}),
           'sentinel_scenes':None,'full_index_pixel_counts':None,'pilot':summaries,'pilot_pairs':len(rows),
           'author_reproduction_counts':dict(Counter(plan['author_reproduction'].values()))}
    Path('research_outputs/tables/phase3_statistics.json').write_text(json.dumps(stats,indent=2)+'\n')
    Path('research_outputs/tables/phase3_leakage.json').write_text(json.dumps(leaks,indent=2)+'\n')
    write_csv(Path('research_outputs/tables/phase3_pixel_audit.csv'),audit)
    for scope,source,assigns in [('pilot',rows,plan['splits']),('index',index,plan['index_splits'])]:
        for strategy,a in assigns.items():
            write_csv(Path(f'data/metadata/phase3/{scope}_{strategy}_split.csv'),
                      [{'sample_id':r['sample_id'],'split':a[r['sample_id']],'subtile_id':r['subtile_id'],'spatial_group_id':r['spatial_group_id']} for r in source])
    fig,axes=plt.subplots(1,2,figsize=(11,5))
    colors={'train':'#377eb8','validation':'#ff7f00','test':'#e41a1c'}
    for ax,tile in zip(axes,('6_2','7_2')):
        groups={r['subtile_id']:r for r in index if r['region']==tile}
        for split in colors:
            part=[r for r in groups.values() if plan['index_splits']['geographic'][r['sample_id']]==split]
            ax.scatter([int(r['subtile_x']) for r in part],[int(r['subtile_y']) for r in part],c=colors[split],marker='s',s=90,label=split)
        ax.set(title=f'CyAN tile {tile}: selected author grid',xlabel='Parent X (source column)',ylabel='Parent Y (source row)',xlim=(-50,2000),ylim=(2000,-50))
        ax.set_aspect('equal'); ax.legend(fontsize=8)
    fig.suptitle('Fixed geographic pilot split — grid schematic, not a latitude/longitude map')
    fig.tight_layout(); fig.savefig('research_outputs/figures/phase3_author_grid_split.png',dpi=150); plt.close(fig)
    print(json.dumps(stats,indent=2))

if __name__=='__main__': main()

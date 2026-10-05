"""Acquire support-selected real pairs only after the completed reference audit."""
import csv,hashlib,json,time
from collections import defaultdict
from pathlib import Path
import numpy as np
import requests
from aquavision.data.evaluation_support import group_support,choose_groups,validate_support,qualifies
from aquavision.data.geographic_split import freeze_json
from aquavision.data.reference_ranges import coalesce_touching,parse_multipart,decode_zip_member
from aquavision.data.download import save_member
from aquavision.data.loader import load_pair
from aquavision.data.metadata import write_csv

ROOT=Path('data/metadata/phase3_5');OUT=Path('research_outputs/phase3_5')


def rank(s):return hashlib.sha256(('35042:'+s).encode()).hexdigest()


def main():
    config=json.loads(Path('configs/phase3_5.json').read_text());criteria=config['criteria']
    audit=json.loads((ROOT/'candidate_audit_completed.json').read_text())
    if audit['candidate_gate']!='PASS':raise ValueError('Candidate support gate blocked; no pair download')
    census_path=Path(audit['reference_census_path'])
    if hashlib.sha256(census_path.read_bytes()).hexdigest()!=audit['reference_census_sha256']:raise ValueError('Census changed')
    rows=list(csv.DictReader(census_path.open()))
    plan=json.loads((ROOT/'reference_screening_plan.json').read_text())
    allocation=choose_groups(group_support(rows),criteria)
    selected=[]
    for group in sorted(allocation):
        pool=[r for r in rows if r['spatial_group_id']==group]
        high=[r for r in pool if int(r['high_pixels'])>0]
        dates=sorted({r['date'] for r in high})
        chosen={}
        # Preserve longitudinal anchors; prioritize different grid positions.
        for d in (dates[0],dates[-1]):
            subset=sorted([r for r in high if r['date']==d],key=lambda r:(-int(r['high_pixels']),rank(r['sample_id'])))
            for r in subset[:2]:chosen[r['sample_id']]=r
        for r in sorted(high,key=lambda r:(-int(r['high_pixels']),rank(r['sample_id']))):
            if qualifies(group_support(list(chosen.values()))[0],criteria):break
            chosen[r['sample_id']]=r
        anchors=set(chosen)
        for r in sorted(pool,key=lambda r:rank(r['sample_id'])):
            if len(chosen)>=48:break
            chosen[r['sample_id']]=r
        if len(chosen)>64:raise ValueError('Support anchors exceed per-group cap')
        for r in chosen.values():
            reason='High support/date/position anchors' if r['sample_id'] in anchors else 'Fixed hash background coverage'
            selected.append({**r,'inclusion_reason':reason,'sen2_member':r['member'].replace('_cyan.npy','_sen2.npy')})
    selected.sort(key=lambda r:r['sample_id'])
    if len(selected)>config['budgets']['max_new_pairs']:raise ValueError('Pair count cap')
    assignments={r['sample_id']:allocation[r['spatial_group_id']] for r in selected}
    context=[]
    for sid in plan['components']:
        r=next(r for r in plan['screening_rows'] if r['subtile_id']==sid)
        context.append({'sample_id':r['sample_id'],'sen2_member':r['member'].replace('_cyan.npy','_sen2.npy')})
    support=validate_support(selected,assignments,criteria,grid_context=context)
    selection={'version':'geographic_split_v2','criteria':criteria,'groups':allocation,'assignments':assignments,
               'samples':selected,'support_before_pair_download':support,'model_scores_used':False,
               'sampling_bias':'High/date support anchors plus fixed-hash background; support-enriched, not natural prevalence'}
    selection_hash=freeze_json(ROOT/'planned_v2_pairs.json',selection)
    write_csv(OUT/'planned_split_support.csv',support)
    needed={r['sen2_member']:r for r in selected};entries={}
    for path in ROOT.glob('*_entries.csv'):
        for r in csv.DictReader(path.open()):
            if r['member'] in needed and r['kind']=='sen2':entries[r['sample_id']]=r
    if set(entries)!={r['sample_id'] for r in selected}:raise ValueError('Missing matching Sentinel members')
    catalog=json.loads(Path('data/metadata/sources/zenodo_record.json').read_text());source={r['key']:r for r in catalog['files']}
    manifest=[];remaining=defaultdict(list)
    old={r['sample_id']:r for r in json.loads(Path('data/metadata/phase3/pilot_manifest.json').read_text())['samples']}
    def complete(row,path):
        ref=Path(row['reference_path']);x,y=load_pair(path,ref)
        if x.shape!=(12,64,64) or y.shape!=(1,64,64):raise ValueError('Alignment shape failure')
        manifest.append({**row,'cyan_path':str(ref),'cyan_sha256':row['reference_sha256'],
                         'sen2_path':str(path),'sen2_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    for row in selected:
        path=Path(old[row['sample_id']]['sen2_path']) if row['sample_id'] in old else Path('data/raw/phase3_5_pairs')/(row['sample_id']+'_sen2.npy')
        if path.exists():
            import zlib
            raw=path.read_bytes();entry=entries[row['sample_id']]
            if len(raw)!=int(entry['size_bytes']) or zlib.crc32(raw)!=int(entry['crc32'],16):raise ValueError('Existing input mismatch')
            complete(row,path)
        else:remaining[row['archive']].append(row)
    access=ROOT/'pair_access.jsonl';logs=[json.loads(x) for x in access.read_text().splitlines()] if access.exists() else []
    used=sum(r['charged_bytes'] for r in logs)
    with requests.Session() as session:
        for name,pool in sorted(remaining.items()):
            pool.sort(key=lambda r:int(entries[r['sample_id']]['header_offset']))
            for start in range(0,len(pool),32):
                batch=pool[start:start+32];infos=[entries[r['sample_id']] for r in batch]
                individual=[(int(r['header_offset']),int(r['header_offset'])+int(r['span_bytes'])-1) for r in infos]
                if any(b-a>200000 for a,b in individual):raise ValueError('Input range exceeds bounded member size')
                ranges=coalesce_touching(individual);cap=sum(b-a+1 for a,b in ranges)+512*len(ranges)+512
                for attempt in range(4):
                    if used+cap>config['budgets']['paired_image_bytes']:raise ValueError('Pair byte budget exceeded')
                    used+=cap;time.sleep(1)
                    with session.get(source[name]['links']['self'],headers={'Range':'bytes='+','.join(f'{a}-{b}' for a,b in ranges),'Accept-Encoding':'identity'},stream=True,timeout=(15,60)) as response:
                        with access.open('a') as f:f.write(json.dumps({'archive':name,'status':response.status_code,'charged_bytes':cap,'ranges':ranges})+'\n')
                        if response.status_code==429:
                            if attempt==3:raise ValueError('Rate limit persisted')
                            time.sleep(30);continue
                        if response.status_code!=206 or response.headers.get('Content-Encoding','identity')!='identity':raise ValueError('Invalid partial response')
                        if int(response.headers.get('Content-Length','0'))>cap:raise ValueError('Oversized response header')
                        body=response.raw.read(cap+1)
                        if len(body)>cap:raise ValueError('Oversized response')
                        if len(ranges)==1:
                            a,b=ranges[0]
                            if response.headers.get('Content-Range')!=f'bytes {a}-{b}/{source[name]["size"]}' or len(body)!=b-a+1:raise ValueError('Bad single range')
                            parts={ranges[0]:body}
                        else:parts=parse_multipart(body,ranges,source[name]['size'])
                    for row,entry,(a,b) in zip(batch,infos,individual):
                        owner=next((x,y) for x,y in ranges if x<=a<=b<=y)
                        raw=decode_zip_member(parts[owner][a-owner[0]:b-owner[0]+1],entry)
                        path=Path('data/raw/phase3_5_pairs')/(row['sample_id']+'_sen2.npy')
                        save_member(path,raw);complete(row,path)
                    break
                print(f'{name}: paired {min(start+32,len(pool))}/{len(pool)}; charged={used:,}',flush=True)
    manifest.sort(key=lambda r:r['sample_id'])
    # Identical Sentinel bytes across groups could compromise independent support.
    hashes=defaultdict(set)
    for r in manifest:hashes[r['sen2_sha256']].add(assignments[r['sample_id']])
    if any(len(parts)>1 for parts in hashes.values()):raise ValueError('Exact input duplicate across partitions; quarantine needed')
    actual=validate_support(manifest,assignments,criteria,grid_context=context)
    final={'version':'geographic_split_v2','selection_sha256':selection_hash,'samples':manifest,'assignments':assignments,
           'criteria':criteria,'support':actual,'integrity':'PASS','model_evaluation_allowed':True,'paired_download_charged_bytes':used}
    freeze_json(ROOT/'geographic_split_v2.json',final)
    output=[{'sample_id':r['sample_id'],'split':assignments[r['sample_id']],'spatial_group_id':r['spatial_group_id'],'source_subtile':r['subtile_id'],
              'date':r['date'],'sen2_sha256':r['sen2_sha256'],'cyan_sha256':r['cyan_sha256']} for r in manifest]
    path=ROOT/'geographic_split_v2.csv'
    if path.exists():raise FileExistsError('Refusing to replace v2 split export')
    write_csv(path,output);write_csv(OUT/'split_support.csv',actual)
    print(json.dumps({'frozen_pairs':len(manifest),'support':actual,'integrity':'PASS'},indent=2))

if __name__=='__main__':main()

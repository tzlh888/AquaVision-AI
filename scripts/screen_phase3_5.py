"""Full cached-pool reference census plus bounded, label-only regional screening."""
import csv, hashlib, io, json, time, zlib
from collections import defaultdict
from pathlib import Path
import requests
import sys
import numpy as np
from aquavision.data.reference_ranges import parse_multipart,decode_zip_member,load_reference,coalesce_touching
from aquavision.data.labels import segmentation_target
from aquavision.data.geographic_split import spatial_rows,freeze_json
from aquavision.data.download import save_member
from aquavision.data.metadata import write_csv

ROOT=Path('data/metadata/phase3_5')
RAW=Path('data/raw/phase3_5_references')


def rank(value):return hashlib.sha256(('35042:'+value).encode()).hexdigest()


def build_plan():
    by_subtile=defaultdict(list); metadata=[]; labels=[]; archive_counts={}
    for path in sorted(ROOT.glob('*_entries.csv')):
        count=0
        for row in csv.DictReader(path.open()):
            if row['kind']!='cyan':continue
            count+=1; labels.append(row); by_subtile[row['subtile_id']].append(row)
        archive_counts[path.stem]=count
    examples=[{'sample_id':r[0]['sample_id'],'sen2_member':r[0]['member'].replace('_cyan.npy','_sen2.npy')} for r in by_subtile.values()]
    components={r['subtile_id']:r['spatial_group_id'] for r in spatial_rows(examples)}
    chosen=[]
    cached={'dataset_train_6_2.zip','dataset_train_7_2.zip'}
    for subtile,rows in sorted(by_subtile.items()):
        for row in rows:row['spatial_group_id']=components[subtile]
        if rows[0]['archive'] in cached:
            chosen.extend(rows);continue
        dates=defaultdict(list)
        for row in rows:dates[row['date']].append(row)
        # Screening heuristic, not a prevalence sample: broad date support and
        # complex reference arrays. Compressed length does not establish High.
        selected_dates=sorted(dates,key=rank)[:16]
        for date in selected_dates:
            chosen.extend(sorted(dates[date],key=lambda r:(-int(r['compressed_bytes']),rank(r['sample_id'])))[:4])
    chosen.sort(key=lambda r:(r['archive'],int(r['header_offset'])))
    assert len(chosen)<=50000
    plan={'scope':'complete_original_24518_pool_plus_targeted_other_region_screening',
          'selection':'all original two-archive references; up to 16 hash-selected dates x4 highest compressed-size masks per other subtile',
          'selection_bias':'outside original pool: enriched reference-complexity screening, not natural prevalence',
          'archive_pair_counts':archive_counts,'all_pairs':len(labels),'subtiles':len(components),
          'components':components,'screening_rows':chosen,
          'index_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.glob('*_entries.csv'))}}
    freeze_json(ROOT/'reference_screening_plan.json',plan)
    summary={k:v for k,v in plan.items() if k not in ('screening_rows','components','index_sha256')}
    summary['components_count']=len(set(components.values()));summary['planned_masks']=len(chosen)
    print(json.dumps(summary),flush=True)
    return plan


def main():
    RAW.mkdir(parents=True,exist_ok=True)
    round2='--round2' in sys.argv
    plan=json.loads((ROOT/'reference_screening_plan_round2.json').read_text()) if round2 else build_plan()
    suffix='_round2' if round2 else ''
    catalog=json.loads(Path('data/metadata/sources/zenodo_record.json').read_text())
    sources={f['key']:f for f in catalog['files']}
    log_path=ROOT/'reference_access.jsonl'
    old_logs=[json.loads(x) for x in log_path.read_text().splitlines()] if log_path.exists() else []
    used=sum(x.get('charged_bytes',0) for x in old_logs); calls=len(old_logs)
    existing={}
    for path in ('data/metadata/sample_manifest.json','data/metadata/phase3/pilot_manifest.json'):
        for r in json.loads(Path(path).read_text())['samples']:existing[r['sample_id']]=r['cyan_path']
    diagnostics=[]
    def record(entry,raw,path):
        arr=load_reference(raw); target=segmentation_target(arr)
        c=np.bincount(target[target>=0],minlength=3)
        diagnostics.append({**entry,'reference_path':str(path),'reference_sha256':hashlib.sha256(raw).hexdigest(),
            'valid_pixels':int(c.sum()),'low_pixels':int(c[0]),'moderate_pixels':int(c[1]),'high_pixels':int(c[2]),
            'ignored_pixels':int((target<0).sum()),'high_percent':100*int(c[2])/int(c.sum()) if c.sum() else 0,
            'status':'DECODED_CRC_VERIFIED'})
    remaining=defaultdict(list)
    for entry in plan['screening_rows']:
        path=Path(existing.get(entry['sample_id'],str(RAW/(entry['sample_id']+'_cyan.npy'))))
        if path.exists():
            raw=path.read_bytes()
            if len(raw)!=int(entry['size_bytes']) or zlib.crc32(raw)!=int(entry['crc32'],16):raise ValueError('Cached reference mismatch')
            record(entry,raw,path)
        else:remaining[entry['archive']].append(entry)
    session=requests.Session()
    try:
        # Finish current pool first, then inspect additional tiles.
        names=sorted(remaining,key=lambda s:(s not in ('dataset_train_6_2.zip','dataset_train_7_2.zip'),s))
        for name in names:
            rows=remaining[name]; source=sources[name]
            for start in range(0,len(rows),64):
                batch=rows[start:start+64]
                member_ranges=[(int(r['header_offset']),int(r['header_offset'])+int(r['span_bytes'])-1) for r in batch]
                if any(b-a+1>20000 for a,b in member_ranges):raise ValueError('Reference member span exceeds strict limit')
                ranges=coalesce_touching(member_ranges)
                # A single last member uses ordinary Content-Range, not multipart.
                cap=sum(b-a+1 for a,b in ranges)+512*len(ranges)+512
                for attempt in range(4):
                    if used+cap>67108864 or calls>=1200:raise RuntimeError('Reference budget exhausted')
                    used+=cap;calls+=1
                    headers={'Range':'bytes='+','.join(f'{a}-{b}' for a,b in ranges),'Accept-Encoding':'identity'}
                    time.sleep(0.9)
                    with session.get(source['links']['self'],headers=headers,stream=True,timeout=(15,60)) as response:
                        log={'archive':name,'ranges':ranges,'status':response.status_code,'charged_bytes':cap,'attempt':attempt+1}
                        with log_path.open('a') as f:f.write(json.dumps(log)+'\n')
                        if response.status_code==429:
                            retry=response.headers.get('Retry-After','30')
                            delay=max(30,min(120,int(retry))) if retry.isdigit() else 30
                            print(f'429: waiting {delay}s',flush=True)
                            if attempt==3:raise RuntimeError('Repeated source rate limit')
                            time.sleep(delay);continue
                        if response.status_code!=206:raise ValueError('Expected 206; full responses refused')
                        if response.headers.get('Content-Encoding','identity')!='identity':raise ValueError('Encoded range response')
                        declared=response.headers.get('Content-Length')
                        if declared and int(declared)>cap:raise ValueError('Oversized response header')
                        body=response.raw.read(cap+1)
                        if len(body)>cap:raise ValueError('Oversized body')
                        if len(ranges)==1:
                            a,b=ranges[0]
                            if response.headers.get('Content-Range')!=f'bytes {a}-{b}/{source["size"]}' or len(body)!=b-a+1:raise ValueError('Bad single range')
                            parts={ranges[0]:body}
                        else:
                            try:parts=parse_multipart(body,ranges,source['size'])
                            except ValueError:
                                (ROOT/'failed_multipart_response.bin').write_bytes(body)
                                raise
                    for entry,(a,b) in zip(batch,member_ranges):
                        owner=next((x,y) for x,y in ranges if x<=a<=b<=y)
                        raw=decode_zip_member(parts[owner][a-owner[0]:b-owner[0]+1],entry)
                        path=RAW/(entry['sample_id']+'_cyan.npy')
                        save_member(path,raw);record(entry,raw,path)
                    break
                if (start//64)%10==0 or start+64>=len(rows):
                    print(f'{name}: {min(start+64,len(rows))}/{len(rows)} new masks; total decoded={len(diagnostics)}; charged={used:,}; requests={calls}',flush=True)
                    write_csv(ROOT/f'reference_census{suffix}_partial.csv',diagnostics)
    finally:
        session.close()
        if diagnostics:write_csv(ROOT/f'reference_census{suffix}_partial.csv',diagnostics)
    write_csv(ROOT/f'reference_census{suffix}.csv',sorted(diagnostics,key=lambda r:r['sample_id']))
    freeze_json(ROOT/f'reference_census{suffix}_completion.json',{'decoded':len(diagnostics),'planned':len(plan['screening_rows']),'charged_bytes':used,'requests':calls,'complete':len(diagnostics)==len(plan['screening_rows'])})
    print('Reference census/screen complete.',flush=True)

if __name__=='__main__':main()

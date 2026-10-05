"""Read only ZIP central directories; preserve original cached Phase 3 indices."""
import csv
import json
import time
import zipfile
from pathlib import Path
from aquavision.data.download import HTTPRangeReader, ByteBudget, RangeProtocolError
from aquavision.data.metadata import parse_member, write_csv

ROOT=Path('data/metadata/phase3_5')

class PoliteReader(HTTPRangeReader):
    def read(self,size=-1):
        for attempt in range(4):
            try: return super().read(size)
            except RangeProtocolError as e:
                if 'got 429' not in str(e) or attempt==3: raise
                print('Metadata rate limit: wait 30s',flush=True); time.sleep(30)


def main():
    config=json.loads(Path('configs/phase3_5.json').read_text())
    catalog=json.loads(Path('data/metadata/sources/zenodo_record.json').read_text())
    budget=ByteBudget(config['budgets']['index_bytes'])
    logs=[]
    for item in sorted(catalog['files'],key=lambda f:f['key']):
        path=ROOT/(Path(item['key']).stem+'_entries.csv')
        if path.exists():
            print('Cached:',path.name,flush=True); continue
        with PoliteReader(item['links']['self'],item['size'],budget) as remote:
            try:
                with zipfile.ZipFile(remote) as archive:
                    infos=sorted([i for i in archive.infolist() if not i.is_dir()],key=lambda i:i.header_offset)
                    pairs={}; entries=[]; end=archive.start_dir
                    for n,info in enumerate(infos):
                        row=parse_member(info.filename)
                        pair=pairs.setdefault(row['sample_id'],set()); pair.add(row['kind'])
                        entries.append({'archive':item['key'],'member':info.filename,'kind':row['kind'],
                            'sample_id':row['sample_id'],'tile':row['region'],'subtile_id':row['spatial_group_candidate'],
                            'date':row['acquisition_date'],'patch_row':row['patch_row'],'patch_col':row['patch_col'],
                            'header_offset':info.header_offset,'span_bytes':(infos[n+1].header_offset if n+1<len(infos) else end)-info.header_offset,
                            'compressed_bytes':info.compress_size,'size_bytes':info.file_size,'crc32':f'{info.CRC:08x}',
                            'compression':info.compress_type})
                    if any(k != {'cyan','sen2'} for k in pairs.values()):raise ValueError('Unpaired members')
                    write_csv(path,entries)
                    print(json.dumps({'archive':item['key'],'pairs':len(pairs),'subtiles':len({r['subtile_id'] for r in entries}),'charged_bytes_so_far':budget.used}),flush=True)
            finally:
                logs.append({'archive':item['key'],'requests':remote.requests_log,'charged_bytes_so_far':budget.used})
                (ROOT/'index_access.json').write_text(json.dumps(logs,indent=2)+'\n')
    print('Metadata index complete; no array members downloaded.',flush=True)

if __name__=='__main__':main()

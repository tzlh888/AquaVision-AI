"""Freeze label-blind pilot membership/splits, then optionally fetch bounded pairs."""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import zipfile
import time
from datetime import datetime, timezone

from aquavision.data.download import HTTPRangeReader, ByteBudget, RangeProtocolError, read_member, save_member
from aquavision.data.geographic_split import spatial_rows, experiment_partitions, author_partition, ratio_diagnostics, freeze_json


class ChunkReader(HTTPRangeReader):
    """64 KiB cache reduces ZIP header/payload network round trips; budget charged."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chunks = {}

    def bounded_read(self, count):
        for attempt in range(4):
            time.sleep(0.6)
            try:
                return super().read(count)
            except RangeProtocolError as exc:
                if 'got 429' not in str(exc) or attempt == 3:
                    raise
                delay = 30 * (attempt+1)
                print(f'Rate limited; pausing {delay}s before retry', flush=True)
                time.sleep(delay)

    def close(self):
        if not self.closed:
            folder = Path('data/metadata/phase3/access_logs')
            folder.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
            (folder/(stamp+'.json')).write_text(json.dumps({'url':self.url, 'charged_bytes':self.budget.used, 'requests':self.requests_log},indent=2)+'\n')
        super().close()

    def read(self, size=-1):
        count = max(0, self.size-self.position)
        if size >= 0:
            count = min(count, size)
        if not count:
            return b''
        if count > 65536:
            return self.bounded_read(count)
        start, end = self.position, self.position+count
        pieces = []
        for offset in range(start//65536*65536, end, 65536):
            if offset not in self.chunks:
                self.position = offset
                self.chunks[offset] = self.bounded_read(min(65536, self.size-offset))
            pieces.append(self.chunks[offset][max(start-offset, 0):min(end-offset, 65536)])
        self.position = end
        return b''.join(pieces)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    config = json.loads(Path('configs/phase3_pilot.json').read_text())
    rows, hashes = [], {}
    for path in sorted(Path('data/metadata').glob('*_pairs.csv')):
        hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        for row in csv.DictReader(path.open()):
            rows.append({**row, 'archive': path.name.replace('_pairs.csv', '.zip')})
    rows = spatial_rows(rows)
    parent = defaultdict(list)
    for row in rows:
        parent[row['subtile_id']].append(row)
    # Rank by salted SHA256: fixed before loading labels, equal cap per parent.
    selected = []
    for key, items in sorted(parent.items()):
        ranked = sorted(items, key=lambda r: hashlib.sha256(f"{config['seed']}:{r['sample_id']}".encode()).hexdigest())
        selected.extend(ranked[:config['pairs_per_subtile']])
    selected.sort(key=lambda r:r['sample_id'])
    # Components are built on COMPLETE cached inventory, not on sparse sampled nodes.
    assignments = experiment_partitions(rows, config['seed'])
    # Random pilot split is 80/10/10 of the SAME pilot pool; component allocation
    # stays fixed from the complete inventory.
    pilot_random = experiment_partitions(selected, config['seed'])['random']
    pilot_splits = {'random': pilot_random,
                    'geographic': {r['sample_id']: assignments['geographic'][r['sample_id']] for r in selected}}
    plan = {'config':config, 'source_index_sha256':hashes, 'samples': selected,
            'splits':pilot_splits, 'index_splits':assignments,
            'author_reproduction':author_partition(rows, config['seed']),
            'index_ratios':{k:ratio_diagnostics(rows,v) for k,v in assignments.items()},
            'pilot_ratios':{k:ratio_diagnostics(selected,v) for k,v in pilot_splits.items()}}
    digest = freeze_json('data/metadata/phase3/frozen_plan.json', plan)
    print(f'Frozen {len(selected)} label-blind pilot pairs from {len(rows)} indexed pairs: {digest}', flush=True)
    if not args.download:
        return
    catalog = json.loads(Path('data/metadata/sources/zenodo_record.json').read_text())
    archive_info = {f['key']:f for f in catalog['files']}
    old = {r['sample_id']:r for r in json.loads(Path('data/metadata/sample_manifest.json').read_text())['samples']}
    def retrieve(name):
        subset = [r for r in selected if r['archive'] == name]
        item = archive_info[name]
        budget = ByteBudget(config['max_transfer_bytes_per_archive'])
        result = []
        with ChunkReader(item['links']['self'], item['size'], budget) as remote:
            with zipfile.ZipFile(remote) as archive:
                for i, row in enumerate(subset):
                    sample = dict(row)
                    for kind in ('sen2','cyan'):
                        destination = Path('data/raw/phase3_pilot') / Path(row[kind+'_member']).name
                        if row['sample_id'] in old:
                            payload = Path(old[row['sample_id']][kind+'_path']).read_bytes()
                        elif destination.exists():
                            payload = destination.read_bytes()
                            info = archive.getinfo(row[kind+'_member'])
                            import zlib
                            if len(payload) != info.file_size or zlib.crc32(payload) != info.CRC:
                                raise ValueError('Existing pilot member CRC mismatch')
                        else:
                            payload = read_member(archive, row[kind+'_member'])
                        sample[kind+'_sha256'] = save_member(destination, payload)
                        sample[kind+'_path'] = str(destination)
                    result.append(sample)
                    if (i+1)%16 == 0:
                        print(f'{name}: {i+1}/{len(subset)} pairs; {budget.used:,} charged bytes', flush=True)
            requests = remote.requests_log
        return {'archive':name, 'range_transfer_bytes':budget.used, 'requests':requests, 'samples':result}
    with ThreadPoolExecutor(max_workers=2) as pool:
        downloads = list(pool.map(retrieve, sorted({r['archive'] for r in selected})))
    samples = sorted([r for d in downloads for r in d.pop('samples')], key=lambda r:r['sample_id'])
    manifest = {'plan_sha256':digest,'samples':samples,'transfers':downloads,
                'raw_content_bytes':sum(Path(r[k+'_path']).stat().st_size for r in samples for k in ('sen2','cyan'))}
    Path('data/metadata/phase3/pilot_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'Saved {len(samples)} real pairs. No full archive downloaded.', flush=True)

if __name__ == '__main__':
    main()

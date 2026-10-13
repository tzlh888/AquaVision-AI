# Phase 3A-3 reproducibility report

## Frozen inputs

- Protocol: `research_upgrade_v3/phase3a3/V3_EXPANSION_PROTOCOL.md`
- Configuration: `research_upgrade_v3/phase3a3/phase3a3_config.json`
- Six ignored raw CyAN V6 products: 29,336,654 bytes total; each SHA-256 is recorded in `V3_DATASET_MANIFEST.json`.
- Official USGS response evidence: 44,888,528 bytes, stored under ignored `data/raw/phase3a3/usgs/`.
- Derived native-pixel screening evidence: 55,666 bytes, stored under ignored `data/processed/phase3a3/`.
- Free storage before acquisition was 328.1 GiB. Estimated new payload was zero because the stopping gate was reached before Sentinel or additional CyAN payload selection.

## Rebuild commands

```bash
python3 research_upgrade_v3/phase3a3/query_usgs_candidates.py
python3 research_upgrade_v3/phase3a3/fetch_existing_pilot_geometries.py
python3 research_upgrade_v3/phase3a3/screen_candidate_pool.py
python3 research_upgrade_v3/phase3a3/generate_phase3a3_outputs.py
python3 -m unittest discover -s research_upgrade_v3/phase3a3 -p 'test_*.py' -v
python3 -m unittest discover -s research_upgrade_v3/final_label_pilot -p 'test_*.py' -v
```

Network retrieval commands are intentionally bounded and may reproduce a later official service state rather than byte-identical transient HTTP metadata. The preserved raw-response hashes identify the evidence actually used. All label counts and CSV outputs are reproducible from the preserved ignored responses, raw CyAN files, and scripts without credentials.

## Security and history protection

No password, Earthdata token, cookie, Authorization header, or private authentication file is stored. No model was trained. No historical report or result was modified. No commit or push was made. Raw payloads remain ignored by Git.

The pre-Phase-3A-3 untracked research evidence was archived outside the repositories: AquaVision 60 files, SHA-256 `14419204591e1988038827983aee8668a87026f9326c9a5b986671cd9ed7dec0`; WaterSense 131 files, SHA-256 `e44fa74e853bf5569d79e96443d4ad1d58029758db6ff790a3d2010f8ce863b8`.

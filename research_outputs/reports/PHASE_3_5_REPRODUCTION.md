# Phase 3.5 reproduction and artifact locations

All work remains inside AquaVision-AI. Phase 3 pilot results are immutable historical results; 42 prior metrics, splits, reports, checkpoints and environment/config artifacts are covered by `data/metadata/phase3_5/pilot_preservation_manifest.json`. Do not rerun Phase 3 report/training scripts as part of this phase.

## Read-only verification of this completed run

```bash
.venv/bin/python scripts/verify_phase3_5.py
.venv/bin/python -m pytest -q --junitxml=research_outputs/phase3_5/pytest_results.xml
.venv/bin/python -m pip check
```

The verifier reloads all nine models/thresholds and checks 36 pooled/per-group test confusion matrices, split/model-source hashes, unchanged criteria, unchanged pilot artifacts, actual reference counts, training-only normalization/pixel IDs and deterministic geographic allocation. It writes a new-phase verification record, not pilot outputs.

## Recorded acquisition and evaluation sequence

The existing Python environment and `requirements-training.txt` from Phase 3 are retained. No new model dependencies or pretrained weights were installed in this phase.

1. Save the pilot preservation manifest, `configs/phase3_5.json`, `EVALUATION_SUPPORT_CRITERIA.md` and immutable criteria contract.
2. `scripts/index_phase3_5.py`: read bounded central directories into new-phase metadata files. The original Phase 1/3 cached inventories stay unchanged.
3. A transport probe established multipart range support. Acquisition amendment A raised only the decoded-mask ceiling while retaining the byte/request and scientific criteria limits.
4. `scripts/screen_phase3_5.py`: complete the original 24,518-reference census and a frozen metadata-selected screen in other subtiles.
5. `scripts/audit_high_support.py`: first audit found five qualifying groups; preserve it under `research_outputs/phase3_5/round1_audit/`.
6. `scripts/plan_high_support_followup.py`, then `scripts/screen_phase3_5.py --round2`: freeze and execute a dataset-only follow-up in High-bearing regions lacking enough date/position support. Re-run the audit on the merged round-2 evidence. All budgets are cumulative; no model scores enter this step.
7. `scripts/prepare_phase3_5_pairs.py`: require the completed passing candidate audit, freeze selected pair IDs and planned support, fetch only selected Sentinel-2 members, verify matches/hashes/duplicates, then persist the final `geographic_split_v2.json` and `.csv` with checked support.
8. Run the test suite and dependency check. Only after support tables and integrity checks pass, run `scripts/run_phase3_5.py`.
9. `scripts/verify_phase3_5.py`, then `scripts/report_phase3_5.py` reproduce and document the completed result.

These steps describe the executed sequence, not permission to replace frozen artifacts. Frozen JSON rejects differing contents; existing final split CSVs refuse overwrite. Preserve prior outputs before any intentional rerun. A changed membership/configuration requires a new experiment version.

## Evidence files

- `data/metadata/phase3_5/criteria_contract.json`: original criteria/config/pilot-manifest hashes.
- `acquisition_amendment_A.json`, `multipart_range_probe.json`: reason for acquisition-only amendment.
- `reference_screening_plan.json`, `reference_screening_plan_round2.json`: exact reference-screening membership and selection rules.
- `reference_census.csv`, `reference_census_round2.csv`: decoded class counts, paths, SHA-256, member offsets/CRC and grouping per inspected mask. Round 1 remains intact.
- `downloaded_file_manifest.csv`: every decoded reference and selected input, source URL/member, content size, local hash, reused/new status and inclusion reason.
- `index_access.json`, `reference_access.jsonl`, `pair_access.jsonl`: bounded source requests and charged-byte accounting.
- `geographic_split_v2.json`, `geographic_split_v2.csv`: exact final membership, support criteria, sample paths and hashes.
- `research_outputs/phase3_5/split_support.csv`: pre-training split support, including per-class percentages and independent-group counts.
- `research_outputs/phase3_5/models_v2/`: existing-family refits, train-only statistics/sampled pixels, complete pooled and group metrics, model code hashes and artifact hashes.
- `research_outputs/phase3_5/model_metrics.csv`, `per_geographic_group_metrics.csv`, `pilot_vs_expanded.csv`: reviewable numerical results.

Large raw NPY files, archive directory caches and checkpoints are local artifacts excluded from Git where appropriate. All reported values come from retained real source data; synthetic arrays are confined to software tests. Author-grid plots use source row/column IDs and do not invent geographic coordinates.

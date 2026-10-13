# AquaVision AI — Final Release Readiness Report

Date: 2026-10-12

Branch: `research-upgrade-v3`

Frozen starting HEAD: `bd11ece`
Release decision: **CONDITIONALLY READY**

## 1. Scope and safety boundary

This pass did not train or tune a model, expand the dataset, alter a historical result, stage files, create a commit, push, or publish a release. AquaVision remains a scientifically limited project: the v3 geospatial data-integration pipeline succeeded, but Phase 3B did not start and no qualified independent High unit was obtained.

At entry, Git reported 83 untracked files and no tracked modification. The release-preparation archive contains those files together with the pre-edit `README.md` and `.gitignore`:

- Archive: `outputs/release_prep_snapshots/aquavision_release_prep_start_85_files.tar.gz`
- SHA-256: `86acc9762a41c1762cf5e7b9b46ff377def11926a33e0322dc80290535c8104f`

An additional pre-edit archive protects the test and documentation state before the public-suite contract correction:

- Archive: `outputs/release_prep_snapshots/aquavision_before_release_edits_86_files.tar.gz`
- SHA-256: `0d6e6bc3658b5809a233187f879ffe2f3932f407c501db0c55048f14e4eff5aa`

The Phase 4 start archive also remains intact:

- Archive: `outputs/phase4_snapshots/aquavision_phase4_start_untracked_77.tar.gz`
- SHA-256: `f816f988df70ef39180bf24dd3710144f7df7dfd7167d95846935b18a788cd31`

## 2. File disposition

The authoritative path-level allowlist is `RELEASE_FILE_CLASSIFICATION.csv`.

| Action | Count | Release treatment |
|---|---:|---|
| `COMMIT` | 96 | Suitable for reviewed Git commits including eight final staging-audit deliverables and the scoped attributes policy |
| `HUMAN_REVIEW` | 1 | Do not stage until the owner confirms the contribution statement |
| `KEEP_IGNORED` | 6 | Large regenerated historical ZIP indices; retain locally only |
| `CANNOT_PUBLIC` | 0 | No prohibited item was found among the 83-file baseline |

The six regenerated `data/metadata/phase3_5/*_entries.csv` files exactly match their frozen preservation hashes but total roughly 179 MB. They remain ignored and are not required for the lightweight public test run. Raw Sentinel/CyAN arrays, GeoTIFF/NPZ products, model checkpoints, caches, Earthdata authentication state, and local environments must also remain excluded.

## 3. Scientific consistency

The README and final reports consistently state:

- the historical v2 labels are CyAN remote-sensing proxy labels, not in-situ toxin ground truth;
- 288 historical Sentinel arrays and 288 paired CyAN arrays were recovered, but 0/288 historical records have confirmed real geographic identities;
- six frozen NASA CyAN V6 products were acquired and aligned across three identified waterbodies in the v3 pilot;
- pipeline success is not a classification-model performance result;
- Phase 3A-3 ended with 0 qualified independent High units and a Training/Validation/Confirmation count of 0/0/0;
- Phase 3B did not start, and reliable cross-geographic three-class generalization has not been demonstrated;
- the final research status is **LIMITED**.

The reports distinguish High pixels, scenes, waterbodies, and qualified independent units. They do not inflate resampled 20 m pixels into independent 300 m CyAN observations and do not present proxy class labels as field-measured hazard levels.

## 4. Security, privacy, licensing, and size audit

- No Earthdata credential, cookie, authorization header, GitHub token, AWS credential, private-key block, private user-home path, or AI development-workspace trace was found in proposed public text/code files.
- No symlink was found in the proposed release set.
- The largest new proposed file is approximately 2.0 MB; no proposed file approaches GitHub's 100 MB object limit.
- Existing tracked metadata objects are below 100 MB. Large regenerated indices and all raw/derived raster data remain ignored.
- NASA, Copernicus, and USGS source licenses and access conditions are not replaced by repository licensing. Product identifiers, checksums, processing records, and redownload instructions may be published; third-party binary redistribution requires an independent license review.
- `RESEARCH_CONTRIBUTION_STATEMENT.md` is blocked on owner confirmation and does not infer authorship from repository ownership.

## 5. Clean-environment verification

A new Python 3.12.14 virtual environment was created and `requirements-training.txt` installed successfully, including the package in editable form.

### Historical public suite

Command:

```bash
python -m pytest -q
```

Observed sequence, retained for transparency:

1. **122 passed, 1 failed** — the frozen preservation test required a missing ignored ZIP-index file.
2. Six metadata-only indices were regenerated with the bounded repository script; each matched its recorded SHA-256.
3. **122 passed, 1 failed** — the same test then reached 12 intentionally unavailable ignored model/checkpoint artifacts.
4. A stricter partial-manifest run exposed three `egg-info` records regenerated by editable installation; these are packaging outputs, not research evidence.
5. The final test contract fails on any present non-generated research-artifact mismatch, records generated packaging differences separately, and skips only the complete frozen-environment condition.
6. Final public result: **122 passed, 1 skipped, 0 failed** in approximately 1.8 seconds. The skip reports 12 unavailable artifacts and 3 generated packaging records.

This is not represented as “123 tests passed.” A true full-artifact 123/123 rerun remains **not run in this release environment** because 12 registered historical model/checkpoint artifacts are unavailable and editable installation changed 3 frozen packaging records. The skip states both counts explicitly.

### Research-upgrade suites

Command:

```bash
python scripts/run_research_upgrade_tests.py
```

Result: **60 passed, 0 failed, 0 skipped**, comprising 10 Phase 3A, 11 Phase 3A-1, 11 Phase 3A-2, 15 final-label-pilot, and 13 Phase 3A-3 tests.

Static and artifact checks also passed:

- Python source compilation;
- CSV and JSON parsing;
- Markdown local-link resolution;
- frozen v3 evidence-count checks;
- scan for secrets, local paths, and development-tool directories.

No research model was fitted. Test-only tensor and synthetic-fixture operations are not research training.

## 6. Public reproducibility

A third party can inspect the v3 protocols and manifests, run the lightweight 122-pass/1-skip historical suite, run all 60 research-upgrade tests, verify the six CyAN product identities and hashes, and reproduce the geospatial integration logic after independently acquiring authorized source products. The repository cannot provide a fully independent High-class evaluation, because no qualified units exist. Exact reproduction of every historical v2 benchmark also remains partial because geographic identities and 12 ignored model/checkpoint artifacts are unavailable.

## 7. Proposed staged commit sequence

Do not use `git add .`. Review `RELEASE_FILE_CLASSIFICATION.csv`, then stage only explicit paths in this order:

1. **Public test contract and runner** — `tests/test_phase4_reliability.py` and `scripts/run_research_upgrade_tests.py`.
2. **Phase 3 evidence and data-integration code** — the explicit publishable files under `research_upgrade_v3/phase3a/`, `phase3a1/`, `phase3a2/`, `final_label_pilot/`, and `phase3a3/`; exclude caches, rasters, arrays, credentials, and ignored indices.
3. **Final closeout and release governance** — final scientific report, one-page summary, reproducibility/public-release audits, interview Q&A, classification CSV, this report, and README.
4. **Contribution statement only after human approval** — stage `RESEARCH_CONTRIBUTION_STATEMENT.md` separately after the owner confirms authorship, AI assistance, framework usage, and personal technical work.

Before each commit, run `git diff --cached --check`, inspect `git diff --cached --stat`, and confirm that no `data/metadata/phase3_5/*_entries.csv`, raster, array, checkpoint, credential, environment, or cache path is staged.

## 8. Remaining release gates

The repository is **CONDITIONALLY READY**, not fully READY, because:

1. the owner must confirm the contribution statement;
2. the exact staging allowlist must receive human review;
3. the full historical 123-test condition cannot be reproduced without the 12 registered local artifacts and frozen packaging-metadata state, and must remain documented as 122 passed / 1 skipped in a public checkout;
4. any redistribution of third-party imagery or CyAN binary products requires separate license review;
5. README edits must retain the LIMITED, 0/0/0, and no-Phase-3B wording.

These gates do not justify further model training or dataset expansion. After owner approval, the reviewed public code and evidence can be committed in the sequence above.

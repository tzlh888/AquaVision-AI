# AquaVision AI — Proposed Commit Plan

No commit has been created. The staging index contains one reviewed superset that should be committed in three groups after owner approval.

## Group 1 — Implementation, scripts and tests

Expected paths: **24**. This group contains audit, recovery, catalog, label-integration, screening, test-runner, and fail-safe preservation-test code.

Before committing, reset only the index without changing working-tree files, then stage the rows marked `1_implementation_tests` in `STAGED_FILE_MANIFEST.csv`.

Suggested message: `Add reproducible geospatial evidence tooling and tests`

## Group 2 — Research protocols, results and reports

Expected paths: **55**. This group contains frozen protocols, provenance manifests, catalogs, High-support and overlap audits, negative gate results, and handoffs. Raw imagery, arrays, rasters, checkpoints, and large regenerated indices remain excluded.

Suggested message: `Add bounded v3 provenance and negative readiness evidence`

## Group 3 — README, reproducibility and release documentation

Expected paths: **17**. This group contains the minimal README update, scoped attributes policy, final closeout documents, and staging/security audits.

Suggested message: `Document LIMITED conclusion and release status`

## Safety checks for every group

Inspect `git diff --cached --stat`, `git diff --cached`, and `git diff --cached --check`. Confirm the staged paths equal the selected group rows exactly. Do not stage the contribution statement, regenerated indices, raw or derived remote-sensing data, checkpoints, credentials, environments, caches, or temporary service payloads.

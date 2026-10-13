# Phase 3A-2 Final Handoff

## Final status: NOT READY

Phase 3A-2 established a real, metadata-first prospective pipeline and six geographically identified candidates, but it did not establish a qualified labeled dataset. CyAN file transfer requires Earthdata authentication; source bytes, hashes, exact processing version, and High support are not yet confirmed. There are 0 qualified High units and 0 confirmation members. Phase 3B model experimentation is not authorized.

No model was trained. No legacy test metric was used to tune the pilot. No commit or push was performed.

## A–K decision record

### A. Is further historical metadata recovery reasonably hopeful?

Not from currently public artifacts. The bounded search is exhausted and the 288 v2 identities remain UNVERIFIED. Recovery is still possible only if an author or original storage system supplies inspectable sample-level primary metadata. An inquiry was drafted but not sent.

### B. Were real v3 samples with complete geographic identity obtained?

Six candidate records have complete waterbody, scene, CRS, affine, patch footprint, and acquisition-time identity. They are real metadata records, not synthetic samples. However, none is a complete **labeled** v3 sample because the CyAN bytes, hash, and exact version were not obtained.

### C. Were at least 3 qualified independent High validation units obtained?

No. The count is 0. The six candidate rows represent only 3 waterbody groups, and High support is unmeasured.

### D. Can the collection be expanded to 10 or more?

Potentially, but this is not demonstrated. Expansion first requires authenticated label acquisition and a successful High-support census. The pipeline must screen more independently identified waterbodies under the frozen rule; repeated patches/dates cannot increase the unit count.

### E. Can training, validation, and confirmation remain truly independent?

The frozen v3-only protocol can enforce that relationship, but no actual split can yet be made. Because v2 footprints are unknown, using v2 for training while calling v3 evaluation fully independent is prohibited. The clean path uses only identity-complete v3 components.

### F. Are CyAN source, version, and mapping traceable?

The official daily catalog URL, six product filenames, acquisition-date match, and frozen DN-to-class mapping are traceable. The exact processing version and raw label-file hashes are not confirmed. `V6_CURRENT_CATALOG_CANDIDATE` is deliberately not treated as CONFIRMED.

### G. Is the data pipeline fully reproducible?

Metadata selection, geometry, patch derivation, and saved-evidence validation are reproducible. End-to-end labels are not: Earthdata authentication is required, and one later live rerun encountered bounded USGS HTTP 504 failures. The initial successful official responses and their hashes are retained in the manifest.

### H. Are the practical conditions for sealing a confirmation set met?

No. There are no label-qualified members, no measured High units, and no finalized contamination graph over eligible data.

### I. How much additional data and engineering work remains?

First, download and hash the 6 preselected CyAN files with authorized Earthdata access, confirm their exact version/encoding, implement and test the frozen spatial resampling and masks, and census High support. If viable, the absolute protocol floor requires at least 9 independent High-support units across training (3), validation (3), and confirmation (3), or at least 18 qualifying scene/date observations under the two-date rule. The preferred target is at least 23 High-support units (training floor 3, validation 10, confirmation 10), and real screening will likely require many more candidates because failures and non-High waterbodies cannot be counted.

### J. Is further investment justified?

Only one further bounded, credentialed label-integration pilot is justified. If the six labels cannot be obtained/versioned or the resulting support is inadequate, stop dataset expansion. Model development has no present marginal scientific value.

### K. Is Phase 3B allowed?

No. Required gates are: confirmed and hashed CyAN labels and version; reproducible band/mask/resampling processing; at least 3 independent High units in development, 3 in validation spanning at least 2 waterbodies and 3 scenes, and 3 sealed confirmation units; a frozen zero-overlap contamination graph; and all split/manifest hashes recorded before training. The target remains 10 validation and 10 confirmation units. Failure must retain the `NO QUALIFIED MODEL` outcome.

## Pilot evidence

| Evidence | Result |
|---|---:|
| Candidate rows | 6 |
| Unique Sentinel scenes | 6 |
| Verified waterbody groups | 3 |
| Geographic-identity-complete rows | 6 |
| Label-identity-complete rows | 0 |
| Qualified High units | 0 |
| Confirmation members | 0 |

## Test result

The targeted test suite contains 11 tests. Synthetic unit tests cover schema rejection, scene/grid identity, CRS and contained footprints, spatial intersection, temporal matching, label boundaries, waterbody identity, duplicate detection, cross-split isolation, confirmation exclusion, fail-closed High qualification, and hashes. Saved-official-evidence integration tests cover the six-row/three-waterbody/six-scene census, patch containment/temporal match, artifact hashes, zero qualified units, and zero confirmation assignments.

Final execution result and artifact hashes are recorded in the final user handoff after the post-write integrity audit.

## Evidence protection and Git audit

Before Phase 3A-2 files were added, recoverable local archives and per-file SHA-256 manifests were created for both repositories. Archive SHA-256 values are:

- AquaVision pre-work untracked archive: `7dd26a3f0bd787343bd74ad97f53e6bc2d2b02f7f5510c260acfad6e2f07bad4`.
- WaterSense pre-work untracked archive: `1c854fa663ac298b2d640af63fa78b4e53828ac64bbf12b7eb477fecb04c4b00`.

All 35 pre-existing AquaVision untracked files and all 131 WaterSense untracked files passed individual checksum verification after the work. AquaVision remained on `research-upgrade-v3` at `bd11eceaa7efa7ca785d5e466cf807312ed70df0`; WaterSense remained on `research-upgrade-v3` at `3553b29ff104918b12da8c84d2c9a8c5ed032e18`. Both tracked and staged diffs are empty. The only repository additions are 15 untracked Phase 3A-2 files in AquaVision; WaterSense remains at the original 131 untracked files.

## SHA-256 register

The handoff file itself is excluded from this in-file register because inserting its own digest would change it; its digest is reported externally after the final write.

| Artifact | SHA-256 |
|---|---|
| `LEGACY_METADATA_FINAL_RECOVERY.md` | `26cf1c38719f82466341c62bcf5d6d23437def099125f55d69ea81ec098735c2` |
| `PROSPECTIVE_V3_PILOT_REPORT.md` | `aad5f9531c04c6cb9da9674e5be5a08c40ce3e7f9e7406ad262f4563469d8296` |
| `V3_CONFIRMATION_SET_PROTOCOL.md` | `5eccce15486990538b2acc8ce816cd381347fbeb2ddb10c9093f0ab657e5f1ac` |
| `V3_DATASET_SPLIT_PROTOCOL.md` | `16d110b7cc71c65d994573ccbc42834ebccab862b611374b67453bd40881c0d5` |
| `V3_DATA_PROVENANCE_MANIFEST.json` | `9122f29468cd59e92a39db0de9ab01f658cd5fad4acc4f75b240ec5ee06ede1c` |
| `V3_GEOGRAPHIC_IDENTITY.csv` | `5dbc2af250bc1c4cc16c31ba5d3137a23bb50323de979e6b0e18eaab6a4c5b3e` |
| `V3_HIGH_SUPPORT_AUDIT.csv` | `0261824d134f1bb00fe629af679cbab29b928e03deb2194b19c8b92bbc5b96c9` |
| `V3_METADATA_CATALOG.csv` | `f74b20697f429b591e6fb2effff3012b5af2c16683056ae3057b53fb00eb5a5f` |
| `V3_SPATIAL_OVERLAP_AUDIT.md` | `605fbbe58e5d1d085098f4723cb29fb4c8740d0ce004b5af7d0104cd290f5345` |
| `phase3a2_audit.py` | `d87dd639210bb9d4244e98bd161a476988baff741044836c713b4ebd5eab4513` |
| `phase3a2_pilot_config.json` | `714563cc9fec540e9f5672b3281286c6afeb3e403aa7e585aeafed2784513fa1` |
| `refresh_cyan_access_evidence.py` | `82e9a28b115c0bb0932cc1987e95af6f33609f81ca5f1ef8bb7a9c62ab3de1f5` |
| `run_phase3a2_pilot.py` | `81c01f1bdf2ce99754a770c4f9871190b3f069fbb3d3c049ed3360ec79a21f40` |
| `test_phase3a2_audit.py` | `e782360de4e60816fc53380c80f2a344c01f416c6774c743c2ae54467962893a` |

## Delivered artifacts

- `LEGACY_METADATA_FINAL_RECOVERY.md`
- `PROSPECTIVE_V3_PILOT_REPORT.md`
- `V3_METADATA_CATALOG.csv`
- `V3_GEOGRAPHIC_IDENTITY.csv`
- `V3_HIGH_SUPPORT_AUDIT.csv`
- `V3_SPATIAL_OVERLAP_AUDIT.md`
- `V3_DATA_PROVENANCE_MANIFEST.json`
- `V3_DATASET_SPLIT_PROTOCOL.md`
- `V3_CONFIRMATION_SET_PROTOCOL.md`
- `PHASE3A2_FINAL_HANDOFF.md`
- `phase3a2_pilot_config.json`
- `phase3a2_audit.py`
- `run_phase3a2_pilot.py`
- `refresh_cyan_access_evidence.py`
- `test_phase3a2_audit.py`

## Research limitations

- Legacy v2 location and cross-overlap remain unknowable from public evidence.
- The pilot is purposive and geographically small; it says nothing about population prevalence.
- Scene tile cloud percentage is not a guarantee of clear conditions over the selected water patch.
- CyAN is coarser than the 20 m Sentinel grid; processing and aggregation rules still require a real-data integration test.
- Three waterbodies would still be highly uncertain even if all qualified.
- Official live services can be temporarily unavailable; saved response hashes preserve evidence but do not remove this dependency.

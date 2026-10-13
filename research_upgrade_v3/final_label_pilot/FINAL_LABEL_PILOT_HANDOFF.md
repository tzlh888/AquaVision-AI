# Final CyAN Label Pilot Handoff

## Final status: PILOT SUCCESS

Actual NASA data demonstrate a complete and reproducible bounded label-integration workflow for all six frozen candidates. This authorizes consideration of a separately approved, bounded prospective data expansion. It does **not** make AquaVision Phase 3B ready: the frozen independent High-unit count remains zero.

No model was trained. No target was replaced. No legacy metric or model prediction influenced data selection. No commit or push was performed.

## A–I decision record

### A. How many frozen products were acquired?

**6/6 unique products.** One byte-identical duplicate of the first product created while capturing the authorization download event was excluded and moved outside the repository.

### B. How many products have confirmed version and source?

**6/6.** Each downloaded GeoTIFF has a NASA Ocean Color source URL, local SHA-256, exact daily product ID, and embedded `OBPG_version=6.0`.

### C. How many Sentinel candidates were credibly aligned?

**6/6.** Every record has a verified Sentinel patch affine/CRS, same-date CyAN product, transformed polygon, overlapping source cells, and a hashed 64×64 nearest-neighbor artifact.

### D. How many real waterbody groups have High support?

**2/3 contain High:** Utah Lake and Upper Klamath Lake. Lake Okeechobee does not. This represents 3 High scenes/patches and 48 native High pixels under the primary alignment, but **0 qualified independent High units**.

### E. Is the v3 pipeline technically feasible?

**Yes, for this bounded pilot.** Retrieval, embedded-version verification, hashing, CRS transformation, temporal matching, masking, nearest-neighbor labels, diagnostic interpolation, traceability, and offline rebuilding all succeeded. General data availability and scientific representativeness are not established by six scenes.

### F. Is acquiring additional independent waterbody data justified?

**Yes, conditionally.** The technical blocker is resolved and two waterbodies show real High support. A next tranche should be pre-budgeted and metadata-first, use no model predictions, and stop if the yield of qualified groups is too low. It must add independent waterbodies and sufficient within-waterbody High patches rather than merely adding dates or resampled pixels.

### G. What independent-unit deficits remain?

At the minimum frozen gate, current qualified-unit counts are zero, so the deficits are:

- Training/development: **3 independent High units**.
- Validation: **3 independent High units**, target 10.
- Confirmation: **3 sealed independent High units**, target 10.

Thus the minimum total deficit is 9 qualified units; the preferred total deficit is at least 23. Utah and Upper Klamath cannot count until each reaches all within-unit support gates, and one waterbody can belong to only one split. Repairing those two could reduce the number of additional independent waterbodies needed, but cannot fill multiple partitions.

### H. Do unacceptable label or independence problems remain?

Yes for model experimentation. CyAN is a 300 m proxy rather than field ground truth; 20 m labels are spatial repetitions; one-cell boundary sensitivity exists; legacy-v2 overlap remains unknown; and no prospective split or confirmation set exists. These are not failures of the integration code, but they prevent confirmatory or deployment claims.

### I. Continue dataset construction or accept a LIMITED conclusion?

The recommended decision is **one separately approved, bounded v3-only dataset-construction tranche**, not model training and not open-ended collection. If that tranche cannot produce qualified independent units at a reasonable rate, accept the existing **LIMITED** conclusion and stop AquaVision expansion. The current scientific conclusion remains LIMITED until those data gates pass.

## Core counts

| Measure | Count |
|---|---:|
| Downloaded frozen products | 6 |
| Version-confirmed products | 6 |
| Credibly aligned scenes | 6 |
| Waterbody groups | 3 |
| Scenes/patches containing High | 3 |
| Waterbodies containing High | 2 |
| Native High pixels | 48 |
| Qualified independent High units | 0 |
| Training / validation / confirmation members | 0 / 0 / 0 |

## Delivered files

- `CYAN_DOWNLOAD_AUDIT.md`
- `CYAN_PRODUCT_MANIFEST.json`
- `LABEL_INTEGRATION_REPORT.md`
- `GEOSPATIAL_ALIGNMENT_AUDIT.md`
- `HIGH_SUPPORT_PILOT.csv`
- `PILOT_REPRODUCIBILITY.md`
- `FINAL_LABEL_PILOT_HANDOFF.md`
- `cyan_label_integration.py`
- `run_final_label_pilot.py`
- `test_final_label_pilot.py`

Raw and derived raster files are locally retained in Git-ignored data directories and registered by SHA-256 in the manifest.

## Public artifact SHA-256 register

The handoff file is excluded from its own in-file register because inserting its digest would change it. Its final digest is reported externally after the last write.

| Artifact | SHA-256 |
|---|---|
| `CYAN_DOWNLOAD_AUDIT.md` | `6dd1efbb1c6302ebb140f1a4b4bf56779c07b23797c387519cf82945a88d36ec` |
| `CYAN_PRODUCT_MANIFEST.json` | `b0eddffc9ee302f49c81a28d72053a8b9ba4c1fc6a5a6793325ac2be03b40dd2` |
| `GEOSPATIAL_ALIGNMENT_AUDIT.md` | `54a322adcc1abb2b71ba247fdfdbce888750ce9589203697cdc35bade51a5ce5` |
| `HIGH_SUPPORT_PILOT.csv` | `ff80c964bdcf67a7306e8d92e3bda7167c4c86de28c27b034e1b1f22219620d3` |
| `LABEL_INTEGRATION_REPORT.md` | `977db500171844d1229bae5ee39d76730b3c8861e7d966c2d486068cab7b171b` |
| `PILOT_REPRODUCIBILITY.md` | `7c48f73c8290dd5601af71e66420a56cff8c9f2f9970bd7886c9a3fe813286fe` |
| `cyan_label_integration.py` | `ada749886748ed4629a82ae2e79cd7203f1d857a1ea8355e729266cb75a0d736` |
| `run_final_label_pilot.py` | `b46b72c9916c0c75e87284314692c80c3486a0aa24ac9e6daf6e406a2e6753de` |
| `test_final_label_pilot.py` | `9d173618ed106d8fc4d74655e5ddda605302aae16b646cd6338c21c9153e7eca` |

## Final evidence and Git audit

- All 50 AquaVision files present before this pilot passed checksum verification after the pilot: 35 against the pre-Phase-3A-2 snapshot and 15 against the Phase 3A-2 final register.
- All 131 WaterSense untracked files passed checksum verification; its status SHA-256 remains `1ad752764355498fe02f2c6762ce23b561e3aca7dd04049541819eed29f2de25`.
- AquaVision remains on `research-upgrade-v3` at `bd11eceaa7efa7ca785d5e466cf807312ed70df0`, with 60 untracked files: 50 preserved and 10 new public pilot files. Its final full untracked status SHA-256 is `9cca88b42aac151bfacebd59c74a5b70b46e5d7f1ef890883fdb34986d40fe8d`.
- WaterSense remains on `research-upgrade-v3` at `3553b29ff104918b12da8c84d2c9a8c5ed032e18` with 131 untracked files.
- Tracked and staged diffs are empty in both repositories.
- Six raw GeoTIFFs and six processed `.npz` files are confirmed ignored by the existing `.gitignore` rules.
- Private-path and credential-pattern scans of public pilot files returned no findings.

## Stop condition

Phase 3B remains prohibited. This task stops after the final audits; no large-scale collection or model training follows automatically.

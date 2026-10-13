# Prospective v3 Pilot Report

## Decision

The metadata-first pipeline is technically viable, but the pilot does **not** yet yield a qualified labeled v3 dataset. Six candidate scene/date records across three named waterbodies have complete geographic identity; none has an authenticated, downloaded, hashed, version-confirmed CyAN label. Therefore there are **0 qualified High units**, **0 assigned development/validation members**, and **0 sealed confirmation members**.

No model was trained, no model prediction was used for selection, and no legacy test metric was used to alter the design.

## Frozen pilot design

The three large CONUS waterbodies and two calendar windows were fixed before CyAN pixel access:

| Waterbody | USGS Permanent ID | NHDPlus ID | Windows | Selected scenes |
|---|---:|---:|---:|---:|
| Lake Okeechobee | 120024129 | 15000800177920 | 2025-07, 2025-09 | 2 |
| Utah Lake | 83636441 | 70000400075631 | 2025-07, 2025-09 | 2 |
| Upper Klamath Lake | 168095445 | 50000400343697 | 2025-07, 2025-09 | 2 |

Within each window, the pipeline chose the Sentinel-2 L2A item covering the verified waterbody representative point with the smallest tile cloud percentage at or below 30%; ties were ordered by acquisition time and item ID. It used the `B05_20m` grid and derived one 64×64, 20 m, grid-aligned patch whose four corners are inside the USGS waterbody geometry.

This is a purposive pipeline sample, not a representative sample of lakes or bloom prevalence.

## Obtained real metadata

- 6 unique Sentinel product IDs and acquisition timestamps.
- Sentinel processing version `05.11`, native projected CRS, affine transform, raster shape, asset checksum multihash, and tile cloud percentage.
- 3 USGS NHDPlus HR waterbody identities, WGS84 geometries, and scene-CRS transformed geometries.
- 6 actual patch windows, affine transforms, native-coordinate footprints, and deterministic patch identities.
- Six same-date NASA daily CyAN catalog filenames; temporal mismatch is 0 days.
- Daily-pair spacing within the three waterbody groups is 53, 62, and 73 days.

The six rows are only three geographic groups. Repeated dates or patches do not increase the independent-waterbody count.

## Missing evidence and stop

The NASA directory listings were public, but file retrieval redirected to Earthdata authentication. A bounded HEAD check returned HTTP 302 to the authenticated get-file route for all six products. No raster bytes were downloaded. Consequently:

- source-label file hashes are UNVERIFIED;
- exact CyAN processing version is only CANDIDATE, not CONFIRMED;
- pixel values and High support were not measured;
- no candidate may pass the High-unit qualification gate;
- no split assignment is permitted.

The public V6 release note is consistent with the catalog period but does not by itself prove that these exact files were produced with V6. The frozen label mapping remains Low 0–99, Moderate 100–199, High 200–253, Ignore 254–255; no threshold was changed to fit historical results.

## Reproducibility

The initial official-source run completed and its normalized evidence, response hashes, transformations, selected items, and generated artifact hashes are embedded in `V3_DATA_PROVENANCE_MANIFEST.json`. A subsequent live rerun was stopped after bounded retries because the USGS service returned HTTP 504. Outputs were not partially overwritten. This distinguishes a saved-evidence reproducibility result from live-service availability.

The metadata and identity tables can be validated offline using the saved manifest. An end-to-end label pipeline is not yet reproducible because it requires authorized Earthdata file transfer and an explicit version check from downloaded source/header metadata.

## Qualification count

| Measure | Result |
|---|---:|
| Candidate rows | 6 |
| Unique scenes | 6 |
| Named waterbodies | 3 |
| Geographic-identity-complete rows | 6 |
| Label-identity-complete rows | 0 |
| Qualified independent High units | 0 |
| Validation High-unit minimum | 3 |
| Validation target | 10 |
| Confirmation members | 0 |

## Bounded next action

One additional bounded, credentialed data-integration step is scientifically justified: authenticate to Earthdata, download and hash only the six already selected CyAN files, record their exact processing version, perform the frozen grid/resampling/mask procedure, and census High support. If this fails to establish label provenance or yields insufficient support, stop this pilot and do not move to model experimentation. If it succeeds, expand the metadata-first candidate pool under the frozen selection protocol; do not select candidates using model predictions.

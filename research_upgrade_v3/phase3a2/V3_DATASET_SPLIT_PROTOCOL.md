# v3 Dataset Split Protocol

## Status

**Frozen design; not instantiated.** All Phase 3A-2 rows remain `PILOT_CANDIDATE_UNASSIGNED`. This protocol cannot authorize training until label provenance, High support, independence, and minimum unit counts pass.

## Eligibility

A record is eligible only when all of the following are CONFIRMED and recorded in the manifest:

- stable waterbody ID and official geometry;
- Sentinel product ID, acquisition time, processing version, asset, CRS, affine transform, and source checksum metadata;
- exact patch row/column window and geographic footprint;
- CyAN product ID, exact processing version, acquisition/composite time, downloaded raw-file SHA-256, units/encoding, mask values, and use terms;
- deterministic spatial and temporal match evidence;
- label mapping using the frozen bins Low 0–99, Moderate 100–199, High 200–253, Ignore 254–255;
- no missing required metadata and no duplicate candidate identity.

The processing manifest must record Sentinel bands, scale/offset, cloud/water masks, reprojection library/version, resampling method, target grid, nodata handling, window logic, and all raw/processed hashes. Data-dependent normalization or imputation must later be fitted only within the training fold.

## Independent grouping

Use the connected-component unit defined in `V3_SPATIAL_OVERLAP_AUDIT.md`. At minimum, every record from the same waterbody remains in one split. Scene siblings, intersecting patches, and observations from one bloom event are inseparable. Unit counts—not patches or pixels—are the primary support counts.

## Assignment order

1. Freeze source versions, inclusion/exclusion rules, event grouping, and High-unit support rules.
2. Acquire labels and apply the frozen support census without viewing model predictions.
3. Construct the contamination graph and reject unresolved metadata.
4. Select and seal confirmation components first under `V3_CONFIRMATION_SET_PROTOCOL.md`.
5. Assign the remaining eligible components to development/training and validation using a deterministic, seeded group-level procedure with documented stratification on High support and broad geography.
6. Save member IDs, selection seed, input-manifest hash, split-manifest hash, and a zero-overlap audit before any model fit.

No legacy test metric, candidate-model prediction, threshold optimization, or architecture result may change membership. Any change requires a new dataset version and a new prospective declaration.

## Minimum gates

The existing exploratory Phase 3 protocol is retained:

- Training/development: at least 3 independent High-support units; more are strongly preferred.
- Validation: at least 3 independent High-support units spanning at least 2 verified waterbodies and 3 scenes; target at least 10 units.
- Confirmation: at least 3 sealed independent High-support units; target at least 10 units.
- Every qualifying High unit: at least 2 dates separated by at least 30 days, at least 3 High patches, and at least 100 High pixels under the frozen mapping.

These minima are eligibility floors, not claims of statistical reliability. Three units imply very wide uncertainty and prohibit strong generalization claims.

## Validation analysis

Report class support and metrics at both patch and independent-unit levels. Uncertainty must resample independent groups, not patches. Any fold or split lacking a class needed for a metric reports that metric as undefined and triggers the predeclared qualification rule. Failed or disqualified models remain in the record under the existing `NO QUALIFIED MODEL` exit mechanism.

## Legacy v2 rule

Because v2 geographic footprints are unverified, v2 cannot be mixed into development while claiming new v3 validation or confirmation is fully geographically independent. The preferred confirmatory path is v3-only. Any v2-assisted analysis must be clearly labeled exploratory and contamination-uncertain.

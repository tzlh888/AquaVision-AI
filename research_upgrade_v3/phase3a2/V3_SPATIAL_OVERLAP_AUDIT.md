# v3 Spatial Overlap Audit

## Result

The three pilot waterbodies are geographically distinct, but the dataset is not yet partitionable and independence from legacy v2 cannot be demonstrated.

| Waterbody | WGS84 bounding box | Scene dates | Independence interpretation |
|---|---|---:|---|
| Lake Okeechobee | [-81.096933, 26.716416, -80.611116, 27.207276] | 2 | One waterbody group, not two units |
| Utah Lake | [-111.943142, 40.015658, -111.653400, 40.362057] | 2 | One waterbody group, not two units |
| Upper Klamath Lake | [-122.090686, 42.233568, -121.801625, 42.496533] | 2 | One waterbody group, not two units |

The three WGS84 bounding boxes do not intersect. Each selected patch is fully contained within its matched USGS waterbody polygon. Within each waterbody, the July and September records reuse the same physical patch footprint; they are repeated observations of one geographic unit and must remain in the same partition.

## Frozen independent-unit definition

The conservative unit is the connected component formed by any of these relations:

1. same verified waterbody identity;
2. same Sentinel scene or overlapping source-scene footprint;
3. intersecting or duplicated patch footprint;
4. observations assigned to the same bloom/event window under a predeclared event rule.

All records in one component must share one split. Patch count, pixel count, dates, or different crops from one scene do not create independent validation units. Until event independence can be justified, all dates from the same waterbody are conservatively grouped together.

## Cross-split status

- Current `split_membership`: `PILOT_CANDIDATE_UNASSIGNED` for all six rows.
- Development–validation overlap: not applicable; no assignments exist.
- Confirmation exclusion: passes vacuously because there are no confirmation members.
- v3 candidate-to-candidate duplicate scene IDs: none.
- v3 candidate geographic groups: 3.
- v3-to-v2 spatial overlap: **UNVERIFIED** because all legacy v2 footprints are unknown.

Therefore a study that trains on legacy v2 and evaluates on these candidates must not call the result fully geographically independent. The clean route is v3-only training, validation, and confirmation after sufficient qualified units are obtained and split components are frozen.

## Required future audit

Before any split is released, build a contamination graph over waterbody IDs, scene IDs, projected patch polygons, acquisition/event windows, and source-label products. Reject or merge any cross-split connected components. The audit must run before model fitting and must be rerun after every data-manifest change; any changed membership produces a new dataset version.

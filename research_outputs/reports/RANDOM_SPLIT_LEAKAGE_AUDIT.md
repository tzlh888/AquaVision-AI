# Random split leakage audit

Counts are test patches whose identifier also occurs in training. Validation is not included in these exposure denominators. Both designs preserve the same eligible pool within each scope; the 272-patch pilot is separate from the 24,518-pair index audit.

| Pool / split | Shared subtile | Shared CyAN tile | Shared component | Repeated grid-position candidate | Same-date adjacent patch |
|---|---:|---:|---:|---:|---:|
| index / random | 2452/2452 | 2452/2452 | 2452/2452 | 2449/2452 | 2440/2452 |
| index / geographic | 0/3945 | 3945/3945 | 0/3945 | 0/3945 | 0/3945 |
| pilot / random | 28/28 | 28/28 | 28/28 | 5/28 | 2/28 |
| pilot / geographic | 0/32 | 32/32 | 0/32 | 0/32 | 0/32 |

On the complete indexed pool, 100% of random test patches share a parent subtile and connected region with training; 99.88% share a patch-grid position candidate across dates, and 99.51% have a same-parent/date neighbor in training. The author-grid geographic split removes those measured overlaps. Sharing the larger CyAN tile is expected: this is unseen *subregion* evaluation, not an unseen-CyAN-tile experiment.

Sentinel-2 scene overlap remains UNKNOWN because `sen2_uuid` was discarded. The paper reports 1,789 products in its full experiment; this number is not assigned to our subset. Date/subtile combinations are not relabeled as scenes. Repeated physical footprints and cross-tile waterbody overlap remain UNKNOWN without original transforms and IDs.

All 17 parents recur over dates; 1,386 of 1,391 patch-position candidates recur. Parent assignment keeps all those dates together in the geographic design. Native crop offsets do not prove exact repeated physical footprints after reprojection.

In the pilot, no train/test input pair has the same complete-file SHA-256. A fixed appearance diagnostic compares 12-band 8×8 block means after /10000: one random test patch and zero geographic test patches have a nearest-training mean absolute difference ≤0.001. This is not a geographic-footprint test or proof of duplication. All distances are saved in `phase3_leakage.json`; no thresholds were selected using model scores.

No latitude/longitude is required for these verified author-grid constraints. This audit does not assert that the geographic split prevents all scene, lake, basin or cross-tile dependence. With four components and one held-out component, independence is limited.

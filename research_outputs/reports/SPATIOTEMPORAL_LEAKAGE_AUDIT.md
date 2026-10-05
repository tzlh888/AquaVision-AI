# Spatiotemporal leakage audit — cached metadata only

Measured from the two complete Phase 1 filename inventories; no new image corpus was downloaded. Counts refer to those inventories, not the full published dataset.

| Quantity | Observed value / status |
|---|---|
| Paired sample IDs | 24,518 |
| CyAN archive tiles | 6_2 and 7_2 |
| Distinct calendar dates | 106 |
| Date span | 2019-01-04 through 2020-12-10 |
| Parent grid identifiers | 17, all 17 seen on multiple dates |
| Parent-grid/date combinations | 347 |
| Lowercase patch-grid position candidates | 1,391 |
| Positions observed on multiple dates | 1,386 |
| Extra samples sharing the same position-candidate/date | 0 |
| Within-tile adjacent parent pairs (including diagonal) | 23 |
| Connected parent-grid candidates | 4, all repeated over dates |
| Verified repeated waterbody observations | UNKNOWN: no waterbody IDs |
| Verified identical physical footprints across dates | UNKNOWN: no final geotransforms |

The 347 parent-date combinations are obtained as 24,518 minus 24,171 additional samples sharing a parent and date. Those additional samples are different patches, **not duplicate images**. Similarly, 1,386 recurring patch-grid candidates indicate potential repeated locations; their exact physical alignment is not proven after reprojection.

## Temporal density

| Candidate component | Indexed pairs | Unique dates | Span days | Median gap between observed dates |
|---|---:|---:|---:|---:|
| 6_2_X0650_Y0900_S050 | 3,945 | 42 | 675 | 10 days |
| 6_2_X1800_Y1050_S050 | 2,398 | 21 | 625 | 25 days |
| 7_2_X0000_Y1750_S050 | 17,893 | 35 | 705 | 12.5 days |
| 7_2_X1050_Y1550_S050 | 282 | 14 | 550 | 30 days |

These are retained-observation gaps, not orbital revisit periods or evidence that unobserved dates lack blooms. Tables `temporal_spatial_group_candidate.csv`, `temporal_grid_position_candidate.csv`, and `temporal_candidate_component_id.csv` report date counts, span, gaps and observed dates per 30 days using an explicitly inclusive calendar span denominator.

## Risk pathways

1. Random patch splitting can distribute multiple dates or neighboring patches of one location across train and test. This is exactly why the conventional benchmark is insufficient.
2. Splitting merely on parent ID allows adjacent parents to cross splits; the 17-to-4 component collapse demonstrates the issue.
3. Connected components are computed only on selected same-tile parents. Unselected intermediate parents, a lake crossing two CyAN tiles, or disconnected parts of one lake can still connect apparently distinct components.
4. A coarse S2 source scene can cover multiple parent groups; scene UUIDs were dropped from saved names, so scene-level overlap cannot currently be enumerated.
5. Seasonal and geographic shifts may be confounded. Future splits must report year/month distributions and independent units, not only sample percentages.

## Enforced design requirement

A geographic test lake must never occur in training on any date. Validation is also geographically disjoint. Require all intersecting waterbody identities and hold out entire verified basin/block units with crossing-waterbody unions/buffers. A temporal-generalization experiment would be separately named and designed; it is not substituted for the requested unseen-waterbody evaluation.

All current sample geographic identities are UNVERIFIED, so the split API refuses them. Synthetic tests confirm the intended invariants, including a sample intersecting two water bodies and a repeated footprint assigned to different groups. This validates software safeguards, not the current dataset geography. Actual spatial distances, basin membership and cross-lake exclusions remain UNKNOWN.

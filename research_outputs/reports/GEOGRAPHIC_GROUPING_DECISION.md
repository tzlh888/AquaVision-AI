# Geographic grouping decision — candidate constraints, no approved holdout yet

**Preferred design:** verified basin units, with all patches intersecting the same water body and all dates kept together. Merge or exclude units when a lake crosses a boundary. If basin metadata is unavailable, consider sufficiently large buffered spatial blocks subject to the same whole-waterbody constraint. No block size or real partition is selected from the current data.

## What can be recovered

The verified author filename code establishes CyAN tile, parent grid X/Y/S, date, patch row/column and sequence. In `generate_tiles.py`, parent X indexes raster columns and Y indexes rows. In `download_and_process.py`, lowercase patch `x` indexes array rows and `y` indexes columns. **These two naming conventions must not be conflated.**

`data/metadata/sample_metadata.csv` is canonical for the eight audited pairs. Coordinates, WKT footprint, Sentinel/MGRS tile, lake/waterbody IDs, basin/HUC and state remain null with explicit UNVERIFIED/UNKNOWN status. They are not set to zero, inferred from a picture, or confused with CyAN tile IDs. Parent and connected-component candidates are separate fields; `spatial_group_id` remains unset.

Why not calculate latitude/longitude from the name: the original CyAN transform/CRS and generated scene window are absent; final S2 reprojection determines pixel sizes; `sen2_uuid` is not saved; the absolute crop origin and final grid transform cannot be uniquely recovered from row/column indices alone. A known coarse tile bounding box would still not determine the exact final patch footprint.

Two original GeoTIFF attempts redirect to Earthdata authentication. Two NASA tile-shapefile URL forms returned 403. Current source tree, path history and the removed historical ZIP do not provide the missing `data.json`. See LABEL_PROVENANCE.md and `data/metadata/phase2_sources/*access*.json`. No coordinates were invented.

## Ranked candidate methods

Ranking is methodological preference for this project, not a measured performance ranking. All require checks for crossing water bodies and repeated scenes.

| Rank / method | Advantages | Leakage risk | Data requirements | Decision |
|---|---|---|---|---|
| 1. Watershed/basin + whole-waterbody constraints | Hydrologically meaningful separation; broader context shift | Connected waters or lakes can cross chosen basin units; nearby basins can remain correlated | Verified footprints, chosen HUC/basin level, all waterbody intersections, buffers | Preferred once validated; basin level not guessed |
| 2. Large spatial blocks + waterbody union/buffers | Explicit geographic distance and scale; reproducible | Arbitrary block edge can bisect a lake; neighboring blocks share context | Verified coordinates/footprints, projected metric CRS, lake polygons, declared block size/origin/buffer | Fallback; do not tune block size for scores |
| 3. Water-body grouping | Directly prevents same-lake temporal leakage | Nearby lakes, shared watersheds and overlapping S2 scenes remain correlated | Stable waterbody IDs for every intersected lake, not only center point | Mandatory constraint, potentially insufficient standalone geography |
| 4. Sentinel-2 tile grouping | Coarse acquisition grouping | Overlapping tiles and lakes crossing MGRS boundaries; two sensors may view same lake | Original scene/tile metadata and lake intersection checks | Unavailable; never substitute CyAN tile for MGRS |
| 5. State grouping | Simple policy-scale description | State lines often cross lakes/basins; adjacent states are not independent | Verified footprints and boundaries | Last resort; not selected |
| Diagnostic only: connected parent grids within CyAN tile | Available now; keeps neighboring parents and repeated dates together | Same lake may span disconnected selected parents or tile borders; missing parents can break graph connectivity | Verified filename convention, parent offsets | Implemented as candidates only; forbidden as final geography |

## Current connected components

Using all 24,518 names already cached, join same-tile parent cells with X and Y separation no greater than their encoded size 50, including diagonals. This follows the authors' adjacency concept, not an invented geographic transform.

| Candidate component anchored at | Parent-grid context | Indexed pairs | Distinct dates |
|---|---|---:|---:|
| 6_2_X0650_Y0900_S050 | CyAN tile 6_2 | 3,945 | 42 |
| 6_2_X1800_Y1050_S050 | CyAN tile 6_2 | 2,398 | 21 |
| 7_2_X0000_Y1750_S050 | CyAN tile 7_2 | 17,893 | 35 |
| 7_2_X1050_Y1550_S050 | CyAN tile 7_2 | 282 | 14 |

Seventeen parent IDs collapse to **four candidate components**. This materially reduces the apparent number of independent units; the actual independent-waterbody count is UNKNOWN. Cross-tile connections and unselected intermediary areas are not resolved. Do not call these four lakes or four independent regions.

## Split safeguards implemented

`src/aquavision/data/splits.py` requires verified targets, geography evidence, footprint IDs, finite coordinates and **all intersecting waterbody IDs**. It rejects sample/group/footprint/waterbody overlap, missing metadata, unrepresented classes and duplicate sample IDs. Geographic assignments must be supplied explicitly; the code does not search for a favorable allocation. Random stratification is seed-fixed and row-order independent. Frozen outputs are created exclusively, hash the source metadata and record the protocol.

These guards are tested using synthetic fixtures only. They cannot validate the truth of a caller-supplied VERIFIED flag; external evidence and spatial intersection/buffer audits remain mandatory. No final real split passes the prerequisites. The saved `splits/protocol.json` is a non-executable draft with null group assignments.

## Maps

No audited-sample, geographic-group or train/validation/test map is generated because no sample footprint is verified. `phase2_map_status.json` records each reason. The aggregation diagnostic figure is not a geographic map. No unknown location is plotted at (0,0).

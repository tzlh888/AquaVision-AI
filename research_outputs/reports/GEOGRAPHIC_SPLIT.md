# Geographic split design — not yet executed

The primary evaluation will hold out verified geographic units; the approximate 80/10/10 random split is only a conventional benchmark. Train, validation and test region lists and maps remain **undefined**, because verified footprints and water-body/basin IDs have not been recovered. Filename X/Y indices are not latitude/longitude.

Metadata inspection of the two training archives found:

| Archive tile | Pairs indexed | Parent groups | Groups with multiple dates | Grid-position candidates with multiple dates | Adjacent parent-group pairs |
|---|---:|---:|---:|---:|---:|
| 6_2 | 6,343 | 6 | 6 | 551 | 5 |
| 7_2 | 18,175 | 11 | 11 | 835 | 18 |

These are exact counts from the cached names; “adjacent” follows same-tile X/Y separation no greater than the encoded parent size, including diagonals. It is not a physical distance, a lake ID, or proof of footprint alignment. Cross-tile adjacency is not checked yet. Details and date distributions are in `research_outputs/tables/archive_metadata_summary.json`.

The source paper/code already attempts geographic separation through connected neighboring subtiles. Do not describe its original split as random patch splitting. AquaVision's eventual experiments need their own documented group audit and controlled random benchmark.

Future split hierarchy: basin → sufficiently large buffered spatial blocks checked for lake overlap → water-body group → state only if necessary. Hold out all dates of each unit, guard crossing lakes and overlapping scenes, fit preprocessing on training only, and freeze test units before model selection. Only when coordinates are verified can distance summaries and geographic maps be generated.

Mandatory implementation tests in the next split phase: pairwise-disjoint sample IDs; complete partition accounting; no train/validation/test group overlap; zero intersection between train and test group-ID sets; no missing/ambiguous groups accepted; repeated scenes/dates assigned consistently; required class support checked rather than assumed. These tests are **not claimed to pass now**, because no split implementation or actual split exists in Phase 1.

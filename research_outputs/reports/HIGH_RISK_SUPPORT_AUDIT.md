# High-risk support audit

The original 24,518-pair pool now has a **complete decoded reference census**, not a CRC-based inference. Every reference was read from its source or an already verified local pair; ZIP CRC, uncompressed size, NPY shape/dtype and SHA-256 were recorded. No Sentinel-2 member was downloaded for this census.

| Scope | Decoded pairs | High pairs | Valid pixels | High pixels | High % | High components | High dates | High source tiles |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Original cached pool — complete census | 24,518 | 123 | 85,603,357 | 99,620 | 0.116374 | 3 | 7 | 6_2, 7_2 |
| All screened — selected outside pool | 38,002 | 187 | 125,483,006 | 149,720 | 0.119315 | 12 | 35 | 6_2, 6_5, 7_2, 7_5, 8_3 |

The full six-archive directory inventory contains **404,450 paired IDs, 156 selected subtiles and 38 connected selected regions**. The publication's 938,607-pair experiment is a different reported total; it must not replace the measured deposit inventory. All six central directories were read, but only 38,002 reference masks were decoded. The other 366,448 reference contents remain uninspected.

Outside the original pool, screening selected up to 16 hash-ranked dates per subtile and up to four high-compressed-size reference members per date. This metadata-only heuristic favors varied masks; it does not imply High until decoded. These selected counts are **not** full-deposit class prevalence. No model outputs were accessed for candidate selection.

| Component | High pixels | High dates | Date span days | High grid positions | Qualified |
|---|---:|---:|---:|---:|---|
| author_grid_component:7_5_X1800_Y1700_S050 | 33,524 | 13 | 695 | 13 | True |
| author_grid_component:6_2_X0650_Y0900_S050 | 18,673 | 4 | 348 | 38 | True |
| author_grid_component:6_2_X0500_Y1150_S050 | 13,286 | 4 | 423 | 12 | True |
| author_grid_component:6_5_X0250_Y0450_S050 | 1,562 | 2 | 370 | 11 | True |
| author_grid_component:6_5_X0250_Y0300_S050 | 448 | 2 | 105 | 4 | True |
| author_grid_component:7_5_X1300_Y0900_S050 | 283 | 2 | 220 | 3 | True |
| author_grid_component:8_3_X0350_Y1550_S050 | 207 | 2 | 42 | 3 | True |
| author_grid_component:7_2_X0000_Y1750_S050 | 80,715 | 2 | 10 | 66 | False |
| author_grid_component:7_5_X1450_Y0500_S050 | 88 | 2 | 55 | 2 | False |
| author_grid_component:7_2_X1050_Y1550_S050 | 232 | 1 | 0 | 4 | False |
| author_grid_component:8_3_X0200_Y1550_S050 | 473 | 1 | 0 | 2 | False |
| author_grid_component:7_5_X1150_Y0350_S050 | 229 | 1 | 0 | 1 | False |

Candidate usefulness depends on dates, distinct grid positions and subtiles within independently held-out components; raw High pixel count alone is insufficient. Allocation tie-breaking is fixed seed-35042 hashing, never model performance. Exact candidate rows and every component/date/subtile are in `research_outputs/phase3_5/high_group_candidates.csv`, `high_group_subtile_date.csv`, and `high_patch_candidates.csv`.

The preregistered candidate gate is **PASS**; qualifying components: 7. Passing this candidate gate does not yet freeze a split or authorize model evaluation: selected pairs must still meet support and integrity criteria after acquisition.

The original support-criteria contract is preserved. Acquisition amendment A was recorded after a two-range transport probe showed batching could make a full census practical. It changed only the mask-count limit; all scientific support criteria, 64 MiB reference byte budget and 1,200-request cap stayed fixed. Reference requests and charged bytes are logged under `data/metadata/phase3_5/`.

## Targeted follow-up (round 2)

The first round identified five qualifying regions. Before any paired imagery or model evaluation, a frozen follow-up plan examined alternate dates (prioritizing spans ≥30 days) at known High grid positions, neighboring positions and then other positions in High-bearing but nonqualifying components. At most 1,024 additional masks per such component were selected. All criteria and the cumulative reference budget stayed unchanged. The original complete 24,518-mask census and round-1 audit are preserved; merged round-2 counts add targeted observations and remain unsuitable as full-corpus prevalence.

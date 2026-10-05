# High-risk independence audit

Pixel totals and numbers of independent geographic components are reported separately. The complete selected-grid graph contains 38 components across five CyAN tiles. Source subtiles inside a connected component are not counted as independent test regions. All dates inherit the same grouping.

Among decoded High-bearing references, there are 136 patches with another High-bearing adjacent patch on the same parent/date grid, 23 grid positions recurring across dates, and 7 positions repeating within 30 days. These are correlated support, not independent geographic replicates. Exact tabulations are in `high_independence.csv`.

Identical label-mask hashes are also counted, but equal reference masks alone do not prove duplicate Sentinel inputs or identical geographic footprints. Input content hashes are checked after any selective paired-image acquisition. Final grid transforms and scene UUIDs were not preserved; exact source-scene sharing and physical overlap remain UNKNOWN. Dates are not renamed scene identifiers.

A 30-day span criterion reduces dependence on a single short observation window but cannot establish bloom-episode identity. Long events may span months, neighboring patches share interpolated coarse reference cells, and separate subtiles may share a lake or source scene. Same CyAN tile is reported as a shared larger source unit; multiple within-tile components are not assumed hydrologically independent.

The best-supported independence claim is **disjoint connected selected author-grid regions**, with test regions spanning multiple CyAN tiles when the gate permits. Unknown cross-tile lake/scene dependence remains a limitation. No latitude/longitude or bloom-event IDs are invented. Rankings use only source metadata and decoded references, never model scores.

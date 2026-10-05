# Evaluation support criteria — frozen before expansion evaluation

Version: phase3_5_v2. Date: 2026-10-04. The order is **dataset characteristics → support criteria → frozen split → model evaluation**. Existing pilot metrics, memberships and checkpoints are immutable. No model score, prediction, loss or model-derived uncertainty will rank candidate regions or determine new membership.

## Required support

The primary geographic unit is the connected component of selected fixed author subtiles within a CyAN tile, including diagonal adjacency and all dates. Subtiles within one component are not counted as independent geographic evidence. Components are reconstructed on the complete available indexed selection before sampling. Source subtile IDs, source CyAN tile IDs and temporal support are reported separately. Same-scene/lake/cross-tile dependence remains unverified where metadata is missing.

Before allowing a three-class evaluation, require:

- Test: at least **three High-containing connected geographic components**, spanning at least **two CyAN tiles**.
- Validation: at least **one separate High-containing component**.
- Train: at least **two separate High-containing components**.
- For each qualifying component: verified High support from at least **two dates spanning ≥30 days**, at least **two patch-grid positions**, and at least **100 High reference pixels** across the selected evidence. Pixel count is only a small support floor, never a substitute for spatial replication.
- All three target classes occur in each partition's valid reference pixels.
- No sample ID, source subtile, connected component or prohibited selected-grid adjacency crosses geographic partitions. Check content-hash duplicates and quarantine any confirmed cross-partition duplicate rather than silently accepting it.
- Actual downloaded reference/input pairs have matching sample identities, 12×64×64 input and 1×64×64 reference shape, and verified source CRC/hash. Shape/ID alignment does not independently prove historical physical registration.

These are preregistered **operational adequacy criteria for this study**, not universally validated sample-size thresholds. Thirty days reduces a short-event concentration but does not prove two independent bloom episodes. Pixel-level uncertainties must not treat interpolated pixels as independent samples. Three test components still provide limited geographic replication; any stronger reliability claim would require more.

## Evidence and bounded screening

Audit the 24,518-pair metadata pool completely. File names alone contain no High counts. CRC/size matches can prioritize reference retrieval but are not cryptographic proof of equal pixel content; do not convert them into verified corpus-wide counts. Distinguish exactly decoded observations from unscreened candidates. Reference-only retrieval precedes any additional Sentinel-2 pair acquisition.

The acquisition budget is explicit in `configs/phase3_5.json`: up to 192 MiB of ZIP index ranges, 64 MiB of reference ranges, 1,200 reference HTTP requests, and 1,024 new decoded reference masks. If support qualifies, a later pair acquisition is capped at 64 MiB and 384 new pairs. No full archive fallback exists. Rate limits trigger bounded backoff and are reported. Budget-limited screening cannot prove absence of High in unscreened data.

Use no model outputs. Rank verified candidates by independent-component contribution, date/position diversity and demonstrated class support. Break ties deterministically with a salted seed-35042 hash. More High pixels from one event or parent cannot compensate for a missing test component.

## Split and stop rules

Only freeze a new geographic v2 membership after required support is measured and checked. Existing pilot splits remain unchanged. If fewer than six qualifying components are found, or three eligible test components cannot cover two source tiles while preserving train/validation support, do not force a nominal three-class split. Publish a blocked split status, exact support tables, scope of screening and remaining unknowns; do not run models.

If the gate passes, use the existing Phase 3 model definitions/configuration before tuning. Report pooled and per-component accuracy, macro/weighted F1, all per-class precision/recall/F1 and confusion matrices. Save every result under a new Phase 3.5 directory.

Outcome A requires valid independent support and meaningful performance; B denotes limited/unstable evidence; C denotes insufficient support in the audited available data. Under bounded incomplete screening, C must not be generalized to a claim that the complete deposit contains no adequate High-risk regions.

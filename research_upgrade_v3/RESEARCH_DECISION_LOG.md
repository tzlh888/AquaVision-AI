# AquaVision Research Decision Log

Append new entries; do not rewrite historical decisions or failed outcomes.

| Date | ID | Decision | Evidence / rule | Outcome / status |
| --- | --- | --- | --- | --- |
| 2026-10-12 | AV-D-001 | Freeze baseline at `bd11eceaa7efa7ca785d5e466cf807312ed70df0` on `research-upgrade-v3`. | Clean `main`; repository configs/results retained. | Complete; no commit or push. |
| 2026-10-12 | AV-D-002 | Register all pilot, v2 validation/test, Phase 4 and Phase 5 evaluations as legacy. | Results have been inspected or used in decisions. | Frozen; none is a new holdout. |
| 2026-10-12 | AV-D-003 | Preserve NDCI as the historical validation-selected model and weighted DeepLab as diagnostic/non-eligible. | Registered validation selection; post-hoc test performance cannot revise it. | Historical conclusion unchanged. |
| 2026-10-12 | AV-D-004 | Count connected geographic components separately from patches/pixels and retain lake/scene/event independence as unknown. | Missing exact geospatial/scene/event provenance. | Frozen limitation. |
| 2026-10-12 | AV-D-005 | Perform no AquaVision training or model selection in Phase 2A. | User scope and lack of new independent data. | Enforced. |

## Required future fields

Record the research hypothesis, eligible-data hashes, grouping unit, split hashes, seed, candidates/search space, qualification and selection rules, uncertainty method, stopping criteria, failure interpretation, output directory, and whether evidence is exploratory or confirmatory before execution.

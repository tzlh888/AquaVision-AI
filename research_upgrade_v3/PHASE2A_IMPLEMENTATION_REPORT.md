# AquaVision Phase 2A Implementation Report

## Outcome

The AquaVision protocol freeze succeeded on `research-upgrade-v3`. The baseline commit, configuration/result hashes, legacy benchmark registry, evidence eligibility, independence limits, decision log, and unresolved gaps are now explicit. No historical file, model, split, result, figure, or report was modified. No model was trained, tuned, selected, committed, or pushed.

## Preserved findings

- The target is a CyAN-derived proxy, not direct field ground truth.
- The v2 split remains 96/48/144 train/validation/test patches across 2/1/3 connected groups.
- High support remains 647/931/37,768 pixels across those splits; pixel volume does not equal independent geographic evidence.
- NDCI remains the historical validation-selected model. Logistic Regression test High F1 is post-hoc and non-selecting.
- No CNN passed the registered validation class guard; the weighted DeepLab remains diagnostic.
- The final scientific status remains LIMITED.

## Reproducibility boundary

`EVIDENCE_MANIFEST.csv` records hashes for the checked-in configs, contracts, support table, model metrics, selection timestamp, results, delivery manifests and final audit. Phase 5's complete local reload remains the strongest historical reproduction record. Raw arrays, checkpoints and prediction caches are absent from the public checkout, so no fresh end-to-end inference claim is made here.

## Remaining requirements

AquaVision should not enter a new selection phase without new or restructured development evidence and a genuinely untouched confirmation source with verified lake/scene/footprint/event provenance. Existing test data remain useful only as legacy context.

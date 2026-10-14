# AquaVision V4 dataset readiness decision

## Decision: **NOT READY**

The frozen minimum is nine qualified independent real-waterbody units: 3 Training, 3 Validation, and 3 Confirmation. A dynamic, fail-closed review of the **current frozen V3 evidence pool** found **0** qualified units. Because the pool remains below the gate, it assigns **0/0/0** members. This is not a claim that new external data were audited, no confirmation set is sealed, and no new model training is permitted.

The evaluator derives the outcome from explicit identity, date span, non-overlapping High-patch support, unique dated native High identity support, complete Sentinel/CyAN provenance, registration/mask/product-version checks, and resolved independence. Missing or conflicting evidence fails closed. The V3 table does not expose the last two gates as independently reviewable unit-level fields, so those fields are reported as `UNKNOWN`, never inferred from `provenance_complete_for_available_scenes`. The audit treats a waterbody history—not a 64×64 patch, Sentinel crop, resampled target pixel, or native CyAN pixel—as the independent unit and deduplicates repeated waterbody identities before counting.

This is a scientific stop decision, not a failed software run. See `GEOGRAPHIC_IDENTITY_AUDIT.csv` and `INDEPENDENT_HIGH_UNIT_AUDIT.csv` for every inclusion/exclusion reason.

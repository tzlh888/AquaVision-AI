# v3 Confirmation Set Protocol

## Status

No confirmation set exists in Phase 3A-2. Membership count is 0. The six pilot candidates are unassigned and may not be described as confirmation observations.

## Purpose

The confirmation set is a one-time, model-independent assessment source. It is not a tuning split and cannot repair weak development or validation evidence.

## Pre-seal eligibility

Confirmation candidates must pass every v3 data-eligibility gate, including exact source hashes, CyAN version, complete geographic identity, frozen label processing, and High-support census. Support-based sampling is permitted only under the predeclared rule and must be documented as stratified sampling that changes the observed class distribution. No model prediction, error, embedding, or uncertainty score may be used to select a member.

At least 3 independent High-support units are required to instantiate a minimal set; 10 or more are the target. The minimal set carries high uncertainty and is insufficient for a deployment claim.

## Seal procedure

1. Remove every component connected to development or validation by waterbody, scene, overlapping footprint, duplicate source product, or bloom/event group.
2. Assign remaining eligible units using a deterministic, documented selection rule.
3. Save the complete member list, exclusions, source/product hashes, label-processing configuration, contamination graph hash, and dataset-manifest hash.
4. Record a seal timestamp and create a read-only local evidence snapshot before any candidate model is trained.
5. Expose only aggregate support needed to prove set eligibility. Do not compute, view, or release candidate-model performance on the sealed members during selection.

Once sealed, membership, preprocessing, label thresholds, and primary metrics cannot change in response to model results. A broken seal or membership correction creates a new confirmation version; the earlier set becomes legacy evidence.

## Permitted use

- One final evaluation of a model and decision rule frozen using development and validation only.
- Predeclared aggregate and independent-unit metrics with group-clustered uncertainty.
- Honest reporting of undefined metrics, failures, and adverse tradeoffs.

## Prohibited use

- hyperparameter, architecture, threshold, feature, preprocessing, or early-stopping selection;
- repeated peeking followed by further model development;
- splitting scenes, patches, or dates from one independent component across roles;
- calling v3 confirmation independent of v2 when a v2-trained model is used and v2 footprints remain unknown;
- interpreting three units as population-level or deployment validation.

## Release gate

Confirmation evaluation remains prohibited until the actual set is sealed, its hash is registered, cross-split isolation passes, and the research decision log records that all model choices are frozen. Current gate result: **FAIL — zero eligible members**.

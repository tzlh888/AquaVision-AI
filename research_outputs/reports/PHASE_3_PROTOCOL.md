# Frozen bounded pilot protocol

The scientific task is **multispectral semantic segmentation of published CyAN reference risk classes**, emphasizing generalization to geographically unseen author-grid regions. This is not an in-situ cell-count estimator.

## Selection and split contract

The 24,518-pair pool is indexed, not fully downloaded. It includes 17 selected parents in two training archives. Before inspecting new labels, rank sample IDs independently within each parent using SHA-256 of `42:sample_id`, retain 16 per parent, and sort the resulting **272** IDs. This provides every selected parent but deliberately does not preserve whole-pool geographic prevalence. The selection uses no risk labels. The original eight access-probe samples are not forced into the pool.

Connected components are calculated on the complete cached pool before sampling. The author adjacency condition connects same-tile parents when both coordinate differences are ≤50, including diagonals. Date is excluded from the grouping key. Seed 42 shuffles sorted components once: reserve last for test, penultimate for validation, remainder for train. This protocol is a new three-way holdout, not the author's unrecoverable original full-corpus membership.

The random comparator partitions the exact same 272 patches 80/10/10 with a seed-42 shuffle. It is not stratified by a fabricated image-level class. The complete pool also has frozen random/geographic index assignments for leakage diagnostics. Pilot random assignments are generated on the pilot pool and therefore need not match the full-pool random table.

`data/metadata/phase3/frozen_plan.json` contains all assignments, metadata hashes and hyperparameters. It was persisted before pilot label retrieval and refuses non-identical replacement. CSV split tables are readable exports; training consumes and checks the immutable JSON contract.

## Reference handling

Y is an int64 H×W map: DN 0–99 → 0, 100–199 → 1, 200–253 → 2. Both special values 254/255 and invalid numerical values use ignore index -100. Zero remains Low. No scalar image class is constructed. No additional S2-derived cloud/land heuristic is imposed after source processing. Patch filtering discrepancies are retained as a limitation, with per-patch valid counts recorded.

## Same-model comparisons

Five one-index baselines use equations (6)–(10) of the paper. FAI uses nominal 665/865/1610 nm wavelengths; no spacecraft-specific response is inferred. Fit two thresholds and increasing/decreasing class direction on training pixel samples only, using an 11-quantile candidate grid and fixed three-class macro F1. Undefined ratios are imputed with the training median for one-index baselines; coverage is recorded. This is a bounded threshold search, not the paper's Bayesian optimizer.

Classical models use 12 bands scaled by 10,000, five justified indices and five missing-index indicators. Select at most 256 valid pixels per training patch uniformly without replacement, then cap total training pixels at 32,768. No class balancing is used in the initial baseline. Save every sampled pixel identity. Logistic regression fits standardized features with up to 400 iterations; the random forest uses 64 trees, depth 12 and minimum leaf size 2. Class predictions and confusion matrices remain pixel-level.

SmallSegCNN uses Conv2d → ReLU → pooling → Conv2d → ReLU → bilinear upsampling → convolutional logits. DeepLabV3 uses the author's ResNet18 constructor with 12 channels, three output classes and **random initialization**. No pretrained weights are downloaded. Both use pixel-wise unweighted cross entropy, ignore masks, Adam (learning rate 0.0001, weight decay 0.01), and joint horizontal/vertical image-mask flips. SmallSegCNN has three epochs and DeepLab two; CPU execution is deterministic with four threads. An elapsed budget of 240 seconds is checked after each epoch, so one epoch may extend beyond it. This is a pilot budget, not convergence training.

Training inputs alone provide channel means/stds. Epoch shuffling is seeded. A final singleton batch is merged into the preceding batch, preserving all patches and avoiding DeepLab global-pooling BatchNorm failure. Select the minimum validation cross-entropy checkpoint within the fixed epoch budget. Test labels do not affect threshold fitting, normalization, pixel sampling, checkpoint selection or hyperparameters.

## Metrics and interpretation

Evaluate every valid pixel in validation and test patches, with no test balancing. Save confusion matrices, per-class precision/recall/F1/support, accuracy, supported-class macro F1, and fixed-three-class macro F1 with zero division set to zero. When a class has no reference support, its recall/F1 is null and full three-class coverage is false. A fixed-three-class scalar remains a computational diagnostic, not evidence about the absent class.

The central table reports random and geographic metrics for the same model and Δ = random minus geographic macro F1. Test regions, class prevalence and training counts differ by design. With a single seed and very few regions, Δ is descriptive and cannot isolate a causal leakage penalty or support population confidence intervals. Model family is held constant; no architecture is tuned separately by split score.

## Imbalance: staged alternatives

The publication's full-corpus ratios (89.51%, 10.34%, 0.15%) are source-reported and must not be assigned to our subset. Measure pilot counts separately. Start unweighted for both splits. Implemented optional loss paths support class-weighted cross entropy and focal modulation, but neither is active in this run. Class-balanced pixel sampling would change training prevalence; keep test prevalence natural. A later single-factor experiment should compare unweighted against training-only inverse-frequency class weighting while keeping membership, initialization and all other settings fixed. Only then consider balanced sampling or gamma-2 focal loss separately. These alternatives are not equivalent to the paper's per-DN weighting D(0)/D(v).

## Resource and inference limits

Download only planned pairs through bounded byte ranges, never full ZIPs. Each archive attempt is capped at 48 MiB; retries reserve budget and use backoff on HTTP 429. Runtime packages and saved checkpoints are additional storage. The first interrupted attempt preceded durable access logging; do not report its traffic as zero. Successful manifests, current-attempt access logs, array CRC/SHA checks and artifact hashes are retained.

No Grad-CAM, robustness, calibration, frontend, Streamlit or hyperparameter sweep is included. This protocol produces a bounded pilot and reusable pipeline; the full Phase 3 milestone remains subject to adequate independent-region and rare-class evaluation support.

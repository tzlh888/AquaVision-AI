# Phase 5 status

## Final scientific conclusion

**LIMITED.** AquaVision provides evidence that 12-band Sentinel-2 observations contain predictive signal for pixel-level CyAN-derived bloom-risk classes, but it does not demonstrate reliable three-class geographic generalization. High-class performance varies substantially among the three held-out regions. The predefined validation procedure selected NDCI even though its validation High F1 is `0`, and no CNN passed the predefined class guard. Logistic Regression's geographic-Test High F1 of `0.5803` is a post-hoc observation and is not a valid reason to override validation-based selection.

## Final repository status

Phase5 packaging is complete. The frozen v2 split, Phase4 metrics, selection result, predictions, and historical reports were preserved. No additional model experiment, seed search, architecture search, hyperparameter tuning, Test-region search, or post-hoc selection was performed. The root README now serves as the concise public entry point, while the canonical report contains the full scientific account.

## Final test count

The final suite reports **123 passed, 0 failed, 0 errors, and 0 skipped**. Pytest output is retained in [`pytest_results.xml`](../phase5/pytest_results.xml).

## Reproducibility status

The full local audit passed. It verified all **443** protected historical files, the frozen split hash, **100** exact confusion-matrix reconstructions, **40** exact class-prediction caches, **96** exact calibration group/mode results, 18 temperature/argmax invariance checks, and hashes for all 288 input pairs. No training occurred during the audit. Public-document links, word limits, figures, table values, and the README's 49 claim-source records also passed automated checks.

Complete checkpoint reload depends on local raw arrays, checkpoints, and caches that are not intended for Git distribution. A fresh public clone therefore supports inspection and metadata auditing, but requires those documented artifacts for full inference reproduction.

## Files created

- Four primary written assets: the canonical research report, portfolio summary, CV description, and application description.
- Two release-control reports: this status report and the final release audit.
- A figure index and an archive/source-scope index.
- Ten core figures in both PNG and SVG formats, plus a machine-readable figure manifest.
- A six-model final-results table in CSV and Markdown formats, with a machine-readable central-results copy.
- A preservation manifest, README claim-source ledger, bounded claim-occurrence ledger, pytest XML, complete audit JSON, metadata audit JSON, and audit logs.
- Reproducible Phase5 builder/audit scripts for figures, indexes, the final table, and release verification.

## Public-facing materials created

- [`RESEARCH_RESULTS.md`](RESEARCH_RESULTS.md) — canonical scientific report.
- [`PORTFOLIO_SUMMARY.md`](PORTFOLIO_SUMMARY.md) — one-page technical overview.
- [`CV_DESCRIPTION.md`](CV_DESCRIPTION.md) — one-line and two-bullet CV versions.
- [`APPLICATION_DESCRIPTION.md`](APPLICATION_DESCRIPTION.md) — reflective application-ready description.
- [`FIGURE_INDEX.md`](FIGURE_INDEX.md) — ten-figure portfolio index with captions and vector links.
- [`FINAL_RELEASE_AUDIT.md`](FINAL_RELEASE_AUDIT.md) — verification evidence and reproducibility boundary.
- Root `README.md` — public project overview, results, limitations, repository map, and run instructions.

## Remaining limitations

CyAN masks are coarse satellite-derived references rather than direct laboratory measurements. High-risk geographic support is concentrated in few independent held-out regions, individual pixels are spatially correlated, and regional spectral shift remains strong. Atmospheric effects, temporal mismatch, resampling, and uncertainty in the reference product limit interpretation. The bounded dataset and compute budget leave model-selection uncertainty. The band-ablation and robustness studies use controlled short protocols and synthetic perturbations, so neither establishes a stable multispectral advantage or operational atmospheric robustness. Attribution is descriptive and does not establish causal reasoning.

## Application-ready assets

The project now has a short public README, a self-contained technical summary, a detailed research report, CV copy, application copy, a concise verified table, and ten publication-quality figures. These materials consistently distinguish validation selection from Test observation and preserve the negative results that make the study credible.

## Recommended next action

Use the package in university applications, GitHub review, technical interviews, and research discussions. Lead with the methodological correction from image classification to segmentation, the geographic-validation design, and the decision to retain a LIMITED conclusion despite an appealing post-hoc Test score. Further model development is not recommended for this completed project; any future research should begin as a separately registered study with new independent geographic support and, ideally, laboratory-linked reference measurements.


# Image-level label definition — primary risk target NOT VALIDATED

**There is no finalized scientifically supported Low/Moderate/High image label yet.** The original archive supports pixel-level DN references. Phase 2 compares candidate reductions transparently; it does not silently make mean DN the image's risk.

The primary recommended next formulation to evaluate is **fraction of verified water area above a validated abundance threshold**, which expresses bloom extent. It cannot yet be computed: conversion and the complete water-area mask are missing. A choice of fraction cutoffs or scalar three-class mapping would be a new experimental definition requiring justification. It is not specified from eight examples or chosen to improve class balance.

The strongest immediately computable alternative is the **native-reference bin-fraction vector** over valid reference pixels. This is a descriptive target with explicit DN units, not a physical risk category. If one wants to reproduce the source study, its native per-pixel classes avoid inventing an image-level aggregation. Changing the project's primary task to this alternative is not assumed.

## Candidate comparison

| Requested rule | What can be calculated now | Environmental meaning / why not finalized |
|---|---|---|
| A. Median abundance | Median stored DN and corresponding native bin | Describes the typical retained encoded pixel; abundance unknown. May suppress spatially small blooms. We use the observed order statistic (`inverted_cdf`), not averaging the two middle DN values |
| B. Mean abundance | Arithmetic mean DN, marked diagnostic only | Mean in encoded/log space is not mean cell density. Rejected as automatic risk target |
| C. Maximum / upper quantile | Maximum and 90th-percentile observed DN | Potential localized-elevated-reference proxy; maximum sensitive to a single artifact. 90th percentile is a declared sensitivity scenario, not a source-validated environmental cutoff |
| D. Majority risk class | Majority native DN bin; ties return UNKNOWN | Supported as a description of dominant native reference category, not proof of risk. Minority elevated areas are lost |
| E. Area exceeding risk threshold | Fraction of retained DN ≥100 and ≥200 | Only native-bin extent among valid reference pixels; land/cloud exclusions prevent a verified water-area denominator. No final class cutoff chosen |
| F. Center/matched pixel | Four central-pixel DN values and bin consensus | The source is dense segmentation, not center-sampled supervision. Even 64x64 images have four center pixels. No single center was arbitrarily selected; mixed/masked centers return UNKNOWN |

Physical median/mean/quantile abundance are not calculated; these comparisons are **native-DN proxies only**. Both raw references and hashes are preserved. DN 0 is retained as below detection, not asserted to be zero cells/mL. Flags 254/255 and invalid/NaN values are excluded; all-invalid patches never become bin 0.

## Measured eight-pair comparison

Complete results: `research_outputs/tables/image_aggregation_comparison.csv` and `phase2_aggregation_sensitivity.png`. Seven patches have only zero DN among their valid reference pixels. The remaining patch is:

`7_2_X1050_Y1550_S050_2020_10_23_x64_y320_64x64_7`

| Statistic on its 1,757 valid reference pixels | Measured value | Diagnostic bin |
|---|---:|---:|
| Median DN | 12 | 0 |
| Mean DN | 41.98634 | 0 |
| Maximum DN | 153 | 1 |
| 90th-percentile DN | 124 | 1 |
| Majority native bin | 1,399 pixels in bin 0, 358 in bin 1 | 0 |
| Fraction DN ≥100 | 20.37564% | No image-class cutoff |
| Fraction DN ≥200 | 0% | No image-class cutoff |
| Four center DNs | 1, 0, 1, 0 | Consensus bin 0 |

Thus **one of eight** audited patches changes native diagnostic category under aggregation. This is a measured sensitivity in a small biased access probe, not an estimate of corpus-wide disagreement. In the patch with 90.53% masking, the four center pixels are all 255; its center label is UNKNOWN even though all observed valid pixels elsewhere are below detection.

## Coverage sensitivity and denominator problem

| Required retained-reference fraction (scenario) | Passing patches out of 8 |
|---:|---:|
| 5% | 8 |
| 50% | 6 |
| 80% | 5 |
| 95% | 5 |

These scenarios compare source-code-like versus strict coverage requirements. They are not approved quality criteria. In particular, a shoreline patch may have little retained reference because of land rather than cloud; since causes are merged, the fraction above is not the fraction of *water* observed. The mixed patch above would be excluded by the 50% scenario, leaving no evidence of aggregation disagreement among the survivors. That does not validate the rule—it changes the observed sample composition.

The [Mishra et al. primary study](https://repository.library.noaa.gov/view/noaa/50665/noaa_50665_DS1.pdf), §2.4, uses a lake-level median of detectable index pixels and a lake valid-area requirement in a presence/absence design. Its lake geometry and estimand differ from our 64x64 patch, so that precedent cannot simply be copied into a three-class patch-risk rule.

## Decision and next evidence

No scalar primary risk label is finalized. Require a verified water mask, matched abundance interpretation, and a larger *independent-location* labeling pilot before selecting an aggregation. Predeclare the target's intended meaning (typical severity versus localized event detection versus extent) and its coverage/boundary sensitivity. Preserve the vector of native reference fractions and UNKNOWN status in the meantime. Do not choose an aggregation after seeing model scores or use the test set to resolve these choices.

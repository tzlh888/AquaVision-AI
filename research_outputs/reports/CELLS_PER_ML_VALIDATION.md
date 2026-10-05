# cells/mL validation — DISABLED for this archive

**Decision: do not convert the AquaVision stored references to cells/mL.** This is an evidence limitation, not a claim that CyAN can never support calibrated abundance estimates.

## Candidate equations and their units

Let `d` be an original valid product digital number; `CI` is the cyanobacteria index, not cell density; `N` is an estimated Microcystis-equivalent cell concentration when a matching calibration is justified.

| Candidate | Equation | Source and status |
|---|---|---|
| A: current original-product DN encoding | `CI = 10^(0.011714*d - 4.1870866)` | [NASA CyAN DN guide](https://oceancolor.gsfc.nasa.gov/about/projects/cyan/), directly inspected HTML |
| B: alternate historical encoding + abundance factor | `N = 10^8 * 10^((3/250)*d - 4.2)` | [O'Shea et al. (2023), section 3.4.2](https://www.frontiersin.org/journals/remote-sensing/articles/10.3389/frsen.2023.1157609/full), applied to their 2018 CyAN analysis and attributed to NASA (2018). The displayed variable name conflates index and abundance; units require the `10^8` factor to be understood separately |
| C: CI-to-abundance calibration | `N ≈ 10^8 * CI` | [Stumpf et al. (2012)](https://doi.org/10.1371/journal.pone.0042444) relates CI 0.001 to about 100,000 cells/mL; [Mishra et al. (2021), §2.4](https://repository.library.noaa.gov/view/noaa/50665/noaa_50665_DS1.pdf) uses CI 0.0001 as 10,000 Microcystis-equivalent cells/mL, citing Lunetta/Wynne |
| Tempting but invalid shortcut | Treat `10^(a*d+b)` itself as cells/mL | Rejected: removes the calibration factor and confuses units |

The [Lunetta et al. (2015) primary publication](https://doi.org/10.1016/j.rse.2014.06.008) concerns validation of MERIS-derived cell estimates, with variable correspondence across abundance ranges. It is not a validation of this later resampled Sentinel-2/CyAN archive. No numerical accuracy from that paper is adopted as AquaVision performance.

**Version matching:** neither A nor B can be pinned to the original daily GeoTIFF processing version used in this deposit. The released and historical processing code uses neither equation; it stores resampled DN directly. Dates of imagery alone do not determine the processing version. Existing eight pairs contain no conversion metadata. Consequently, neither candidate is selected for sample conversion.

## Valid range and flags

NASA documents original DN 1-253 as data, 0 as below detection, 254 as land, 255 as no data. An exponential applied to zero produces a nonzero number but does not recover the below-detection observation. Flags must never enter the exponential or aggregation. A valid-DN numerical range is not proof that empirical cell-count calibration is reliable across all species, water types and high-end/saturated observations. Saturation treatment for this archive remains unverified.

The Microcystis-equivalent relationship is approximate and surface-sensitive. Stumpf et al. discuss sensitivity to wind/vertical distribution and uncertainty in cell correspondence; this is not a generic laboratory count conversion. Calibration transfer from MERIS/source regions to a mixed OLCI product, followed by DN interpolation and reference masking, requires explicit justification.

## Analytical disagreement, not new observations

Solving candidate equations algebraically illustrates why choosing a formula matters. Under A followed by C, 20,000 cells/mL corresponds to DN approximately 41.670 and 100,000 to DN 101.339. Under B those DN values are approximately 41.752 and exactly 100. These are **formula comparisons**, not abundance estimates for any of the eight samples.

The paper's DN cutoffs at 100 and 200 therefore do not match the requested 20k/100k thresholds under either candidate. As another algebraic check, candidate A+C maps DN 100 to about 96,452 and DN 200 to about 1,431,243 cells/mL; candidate B maps them to 100,000 and about 1,584,893. These numbers are not written into sample audit cells/mL fields.

## Why an original-product formula is insufficient here

For bilinear weights `w_i`, resampling DN and then exponentiating gives `10^(a*sum(w_i*d_i)+b)`. Resampling physical estimates instead gives `sum(w_i*10^(a*d_i+b))`. These differ in general, even before byte rounding and mask changes. Thus a physical estimate on stored interpolated DN would describe a chosen approximate transformed field, not recovered original pixel cell density. That interpretation might be studied later but is not presently validated.

Original-product version, source flags, GDAL resampling behavior, cell calibration applicability and valid-water denominator all remain unresolved. The two attempted original rasters require Earthdata authentication. The current NASA guide cannot resolve the provenance alone.

## Threshold decision

The requested convention is recorded, disabled, in `configs/phase2.yaml`: Low <20,000; Moderate ≥20,000 and ≤100,000; High >100,000. The key is explicitly `high_above_exclusive`, avoiding the misleading implication of an inclusive `high_min`.

The conversion-validity prerequisite failed, so no operational risk threshold validation or class assignment is claimed. O'Shea et al. discuss those categories for their own analysis; this does not validate their use with our processed reference or prove equivalence to the dataset paper's bins. Original health-guideline applicability would need separate examination if conversion is enabled later.

Tests at 19,999, 20,000, 20,001, 99,999, 100,000 and 100,001 verify **refusal of unsupported conversion** and rejection as native DN. They do not certify a numerical cells/mL conversion. Native DN boundaries, flags and invalid values are separately tested.

## Strongest supported alternative

Retain native CyAN-derived pixel-bin masks and per-patch native-bin fractions as reference-product descriptors. Their units and limited interpretation are explicit. Pixel-level source-task replication is better supported than a new health-risk image classifier, but this is an alternative research formulation, not an automatic change of the user's task. No models are trained under either formulation.

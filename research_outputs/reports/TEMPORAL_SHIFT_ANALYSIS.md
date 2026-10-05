# Temporal composition and reliability

| Region | Unique dates | Months represented | 2019 patches | 2020 patches | Patch-month TV vs Train | LR High F1 |
| --- | --- | --- | --- | --- | --- | --- |
| 6_2_X0500_Y1150 | 14 | 7 | 25 | 23 | 0.4792 | 0.5809 |
| 6_2_X0650_Y0900 | 27 | 10 | 32 | 16 | 0.6146 | 0.4006 |
| 7_5_X1800_Y1700 | 14 | 6 | 33 | 15 | 0.3333 | 0.5964 |

The worst LR/CNN High-F1 region, 6_2_X0650_Y0900, also has the largest patch-month distribution difference from Train (total variation0.6146). That alignment is descriptive. It does not establish that seasonality caused the failure: only three regions exist and date, location, High prevalence and selection mechanism change together.

[`temporal_distributions.csv`](../phase4/temporal_distributions.csv) reports month, year and DJF/MAM/JJA/SON calendar bins with both patch weighting and unique-date weighting, including zero-count months. Unique dates are not independent bloom events; multiple spatial patches on the same date must not be treated as independent acquisitions. All pools cover only 2019–2020; no future-year generalization was evaluated. Regional coverage ranges14–27 dates across 6–10 months, with empty seasons/months and High-enriched anchor selection. Seasonal bins are descriptive calendar bins, not an inferred ecological season model.

[`temporal_shift.json`](../phase4/temporal_shift.json); [month composition](../phase4/plots/temporal_shift.png). Sparse coverage prevents strong temporal attribution or season-specific operating claims.

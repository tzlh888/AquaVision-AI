# Training subset decision

**EXPAND SUBSET — expand independent geographic coverage, not automatically the patch count to 50,000.** Keep the current pool as development data and retain this frozen pilot as historical evidence. No additional archive expansion is performed in this run.

The 24,518 indexed pairs span two CyAN tiles, 17 fixed parent subtiles, four selected adjacency components and 106 dates. Exact Sentinel scene count is UNKNOWN. Four components yield only two train components, one validation component and one test component under the declared three-way protocol. More repeated patches from these same components cannot establish broad regional reliability.

Only 272 label-blind pilot pairs were loaded for this phase. They contain **922,399 valid reference pixels: 858,158 Low (93.0354%), 63,305 Moderate (6.8631%), and 936 High (0.1015%)**, with 191,713 ignored pixels. These are exact pilot counts. Full 24,518-pair valid/class counts and percentages remain UNKNOWN; archive filenames cannot supply them. Equal sampling per subtile means even the pilot percentages are not an unbiased estimate of the indexed population.

| Split | Patches | Valid pixels | Low | Moderate | High |
|---|---:|---:|---:|---:|---:|
| random / train | 217 | 734,682 | 678,778 | 54,968 | 936 |
| random / validation | 27 | 93,425 | 87,501 | 5,924 | 0 |
| random / test | 28 | 94,292 | 91,879 | 2,413 | 0 |
| geographic / train | 224 | 771,926 | 723,755 | 47,243 | 928 |
| geographic / validation | 16 | 37,638 | 27,907 | 9,723 | 8 |
| geographic / test | 32 | 112,835 | 106,496 | 6,339 | 0 |

Neither fixed test partition has a High pixel. Geographic validation has only eight High pixels, from correlated interpolated references. This cannot support an honest high-risk recall estimate. We did not change the seed, swap test groups or cherry-pick a high-risk test patch after observing this problem.

The current data are sufficient to validate loaders, losses, optimizer execution and leakage diagnostics. They are insufficient for the requested final three-class regional-generalization conclusion. This is not a claim that all 24,518 patches lack high-risk evaluation examples: the full reference distribution was not downloaded.

Next, index the remaining regional archives under a separate budget, build connected components over the enlarged selected grid, and perform a reference-only pilot across more independent components. Measure class support by region, season and date before freezing a new experiment version. Do not use existing test *scores* to choose its membership. Favor diverse independent units and natural evaluation prevalence; do not force image-level balancing. The missing full-pool reference census should be explicit until reference members or an authoritative class manifest are examined.

At 102,656 bytes per observed pair, the current 24,518-pair pool would require 2,516,919,808 raw content bytes (about 2.344 GiB). Downloading that whole pool is not necessary for the present bounded milestone. The 272-pair pilot occupies 27,922,432 raw content bytes; runtime libraries and model checkpoints are additional storage.

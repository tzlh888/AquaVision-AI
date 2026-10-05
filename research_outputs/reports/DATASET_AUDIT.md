# Dataset audit — AquaVision AI Phase 1

Audit date: **2026-10-04, Europe/Budapest** (retrieval logs use UTC, which may show October 3).
Status: **access and decoding verified; cell-count labels, image targets and geographic footprints unresolved**.
No model training has occurred.

## Evidence and exact sources

1. **Dataset deposit:** Hänsch, Ronny; Schloer, Conrad (2024), *Dataset for Increasing the Spatial Resolution of Harmful Cyanobacterial Bloom Detection using Deep Learning and Sentinel-2 Satellite Imagery*.
   Version record [14230064](https://zenodo.org/records/14230064), [DOI 10.5281/zenodo.14230064](https://doi.org/10.5281/zenodo.14230064), [JSON API](https://zenodo.org/api/records/14230064).
   Published 2024-11-27; the catalog identifies concept record 14230063. Pin the version record, not a moving latest-version URL.
2. **Related paper:** Schloer and Hänsch, *Harmful Cyanobacterial Bloom Detection using Deep Learning and Sentinel-2 Imagery*, [DOI 10.1109/JSTARS.2025.3629586](https://doi.org/10.1109/JSTARS.2025.3629586).
   [DLR author manuscript](https://elib.dlr.de/219745/1/Harmful_Cyanobacterial_Bloom_Detection_using_Deep_Learning_and_Sentinel-2_Imagery.pdf), specifically methods on manuscript pp. 3-5 and dataset statistics on p. 5. The manuscript has a template header; the DOI and publication notice identify the article. This is an accepted author version, not an assumption that every line matches the final typeset article.
3. **Author code:** [cschloer/hab_detection_s2](https://github.com/cschloer/hab_detection_s2), pinned tree `e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37`.
   Key files: [download_and_process.py](https://github.com/cschloer/hab_detection_s2/blob/e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37/code/dataset/download_and_process.py), [generate_tiles.py](https://github.com/cschloer/hab_detection_s2/blob/e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37/code/dataset/generate_tiles.py), [create_dataset.py](https://github.com/cschloer/hab_detection_s2/blob/e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37/code/dataset/create_dataset.py), [helpers.py](https://github.com/cschloer/hab_detection_s2/blob/e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37/code/dataset/helpers.py).
4. **Product authority:** [NASA/OB.DAAC CyAN documentation](https://oceancolor.gsfc.nasa.gov/about/projects/cyan/), especially the DN guide and data-product description. The web search reader returned 403, but a normal verified-TLS HTTP fetch succeeded; the exact HTML is retained.
5. **Direct archive evidence:** `data/metadata/sample_manifest.json`, the two `*_members.csv` and `*_pairs.csv` inventories, and `research_outputs/tables/sample_*.{csv,json}`. These are local measurements, not statements taken from the paper.

Supporting files have URL, size and SHA-256 records in `data/metadata/sources/sources_manifest.json`. Source code was read, not executed. The original host Python had a certificate-store error; curl and the isolated Python environment worked with TLS verification enabled. The pipeline also corrected gzip handling for the catalog response; byte-range responses require identity encoding.

## VERIFIED FACTS

Here, **observed** means measured from retrieved metadata/bytes; **documented** means confirmed that the primary source makes the statement, without claiming the entire archive has been independently validated.

| Property | Finding | Evidence and scope |
|---|---|---|
| Official source | Public Zenodo deposit linked from the authors' paper; API accessible without a token | Observed catalog and paper |
| Archive location/DOI | Version-specific record 14230064; DOI above | Observed catalog |
| Input container | ZIP members named `*_sen2.npy`; reference members named `*_cyan.npy` | Both indexed archives and eight decoded pairs |
| Input dimensions/dtype | `(12, 64, 64)`, `uint16`, channel-first | Observed in all eight pairs |
| Available bands | B01, B02, B03, B04, B05, B06, B07, B08, B8A, B09, B11, B12, in that order; no B10 | 12 channels observed; semantic order documented by the pinned `generate_all_bands` function and its sorted keys, not embedded in NPY headers |
| Input processing | Sentinel-2 Level-2A; bands first placed on a nominal 20 m grid; later reprojection/cropping | Documented in code and paper; sample NPY has no physical geotransform or scale |
| Spatial resolution | Original MSI bands have mixed nominal 10/20/60 m sampling; source CyAN nominally 300 m; both processed to nominal 20 m before patching | Source methods and NASA. Do **not** describe the upsampled reference as independent 20 m measurements. Final EPSG:4326 warp means exact ground sampling needs its transform |
| Label representation | `(1, 64, 64)`, `uint8`; processed native DN reference mask, not one label per patch | Observed decoding; original project performs segmentation |
| Reference product | Code builds daily `L<year><dayofyear>.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m_<tile>.tif` filenames, warps/interpolates and masks them | Pinned `helpers.py` and processing code; original GeoTIFFs/product version were not retrieved |
| Geographic metadata | Names retain CyAN tile ID, parent subtile X/Y and size, within-crop patch row/column and sequence | Observed inventory, supported by filename-generation code |
| Acquisition dates | Year/month/day in names; selected pairs cover 2019 and 2020 | Observed; no time-of-day fields or complete original scene identifiers in NPY |
| Sample IDs | Full filename stem before `_sen2.npy`/`_cyan.npy`; pairs matched on that stem, not ZIP order | Both inventories, no unpaired or unrecognized file members |
| Coordinates/water-body IDs | Absent from sample arrays and two archive inventories. Parent-grid candidates are available; no verified latitude/longitude, CRS, geotransform, lake ID or watershed ID | Observed. No map or invented location names produced |
| Total archive byte size | Six files, **23,402,209,757 bytes** (23.402 decimal GB; 21.795 GiB) | Sum of API file sizes; whole ZIPs not downloaded |
| Sample counts | Two inventories contain **6,343** and **18,175** paired samples. **Eight** pairs downloaded. Full corpus count is not independently verified | Direct ZIP-directory inspection |
| Published corpus count | Paper reports 938,607 pairs and approximately 1.86 billion usable pixels, with 776,864 training and 161,743 test pairs | Paper statement only; not local measured counts and not a verified match to every deposit member |
| Licensing | Dataset CC BY 4.0/open access; author code Apache 2.0; retrieved manuscript CC BY 4.0 | Catalog, author LICENSE, manuscript footer; retain attribution and identify derived outputs |

### Archive inventory

| File | Catalog bytes | Phase 1 action |
|---|---:|---|
| dataset_train_6_2.zip | 307,193,636 | Remote index + four pairs |
| dataset_train_6_5.zip | 8,394,962,314 | Catalog metadata only |
| dataset_train_7_2.zip | 861,960,775 | Remote index + four pairs |
| dataset_train_7_5.zip | 2,297,938,292 | Catalog metadata only |
| dataset_train_8_3.zip | 4,739,267,422 | Catalog metadata only |
| dataset_test.zip | 6,800,887,318 | Catalog metadata only; no test imagery inspected |

The selected files are the two smallest training archives. This is an access-cost decision, **not** a scientifically sufficient selection of research regions. No full ZIP was downloaded. Verified HTTP 206 responses and `Content-Range` allow directory/member retrieval; the successful sample run reserved/read **6,841,460 bytes** of ZIP responses plus a 5,586-byte catalog. Exploratory probes before that run are recorded separately in Phase 1 status.

Members pass ZIP CRC32 verification and receive local SHA-256 hashes. Catalog MD5 values are recorded but **not verified for the complete archives**. ZIP central directories support date/region/grid filtering; they contain no label histograms, cell densities, cloud quality metrics or geographic footprints. Label-aware screening would require selected reference-member reads later.

### What the reference values mean

NASA's original-product DN guide distinguishes 0 (below detection), 1-253 (data), 254 (land), and 255 (no data, including cloud). Zero must not be interpreted as proven zero cells/mL. The author pipeline remaps/masks land and cloud into 255; postprocessed 255 does not identify the missingness cause.

The retrieved NASA page gives a **DN-to-CIcyano** equation:

`CIcyano = 10 ** (DN * 0.011714 - 4.1870866)`.

This is a documented original-product index formula, **not an implemented cells/mL conversion for this archive**. It does not establish the provenance/version of the daily GeoTIFFs used for the deposit, recover removed flags, or undo bilinear interpolation and integer storage. A separately justified abundance calibration and a clear treatment of below-detection/saturation are also needed. Bilinear interpolation in a logarithmically encoded DN space is not equivalent to interpolation of cell density. Applying a published conversion to these processed pixels would therefore require an explicit approximation argument and sensitivity analysis, not a claim of exact recovered cell counts.

The paper uses pixel bins **0-99, 100-199, 200-253**. These are not automatically equivalent to the requested **<20,000 / 20,000-100,000 / >100,000 cells/mL** thresholds. Phase 1 only reports those native bins, clearly named `Paper DN bin ...`; it does not assign Low/Moderate/High image-level risk. Flags and invalid values receive no bin. Raw values and their units are preserved. The conversion entry point deliberately fails closed.

### Conflicting primary-source evidence

1. **Input/label reversal in deposit description.** The Zenodo text describes CyAN patches as features and Sentinel-2 as labels. The paper, saving code, twelve-band arrays and one-channel reference masks support Sentinel-2 as input and CyAN as reference. Treat the deposit prose as a documentation conflict; do not reverse the model's scientific task.
2. **5% versus 95% missing pixels.** Manuscript p. 5 says patches with more than 5% no-data pixels are discarded. Released code instead checks `count(cyan == 255) / 64**2 >= 0.95`, with a narrow fallback condition. Three observed patches exceed 5% masked pixels; one contains **3,708/4,096 = 90.53%** masked pixels. The sample directly rules out applying a universal “at least 95% valid reference” claim to these downloaded files. A future usable-area threshold must be explicitly chosen and sensitivity-tested.
3. **Cloud/land masking differences.** Manuscript equations and released code differ in cloud-index numerator, AND/OR logic and threshold formulation. In code `get_land_filter`, the variable named `band_11` uses channel index 11, which the published channel order identifies as B12. These are audit observations, not a claim about the authors' intent or proof of the exact archive-generation version. We do not silently correct or regenerate the reference masks.
4. **Channel wording.** The abstract mentions influence across 11 bands, whereas the method uses 12 channels and the downloaded arrays have 12. The band list comes from the actual saving code and channel count, not the abstract's wording. Physical band identity remains a provenance assertion until checked against original products.

## ASSUMPTIONS

These are explicit working assumptions, not verified experimental facts:

- The released code approximates how the deposit was created. A generation commit/version is not embedded in NPY files, so code inspection is not proof that every operation was used for every file.
- Filename dates are intended acquisition dates; the saving code supports this, but original product metadata was not retrieved.
- Matching parent-group identifiers identify recurring broad locations. Matching patch offsets across dates are only *candidates* for the same footprint; reprojection can change pixel alignment.
- The requested later research subset could fit a personal computer. Capacity estimates below are arithmetic scenarios, not counts of screened usable samples.

## UNRESOLVED QUESTIONS

| Question | Why it matters | Evidence needed before advancing |
|---|---|---|
| Can exact 20k/100k cells/mL categories be defended for the processed DN? | Defines the scientific target | Original CyAN product version, calibration source, encoding/flag treatment, interpolation audit; otherwise document that those thresholds are unsupported and select an explicitly different reference target only after resolving scope |
| What is the patch-level target? | Source labels are pixel masks; max, majority or valid-water percentile imply different tasks | Preregister aggregation, valid-area minimum, heterogeneous-patch handling, uncertain/near-boundary handling and threshold sensitivity before modeling |
| Where are the true footprints and water bodies? | Filename groups alone cannot validate unseen lakes, basin separation or distances | Author-generated `data.json` (referenced but not in the indexed public code tree), or reproducible reconstruction from original GeoTIFF CRS/transforms and scene metadata; validate against authoritative hydrography |
| Do adjacent regions/subtiles share water bodies or input scenes? | Could leak geography despite different IDs | Cross-tile adjacency, original Sentinel product IDs, water-body intersection and spatial buffer checks |
| Does the deposit match the complete published sample count? | Prevents conflating paper corpus with the downloadable version | Bounded indexing of the remaining four archives in a later phase, with duplicate and pairing checks |
| Which mask behavior generated these arrays? | Controls usable area and potential spurious image cues | Reconcile source versions and data observations; retain and report existing masks meanwhile |
| What is the physical scaling of stored S2 DN and its nodata treatment? | Required for interpretable reflectance features and physically scaled perturbations | Original Level-2A processing baseline, quantification values/offsets and nodata metadata; no blind division by 10,000 |
| Are all three intended classes sufficiently represented across independent groups and seasons? | Necessary for geographic validation and calibration | Label-aware metadata screening after target definition; eight access probes cannot answer it |
| What are the intraday time differences? | Daily matching does not establish simultaneous observations | Actual Sentinel-2/Sentinel-3 sensing timestamps and CyAN compositing provenance |

## Decision

**Proceed with reproducible access/inspection infrastructure; stop label conversion, subset finalization and training at these gates.**
The dataset itself is accessible. The blockers are scientific provenance and task-definition questions, not download permission. No metric, geographic region name, usable sample count, or conversion has been invented.

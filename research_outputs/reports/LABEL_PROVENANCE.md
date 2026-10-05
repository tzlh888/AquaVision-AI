# Label provenance — Phase 2

Date: 2026-10-04 (Europe/Budapest). **The stored reference is processed CyAN DN, not cell density.**
Evidence categories: VERIFIED = directly observed in files or explicitly present in cited primary source; LIKELY = plausible correspondence not proven for this deposit; UNKNOWN = required evidence unavailable; CONFLICTING = sources disagree. Verified code describes the released implementation, not proof of the binary-generation environment.

## Sources inspected

- [Dataset version 14230064](https://doi.org/10.5281/zenodo.14230064); cached catalog and member inventories.
- [Author manuscript](https://elib.dlr.de/219745/1/Harmful_Cyanobacterial_Bloom_Detection_using_Deep_Learning_and_Sentinel-2_Imagery.pdf), methods pp. 3-5; [paper DOI](https://doi.org/10.1109/JSTARS.2025.3629586).
- [Released processing code](https://github.com/cschloer/hab_detection_s2/blob/e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37/code/dataset/download_and_process.py), especially `warp_and_crop`, `get_cloud_filter`, `get_land_filter`, `apply_cloud_and_land_filter`, `save_data`.
- [Region generation](https://github.com/cschloer/hab_detection_s2/blob/e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37/code/dataset/generate_tiles.py), [scene enumeration](https://github.com/cschloer/hab_detection_s2/blob/e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37/code/dataset/create_dataset.py), [daily CyAN URL construction](https://github.com/cschloer/hab_detection_s2/blob/e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37/code/dataset/helpers.py).
- [NASA CyAN product DN guide](https://oceancolor.gsfc.nasa.gov/about/projects/cyan/), cached in Phase 1.
- Prior commit `66ea8048f94b5af9589f92e92e9e81194628b16b` contained [hab_detection.zip](https://github.com/cschloer/hab_detection_s2/blob/66ea8048f94b5af9589f92e92e9e81194628b16b/code/hab_detection.zip). Its 36-entry directory and small source members were read using **26,682 bytes** of ranges, not a full 103,541,869-byte ZIP. The archived processing file is byte-identical to the current version. Neither its index nor the current public tree contains the generated `data.json`; no code in it was executed.
- Crossref metadata exposed no related supplement link. IEEE's page returned a browser-verification interstitial. **No accessible supplement was located; this is not proof that no supplement exists.** See `phase2_sources/crossref_paper`, `author_commits`, `previous_tree.json`, and access manifests.

## Supported chain

```text
Original daily CyAN CI_cyano GeoTIFF (encoded DN, not cells/mL)
  -- helpers.get_cyan_url / NASA product guide -->
Reproject to EPSG:4326, remap land 254 toward nodata 255
  -- warp_and_crop gdalwarp arguments -->
Bilinear resampling of reference to resolution from warped Sentinel-2
  -- -tr abs(xres), abs(yres), -r bilinear, -tap, -srcnodata 255 -->
Crop both rasters to the same supplied geographic window
  -- gdal_translate -projwin window, same date from product lookup -->
Apply additional Sentinel-2-derived land and cloud filters to CyAN mask
  -- get_*_filter / apply_cloud_and_land_filter -->
Cut paired 64x64 arrays with stride 64 and missing-area selection
  -- patch loop and save_data -->
Stored *_cyan.npy: one uint8 channel; *_sen2.npy: twelve uint16 channels
  -- ZIP CRC32, SHA-256 and direct NPY inspection -->
AquaVision: unchanged stored references plus flag/bin diagnostics
  -- labels.inspect_reference / aggregate_native_reference -->
Native pixel-bin fractions and alternative aggregation diagnostics
  -- NO SUPPORTED ARROW YET -->
Physical abundance / final Low–Moderate–High image risk label
```

Every implemented arrow above points to an inspected source or measured local operation. No arrow to cell density or a final image label is implied. The entire historical product-to-deposit chain is **LIKELY**, with individual code steps **VERIFIED as code**, because the exact generation commit, raster headers and GDAL versions were not saved with the samples.

## Transformation ledger

| Stage | Representation, units and operation | Evidence status |
|---|---|---|
| Raw variable | Filename variable `CI_cyano`, Level-3 mapped daily CyAN product, nominal 300 m. Raster DN encodes an index; it is not a numeric cells/mL field | VERIFIED in NASA guide and URL-generating code; original sample-date raster headers UNKNOWN |
| Raw flags | NASA: DN 0 below detection; 1-253 data; 254 land; 255 no data, e.g. cloud. Zero does not establish zero abundance | VERIFIED documentation; distinct original masks lost in stored samples |
| Scaling | Current NASA DN-to-index coefficients 0.011714 and -4.1870866; alternate historical coefficients documented in literature. No cells/mL conversion appears in released dataset generation | VERIFIED source statements; version applicable to deposit UNKNOWN |
| Reprojection | S2 warped to EPSG:4326; CyAN reprojected to that CRS. The initial warps do not explicitly set a resampler in code | VERIFIED code; effective library defaults/version UNKNOWN |
| Flag remapping | First CyAN warp requests source 254 and destination 255; argument strings include quote characters. Effective original command behavior cannot be independently replayed from NPY | VERIFIED code; exact historical output behavior UNKNOWN |
| Resampling | Second CyAN warp explicitly uses bilinear interpolation with pixel size taken from the reprojected S2 transform and target alignment | VERIFIED code and broadly consistent paper description; continuous DN interpolation precedes integer NPY storage |
| Clipping/rounding | No explicit numeric DN clipping or float-to-byte conversion in saving code; byte-valued source/GDAL processing is a likely route to integer values. Exact rounding/clipping at resampling is not proven | UNKNOWN effective GDAL behavior; observed output uint8 VERIFIED |
| Spatial pairing | Both rasters cropped using same `window`, then identical array-index slices. Original transforms and window JSON are not in NPY | VERIFIED code, LIKELY same intended footprint; exact alignment UNKNOWN |
| Temporal pairing | Sentinel product `beginposition` contributes date; the daily CyAN URL uses that calendar day. Collection window in code is 2019-2020 | VERIFIED code and filenames; intraday mismatch/compositing details UNKNOWN |
| Masking | Additional S2-derived cloud/land filters write 255 into reference; no separate water/cloud/land layers are stored | VERIFIED code and observed masks; mask accuracy UNKNOWN |
| Patch extraction | 64x64, stride 64, saved together. Input imagery is retained, including surrounding land; filtering is applied to references | VERIFIED code and eight decoded pairs |
| Patch eligibility | Code excludes at least 95% flag-255 patches, subject to a fallback; manuscript says more than 5% missing. Measured sample includes 90.53% missing | CONFLICTING source descriptions; direct archive counterexample VERIFIED |
| Final stored reference | uint8 shape (1,64,64), no CRS, geotransform, units attribute, quality-mask layers, lake ID or original scene UUID | VERIFIED NPY headers and arrays |
| Native classes | Paper pixel bins 0-99 / 100-199 / 200-253; flags excluded. These are diagnostic bins here, not health categories | VERIFIED paper; cells/mL equivalence unsupported |
| Image aggregation | Source model predicts per-pixel segmentation, not one label per patch | VERIFIED manuscript; no original image-class aggregation rule exists in inspected implementation |

## Conflicting or missing evidence with practical consequences

1. Deposit text reverses features and labels; array dimensionality, paper and saving code resolve the intended direction to S2 input → CyAN reference.
2. The 5%/95% missingness conflict is not repaired silently. Coverage sensitivity is measured separately; valid reference fraction is **not valid water-area fraction**, since 255 combines land and other exclusions.
3. Manuscript cloud equations differ from code in numerator, logical operator and threshold definition. Code's land-filter variable `band_11` indexes channel 11 (B12 under its own band order). We preserve observed masks and document uncertainty.
4. `sen2_uuid` is passed to `save_data` but is never written into the filename or arrays. Reconstructing exact S2 tile/MGRS, sensing timestamp and warped resolution from a date and region alone is not unique.
5. Attempts to retrieve two original CyAN rasters ended in Earthdata authentication HTML with HTTP 200. They are **not successfully downloaded GeoTIFFs**. NASA tile-shapefile URLs returned 403. Authenticated source access or author metadata is needed; no access controls were bypassed.

## Decision

The source label is understood at the **stored DN and released-code level**. The product-version-specific physical interpretation and exact patch footprint remain unresolved. Preserve the raw references and continue to block physical conversion and final image-risk classes. See CELLS_PER_ML_VALIDATION.md and IMAGE_LABEL_DEFINITION.md.

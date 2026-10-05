# Original pipeline reconstruction and scientific corrections

Re-read on 2026-10-04 before implementation. Primary sources: [author manuscript, §§III–IV](https://elib.dlr.de/219745/1/Harmful_Cyanobacterial_Bloom_Detection_using_Deep_Learning_and_Sentinel-2_Imagery.pdf), [published DOI](https://doi.org/10.1109/JSTARS.2025.3629586), [author code pinned at e24e311](https://github.com/cschloer/hab_detection_s2/tree/e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37), and [Zenodo version 14230064](https://zenodo.org/records/14230064). Existing source snapshots and their hashes are retained. The public GitHub page still lists three commits. Online PDF retrieval exceeded the browser's size limit; the previously downloaded full primary manuscript and extracted text were re-read. The cached version-specific Zenodo catalog and complete two-archive inventories were inspected; the browser could not open the landing page.

## Corrections to Phase 2 framing

1. **The primary task is semantic segmentation.** Each multispectral input is `12×64×64`; its target is an `int64` `64×64` map. No image aggregation is required for learning.
2. **Published DN classes are sufficient target definitions.** They are called Low, Moderate and High risk by the source, but represent categories of a processed remote-sensing reference, not measured cell concentration or toxin risk. Physical cells/mL interpretation remains optional and disabled.
3. **A fixed author-grid ID is sufficient for region holdout.** CyAN tile plus parent X/Y/S identifies a selected fixed source window. Coordinates and lake identities are not mandatory for replicating this region-based evaluation. They remain necessary for a stronger claim of verified unseen *water bodies*.
4. **Adjacency components are verified for the selected author grid.** The earlier candidate graph can be used with this narrower interpretation. It is not a basin/lake graph and cannot establish cross-tile nonoverlap.
5. **Author splitting is probabilistic by component, not a guaranteed sample ratio.** On the current four components, the exact seed-42 70/30 rule yields all train. AquaVision uses a declared three-way extension; it does not claim to recover the publication's original partition.

## Pipeline evidence ledger

| Property | Status | Evidence and implementation consequence |
|---|---|---|
| Pixel segmentation task | BOTH | Paper §III-B, inference `functions.py` uses three-channel DeepLab logits and spatial argmax. |
| DN 0–99, 100–199, 200–253 classes | VERIFIED IN PAPER | §III-B exact intervals. Inference visualization cutoffs `[100,200,254]` are consistent, but released code does not include training target generation. |
| DN 0 | BOTH | Paper includes 0 in Low; selection code counts it as no bloom occurrence, not as a training ignore class. Retain class 0. |
| DN 254 land | BOTH | Paper §III-A and `generate_tiles.py` exclude land in selection; processing attempts remap 254→255. Residual 254 is explicitly ignored by AquaVision. |
| DN 255 and added cloud/land masks | BOTH | Paper excludes masked pixels; `apply_cloud_and_land_filter` writes 255. No attempt to reconstruct lost mask causes. |
| Original training ignore index | UNRESOLVED | Training loop/target transform is absent from public tree and inspected historical ZIP. AquaVision chooses **-100** explicitly, matching PyTorch cross-entropy ignore convention. Invalid/nonfinite/noninteger/out-of-range references also map to -100. |
| Patch shape and stride | BOTH | Paper 64×64, stride 64. `download_and_process(...subset_resolution=64,subset_stride=64)`. No overlap within a given crop/date grid. Repeated acquisitions are a separate issue. |
| Patch loop endpoint | VERIFIED IN CODE | `range(0, dimension-64, 64)` omits the last exact-fit start; not silently changed in the archive. |
| No-data exclusion | UNRESOLVED | Paper says >5% no data; code skips ≥95% flag-255 with a last-patch fallback. Existing 90.53%-masked patch contradicts the paper description. Pilot retains provided patches, ignores masked pixels, and reports support rather than asserting a 95%-valid filter. |
| Sentinel band count/order | BOTH | Twelve L2A channels, no B10: B01,B02,B03,B04,B05,B06,B07,B08,B8A,B09,B11,B12. Verified arrays and `generate_all_bands` sorted keys. |
| Sentinel nominal resolution | BOTH | Code VRT `-tr 20 20`, paper 20 m. Later EPSG:4326 reprojection means exact final metric pixel dimensions cannot be asserted from bare NPY files. |
| Sentinel resampler | VERIFIED IN PAPER | Paper and `run_model.py` documentation say nearest neighbor; VRT creation does not explicitly pass a resampler. Exact historical GDAL environment is unavailable. |
| CyAN resampler | BOTH | Nominal 300 m source; paper bilinear and `warp_and_crop` explicitly `-r bilinear` to warped S2 resolution. Interpolation does not create independent 20 m ground truth. |
| Crop/date pairing | BOTH | Same geographic window then identical patch slices; daily CyAN lookup uses Sentinel calendar day. Different acquisition times remain possible. |
| Input scaling | VERIFIED IN CODE | `functions.handle_input_transform`: float32 /10000 then per-band mean/std normalization. Training-statistic provenance for author's constants is not supplied. AquaVision fits its own statistics from training inputs only. |
| Selected subtiles | BOTH | 2,000×2,000 CyAN grid, parent cells 50×50 (paper nominal 15×15 km); reject >90% land, select summer bloom-rich regions. Code rounds mean occurrence percent then retains ≥10; paper says >10%, a boundary discrepancy. |
| Fixed parent identifier | VERIFIED IN CODE | `get_scene_id`: `{tile}_X{column:04d}_Y{row:04d}_S{size:03d}`; `ds.xy` establishes window saved in `data.json`. Same ID carries that window across dates. Names preserve this ID. |
| Patch crop offsets | VERIFIED IN CODE | Lowercase `x` is array row and `y` is array column; these differ from parent X/Y convention. Patch offset can be used as a footprint candidate, not proof of exact repeated geotransform. |
| Sentinel product UUID | VERIFIED IN CODE | Present in generation call but unused by `save_data`; not recoverable uniquely from stored names. Date/subtile is not a scene ID. |
| Geographic adjacency | BOTH | Same CyAN tile and absolute X/Y separations ≤S, including diagonals; recursive transitive closure among selected parents. All dates inherit parent designation. |
| Original seed and ratio | VERIFIED IN CODE | `random.seed(42)`, sorted parent traversal, draw train iff random ≤0.7 for each unassigned component. Paper describes 70/30 intent and reports a realized roughly 80/20. |
| Deep model | BOTH | DeepLabV3, ResNet18, 12 input bands, 3 classes, random initialization. Exact constructor released in `functions.load_model`. |
| Loss weighting | VERIFIED IN PAPER | Cross entropy weighted by raw-DN frequency ratio D(0)/D(v), not ordinary inverse three-class frequency. Training implementation not released. AquaVision starts unweighted; alternatives are separate future ablations. |

## Scope of reproduction

`geographic_split.author_partition` implements the same component coin toss without recursion limits. Sorted component anchors reproduce the source traversal's random draw order. All selected parents from the relevant inventory must be included before sampling. The original 183-parent selection and generated designations are unavailable here; current archives are explicitly named **dataset_train**. Re-splitting this pool is a new experiment, not a recreation of the original published test set.

`geographic_split.experiment_partitions` shuffles sorted components once with seed 42, reserves the last for test and penultimate for validation, and puts the rest in training. This is a deliberate three-way extension to guarantee evaluable partitions; no risk labels or scores affect allocation. The independent random patch comparator uses 80/10/10 on the same pilot pool. Frozen JSON records source index hashes, all assignments and configuration before downloading pilot labels.

Cells/mL and image-aggregation reports remain intact as historical audits. Their old mandatory-gate interpretation is superseded for this explicitly authorized segmentation task.

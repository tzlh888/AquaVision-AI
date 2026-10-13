# AquaVision AI — Final Scientific Report

## Research question

Can Sentinel-2 multispectral imagery identify NASA CyAN-derived Low, Moderate, and High bloom-proxy classes at geographically unseen waterbodies, and what evidence is required before that claim is scientifically defensible?

CyAN is a remote-sensing proxy. It is not an in-situ toxin measurement, laboratory truth, or operational health-warning label.

## Historical v2 data and provenance

The historical source dataset is Zenodo record 14230064, licensed CC BY 4.0 and associated with Schloer and Hänsch. Each modelling pair contains a 12 × 64 × 64 Sentinel-2 array and a 64 × 64 processed CyAN mask. Stored CyAN digital numbers 0–99, 100–199, and 200–253 map to Low, Moderate, and High; 254/255 and invalid values are ignored.

The research-upgrade audit exactly recovered and hash-verified all 288 historical Sentinel arrays and all 288 historical CyAN arrays. It also verified the frozen v2 membership: 96 training, 48 validation, and 144 test pairs. However, the public historical artifacts do not retain the Sentinel product UUID, source CRS and affine transform, actual patch footprint, true waterbody identity, or confirmed historical CyAN processing version. Consequently:

- historical author-grid components are not verified waterbodies;
- cross-split physical overlap and shared bloom events cannot be ruled out;
- High pixels and patches cannot be interpreted as independent geographic units;
- historical v2 results remain legacy, exploratory model evidence rather than confirmed geographic generalization.

## Historical modelling result

The v2 pipeline evaluated spectral indices, Logistic Regression, Random Forest, SmallSegCNN, and DeepLabV3/ResNet18 with twelve input channels and random initialization. The registered selection rule chose NDCI by validation Macro F1, although validation High F1 was 0. The selected NDCI test Macro F1 was 0.5185 and High F1 was 0.0006. Logistic Regression showed a post hoc test High F1 of 0.5803 but was not validation-selected and cannot replace the frozen winner. No CNN passed the fixed class guard; weighted DeepLab remained diagnostic.

These saved metrics are technically reproducible under the historical split. They do not demonstrate reliable cross-waterbody three-class generalization because geographic identity and independent High support were not established. The v2 test set was also deliberately High-enriched, so its precision and calibration do not estimate natural-population behavior.

## Prospective v3 evidence recovery

The upgrade therefore shifted from model optimization to identity-first data engineering.

### Final bounded label-integration pilot

Six pre-frozen Sentinel candidate scenes across Lake Okeechobee, Utah Lake, and Upper Klamath Lake were matched to six official NASA Ocean Color CyAN daily GeoTIFFs. All six source files were acquired and verified with:

- exact product ID and source URL;
- embedded `OBPG_version=6.0`;
- acquisition/composite date;
- CRS, affine grid, native resolution, encoding, and no-data rules;
- SHA-256 of the raw source and derived 64 × 64 label artifact;
- same-date temporal matching and spatial footprint intersection.

Discrete production labels use nearest-neighbor source-DN sampling followed by the frozen class mapping. Bilinear interpolation is retained only as a diagnostic on continuous DN values before classification; it is not used to interpolate already discrete classes.

The pilot integrated 6/6 scenes and found High support in two of three waterbody groups. It contained three High scenes/patches and 48 distinct native High pixels, but **zero qualified independent High units** under the frozen requirements. The result was **PILOT SUCCESS** for engineering feasibility, not model readiness.

### Bounded Phase 3A-3 expansion

Twelve additional candidate waterbodies were frozen before label screening. Five obtained authoritative identity and geometry and were screened against the six preserved CyAN V6 products: Lakes Erie, Champlain, Winnebago, Pontchartrain, and Pyramid. Seven bounded official-service attempts ended in timeout or HTTP 502 conditions. Three screened candidates contained at least one native High pixel; only Lake Winnebago showed strong multi-date label-side potential.

No new Sentinel payload or patch set was acquired because the candidate arithmetic had already failed: five verified new candidates plus the original three waterbodies could supply at most eight units, below the nine independent units required for minimum 3/3/3 training, validation, and confirmation partitions. No candidate therefore became a complete v3 sample unit.

## Native-pixel and independence analysis

CyAN’s native grid is approximately 300 m while a Sentinel patch is 64 × 64 at 20 m. Resampling a native label to many 20 m pixels does not create new evidence. A Sentinel patch intersects roughly 19 native CyAN cell centers, so the frozen requirement of at least 100 distinct native High pixels normally needs about six low-overlap patches, even though a separate minimum says three patches. The 100-pixel gate corresponds to roughly 9 km² of dated High proxy support. It is feasible for large blooms but systematically favors large lakes and broad events.

The project counts independent units conservatively by real waterbody, with scene, time/event, footprint, and native-cell relationships retained. The same waterbody cannot cross splits. Same-scene crops, repeated native cells, or nearby dates are not promoted to independent units. Historical v2 overlap remains unknown, so the only defensible future path would be v3-only.

## Results and final gates

| Evidence item | Verified result |
| --- | ---: |
| Historical Sentinel arrays recovered | 288/288 |
| Historical CyAN arrays recovered | 288/288 |
| Historical patches with confirmed real geography | 0/288 |
| Frozen CyAN V6 products acquired and version-confirmed | 6/6 |
| Pilot Sentinel/CyAN scenes aligned | 6/6 |
| Pilot waterbody groups with any High | 2/3 |
| Pilot distinct native High pixels | 48 |
| Qualified independent High units | 0 |
| Training / validation / confirmation units | 0 / 0 / 0 |
| Confirmation set sealed | No |

Phase 3B was not started. The final research status is **LIMITED**; Phase 3A-3 readiness is **NOT READY**.

## Error, uncertainty, and limitations

The central uncertainty is not a missing pixel-level confidence interval. It is the absence of verified independent High units. Thousands of pixels cannot compensate for unknown or shared waterbody, scene, footprint, and event identities. Only three historical test components and one validation component were used, and those components are not confirmed lakes.

The six-scene v3 pilot proves technical compatibility for a bounded set of products. It does not establish representative availability, natural class prevalence, label validity at 20 m, or model generalization. CyAN missingness varies by scene and waterbody; High-enriched screening biases the sample distribution and must never be presented as ecological prevalence. No field measurements validate biological concentration or toxins.

## Reproducibility

The repository retains historical split membership, recovered-artifact manifests, exact hashes, label rules, metadata catalogs, frozen screening protocols, source code, and synthetic/real integration tests. At closeout, 60 upgrade tests passed: 10 Phase 3A, 11 Phase 3A-1, 11 Phase 3A-2, 15 Final Label Pilot, and 13 Phase 3A-3 tests.

Final release preparation added a root-level upgrade-test runner and installed `requirements-training.txt` in a clean Python 3.12.14 environment. The five upgrade suites passed **60/60**. The public historical suite completed as **122 passed / 1 skipped / 0 failed**: the skipped complete-frozen-environment condition reports 12 unavailable ignored model/checkpoint artifacts and 3 packaging records regenerated by editable installation. Every present non-generated registered research artifact remains hash-checked. The historical complete-artifact record of 123 passing tests was therefore not reproduced in full and must not be reported as a fresh 123/123 run.

## Final scientific conclusion

AquaVision produced two valid outcomes. First, it recovered historical artifacts and showed why their geographic evidence is insufficient for a strong generalization claim. Second, it demonstrated a reproducible official-data pipeline linking a Sentinel patch to a named waterbody, scene, footprint, date, CyAN V6 product, native cells, and derived label.

It did **not** produce an independently partitionable v3 dataset or a qualified High unit. Therefore no reliable three-class cross-geographic model claim is supported, and the engineering pilot must not be described as a classification breakthrough. Under the exhausted bounded protocol, further open-ended expansion has low marginal value. The scientifically honest closeout is **LIMITED**, with model training stopped.

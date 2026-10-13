# Label Integration Report

## Result

Six of six frozen Sentinel candidates now have a traceable NASA CyAN V6 label source and a deterministic 64×64 alignment artifact. Three scenes contain High support, distributed across two waterbody groups. Nevertheless, **zero waterbodies pass the frozen independent High-unit gate** because each group remains below 3 High patches and 100 native High pixels.

## Label definition

The downloaded GeoTIFF stores an 8-bit palette index, not RGB values. The palette changes display only; the underlying index is the label proxy.

| Source value | NASA meaning | Frozen research class |
|---:|---|---|
| 0 | below CIcyano detection threshold | Low |
| 1–99 | valid CIcyano code | Low |
| 100–199 | valid CIcyano code | Moderate |
| 200–253 | valid CIcyano code | High |
| 254 | land | Invalid/excluded |
| 255 | no data, including cloud/ice | Invalid/excluded |

The v3 integer mapping is therefore compatible with the frozen v2 bins and was not changed retrospectively. It remains an ordinal satellite-derived proxy; the three classes are not direct cell-count or field-water-quality measurements. The Low class combines NASA's code 0 with codes 1–99, which must be disclosed in any interpretation.

For diagnostic interpolation only, the equivalent continuous boundaries are `[0,100)`, `[100,200)`, and `[200,253]`. This closes the otherwise undefined intervals between integer codes without changing any integer label.

## Primary support rule

Independent support counts use native 300 m CyAN cells whose **cell centers** fall inside the verified Sentinel patch polygon. Each 1.28 km Sentinel patch contains 19 such centers. The 64×64, 20 m nearest-neighbor label grid is a co-registered training artifact; its 4,096 values are repeated representations of coarse source cells and are never counted as 4,096 independent observations.

| Candidate | Native valid | Low | Moderate | High | Nearest 20 m Low/Moderate/High | Bilinear-vs-nearest class disagreement |
|---|---:|---:|---:|---:|---|---:|
| Okeechobee 2025-07 | 19 | 2 | 17 | 0 | 428 / 3,668 / 0 | 197 / 4,096 |
| Okeechobee 2025-09 | 19 | 19 | 0 | 0 | 4,096 / 0 / 0 | 0 / 4,096 |
| Utah Lake 2025-07 | 19 | 0 | 19 | 0 | 0 / 4,096 / 0 | 0 / 4,096 |
| Utah Lake 2025-09 | 19 | 0 | 0 | 19 | 0 / 0 / 4,096 | 0 / 4,096 |
| Upper Klamath 2025-07 | 19 | 0 | 9 | 10 | 0 / 2,003 / 2,093 | 299 / 4,096 |
| Upper Klamath 2025-09 | 19 | 0 | 0 | 19 | 0 / 0 / 4,096 | 0 / 4,096 |

All six nearest-neighbor patches have 100% valid coverage; no selected native-center cell is land or no-data. This local result does not imply that future lakes or dates will have full coverage.

## Resampling finding

The released label artifact uses nearest-neighbor sampling of the source DN followed by class mapping. It never applies bilinear interpolation to categorical labels.

A diagnostic alternative interpolated only four-neighbor valid DN codes and then applied the bins. It disagreed with nearest-neighbor classification at 197 target pixels for Okeechobee July (4.81%) and 299 for Upper Klamath July (7.30%), with zero disagreement in the other four scenes. Because the DN is a processed proxy and the 20 m grid does not create new 300 m evidence, bilinear output is retained only for sensitivity analysis and cannot determine qualification.

## High-support audit

| Independent waterbody group | Dates | Span | High scenes/patches | Native High pixels | ±10 m alignment sensitivity | Any High | Qualified High unit |
|---|---:|---:|---:|---:|---:|---|---|
| Lake Okeechobee | 2 | 53 days | 0 | 0 | 0 | No | No |
| Utah Lake | 2 | 62 days | 1 | 19 | 18–19 | Yes | No |
| Upper Klamath Lake | 2 | 73 days | 2 | 29 | 29–30 | Yes | No |

The waterbody qualification rule remains: at least 2 dates separated by at least 30 days, at least 3 High patches, and at least 100 native High pixels. Utah and Upper Klamath meet the temporal condition but fail both High-support thresholds. High pixels, High patches, High scenes, High waterbodies, and qualified independent High units are all separately reported:

- Native High pixels: 48 under the primary alignment, across all scenes.
- High patches: 3.
- High scenes: 3, equal to High patches here because there is one patch per scene.
- Waterbodies containing any High: 2.
- Qualified independent High units: 0.

## Scientific interpretation

**Confirmed:** The bounded six-product pipeline can acquire, version, hash, geolocate, mask, and align genuine NASA CyAN data to the six frozen Sentinel patches.

**Confirmed:** High support exists in Utah Lake and Upper Klamath Lake under the unchanged mapping.

**Confirmed:** The current candidates remain insufficient for training, validation, or confirmation eligibility under the frozen gate.

**Exploratory:** Bilinear-versus-nearest disagreement shows that resampling choice can affect boundary labels. It does not show which interpolation is physically superior.

**Unresolved:** Generalization to other waterbodies, cloud conditions, seasons, bloom events, and field measurements remains untested. Legacy v2 spatial overlap also remains unknowable.

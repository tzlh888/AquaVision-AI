# V3 native CyAN pixel audit

## Result

The six previously verified OBPG CyAN V6 products were reused without a new CyAN download. Five of the 12 frozen new candidates obtained an authoritative USGS geometry and were screened on the native 300 m grid. Three contain at least one High native pixel on the six frozen dates: Lake Erie, Lake Champlain, and Lake Winnebago. Only Lake Winnebago has both abundant native High support and High observations separated by at least 30 days. No new Sentinel payload or patch was acquired because the successfully identified candidate universe, even combined with the three original pilot waterbodies, contains fewer than the nine independent waterbodies required for a 3/3/3 seal.

## Identity and counting rule

- Dated native identity: `(CyAN product ID, native row, native column)`.
- Repeated sampling of the same cell in the same product is counted once.
- A repeated location on another date is a separate dated observation but not a new spatial location; no 20 m resampled pixel is treated as a new 300 m observation.
- Discrete classes use nearest-neighbour semantics only. Frozen mapping is Low 0--99, Moderate 100--199, High 200--253, land 254, no-data 255.

## Scale compatibility

A 64 x 64 Sentinel patch at 20 m spans 1.28 km x 1.28 km (1.6384 km²). A 300 m CyAN cell spans 0.09 km². The theoretical area ratio is 18.2 cells per patch and the Final Label Pilot observed 19 native cell centres. Therefore three non-overlapping patches supply only about 55 area-equivalent cells (57 observed centres), below the separate 100-native-pixel requirement. At least six suitably positioned, low-overlap patches are normally necessary. The 100-pixel rule corresponds to roughly 9 km² of dated native label support. It is feasible for large lakes and spatially extended blooms, but systematically excludes small waterbodies and compact bloom footprints. The gate was not changed.

## Boundary sensitivity

Across the five newly screened official geometries and six dates, the aggregate native counts classified High would be 5,509 at a threshold of 199, 5,363 at the frozen threshold of 200, and 5,211 at a threshold of 201. This is a descriptive ±1 digital-number sensitivity check, not a threshold optimization. Candidate-level values are preserved in `V3_WATERBODY_CATALOG.csv`.

## Missingness and limitations

CyAN valid coverage varies sharply by product and waterbody; for example, some frozen dates have zero or very low valid support in a waterbody. Counts represent the CyAN proxy product, not in-situ hazard measurements. USGS rasterization is evaluated at native-cell centres in EPSG:5070. No model prediction contributed to candidate selection.

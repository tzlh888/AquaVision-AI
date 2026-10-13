# Geospatial Alignment Audit

## Source grids

Sentinel patches retain their scene-native WGS84 UTM grids: EPSG:32617 for Lake Okeechobee, EPSG:32612 for Utah Lake, and EPSG:32610 for Upper Klamath Lake. Each patch is 64×64 at 20 m with the original affine transform from the frozen catalog.

Every CyAN file has the same 300 m grid:

- shape: 26,328 columns × 15,138 rows;
- origin: x = −3,949,197.04668988 m, y = 3,791,526.2670775685 m;
- affine: `[300, 0, origin_x, 0, -300, origin_y]`;
- geographic datum GeoKey: NAD83 (`4269`);
- projection method: Albers Equal Area (`11`);
- standard parallels: 29.5° and 45.5°;
- latitude of origin: 23°; central meridian: −96°;
- metre units, zero false easting/northing.

These parameters are equivalent to EPSG:5070, although the TIFF records a user-defined projected CRS rather than embedding the EPSG:5070 authority code. The manifest retains the original GeoKey directory and projection doubles.

## Transformation and overlap

Patch corners and 20 m pixel centers are transformed by an explicit WGS84 UTM inverse followed by the embedded NAD83/CONUS-Albers forward equations. No spatial inference from image appearance is used.

| Patch group | Albers bounding box, metres | CyAN row range | CyAN column range | Native centers inside |
|---|---|---:|---:|---:|
| Okeechobee, both dates | [1512047.402, 552742.865, 1513520.572, 554202.610] | 10791–10795 | 18204–18208 | 19 |
| Utah Lake, both dates | [−1329757.715, 2020665.395, −1328301.783, 2022139.839] | 5898–5902 | 8732–8735 | 19 |
| Upper Klamath, both dates | [−2095017.955, 2441963.724, −2093434.713, 2443558.799] | 4493–4497 | 6181–6185 | 19 |

All patch polygons lie within the CyAN CONUS raster. The same physical patch is reused across the two dates for each waterbody, so the two dates remain one geographic group rather than independent waterbodies.

## Temporal alignment

The daily CyAN product year/day-of-year converts to the same calendar date as its paired Sentinel acquisition in all six records. Temporal mismatch is therefore 0 calendar days. The CyAN daily file does not provide a Sentinel-matched within-day timestamp; “same date” must not be restated as simultaneous acquisition.

## Alignment and mask rules

1. Primary evidence: native CyAN pixel centers inside the Sentinel polygon.
2. Training-grid label: nearest native DN at each Sentinel 20 m pixel center, then integer class mapping.
3. Invalid data: values 254 and 255 excluded; bilinear diagnostic is invalid if any of four neighbors is invalid.
4. Diagnostic only: bilinear interpolation of valid DN values before class mapping.
5. Qualification: native 300 m support only; resampled 20 m pixels never inflate independent evidence.

## Datum and boundary sensitivity

The implementation does not apply a time-dependent WGS84-to-NAD83 grid shift because the Sentinel metadata does not supply a geodetic realization/epoch and the CyAN GeoTIFF does not embed a transformation. At 300 m scale this is small relative to a source pixel, but boundary-cell inclusion can still change.

A conservative ±10 m shift audit changed the number of included native centers by at most one. Scene-level presence/absence of High remained unchanged in all six scenes. Native High support ranges were 18–19 for Utah September, 10 for Upper Klamath July, and 19–20 for Upper Klamath September; all qualification conclusions remain unchanged. Exact source-cell counts should therefore be read with one-cell boundary sensitivity, while the conclusion of 0 qualified High units is robust.

## Remaining limitations

- CyAN has approximately 15× coarser linear resolution than the Sentinel grid.
- Nearest-neighbor creates spatially repeated labels and cannot add information.
- Tile cloud percentage from Sentinel does not prove local cloud-free conditions; CyAN validity flags establish only that selected label cells are not code 254/255.
- The source is a remote-sensing proxy and has no paired field measurement in this pilot.
- Independence from legacy v2 cannot be proven because v2 footprints remain unknown.

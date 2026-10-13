# CyAN Download Audit

## Outcome

All six and only the six frozen NASA CyAN targets were retrieved successfully through the official Ocean Color get-file service after the research owner completed Earthdata login in the trusted browser interface. No target was substituted, no date range was expanded, and no model output was consulted.

The official search endpoint returned exactly the product ID already frozen for each Sentinel acquisition date. The files are stored under the Git-ignored `data/raw/final_label_pilot/cyan/` directory; only checksums and non-secret provenance are recorded publicly.

## Authentication handling

- Before access, neither `~/.netrc` nor `~/.urs_cookies` existed.
- The researcher entered credentials directly on `urs.earthdata.nasa.gov`; credentials were never requested in chat.
- No token, cookie, authorization header, username, authentication file, or browser profile was copied into the repository.
- The manifest records only `Earthdata OAuth browser session; no credential retained`.
- The first product was received twice while capturing the browser download event. The duplicate was byte-identical and moved outside the repository to a temporary location; it was not used. The research data directory contains exactly six unique target products.

## Official retrieval evidence

Search endpoint: `https://oceandata.sci.gsfc.nasa.gov/api/cyan_file_search`

Frozen search parameters per date: `region=1`, `period=2`, `product=1`, `areaids=all`, identical start/end date, `addurl=1`, `results_as_file=1`, and mandatory `wgetflag=1`.

| Product ID | Sentinel date | Bytes | SHA-256 | Result |
|---|---:|---:|---|---|
| `L2025193.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif` | 2025-07-12 | 4,530,952 | `ee9775ca7c1b7b12e64c68b3c24595e2991b3a73b513f5af47cad15441c39b40` | SUCCESS |
| `L2025206.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif` | 2025-07-25 | 4,651,116 | `0eed1b55b0fbdc8fbbb0bb8ccbfa70ad9b33d1451fa39b9ce1f0d927ffa4cd8f` | SUCCESS |
| `L2025209.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif` | 2025-07-28 | 4,603,474 | `5a778a76124f33ee48e03c2f6146a2c1dd1125ef37519dca446384d565bf530c` | SUCCESS |
| `L2025262.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif` | 2025-09-19 | 5,007,142 | `4624d8b25c0ab28dd9d37beb4abac00355642531e3d30d2dfaf22a2055874d30` | SUCCESS |
| `L2025266.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif` | 2025-09-23 | 5,156,960 | `e8aa9de2ca1a7dc8e465d58975383990d6a9adda18145f87ecf55804a35aae4e` | SUCCESS |
| `L2025268.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif` | 2025-09-25 | 5,387,010 | `18348a9b777cfd5b485e638b1bea1792615f9053915a8ee0e85363d9991b4c8f` | SUCCESS |

## Product integrity

Every file is a one-band, 8-bit, palette-index, LZW-compressed GeoTIFF with shape 15,138 rows × 26,328 columns, 300 m pixels, and the same CONUS Albers georeference. Every file contains the primary metadata field `OBPG_version=6.0`; version is therefore CONFIRMED from the downloaded product rather than inferred from its date.

The product name and official search request identify `CI_cyano`. The applicable NASA V6 release note is:

`https://oceancolor.gsfc.nasa.gov/images/cyan/version/6/CyAN_NASA_MERISOLCI_CI_release_notes_V6_Aug_2025.pdf`

It defines 0 as below detection, 1–253 as data, 254 as land, and 255 as no-data such as cloud or ice. No authenticated checksum supplied by the service was available in the browser flow, so the manifest records locally calculated SHA-256 values rather than mislabeling them as provider-signed checksums.

## Failures and limits

There were no product-download failures. The interactive OAuth redirect could not be reused as a command-line credential, by design. Re-downloading from a clean environment therefore requires the researcher to authenticate again; reproduction from already downloaded, checksum-matching raw files requires no credentials.

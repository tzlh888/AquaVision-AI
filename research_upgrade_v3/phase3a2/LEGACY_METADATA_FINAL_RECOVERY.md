# Legacy Metadata Final Recovery

## Scope and stopping rule

This was the final bounded public-evidence search for the missing geographic identity of the 288 legacy v2 samples. It was limited to the Zenodo deposit, the public source repository and history, one previously unaudited public branch, and public author/contact records. No image-similarity geolocation was attempted. Recovery stops after these sources because none supplies a sample-level link from a v2 array to a Sentinel product, georeferenced crop, waterbody, or CyAN processing version.

## Result

**Historical geographic identity recovery remains NOT READY.** For all 288 v2 samples, Sentinel product UUID, source CRS, affine transform, source crop coordinates, patch footprint, waterbody identity, and exact CyAN processing version remain **UNVERIFIED**. The earlier recovery of array contents, dates, author-grid grouping, and relative offsets does not make the author-grid components physical waterbodies.

Unless a new primary artifact is produced by the authors or an original storage system, these identities should be treated as permanently unverified. No v2 test result may be relabeled as geographically independent evidence.

## Evidence exhausted

### Zenodo deposit

- DOI: `10.5281/zenodo.14230064`, record revision 3, published 2024-11-27.
- The record exposes six ZIP attachments and no geospatial sidecar, provenance table, STAC item list, UUID table, or `data.json`.
- Record API response: HTTP 200, 5,440 bytes, raw SHA-256 `cc3ac774dfcd0544cdc75903f3ca5237fd2842bb0aa21397626b84c6fac7de2c`.
- Versions API: one version only; response SHA-256 `823cdfcae7cd7c078565effb333020f9d19844b6df6a57d1994107fd585aa156`.

### Public source repository and history

- Repository default branch commit: `e24e311b...`; repository API response SHA-256 `f8bc59d0...`.
- Three public commits were returned: `e24e311...`, `66ea804...`, and `6a35863...`.
- Path history for `code/dataset/data.json` is empty. The archived repository artifact previously audited also lacks this file.
- Public releases, tags, and issues are empty. The empty-array response SHA-256 is `2ba33c...`.
- Two branches exist. The branch-list response SHA-256 is `c204023...`.

### Previously unaudited `case-studies` branch

- Commit: `14b315d20828a171dc1579af5fd10f3fdb41dcf5`.
- Recursive tree: 45 entries, not truncated; response SHA-256 `be8fbb6a8912d823b95ba1073dd8effb44b457a463a0d638de93b46474ccaeea`.
- New relevant files include `code/case_studies/get_cyan.py` (SHA-256 `a930856a8ad075121a38155f2e82b1fcc40181bc6e67006fb9ff2b4c33662209`) and `search_dates.py` (SHA-256 `d9272ed99753844a457db1611e8738ed6b8bf17b213d53926188674b45375f4e`).
- These files demonstrate a prospective case-study workflow, a Swan Lake bounding box, and requirements for Earthdata and Copernicus credentials. They do **not** contain the legacy `data.json`, v2 sample UUIDs, affine transforms, crop coordinates, waterbody mapping, or exact CyAN version.
- The branch's visualization thresholds were not adopted. The already frozen mapping remains Low 0–99, Moderate 100–199, High 200–253, Ignore 254–255.
- No inference or model functions from this branch were executed.

## Evidence classification

| Identity field | Status | Reason |
|---|---|---|
| v2 array bytes, date, author-grid and relative offset | CONFIRMED | Recovered and hashed in Phase 3A/3A-1 |
| Sentinel product UUID | UNVERIFIED | Passed through historical code but not retained in artifacts |
| CRS / affine / absolute crop coordinates | UNVERIFIED | Absent from NPY files and public sidecars |
| Patch footprint / waterbody identity | UNVERIFIED | Cannot be reconstructed from author-grid components |
| Exact CyAN processing version | UNVERIFIED | No retained source product or version sidecar |
| Cross-overlap with prospective v3 | UNVERIFIED | v2 footprints are unknown |

## Unsent author inquiry draft

No message was sent. A narrowly scoped inquiry could be sent only with the research owner's approval:

> Subject: Request for sample-level geospatial provenance for the HAB Detection Sentinel-2/CyAN dataset
>
> We are auditing the reproducibility of the public dataset associated with DOI 10.5281/zenodo.14230064. Do you still have the original `data.json` or an equivalent table linking each saved sample to (1) Sentinel product UUID or product ID, (2) acquisition timestamp, (3) CRS and affine transform, (4) absolute crop/window coordinates or geographic footprint, (5) named waterbody, and (6) CyAN product name and processing version? A read-only export or checksummed metadata table would be sufficient; we do not need credentials or private data. We would record any recovered material as author-supplied evidence and preserve its checksum.

Public contact channels identified: the repository commit email `conrad.schloer@gmail.com`, the DLR publication record contact `Ronny.Haensch (at) dlr.de`, and the public GitHub repository. A response alone should not be treated as sample-level confirmation unless accompanied by inspectable primary metadata or a reproducible derivation.

## Final historical decision

The public recovery path is exhausted. Historical v2 remains useful only as a legacy/exploratory benchmark whose geographic independence cannot be demonstrated. Future progress should use the clean, metadata-first v3 path rather than attempting to infer v2 locations.

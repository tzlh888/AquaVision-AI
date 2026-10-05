# Acquisition-only amendment A — before any Phase 3.5 model evaluation

On 2026-10-04, a bounded two-range probe established that the Zenodo file server returns valid multipart byte ranges in one HTTP 206 response. This allows many compressed reference masks to be retrieved in one request, without reading intervening Sentinel-2 members.

The original acquisition plan's 1,024-mask cap was based on one-request-per-mask access. Replace only that cap with **50,000 new reference masks**, using at most 64 masks per multipart request. Keep the original **64 MiB reference-response budget and 1,200 reference HTTP request cap**, bounded retries, source CRC checks and all support criteria unchanged. The 24,518-pair cached pool is the first complete reference census target. Additional archives are screened with deterministic group/date-diverse reference batches within the remaining budget.

This amendment responds to observed transport capability, not model scores or favorable labels. No Phase 3.5 model has been evaluated. The initial criteria contract remains unmodified; this signed acquisition amendment and transport probe are additional provenance records. It does not authorize whole ZIP or whole imagery download, or relax geographic/class-support gates.

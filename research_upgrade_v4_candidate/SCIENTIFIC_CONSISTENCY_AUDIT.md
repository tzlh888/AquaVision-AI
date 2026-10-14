# AquaVision scientific consistency audit

## Audit result: PASS for claim consistency; PARTIAL for complete-artifact reproducibility

The central `LIMITED` conclusion, historical results, validation-selected model, geographic-identity limitations, and stop-training decision agree across code, configuration, and reports. No evidence supports upgrading the project to independent confirmation.

| File | Original statement | Code/data evidence | Classification | Action | Status |
| --- | --- | --- | --- | --- | --- |
| README and final reports | 288 real Sentinel/CyAN patch pairs, not independent waterbodies. | Frozen split contains 96 Train, 48 Validation, 144 Test. | Count check and geography-identity audit. | None. | VERIFIED WITH SCOPE |
| README | LR Test High F1 is 0.5803 but LR was not selected. | Final results and selection config show validation selected NDCI; LR validation High F1 was 0. | Model-selection boundary. | Preserve post-hoc label. | VERIFIED |
| Historical geographic claims | Author-grid components are not verified lakes. | 0/288 legacy patches have confirmed scene, footprint, and waterbody identity. | Evidence limitation. | Do not promote patches/pixels to independent units. | VERIFIED |
| V3 label-pilot report | Six CyAN V6 products and six Sentinel candidates aligned across three named waterbodies. | Product manifest, hashes, footprints, and integration tests. | Engineering/provenance result. | Report as pipeline evidence only. | VERIFIED |
| V3 readiness | 0 qualified independent High units; 0/0/0 split members. | Qualification CSV and V4 unit audit. | Dataset gate. | Stop training. | VERIFIED |
| “12 additional candidates” vs 15 catalog rows | May appear inconsistent. | Catalog has 12 new candidates plus three preserved pilot waterbodies. | Stage/row-scope distinction. | Clarify in V4. | CONSISTENT |
| Pixel support vs independent units | Thousands of resampled pixels may appear to increase sample size. | Protocol counts native CyAN cells and waterbody histories; 64×64 pixels are not independent units. | Resolution/autocorrelation guard. | Retain conservative unit definition. | VERIFIED |
| Public tests | 124 passed and 1 skipped after adding two strict manifest migration/tamper tests. | Fresh 2026-10-14 run reproduced this result; the one complete-frozen-environment skip remains explicit. | Current code check. | None. | REPRODUCED |
| Upgrade tests | 60/60 pass. | Fresh wrapper execution reproduced all five suites. | V3 evidence check. | None. | REPRODUCED |
| Legacy metadata-only audit | Frozen manifest is retained unchanged. | A version-scoped amendment registers exactly three regenerated `egg-info` records and the tracked `tests/test_phase4_reliability.py` change; unregistered source tampering still fails. | Strict compatibility layer, not blanket hash acceptance. | Re-run command and retain the one public-suite environment skip. | VERIFIED FOR METADATA SCOPE |
| AI disclosure | Substantial AI assistance disclosed. | README and closeout documents are aligned. | Disclosure check. | Owner must review public claims. | CONSISTENT |

No historical output, split, checkpoint, or model was altered. V4 is additive.

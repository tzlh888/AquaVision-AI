# Phase4 reproducibility

123 tests pass, including all 103 pre-existing tests unchanged and 20 new tests covering class weighting, focal loss, calibration, temperature, all 6 perturbation families, band mapping, failure metrics, deterministic selection, integration completeness, registration and preservation. The real-data integration tests additionally validate selection and regional sums. [`pytest_results.xml`](../phase4/pytest_results.xml).

All 20 model specifications were reloaded for validation and Test. 100 confusion matrices and 40 class-prediction caches reproduce exactly. All 9 validation temperature fits reproduce and 18 validation/Test argmax checks remain unchanged. RF probability sums vary by at most2.22e-16 under the unchanged parallel n_jobs=2 setting; probability tolerance is 1e-12 absolute,0relative. This floating-point summation issue does not change any predicted class or matrix. The initial failed bitwise RF probability check and correction are disclosed in [`IMPLEMENTATION_NOTES.md`](../phase4/IMPLEMENTATION_NOTES.md).

177 prior files remain SHA-256-identical, including all Phase3.5 reports, splits, metrics, checkpoints/configurations and the original pilot artifacts. Phase4 has new directories/IDs and does not overwrite them. No WaterSense-AI files were changed. Registration/config/protocol hashes, validation-selection-before-Test timestamp order, specification and temperature hashes are verified. [`preservation_check.json`](../phase4/preservation_check.json); [`reproduction_check.json`](../phase4/reproduction_check.json).

Run from the AquaVision-AI root with the existing pinned `.venv`:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_phase4.py
.venv/bin/python scripts/analyze_phase4.py
.venv/bin/python scripts/diagnose_phase4_training.py
.venv/bin/python scripts/report_phase4.py
```

The analysis scripts reuse immutable checkpoints. `scripts/run_phase4.py` intentionally refuses to run when selection.json already exists. To reproduce fitting, use a separate scratch clone/workspace containing the frozen input manifests and model baselines, with a new empty Phase4 output directory; never delete/overwrite the delivered evidence. Registration is in`data/metadata/phase4/preregistration.json`; exact source snapshots are hashed in run_contract.json and the final delivery manifest. IDs/seeds/protocol and normalization are saved with each checkpoint. Data hashes are verified before fitting. No new imagery was downloaded in Phase4.

The final delivery manifest inventories Phase4 code, configs, metadata, reports and output artifacts with byte sizes/SHA-256. Probabilistic inputs/logits and class maps are cached for independent metric recomputation. Reproduction means these local pinned versions and data; bitwise results on different numerical libraries/hardware are not promised.

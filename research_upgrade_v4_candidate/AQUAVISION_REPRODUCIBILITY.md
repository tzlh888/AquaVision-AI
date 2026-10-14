# AquaVision V4 reproducibility

Status: **PARTIAL**. Code and preserved v3 evidence are reproducible; independent confirmation is unavailable.

```bash
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python scripts/run_research_upgrade_tests.py
PYTHONPATH=src python research_upgrade_v4_candidate/v4_audit.py
PYTHONPATH=src python -m unittest discover -s research_upgrade_v4_candidate -p 'test_*.py' -v
```

The public suite retains one explicit complete-frozen-environment skip. The v3 upgrade suites remain separately tested. The version-scoped preservation amendment records three reproducible packaging-metadata files and the changed tracked reliability test without rewriting the frozen manifest; `audit_final_release.py --metadata-only` must verify that exact amendment. No model was trained by V4.

import importlib.util
import hashlib
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("release_audit", ROOT / "scripts/audit_final_release.py")
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(AUDIT)


def test_registered_manifest_change_passes(tmp_path):
    path = tmp_path / "tracked.txt"
    path.write_text("current\n")
    old = "0" * 64
    observed = AUDIT.sha(path)
    result = AUDIT.verify_file_hash_set(
        tmp_path,
        {"tracked.txt": old},
        {},
        {"tracked.txt": {
            "before_sha256": old,
            "after_sha256": observed,
            "classification": "tracked_test_update",
        }},
        full=True,
    )
    assert result["registered_v4_release_candidate_changes"] == ["tracked.txt"]
    assert not result["changed_files"]


def test_unregistered_manifest_tamper_fails(tmp_path):
    path = tmp_path / "critical_source.py"
    path.write_text("tampered = True\n")
    with pytest.raises(AssertionError):
        AUDIT.verify_file_hash_set(
            tmp_path,
            {"critical_source.py": "0" * 64},
            {},
            {},
            full=True,
        )


def test_metadata_only_is_read_only_and_repeatable(tmp_path):
    controlled = [
        ROOT / "research_outputs/phase5/claim_occurrences.json",
        ROOT / "research_outputs/phase5/metadata_audit.json",
    ]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in controlled}
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(filter(None, (str(ROOT / "src"), environment.get("PYTHONPATH", ""))))
    command = [sys.executable, str(ROOT / "scripts/audit_final_release.py"), "--metadata-only"]
    for _ in range(2):
        completed = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True)
        assert completed.returncode == 0, completed.stderr
        assert '"passed": true' in completed.stdout
        assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in controlled} == before

    output = tmp_path / "isolated-audit"
    completed = subprocess.run(command + ["--output-dir", str(output)], cwd=ROOT, env=environment, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr
    assert (output / "claim_occurrences.json").is_file()
    assert (output / "metadata_audit.json").is_file()
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in controlled} == before


def test_authorized_crlf_audit_and_frozen_manifest_bytes():
    audit = ROOT / "research_upgrade_v4_candidate/INDEPENDENT_HIGH_UNIT_AUDIT.csv"
    data = audit.read_bytes()
    assert hashlib.sha256(data).hexdigest() == "6c7abafe758d9a2ec9e1ccb3212ce9a75f8ba98428252e2c9807f247d66d247a"
    assert data.count(b"\r\n") == data.count(b"\n") == 16
    assert b"\n" not in data.replace(b"\r\n", b"")
    frozen = ROOT / "data/metadata/phase5/preservation_manifest.json"
    assert hashlib.sha256(frozen.read_bytes()).hexdigest() == "eecbf26007c651931228426bc8f390d8f946b0a9974065beacce32a78b6aef49"

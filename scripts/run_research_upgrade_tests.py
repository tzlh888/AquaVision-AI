"""Run every Research Upgrade v3 test suite from the repository root.

The stage tests intentionally use local modules. This wrapper supplies each
stage directory on ``PYTHONPATH`` without importing or executing any research
runner, downloading data, or training a model.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
STAGES = ("phase3a", "phase3a1", "phase3a2", "final_label_pilot", "phase3a3")


def main() -> int:
    for stage in STAGES:
        stage_path = ROOT / "research_upgrade_v3" / stage
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONPATH"] = os.pathsep.join(
            (str(ROOT / "src"), str(stage_path))
        )
        print(f"Running Research Upgrade suite: {stage}", flush=True)
        completed = subprocess.run(
            (
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                str(stage_path),
                "-p",
                "test_*.py",
                "-v",
            ),
            cwd=ROOT,
            env=environment,
            check=False,
        )
        if completed.returncode:
            return completed.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

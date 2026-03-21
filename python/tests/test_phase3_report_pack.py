from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from geoclt.artifacts import stable_hash


REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(script: str) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = "python"
    subprocess.run(
        [sys.executable, script],
        cwd=REPO_ROOT,
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )


def test_phase3_report_pack_regeneration_is_deterministic():
    _run("scripts/generate_phase3a_gate_report.py")
    _run("scripts/generate_phase3b_gate_report.py")
    _run("scripts/generate_phase3_report_pack.py")

    tracked = [
        REPO_ROOT / "docs/reports/phase3a/executive_summary.md",
        REPO_ROOT / "docs/reports/phase3a/test_results.md",
        REPO_ROOT / "docs/reports/phase3b/executive_summary.md",
        REPO_ROOT / "docs/reports/phase3b/test_results.md",
    ]
    first = {str(path): stable_hash(path.read_text(encoding="utf-8")) for path in tracked}

    _run("scripts/generate_phase3_report_pack.py")
    second = {str(path): stable_hash(path.read_text(encoding="utf-8")) for path in tracked}

    assert first == second

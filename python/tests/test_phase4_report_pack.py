from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from geoclt.artifacts import stable_hash


def _run(script: str) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = "python"
    subprocess.run(
        [sys.executable, script],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )


def test_phase4_report_pack_regeneration_is_deterministic():
    repo = Path(__file__).resolve().parents[2]

    _run("scripts/generate_phase4a_gate_report.py")
    _run("scripts/generate_phase4a_nightly_model_report.py")
    _run("scripts/generate_phase4b_gate_report.py")
    _run("scripts/generate_phase4_report_pack.py")

    tracked = [
        repo / "docs/reports/phase4a/executive_summary.md",
        repo / "docs/reports/phase4a/test_results.md",
        repo / "docs/reports/phase4b/executive_summary.md",
        repo / "docs/reports/phase4b/test_results.md",
    ]
    first_hashes = {str(path): stable_hash(path.read_text(encoding="utf-8")) for path in tracked}

    _run("scripts/generate_phase4_report_pack.py")
    second_hashes = {str(path): stable_hash(path.read_text(encoding="utf-8")) for path in tracked}

    assert first_hashes == second_hashes

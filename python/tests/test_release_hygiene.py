from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_placeholder_guard_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_no_placeholders.py"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_synthetic_inventory_complete() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/generate_synthetic_inventory.py"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads((REPO_ROOT / "outputs" / "synthetic_inventory_report.json").read_text())
    assert payload["synthetic_inventory_complete"] is True
    assert payload["overall_complete"] is True

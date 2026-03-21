from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "outputs" / "desynthetic_status.json"


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    inventory = _load(REPO_ROOT / "outputs" / "synthetic_inventory_report.json")
    phase01 = _load(REPO_ROOT / "outputs" / "phase_gate_report.json")
    phase2 = _load(REPO_ROOT / "outputs" / "phase2_gate_report.json")
    phase4a = _load(REPO_ROOT / "outputs" / "phase4a_gate_report.json")
    phase4a_nightly = _load(REPO_ROOT / "outputs" / "phase4a_nightly_model_report.json")

    payload = {
        "git_commit": _git_commit(),
        "phase_a": bool(inventory.get("overall_complete")),
        "phase_b": bool(phase2.get("overall_pass")),
        "phase_c": bool(phase01.get("overall_pass"))
        and bool(phase4a.get("overall_pass"))
        and bool(phase4a_nightly.get("overall_pass")),
        "phase_d": os.getenv("GEOCLT_AUTH_MODE", "token").strip().lower() == "token",
        "phase_e": os.getenv("GEOCLT_STORE_BACKEND", "fs").strip().lower() in {"fs", "minio"}
        and os.getenv("GEOCLT_QUEUE_BACKEND", "memory").strip().lower() in {"memory", "redis"},
        "desynthetic_phase": os.getenv("GEOCLT_DESYNTHETIC_PHASE", "A").strip().upper(),
    }
    payload["overall_pass"] = all(payload[key] for key in ["phase_a", "phase_b", "phase_c", "phase_d", "phase_e"])
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

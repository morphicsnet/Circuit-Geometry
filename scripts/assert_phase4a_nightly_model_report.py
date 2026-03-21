from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "outputs" / "phase4a_nightly_model_report.json"

REQUIRED_BOOLEAN_PATHS = [
    "overall_pass",
    "nightly_profiles_valid",
    "nightly_datasets_valid",
    "nightly_shared_lane_dual_model_valid",
    "nightly_receipt_bundle_valid",
    "nightly_latency_memory_recorded",
    "nightly_divergence_within_bounds",
    "nightly_report_complete",
]


def main() -> int:
    if not REPORT_PATH.exists():
        print(f"missing phase4a nightly report: {REPORT_PATH}")
        return 1

    payload = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    for path in REQUIRED_BOOLEAN_PATHS:
        value = payload.get(path)
        if value is not True:
            print(f"phase4a nightly failed at {path}: {value}")
            return 1

    if payload.get("primary_run_id") == payload.get("challenger_run_id"):
        print("phase4a nightly failed: expected distinct primary/challenger runs")
        return 1

    print("phase4a nightly report assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

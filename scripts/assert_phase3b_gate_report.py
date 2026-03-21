from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "outputs" / "phase3b_gate_report.json"

REQUIRED_BOOLEAN_PATHS = [
    "overall_pass",
    "explorer_api_smoke_pass",
    "replay_deterministic",
    "trace_endpoint_deterministic",
    "atlas_switch_consistent",
    "evaluate_lane_deterministic",
    "receipt_endpoint_deterministic",
    "analysis_report_deterministic",
    "differential_analysis_deterministic",
    "mechanism_diff_deterministic",
    "mechanism_diff_uses_ids_only",
    "cohort_analysis_valid",
    "report_bundle_schema_valid",
    "report_bundle_hash_stable",
    "report_bundle_identity_stable",
    "report_pack_regeneration_deterministic",
    "decision_receipt_export_valid",
    "analysis_endpoint_responsive",
    "explorer_read_only_semantics",
]


def main() -> int:
    if not REPORT_PATH.exists():
        print(f"missing phase3b gate report: {REPORT_PATH}")
        return 1

    payload = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    for path in REQUIRED_BOOLEAN_PATHS:
        value = payload.get(path)
        if value is not True:
            print(f"phase3b gate failed at {path}: {value}")
            return 1

    print("phase3b gate report assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "outputs" / "phase4b_gate_report.json"

REQUIRED_BOOLEAN_PATHS = [
    "overall_pass",
    "pilot_scope_policy_valid",
    "pilot_submission_flow_valid",
    "human_review_flow_valid",
    "operator_review_schema_valid",
    "receipt_completeness_100pct",
    "policy_routing_quality_valid",
    "false_allow_within_threshold",
    "false_block_within_threshold",
    "drift_alert_thresholds_valid",
    "mechanism_drift_monitoring_valid",
    "cohort_analysis_deterministic",
    "operator_trust_metrics_valid",
    "report_bundle_identity_stable",
]


def main() -> int:
    if not REPORT_PATH.exists():
        print(f"missing phase4b gate report: {REPORT_PATH}")
        return 1

    payload = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    for path in REQUIRED_BOOLEAN_PATHS:
        value = payload.get(path)
        if value is not True:
            print(f"phase4b gate failed at {path}: {value}")
            return 1

    print("phase4b gate report assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

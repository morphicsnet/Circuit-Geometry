from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "outputs" / "phase4a_gate_report.json"

REQUIRED_BOOLEAN_PATHS = [
    "overall_pass",
    "demo_lane_registry_loaded",
    "model_profile_frozen",
    "run_config_record_valid",
    "golden_dataset_manifest_valid",
    "lane_scorecards_valid",
    "fallback_semantics_valid",
    "replay_trace_deterministic",
    "receipt_generation_valid",
    "policy_action_present",
    "structured_output_schema_valid",
    "operator_demo_flow_valid",
    "median_latency_within_budget",
    "memory_within_budget",
    "success_rate_above_threshold",
    "fallback_rate_within_threshold",
    "report_bundle_identity_stable",
]


def main() -> int:
    if not REPORT_PATH.exists():
        print(f"missing phase4a gate report: {REPORT_PATH}")
        return 1

    payload = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    for path in REQUIRED_BOOLEAN_PATHS:
        value = payload.get(path)
        if value is not True:
            print(f"phase4a gate failed at {path}: {value}")
            return 1

    print("phase4a gate report assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

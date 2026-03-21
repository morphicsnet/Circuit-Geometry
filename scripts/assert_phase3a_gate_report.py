from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "outputs" / "phase3a_gate_report.json"

REQUIRED_BOOLEAN_PATHS = [
    "overall_pass",
    "mechanism_identity_stable",
    "mechanism_identity_runtime_field_exclusion",
    "mechanism_identity_changes_on_semantic_change",
    "mechanism_id_deterministic",
    "mechanism_identity_chart_substitution_stable",
    "mechanism_identity_schema_replay_stable",
    "cluster_deterministic",
    "cluster_identity_deterministic",
    "cluster_high_cardinality_deterministic",
    "cluster_high_cardinality_member_count_valid",
    "mechanism_family_assignment_valid",
    "decision_receipt_schema_valid",
    "decision_receipt_complete",
    "receipt_hash_stable",
    "receipt_repersist_idempotent",
    "receipt_mutation_rejected",
    "receipt_immutability_enforced",
    "lane_registry_loaded",
    "lane_thresholds_valid",
    "lane_falsifiers_valid",
    "lane_policy_actions_valid",
    "lane_registry_immutable",
    "policy_evaluation_deterministic",
    "artifact_bundle_linkage_valid",
    "canonicalization_preserved",
]


def main() -> int:
    if not REPORT_PATH.exists():
        print(f"missing phase3a gate report: {REPORT_PATH}")
        return 1

    payload = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    for path in REQUIRED_BOOLEAN_PATHS:
        value = payload.get(path)
        if value is not True:
            print(f"phase3a gate failed at {path}: {value}")
            return 1

    if payload.get("lane_count", 0) < 4:
        print("phase3a lane registry missing expected lanes")
        return 1

    print("phase3a gate report assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

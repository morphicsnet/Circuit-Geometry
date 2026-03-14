from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "python") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "python"))

from fastapi.testclient import TestClient

from geoclt.artifacts import stable_hash, validate_instance
from geoclt.differential import cohort_summary
from services.api.app import app


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


def _lane_thresholds(lane_id: str) -> dict[str, float]:
    lane_root = REPO_ROOT / "crates" / "geoclt-benchmark" / "lanes"
    for lane_file in lane_root.glob("*/v1.json"):
        payload = json.loads(lane_file.read_text(encoding="utf-8"))
        if payload.get("lane_id") == lane_id:
            return payload.get("thresholds", {})
    raise FileNotFoundError(f"lane not found: {lane_id}")


def main() -> int:
    client = TestClient(app)
    workspace = str((REPO_ROOT / "runs" / "phase4b-gate").resolve())
    lane_id = "realworld-claims-triage.v1"

    demo = client.post(
        "/demo/submit",
        json={
            "workspace": workspace,
            "lane_id": lane_id,
            "requested_action": "allow",
        },
    )
    if demo.status_code != 200:
        print("phase4b failed to create demo run")
        print(demo.text)
        return 1

    demo_run_id = demo.json()["run_id"]

    submit = client.post(
        "/pilot/submit",
        json={
            "workspace": workspace,
            "lane_id": lane_id,
            "user_id": "demo-user",
            "task": "claims-triage",
            "corpus": "golden",
            "requested_action": "allow",
            "demo_run_id": demo_run_id,
        },
    )
    if submit.status_code != 200:
        print("phase4b failed to submit pilot")
        print(submit.text)
        return 1

    pilot_run_id = submit.json()["pilot_run_id"]

    review = client.post(
        "/pilot/review",
        json={
            "workspace": workspace,
            "pilot_run_id": pilot_run_id,
            "reviewer_id": "reviewer-1",
            "task_ref": "task-claims-1",
            "accepted": True,
            "override": False,
            "explanation_usefulness": 0.92,
            "receipt_usefulness": 0.91,
            "escalation_appropriateness": 0.9,
            "confidence_calibration_agreement": 0.89,
        },
    )

    receipt = client.get(f"/pilot/receipt/{pilot_run_id}", params={"workspace": workspace})
    metrics_one = client.get("/pilot/metrics", params={"workspace": workspace})
    metrics_two = client.get("/pilot/metrics", params={"workspace": workspace})

    if review.status_code != 200 or receipt.status_code != 200 or metrics_one.status_code != 200:
        print("phase4b pilot flow failed")
        return 1

    receipt_payload = receipt.json()
    metrics_payload = metrics_one.json()
    metrics_payload_two = metrics_two.json()

    required_receipt_fields = {
        "receipt_id",
        "trace_id",
        "model_id",
        "lane_id",
        "policy_version",
        "action_selected",
        "immutable_bundle_hash",
    }
    receipts = receipt_payload.get("receipts", [])
    receipt_completeness = bool(receipts) and all(
        required_receipt_fields.issubset(set(item.keys())) for item in receipts
    )

    scope_record = metrics_payload["pilot_scope_policy_record"]
    validate_instance(scope_record, REPO_ROOT / "schemas" / "pilot_scope_policy_record.schema.json")

    review_dir = REPO_ROOT / "runs" / "phase4b-gate" / "phase4" / "pilot_reviews"
    review_files = sorted(review_dir.glob("*.json"))
    operator_review_schema_valid = bool(review_files)
    if operator_review_schema_valid:
        latest_review = json.loads(review_files[-1].read_text(encoding="utf-8"))
        validate_instance(latest_review, REPO_ROOT / "schemas" / "operator_review_record.schema.json")
        operator_review_schema_valid = "reviewer_id" not in latest_review["payload"]

    metrics_bundle = metrics_payload["metrics_bundle"]
    metrics_bundle_two = metrics_payload_two["metrics_bundle"]
    thresholds = _lane_thresholds(lane_id)

    trust_metrics = metrics_bundle["payload"]["trust_metrics"]
    trust_keys = {
        "reviewer_acceptance_rate",
        "reviewer_override_rate",
        "explanation_usefulness_score",
        "receipt_usefulness_score",
        "escalation_appropriateness_rate",
        "confidence_calibration_agreement",
    }

    cohort_input = {
        "pilot": [
            {
                "mechanism_family_id": "family-a",
                "mechanism_id": f"mechanism:{pilot_run_id}",
            }
        ]
    }
    cohort_one = cohort_summary(cohort_input)
    cohort_two = cohort_summary(cohort_input)

    routing_quality = float(metrics_bundle["payload"]["routing_quality"])
    false_allow = float(metrics_bundle["payload"]["false_allow_rate"])
    false_block = float(metrics_bundle["payload"]["false_block_rate"])

    drift = metrics_payload["drift_alert_record"]["payload"]

    report: dict[str, Any] = {
        "git_commit": _git_commit(),
        "pilot_scope_policy_valid": bool(scope_record["payload"].get("identity_key_id"))
        and bool(scope_record["payload"].get("in_scope_users")),
        "pilot_submission_flow_valid": submit.status_code == 200,
        "human_review_flow_valid": review.status_code == 200,
        "operator_review_schema_valid": operator_review_schema_valid,
        "receipt_completeness_100pct": receipt_completeness,
        "policy_routing_quality_valid": routing_quality >= 0.8,
        "false_allow_within_threshold": false_allow <= float(thresholds.get("false_allow_max", 1.0)),
        "false_block_within_threshold": false_block <= float(thresholds.get("false_block_max", 1.0)),
        "drift_alert_thresholds_valid": float(drift["threshold"]) > 0 and float(drift["drift_metric"]) >= 0,
        "mechanism_drift_monitoring_valid": bool(drift.get("mechanism_family_id"))
        and drift.get("alert_status") in {"ok", "alert"},
        "cohort_analysis_deterministic": cohort_one["summary_hash"] == cohort_two["summary_hash"],
        "operator_trust_metrics_valid": trust_keys.issubset(set(trust_metrics.keys()))
        and all(0.0 <= float(trust_metrics[key]) <= 1.0 for key in trust_keys),
        "report_bundle_identity_stable": metrics_bundle["artifact_id"] == metrics_bundle_two["artifact_id"]
        and metrics_bundle["content_hash"] == stable_hash(metrics_bundle["payload"]),
        "pilot_run_id": pilot_run_id,
        "demo_run_id": demo_run_id,
        "receipt_count": len(receipts),
        "false_allow_rate": false_allow,
        "false_block_rate": false_block,
        "routing_quality": routing_quality,
    }

    report["overall_pass"] = all(
        report[key]
        for key in [
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
    )

    output = REPO_ROOT / "outputs" / "phase4b_gate_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

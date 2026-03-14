from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SRC = REPO_ROOT / "python"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

from fastapi.testclient import TestClient

from geoclt.artifacts import read_json, validate_instance, verify_bundle_manifest
from geoclt.demo import load_manifest
from geoclt.models import DEFAULT_QWEN_PROFILE, profile_frozen
from services.api.app import DEMO_LANE_ASSET_DIRS, app

ALLOWED_POLICY_ACTIONS = {
    "allow",
    "allow_with_review",
    "route_to_fallback",
    "block",
    "escalate",
}


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


def _load_lane(lane_id: str) -> dict[str, Any]:
    lane_path = REPO_ROOT / "crates" / "geoclt-benchmark" / "lanes" / lane_id.replace(".v1", "") / "v1.json"
    # lane dirs use lane-id sans suffix in this repo.
    if not lane_path.exists():
        # Fall back to explicit mapping for names with dots.
        lane_root = REPO_ROOT / "crates" / "geoclt-benchmark" / "lanes"
        for candidate in lane_root.glob("*/v1.json"):
            payload = read_json(candidate)
            if payload.get("lane_id") == lane_id:
                return payload
        raise FileNotFoundError(f"lane missing: {lane_id}")
    return read_json(lane_path)


def main() -> int:
    client = TestClient(app)
    workspace = str((REPO_ROOT / "runs" / "phase4a-gate").resolve())

    submit = client.post(
        "/demo/submit",
        json={
            "workspace": workspace,
            "lane_id": "realworld-claims-triage.v1",
            "model_profile_id": DEFAULT_QWEN_PROFILE.model_profile_id,
            "requested_action": "allow",
        },
    )
    if submit.status_code != 200:
        print("phase4a demo submit failed")
        print(submit.text)
        return 1

    run_payload = submit.json()
    run_id = run_payload["run_id"]
    report_response = client.get(f"/demo/report/{run_id}", params={"workspace": workspace})
    receipts_response = client.get(f"/demo/receipt/{run_id}", params={"workspace": workspace})
    operator_flow_ok = submit.status_code == 200 and report_response.status_code == 200 and receipts_response.status_code == 200

    if report_response.status_code != 200 or receipts_response.status_code != 200:
        print("phase4a demo report or receipt fetch failed")
        return 1

    report_payload = report_response.json()
    receipts_payload = receipts_response.json()

    run_file = REPO_ROOT / "runs" / "phase4a-gate" / "phase4" / "demo_runs" / f"{run_id}.json"
    run_record = read_json(run_file)

    lane_files = [
        _load_lane("realworld-claims-triage.v1"),
        _load_lane("realworld-policy-qa.v1"),
        _load_lane("realworld-structured-intake.v1"),
    ]
    lane_registry_loaded = len(lane_files) == 3 and all(bool(item.get("lane_id")) for item in lane_files)

    # Validate all phase4a manifests + scorecards, not just the lane run under test.
    manifest_valid = True
    scorecard_valid = True
    for lane_dir in DEMO_LANE_ASSET_DIRS.values():
        manifest = load_manifest(REPO_ROOT / "data" / "golden" / "phase4a" / lane_dir / "manifest.json")
        manifest_valid = manifest_valid and bool(manifest["payload"]["dataset_hash"])
        scorecard = read_json(REPO_ROOT / "data" / "golden" / "phase4a" / lane_dir / "scorecard.json")
        validate_instance(scorecard, REPO_ROOT / "schemas" / "demo_scorecard.schema.json")
        scorecard_valid = scorecard_valid and bool(scorecard["payload"].get("thresholds"))

    validate_instance(run_record["run_config_record"], REPO_ROOT / "schemas" / "run_config_record.schema.json")

    bundle = report_payload["report_bundle"]
    scoring = report_payload["scoring"]
    scorecard = run_record["scorecard"]
    thresholds = scorecard["payload"]["thresholds"]
    success_threshold = float(thresholds.get("success_rate_min", 0.0))
    fallback_threshold = float(thresholds.get("fallback_rate_max", 1.0 - success_threshold))
    latency_budget = float(scorecard["payload"].get("latency_budget_ms", 1e9))

    receipts = receipts_payload["receipts"]
    receipt_schema_valid = True
    for receipt in receipts:
        validate_instance(receipt, REPO_ROOT / "schemas" / "decision_receipt.schema.json")
        if receipt.get("action_selected") not in ALLOWED_POLICY_ACTIONS:
            receipt_schema_valid = False

    outputs = run_record["outputs"]
    structured_valid = all(
        isinstance(item.get("result", {}).get("answer"), str)
        and isinstance(item.get("result", {}).get("routing_label"), str)
        and item.get("result", {}).get("schema_valid") is True
        for item in outputs
    )

    model_profile = run_record["model_profile_record"]["payload"]
    fallback_counters = scoring["fallback_counters"]

    report: dict[str, Any] = {
        "git_commit": _git_commit(),
        "demo_lane_registry_loaded": lane_registry_loaded,
        "model_profile_frozen": profile_frozen(DEFAULT_QWEN_PROFILE)
        and model_profile["model_profile_id"] == DEFAULT_QWEN_PROFILE.model_profile_id,
        "run_config_record_valid": run_record["run_config_record"]["artifact_type"] == "run_config_record",
        "golden_dataset_manifest_valid": manifest_valid,
        "lane_scorecards_valid": scorecard_valid,
        "fallback_semantics_valid": scoring.get("fallback_semantics_valid") is True
        and set(fallback_counters.keys())
        == {"policy_fallback", "model_fallback", "operator_fallback"},
        "replay_trace_deterministic": run_record.get("deterministic_replay") is True,
        "receipt_generation_valid": bool(receipts) and receipt_schema_valid,
        "policy_action_present": all(receipt.get("action_selected") in ALLOWED_POLICY_ACTIONS for receipt in receipts),
        "structured_output_schema_valid": structured_valid,
        "operator_demo_flow_valid": operator_flow_ok,
        "median_latency_within_budget": float(scoring["performance"]["median_latency_ms"]) <= latency_budget,
        "memory_within_budget": float(scoring["performance"]["peak_memory_mb"]) <= 4096.0,
        "success_rate_above_threshold": float(scoring["success_rate"]) >= success_threshold,
        "fallback_rate_within_threshold": float(scoring["fallback_rate"]) <= fallback_threshold,
        "report_bundle_identity_stable": verify_bundle_manifest(bundle),
        "run_id": run_id,
        "lane_id": run_payload["lane_id"],
        "model_profile_id": run_payload["model_profile_id"],
        "success_rate": scoring["success_rate"],
        "fallback_rate": scoring["fallback_rate"],
        "median_latency_ms": scoring["performance"]["median_latency_ms"],
        "peak_memory_mb": scoring["performance"]["peak_memory_mb"],
    }

    report["overall_pass"] = all(
        report[key]
        for key in [
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
    )

    output = REPO_ROOT / "outputs" / "phase4a_gate_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

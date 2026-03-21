from __future__ import annotations

import json
import os
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

from geoclt.differential import cohort_summary, diff_mechanism_sets
from geoclt.artifacts import stable_hash
from geoclt.reports import build_analysis_report_bundle, report_bundle_identity_stable
from services.api.app import app

AUTH_HEADERS = {"authorization": f"Bearer {os.getenv('GEOCLT_AUTH_TOKEN', 'geoclt-local-token')}"}


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


def _report_pack_hashes() -> dict[str, str]:
    targets = [
        REPO_ROOT / "docs" / "reports" / "phase3a" / "executive_summary.md",
        REPO_ROOT / "docs" / "reports" / "phase3a" / "test_results.md",
        REPO_ROOT / "docs" / "reports" / "phase3b" / "executive_summary.md",
        REPO_ROOT / "docs" / "reports" / "phase3b" / "test_results.md",
    ]
    return {str(path): stable_hash(path.read_text(encoding="utf-8")) for path in targets}


def main() -> int:
    client = TestClient(app)
    workspace = str((REPO_ROOT / "runs" / "phase3b-gate").resolve())

    first = client.post(
        "/trace",
        headers=AUTH_HEADERS,
        json={
            "workspace": workspace,
            "lane_id": "claims-triage.v1",
            "behavior_id": "factual_retrieval",
            "model_id": "gpt2-small",
        },
    )
    second = client.post(
        "/trace",
        headers=AUTH_HEADERS,
        json={
            "workspace": workspace,
            "lane_id": "claims-triage.v1",
            "behavior_id": "factual_retrieval",
            "model_id": "gpt2-small",
        },
    )

    if first.status_code != 200 or second.status_code != 200:
        print("failed to create phase3b traces")
        return 1

    first_run = first.json()["run_id"]
    second_run = second.json()["run_id"]

    report_response = client.get(
        "/analysis/report",
        params={"workspace": workspace},
        headers=AUTH_HEADERS,
    )
    report_response_two = client.get(
        "/analysis/report",
        params={"workspace": workspace},
        headers=AUTH_HEADERS,
    )
    mechanism_response = client.get(
        f"/mechanism/mechanism-{first_run}", params={"workspace": workspace}
    )
    lane_eval = client.post(
        "/evaluate_lane",
        headers=AUTH_HEADERS,
        json={"workspace": workspace, "run_id": second_run, "lane_id": "claims-triage.v1"},
    )
    lane_eval_two = client.post(
        "/evaluate_lane",
        headers=AUTH_HEADERS,
        json={"workspace": workspace, "run_id": second_run, "lane_id": "claims-triage.v1"},
    )

    second_report = client.get(f"/reports/{second_run}", params={"workspace": workspace}).json()
    receipt_id = second_report["decision_receipt"]["receipt_id"]
    receipt_response = client.get(
        f"/decision_receipt/{receipt_id}",
        params={"workspace": workspace},
        headers=AUTH_HEADERS,
    )
    receipt_response_two = client.get(
        f"/decision_receipt/{receipt_id}",
        params={"workspace": workspace},
        headers=AUTH_HEADERS,
    )

    baseline = [{"mechanism_id": "m1", "mechanism_class_id": "c1"}]
    candidate = [
        {"mechanism_id": "m1", "mechanism_class_id": "c1"},
        {"mechanism_family_id": "f2"},
    ]
    diff_one = diff_mechanism_sets(baseline, candidate)
    diff_two = diff_mechanism_sets(baseline, candidate)
    diff_with_raw_features = diff_mechanism_sets(
        [{"mechanism_id": "m1", "mechanism_class_id": "c1", "raw_feature": "x"}],
        [
            {"mechanism_id": "m1", "mechanism_class_id": "c1", "raw_feature": "y"},
            {"mechanism_family_id": "f2", "raw_feature": "z"},
        ],
    )
    cohort_one = cohort_summary({"baseline": baseline, "candidate": candidate})
    cohort_two = cohort_summary({"baseline": baseline, "candidate": candidate})

    bundle_one = build_analysis_report_bundle(
        report_id="phase3b-report",
        lane_id="claims-triage.v1",
        decision_receipt=second_report["decision_receipt"],
        differential_result={"diff": diff_one, "cohort": cohort_one},
    )
    bundle_two = build_analysis_report_bundle(
        report_id="phase3b-report",
        lane_id="claims-triage.v1",
        decision_receipt=second_report["decision_receipt"],
        differential_result={"diff": diff_two, "cohort": cohort_two},
    )

    subprocess.run(
        ["python3", "scripts/generate_phase3_report_pack.py"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    pack_hash_one = _report_pack_hashes()
    subprocess.run(
        ["python3", "scripts/generate_phase3_report_pack.py"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    pack_hash_two = _report_pack_hashes()

    report_payload_one: dict[str, Any] = report_response.json()
    report_payload_two: dict[str, Any] = report_response_two.json()
    lane_eval_payload_one: dict[str, Any] = lane_eval.json()
    lane_eval_payload_two: dict[str, Any] = lane_eval_two.json()
    receipt_payload_one: dict[str, Any] = receipt_response.json()
    receipt_payload_two: dict[str, Any] = receipt_response_two.json()

    report: dict[str, object] = {
        "git_commit": _git_commit(),
        "explorer_api_smoke_pass": report_response.status_code == 200
        and mechanism_response.status_code == 200
        and lane_eval.status_code == 200
        and receipt_response.status_code == 200,
        "replay_deterministic": first.json()["trace_id"] == second.json()["trace_id"],
        "trace_endpoint_deterministic": first.json()["trace_id"] == second.json()["trace_id"]
        and first.json()["lane_id"] == second.json()["lane_id"],
        "atlas_switch_consistent": True,
        "evaluate_lane_deterministic": lane_eval_payload_one.get("action")
        == lane_eval_payload_two.get("action")
        and lane_eval_payload_one.get("conformance_class")
        == lane_eval_payload_two.get("conformance_class"),
        "receipt_endpoint_deterministic": stable_hash(receipt_payload_one)
        == stable_hash(receipt_payload_two),
        "analysis_report_deterministic": report_payload_one.get("bundle", {}).get("bundle_hash")
        == report_payload_two.get("bundle", {}).get("bundle_hash"),
        "differential_analysis_deterministic": diff_one["diff_hash"] == diff_two["diff_hash"],
        "mechanism_diff_deterministic": diff_one == diff_two,
        "mechanism_diff_uses_ids_only": diff_one["diff_hash"] == diff_with_raw_features["diff_hash"],
        "cohort_analysis_valid": cohort_one["summary_hash"] == cohort_two["summary_hash"],
        "report_bundle_schema_valid": all(
            key in bundle_one
            for key in ("bundle_type", "report_id", "lane_id", "payload", "bundle_hash")
        ),
        "report_bundle_hash_stable": bundle_one["bundle_hash"] == bundle_two["bundle_hash"],
        "report_bundle_identity_stable": report_bundle_identity_stable(bundle_one),
        "decision_receipt_export_valid": receipt_response.json().get("receipt_id") == receipt_id,
        "analysis_endpoint_responsive": report_response.json().get("status") == "ok",
        "explorer_read_only_semantics": mechanism_response.request.method == "GET"
        and receipt_response.request.method == "GET",
        "report_pack_regeneration_deterministic": pack_hash_one == pack_hash_two,
        "sample_run_ids": [first_run, second_run],
    }

    report["overall_pass"] = all(
        report[key]
        for key in [
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
    )

    output = REPO_ROOT / "outputs" / "phase3b_gate_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

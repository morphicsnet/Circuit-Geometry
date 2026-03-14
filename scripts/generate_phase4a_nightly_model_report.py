from __future__ import annotations

import json
import os
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

from geoclt.artifacts import verify_bundle_manifest
from geoclt.models import DEFAULT_PHI_PROFILE, DEFAULT_QWEN_PROFILE, profile_frozen
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


def _submit(client: TestClient, workspace: str, lane_id: str, profile_id: str) -> dict[str, Any]:
    response = client.post(
        "/demo/submit",
        json={
            "workspace": workspace,
            "lane_id": lane_id,
            "model_profile_id": profile_id,
            "requested_action": "allow",
        },
    )
    if response.status_code != 200:
        raise RuntimeError(f"demo submit failed: {response.status_code} {response.text}")
    return response.json()


def main() -> int:
    client = TestClient(app)
    workspace = str((REPO_ROOT / "runs" / "phase4a-nightly").resolve())
    lane_id = "realworld-claims-triage.v1"

    qwen = _submit(client, workspace, lane_id, DEFAULT_QWEN_PROFILE.model_profile_id)
    phi = _submit(client, workspace, lane_id, DEFAULT_PHI_PROFILE.model_profile_id)

    qwen_report = client.get(f"/demo/report/{qwen['run_id']}", params={"workspace": workspace})
    phi_report = client.get(f"/demo/report/{phi['run_id']}", params={"workspace": workspace})
    if qwen_report.status_code != 200 or phi_report.status_code != 200:
        print("nightly report fetch failed")
        return 1

    qwen_payload = qwen_report.json()
    phi_payload = phi_report.json()
    qwen_score = qwen_payload["scoring"]
    phi_score = phi_payload["scoring"]

    divergence_enabled = os.environ.get("PHASE4_ENABLE_STUB_DIVERGENCE", "1") == "1"
    success_divergence = abs(float(qwen_score["success_rate"]) - float(phi_score["success_rate"]))

    report: dict[str, Any] = {
        "git_commit": _git_commit(),
        "nightly_profiles_valid": profile_frozen(DEFAULT_QWEN_PROFILE)
        and profile_frozen(DEFAULT_PHI_PROFILE),
        "nightly_datasets_valid": all(
            (REPO_ROOT / "data" / "golden" / "phase4a" / name / "manifest.json").exists()
            for name in ("claims", "policy", "intake")
        ),
        "nightly_shared_lane_dual_model_valid": qwen["lane_id"] == phi["lane_id"]
        and qwen["model_profile_id"] != phi["model_profile_id"],
        "nightly_receipt_bundle_valid": bool(qwen["receipt_ids"])
        and bool(phi["receipt_ids"])
        and verify_bundle_manifest(qwen_payload["report_bundle"])
        and verify_bundle_manifest(phi_payload["report_bundle"]),
        "nightly_latency_memory_recorded": all(
            metric > 0
            for metric in [
                qwen_score["performance"]["median_latency_ms"],
                qwen_score["performance"]["peak_memory_mb"],
                phi_score["performance"]["median_latency_ms"],
                phi_score["performance"]["peak_memory_mb"],
            ]
        ),
        "nightly_stub_divergence_within_bounds": (success_divergence <= 0.2)
        if divergence_enabled
        else True,
        "nightly_report_complete": all(
            key in qwen_payload and key in phi_payload
            for key in ["report_bundle", "scoring", "run_hash"]
        ),
        "nightly_divergence_enabled": divergence_enabled,
        "shared_lane_id": lane_id,
        "primary_run_id": qwen["run_id"],
        "challenger_run_id": phi["run_id"],
        "success_rate_primary": qwen_score["success_rate"],
        "success_rate_challenger": phi_score["success_rate"],
    }

    report["overall_pass"] = all(
        report[key]
        for key in [
            "nightly_profiles_valid",
            "nightly_datasets_valid",
            "nightly_shared_lane_dual_model_valid",
            "nightly_receipt_bundle_valid",
            "nightly_latency_memory_recorded",
            "nightly_stub_divergence_within_bounds",
            "nightly_report_complete",
        ]
    )

    output = REPO_ROOT / "outputs" / "phase4a_nightly_model_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

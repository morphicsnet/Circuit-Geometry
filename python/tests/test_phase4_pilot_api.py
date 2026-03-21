from __future__ import annotations

import os

from fastapi.testclient import TestClient

from services.api.app import app

AUTH_HEADERS = {"authorization": f"Bearer {os.getenv('GEOCLT_AUTH_TOKEN', 'geoclt-local-token')}"}


def test_phase4_pilot_flow_and_metrics(tmp_path):
    client = TestClient(app)
    workspace = str(tmp_path / "phase4-pilot")

    demo = client.post(
        "/demo/submit",
        headers=AUTH_HEADERS,
        json={
            "workspace": workspace,
            "lane_id": "realworld-claims-triage.v1",
            "requested_action": "allow",
        },
    )
    assert demo.status_code == 200
    demo_run_id = demo.json()["run_id"]

    submit = client.post(
        "/pilot/submit",
        headers=AUTH_HEADERS,
        json={
            "workspace": workspace,
            "lane_id": "realworld-claims-triage.v1",
            "user_id": "demo-user",
            "task": "claims-triage",
            "corpus": "golden",
            "requested_action": "allow",
            "demo_run_id": demo_run_id,
        },
    )
    assert submit.status_code == 200
    pilot_run_id = submit.json()["pilot_run_id"]

    review = client.post(
        "/pilot/review",
        headers=AUTH_HEADERS,
        json={
            "workspace": workspace,
            "pilot_run_id": pilot_run_id,
            "reviewer_id": "operator-1",
            "task_ref": "task-1",
            "accepted": True,
            "override": False,
            "explanation_usefulness": 0.9,
            "receipt_usefulness": 0.9,
            "escalation_appropriateness": 0.9,
            "confidence_calibration_agreement": 0.9,
        },
    )
    assert review.status_code == 200
    assert review.json()["reviewer_pseudonym"].startswith("reviewer-")

    receipts = client.get(
        f"/pilot/receipt/{pilot_run_id}",
        params={"workspace": workspace},
        headers=AUTH_HEADERS,
    )
    metrics = client.get("/pilot/metrics", params={"workspace": workspace}, headers=AUTH_HEADERS)
    assert receipts.status_code == 200
    assert metrics.status_code == 200

    metrics_payload = metrics.json()
    assert metrics_payload["metrics_bundle"]["artifact_type"] == "pilot_metrics_bundle"
    assert metrics_payload["pilot_run_count"] >= 1


def test_phase4_pilot_scope_rejects_out_of_bounds_request(tmp_path):
    client = TestClient(app)
    workspace = str(tmp_path / "phase4-pilot")

    submit = client.post(
        "/pilot/submit",
        headers=AUTH_HEADERS,
        json={
            "workspace": workspace,
            "lane_id": "realworld-claims-triage.v1",
            "user_id": "unknown-user",
            "task": "claims-triage",
            "corpus": "golden",
            "requested_action": "allow",
        },
    )
    assert submit.status_code == 403

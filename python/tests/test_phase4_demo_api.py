from __future__ import annotations

import os

from fastapi.testclient import TestClient

from services.api.app import app

AUTH_HEADERS = {"authorization": f"Bearer {os.getenv('GEOCLT_AUTH_TOKEN', 'geoclt-local-token')}"}


def test_phase4_demo_submit_report_receipts(tmp_path):
    client = TestClient(app)
    workspace = str(tmp_path / "phase4-demo")

    submit = client.post(
        "/demo/submit",
        headers=AUTH_HEADERS,
        json={
            "workspace": workspace,
            "lane_id": "realworld-claims-triage.v1",
            "requested_action": "allow",
        },
    )
    assert submit.status_code == 200
    payload = submit.json()
    run_id = payload["run_id"]

    report = client.get(
        f"/demo/report/{run_id}",
        params={"workspace": workspace},
        headers=AUTH_HEADERS,
    )
    receipts = client.get(
        f"/demo/receipt/{run_id}",
        params={"workspace": workspace},
        headers=AUTH_HEADERS,
    )
    assert report.status_code == 200
    assert receipts.status_code == 200

    report_payload = report.json()
    receipts_payload = receipts.json()

    assert report_payload["run_id"] == run_id
    assert report_payload["report_bundle"]["bundle_hash"]
    assert receipts_payload["receipt_count"] > 0


def test_phase4_demo_rejects_out_of_contract_action(tmp_path):
    client = TestClient(app)
    workspace = str(tmp_path / "phase4-demo")

    submit = client.post(
        "/demo/submit",
        headers=AUTH_HEADERS,
        json={
            "workspace": workspace,
            "lane_id": "realworld-claims-triage.v1",
            "requested_action": "unsupported-action",
        },
    )
    assert submit.status_code == 400


def test_phase4_demo_replay_deterministic_signal(tmp_path):
    client = TestClient(app)
    workspace = str(tmp_path / "phase4-demo")

    submit = client.post(
        "/demo/submit",
        headers=AUTH_HEADERS,
        json={
            "workspace": workspace,
            "lane_id": "realworld-policy-qa.v1",
            "requested_action": "allow",
        },
    )
    assert submit.status_code == 200
    assert submit.json()["deterministic_replay"] is True

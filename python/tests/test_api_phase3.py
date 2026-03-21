import os

from fastapi.testclient import TestClient

from services.api.app import app

AUTH_HEADERS = {"authorization": f"Bearer {os.getenv('GEOCLT_AUTH_TOKEN', 'geoclt-local-token')}"}


def test_phase3_api_endpoints(tmp_path):
    client = TestClient(app)
    workspace = str(tmp_path / "phase3-api")

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

    assert first.status_code == 200
    assert second.status_code == 200
    run_id = second.json()["run_id"]

    lane_eval = client.post(
        "/evaluate_lane",
        headers=AUTH_HEADERS,
        json={"workspace": workspace, "run_id": run_id, "lane_id": "claims-triage.v1"},
    )
    lane_eval_repeat = client.post(
        "/evaluate_lane",
        headers=AUTH_HEADERS,
        json={"workspace": workspace, "run_id": run_id, "lane_id": "claims-triage.v1"},
    )
    assert lane_eval.status_code == 200
    assert lane_eval_repeat.status_code == 200
    assert lane_eval.json()["action"] == lane_eval_repeat.json()["action"]
    assert (
        lane_eval.json()["conformance_class"]
        == lane_eval_repeat.json()["conformance_class"]
    )

    report = client.get("/analysis/report", params={"workspace": workspace}, headers=AUTH_HEADERS)
    report_repeat = client.get(
        "/analysis/report",
        params={"workspace": workspace},
        headers=AUTH_HEADERS,
    )
    assert report.status_code == 200
    assert report_repeat.status_code == 200
    assert report.json()["status"] == "ok"
    assert report.json()["bundle"]["bundle_hash"] == report_repeat.json()["bundle"]["bundle_hash"]
    assert first.json()["trace_id"] == second.json()["trace_id"]

    run_report = client.get(f"/reports/{run_id}", params={"workspace": workspace}).json()
    receipt_id = run_report["decision_receipt"]["receipt_id"]
    receipt = client.get(
        f"/decision_receipt/{receipt_id}",
        params={"workspace": workspace},
        headers=AUTH_HEADERS,
    )
    receipt_repeat = client.get(
        f"/decision_receipt/{receipt_id}",
        params={"workspace": workspace},
        headers=AUTH_HEADERS,
    )
    assert receipt.status_code == 200
    assert receipt_repeat.status_code == 200
    assert receipt.json()["receipt_hash"] == receipt_repeat.json()["receipt_hash"]

    mechanism = client.get(f"/mechanism/mechanism-{run_id}", params={"workspace": workspace})
    assert mechanism.status_code == 200

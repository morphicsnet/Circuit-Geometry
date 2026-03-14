from fastapi.testclient import TestClient

from services.api.app import app


def test_phase3_api_endpoints(tmp_path):
    client = TestClient(app)
    workspace = str(tmp_path / "phase3-api")

    first = client.post(
        "/trace",
        json={
            "workspace": workspace,
            "lane_id": "claims-triage.v1",
            "behavior_id": "factual_retrieval",
            "model_id": "gpt2-small",
        },
    )
    second = client.post(
        "/trace",
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
        json={"workspace": workspace, "run_id": run_id, "lane_id": "claims-triage.v1"},
    )
    assert lane_eval.status_code == 200

    report = client.get("/analysis/report", params={"workspace": workspace})
    assert report.status_code == 200
    assert report.json()["status"] == "ok"

    run_report = client.get(f"/reports/{run_id}", params={"workspace": workspace}).json()
    receipt_id = run_report["decision_receipt"]["receipt_id"]
    receipt = client.get(f"/decision_receipt/{receipt_id}", params={"workspace": workspace})
    assert receipt.status_code == 200

    mechanism = client.get(f"/mechanism/mechanism-{run_id}", params={"workspace": workspace})
    assert mechanism.status_code == 200

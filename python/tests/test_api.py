from fastapi.testclient import TestClient

from services.api.app import app


def test_api_run_and_export(tmp_path):
    client = TestClient(app)
    workspace = str(tmp_path / "api-workspace")

    create_response = client.post(
        "/runs",
        json={
            "workspace": workspace,
            "lane_id": "factual_retrieval.v1",
            "behavior_id": "factual_retrieval",
            "model_id": "gpt2-small",
        },
    )
    assert create_response.status_code == 200
    run = create_response.json()
    run_id = run["run_id"]

    create_response_two = client.post(
        "/runs",
        json={
            "workspace": workspace,
            "lane_id": "factual_retrieval.v1",
            "behavior_id": "factual_retrieval",
            "model_id": "gpt2-small",
        },
    )
    assert create_response_two.status_code == 200

    list_response = client.get("/runs", params={"workspace": workspace})
    assert list_response.status_code == 200
    assert any(item["run_id"] == run_id for item in list_response.json()["runs"])

    run_response = client.get(f"/runs/{run_id}", params={"workspace": workspace})
    assert run_response.status_code == 200
    assert run_response.json()["run"]["run_id"] == run_id

    determinism_response = client.get(
        f"/runs/{run_id}/determinism", params={"workspace": workspace}
    )
    assert determinism_response.status_code == 200
    assert determinism_response.json()["is_deterministic"] is True

    export_response = client.post(f"/runs/{run_id}/export", params={"workspace": workspace})
    assert export_response.status_code == 200
    assert export_response.json()["status"] == "ok"

    report_response = client.get(f"/reports/{run_id}", params={"workspace": workspace})
    assert report_response.status_code == 200
    assert report_response.json()["run"]["run_id"] == run_id


def test_api_missing_run_returns_404(tmp_path):
    client = TestClient(app)
    workspace = str(tmp_path / "api-workspace")

    response = client.get("/runs/missing-run", params={"workspace": workspace})
    assert response.status_code == 404


def test_api_missing_report_and_export_failures(tmp_path):
    client = TestClient(app)
    workspace = str(tmp_path / "api-workspace")

    missing_report = client.get("/reports/missing-run", params={"workspace": workspace})
    assert missing_report.status_code == 404

    missing_export = client.post("/runs/missing-run/export", params={"workspace": workspace})
    assert missing_export.status_code == 404


def test_api_determinism_endpoint_consistency(tmp_path):
    client = TestClient(app)
    workspace = str(tmp_path / "api-workspace")

    run_one = client.post(
        "/runs",
        json={
            "workspace": workspace,
            "lane_id": "factual_retrieval.v1",
            "behavior_id": "factual_retrieval",
            "model_id": "gpt2-small",
        },
    ).json()
    run_two = client.post(
        "/runs",
        json={
            "workspace": workspace,
            "lane_id": "factual_retrieval.v1",
            "behavior_id": "factual_retrieval",
            "model_id": "gpt2-small",
        },
    ).json()

    det_one = client.get(
        f"/runs/{run_one['run_id']}/determinism", params={"workspace": workspace}
    ).json()
    det_two = client.get(
        f"/runs/{run_two['run_id']}/determinism", params={"workspace": workspace}
    ).json()

    assert det_one["is_deterministic"] is True
    assert det_two["is_deterministic"] is True
    assert det_one["input_signature"] == det_two["input_signature"]

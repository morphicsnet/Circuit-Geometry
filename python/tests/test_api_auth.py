from __future__ import annotations

from fastapi.testclient import TestClient

from services.api.app import app


def test_demo_endpoint_requires_token(tmp_path):
    client = TestClient(app)
    workspace = str(tmp_path / "auth-demo")
    response = client.post(
        "/demo/submit",
        json={
            "workspace": workspace,
            "lane_id": "realworld-claims-triage.v1",
            "requested_action": "allow",
        },
    )
    assert response.status_code == 401


def test_demo_endpoint_rejects_invalid_token(tmp_path):
    client = TestClient(app)
    workspace = str(tmp_path / "auth-demo")
    response = client.post(
        "/demo/submit",
        headers={"authorization": "Bearer invalid-token"},
        json={
            "workspace": workspace,
            "lane_id": "realworld-claims-triage.v1",
            "requested_action": "allow",
        },
    )
    assert response.status_code == 401


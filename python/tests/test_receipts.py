import pytest

from geoclt.receipts import emit_decision_receipt, persist_receipt


def test_receipt_smoke():
    out = emit_decision_receipt()
    assert out["status"] == "ok"
    assert out["receipt_hash"] == out["content_hash"]
    assert out["action_selected"] in {
        "allow",
        "allow_with_review",
        "route_to_fallback",
        "block",
        "escalate",
    }


def test_receipt_auth_identity_and_signature(monkeypatch):
    monkeypatch.setenv("GEOCLT_BUNDLE_SIGNING", "hmac")
    monkeypatch.setenv("GEOCLT_BUNDLE_SIGNING_SECRET", "test-secret")
    out = emit_decision_receipt(
        run_id="run-auth",
        caller_id="token-authenticated",
        auth_policy_version="auth.v1",
        auth_result="passed",
    )
    assert out["caller_id"] == "token-authenticated"
    assert out["auth_policy_version"] == "auth.v1"
    assert out["auth_result"] == "passed"
    assert out["signing_mode"] == "hmac"
    assert out["signature_verified"] is True
    assert isinstance(out["signature"], str) and len(out["signature"]) == 64


def test_receipt_persistence_is_immutable(tmp_path):
    receipt = emit_decision_receipt(run_id="run-immutable")
    target = tmp_path / "receipt.json"
    first = persist_receipt(target, receipt)
    assert first["immutable"] is True

    second = persist_receipt(target, receipt)
    assert second["idempotent"] is True

    mutated = dict(receipt)
    mutated["decision"] = "block"
    with pytest.raises(ValueError):
        persist_receipt(target, mutated)

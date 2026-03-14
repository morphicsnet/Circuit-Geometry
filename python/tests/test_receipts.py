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

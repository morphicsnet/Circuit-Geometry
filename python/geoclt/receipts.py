from __future__ import annotations

from datetime import UTC, datetime
import hmac
from hashlib import sha256
import os
from pathlib import Path
from typing import Any

from .artifacts import content_hash, derive_artifact_id, read_json, write_json, stable_hash


def _hash_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def canonical_receipt_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "receipt_id": payload["receipt_id"],
        "trace_id": payload["trace_id"],
        "model_id": payload["model_id"],
        "lane_id": payload["lane_id"],
        "policy_version": payload["policy_version"],
        "evaluated_claims": sorted(payload["evaluated_claims"]),
        "artifact_inputs": sorted(payload["artifact_inputs"], key=lambda item: item["artifact_id"]),
        "mechanism_classes_used": sorted(payload["mechanism_classes_used"]),
        "evaluation_results": payload["evaluation_results"],
        "thresholds_applied": payload["thresholds_applied"],
        "falsifiers_checked": sorted(payload["falsifiers_checked"]),
        "action_selected": payload["action_selected"],
        "fallback_selected": payload["fallback_selected"],
        "bundle_hash": payload["bundle_hash"],
        "producer": payload["producer"],
        "caller_id": payload.get("caller_id"),
        "auth_policy_version": payload.get("auth_policy_version"),
        "auth_result": payload.get("auth_result"),
    }


def compute_receipt_hash(payload: dict[str, Any]) -> str:
    return stable_hash(canonical_receipt_payload(payload))


def _signing_mode() -> str:
    return os.getenv("GEOCLT_BUNDLE_SIGNING", "off").strip().lower()


def _signing_secret() -> str:
    return os.getenv("GEOCLT_BUNDLE_SIGNING_SECRET", "geoclt-signing-secret")


def _hmac_signature(value: str) -> str:
    digest = hmac.new(_signing_secret().encode("utf-8"), value.encode("utf-8"), sha256)
    return digest.hexdigest()


def persist_receipt(path: str | Path, receipt: dict[str, Any]) -> dict[str, Any]:
    target = Path(path)
    if target.exists():
        existing = read_json(target)
        if existing != receipt:
            raise ValueError(f"receipt already exists and is immutable: {target}")
        return {"status": "ok", "path": str(target), "immutable": True, "idempotent": True}

    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, receipt)
    return {"status": "ok", "path": str(target), "immutable": True, "idempotent": False}


def emit_decision_receipt(
    *,
    run_id: str = "run-default",
    trace_id: str | None = None,
    model_id: str = "gpt2-small",
    lane_id: str = "claims-triage.v1",
    decision: str = "allow_with_review",
    action_selected: str | None = None,
    policy_version: str = "policy.v1",
    evaluated_claims: list[str] | None = None,
    artifact_inputs: list[dict[str, str]] | None = None,
    mechanism_classes_used: list[str] | None = None,
    thresholds_applied: dict[str, float] | None = None,
    falsifiers_checked: list[str] | None = None,
    fallback_selected: str | None = None,
    bundle_hash: str | None = None,
    caller_id: str | None = None,
    auth_policy_version: str = "auth.v1",
    auth_result: str = "passed",
    active_mechanism_class_ids: list[str] | None = None,
    provisional_mechanism_class_ids: list[str] | None = None,
    policy_clauses_triggered: list[str] | None = None,
    geometry_anomaly_flags: list[str] | None = None,
    chart_instability_flags: list[str] | None = None,
) -> dict[str, Any]:
    trace = trace_id or run_id
    action = action_selected or decision

    payload_core = {
        "receipt_id": f"receipt-{run_id}",
        "trace_id": trace,
        "model_id": model_id,
        "lane_id": lane_id,
        "policy_version": policy_version,
        "evaluated_claims": evaluated_claims or [],
        "artifact_inputs": artifact_inputs or [],
        "mechanism_classes_used": mechanism_classes_used or [],
        "evaluation_results": {"decision": decision},
        "thresholds_applied": thresholds_applied or {},
        "falsifiers_checked": falsifiers_checked or [],
        "action_selected": action,
        "fallback_selected": fallback_selected,
        "bundle_hash": bundle_hash or _hash_text(f"{run_id}:bundle"),
        "producer": "geoclt:runtime:0.3.0",
        "caller_id": caller_id,
        "auth_policy_version": auth_policy_version,
        "auth_result": auth_result,
    }

    receipt_hash = compute_receipt_hash(payload_core)
    full_payload = {
        "status": "ok",
        "artifact_id": derive_artifact_id("decision_receipt", 2, receipt_hash),
        "artifact_type": "decision_receipt",
        "schema_version": 2,
        "producer": payload_core["producer"],
        "trace_id": trace,
        "run_id": run_id,
        "content_hash": receipt_hash,
        "created_at": datetime.now(UTC).isoformat(),
        "receipt_hash": receipt_hash,
        "receipt_id": payload_core["receipt_id"],
        "model_id": payload_core["model_id"],
        "lane_id": payload_core["lane_id"],
        "input_hash": _hash_text(f"{run_id}:input"),
        "output_hash": _hash_text(f"{run_id}:output"),
        "active_mechanism_class_ids": sorted(active_mechanism_class_ids or []),
        "provisional_mechanism_class_ids": sorted(provisional_mechanism_class_ids or []),
        "policy_clauses_triggered": sorted(policy_clauses_triggered or []),
        "geometry_anomaly_flags": sorted(geometry_anomaly_flags or []),
        "chart_instability_flags": sorted(chart_instability_flags or []),
        "decision": decision,
        "policy_version": payload_core["policy_version"],
        "evaluated_claims": payload_core["evaluated_claims"],
        "thresholds_applied": payload_core["thresholds_applied"],
        "falsifiers_checked": payload_core["falsifiers_checked"],
        "fallback_selected": payload_core["fallback_selected"],
        "immutable_bundle_hash": payload_core["bundle_hash"],
        "artifact_inputs": payload_core["artifact_inputs"],
        "mechanism_classes_used": payload_core["mechanism_classes_used"],
        "evaluation_results": payload_core["evaluation_results"],
        "action_selected": payload_core["action_selected"],
        "caller_id": payload_core["caller_id"],
        "auth_policy_version": payload_core["auth_policy_version"],
        "auth_result": payload_core["auth_result"],
    }
    if _signing_mode() == "hmac":
        full_payload["signature"] = _hmac_signature(receipt_hash)
        full_payload["signature_verified"] = True
        full_payload["signing_mode"] = "hmac"
    else:
        full_payload["signature"] = None
        full_payload["signature_verified"] = False
        full_payload["signing_mode"] = "off"
    return full_payload

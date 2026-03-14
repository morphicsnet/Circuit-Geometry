from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from ..artifacts import build_artifact_entry
from ..artifacts import validate_instance


def _schema_path(filename: str) -> Path:
    return Path(__file__).resolve().parents[3] / "schemas" / filename


def pseudonymous_reviewer_id(raw_reviewer_id: str, identity_key_id: str, salt: str) -> str:
    digest = sha256(f"{identity_key_id}:{salt}:{raw_reviewer_id}".encode("utf-8")).hexdigest()
    return f"reviewer-{digest[:16]}"


def pseudonymous_reviewer_id_from_scope(
    raw_reviewer_id: str, scope_policy_record: dict[str, Any], salt: str
) -> str:
    return pseudonymous_reviewer_id(
        raw_reviewer_id,
        scope_policy_record["payload"]["identity_key_id"],
        salt,
    )


def build_operator_review_record(
    *,
    raw_reviewer_id: str,
    identity_key_id: str,
    salt: str,
    task_ref: str,
    accepted: bool,
    override: bool,
    explanation_usefulness: float,
    receipt_usefulness: float,
    escalation_appropriateness: float,
    confidence_calibration_agreement: float,
    trace_id: str,
    run_id: str,
) -> dict[str, Any]:
    payload = {
        "review_record_id": f"review-{run_id}-{task_ref}",
        "reviewer_pseudonym": pseudonymous_reviewer_id(raw_reviewer_id, identity_key_id, salt),
        "identity_key_id": identity_key_id,
        "task_ref": task_ref,
        "accepted": accepted,
        "override": override,
        "explanation_usefulness": explanation_usefulness,
        "receipt_usefulness": receipt_usefulness,
        "escalation_appropriateness": escalation_appropriateness,
        "confidence_calibration_agreement": confidence_calibration_agreement,
    }
    record = build_artifact_entry(
        artifact_type="operator_review_record",
        schema_version=1,
        producer="geoclt:pilot:0.4.0",
        trace_id=trace_id,
        run_id=run_id,
        payload=payload,
        created_at="2026-01-01T00:00:00Z",
    )
    validate_instance(record, _schema_path("operator_review_record.schema.json"))
    return record

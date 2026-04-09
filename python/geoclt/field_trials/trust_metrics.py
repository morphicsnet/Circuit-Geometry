from __future__ import annotations

from typing import Any

from .._paths import schema_path
from ..artifacts import build_artifact_entry, validate_instance


def compute_trust_metrics(review_records: list[dict[str, Any]]) -> dict[str, float]:
    if not review_records:
        return {
            "reviewer_acceptance_rate": 0.0,
            "reviewer_override_rate": 0.0,
            "explanation_usefulness_score": 0.0,
            "receipt_usefulness_score": 0.0,
            "escalation_appropriateness_rate": 0.0,
            "confidence_calibration_agreement": 0.0,
        }

    payloads = [record["payload"] if "payload" in record else record for record in review_records]
    total = len(payloads)
    return {
        "reviewer_acceptance_rate": sum(1 for row in payloads if row["accepted"]) / total,
        "reviewer_override_rate": sum(1 for row in payloads if row["override"]) / total,
        "explanation_usefulness_score": sum(row["explanation_usefulness"] for row in payloads) / total,
        "receipt_usefulness_score": sum(row["receipt_usefulness"] for row in payloads) / total,
        "escalation_appropriateness_rate": sum(
            row["escalation_appropriateness"] for row in payloads
        )
        / total,
        "confidence_calibration_agreement": sum(
            row["confidence_calibration_agreement"] for row in payloads
        )
        / total,
    }


def build_pilot_metrics_bundle(
    *,
    pilot_scope_ref: str,
    window_id: str,
    false_allow_rate: float,
    false_block_rate: float,
    routing_quality: float,
    trust_metrics: dict[str, float],
    drift_summary: dict[str, Any],
    trace_id: str,
    run_id: str,
) -> dict[str, Any]:
    bundle = build_artifact_entry(
        artifact_type="pilot_metrics_bundle",
        schema_version=1,
        producer="geoclt:pilot:0.4.0",
        trace_id=trace_id,
        run_id=run_id,
        payload={
            "pilot_scope_ref": pilot_scope_ref,
            "window_id": window_id,
            "false_allow_rate": false_allow_rate,
            "false_block_rate": false_block_rate,
            "routing_quality": routing_quality,
            "trust_metrics": trust_metrics,
            "drift_summary": drift_summary,
        },
        created_at="2026-01-01T00:00:00Z",
    )
    validate_instance(bundle, schema_path("pilot_metrics_bundle.schema.json"))
    return bundle

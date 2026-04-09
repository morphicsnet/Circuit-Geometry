from __future__ import annotations

from typing import Any

from .._paths import schema_path
from ..artifacts import build_artifact_entry, validate_instance


_ALLOWED_FALLBACK_TYPES = {"policy_fallback", "model_fallback", "operator_fallback"}

def build_scorecard(
    *,
    lane_id: str,
    success_condition: str,
    acceptable_fallback_condition: str,
    failure_condition: str,
    latency_budget_ms: float,
    escalation_rules: list[str],
    thresholds: dict[str, float],
    trace_id: str,
    run_id: str,
) -> dict[str, Any]:
    payload = {
        "lane_id": lane_id,
        "success_condition": success_condition,
        "acceptable_fallback_condition": acceptable_fallback_condition,
        "failure_condition": failure_condition,
        "latency_budget_ms": latency_budget_ms,
        "escalation_rules": escalation_rules,
        "thresholds": thresholds,
    }
    scorecard = build_artifact_entry(
        artifact_type="demo_scorecard",
        schema_version=1,
        producer="geoclt:demo:0.4.0",
        trace_id=trace_id,
        run_id=run_id,
        payload=payload,
        created_at="2026-01-01T00:00:00Z",
    )
    validate_instance(scorecard, schema_path("demo_scorecard.schema.json"))
    return scorecard


def validate_fallback_semantics(counters: dict[str, int]) -> bool:
    return set(counters.keys()) == _ALLOWED_FALLBACK_TYPES and all(
        isinstance(value, int) and value >= 0 for value in counters.values()
    )


def classify_result(result: dict[str, Any], scorecard: dict[str, Any]) -> str:
    thresholds = scorecard["payload"]["thresholds"]
    if result.get("schema_valid") is not True:
        return "failure"
    if result.get("confidence", 0.0) >= thresholds.get("success_confidence_min", 0.5) and result.get(
        "evidence_alignment", 0.0
    ) >= thresholds.get("evidence_alignment_min", 0.5):
        return "success"
    if result.get("routing_label") in {"allow_with_review", "route_to_fallback"}:
        return "fallback"
    return "failure"

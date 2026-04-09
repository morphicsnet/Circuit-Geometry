from __future__ import annotations

from typing import Any

from .._paths import schema_path
from ..artifacts import build_artifact_entry, validate_instance


def build_pilot_run_record(
    *,
    pilot_scope_ref: str,
    lane_id: str,
    demo_run_ref: str,
    review_status: str,
    policy_routing_outcome: str,
    adjudication_outcome: str,
    trace_id: str,
    run_id: str,
) -> dict[str, Any]:
    record = build_artifact_entry(
        artifact_type="pilot_run_record",
        schema_version=1,
        producer="geoclt:pilot:0.4.0",
        trace_id=trace_id,
        run_id=run_id,
        payload={
            "pilot_scope_ref": pilot_scope_ref,
            "lane_id": lane_id,
            "demo_run_ref": demo_run_ref,
            "review_status": review_status,
            "policy_routing_outcome": policy_routing_outcome,
            "adjudication_outcome": adjudication_outcome,
        },
        created_at="2026-01-01T00:00:00Z",
    )
    validate_instance(record, schema_path("pilot_run_record.schema.json"))
    return record


def run_cohort(pilot_scope_ref: str, lane_id: str, demo_run_refs: list[str]) -> dict[str, Any]:
    return {
        "pilot_scope_ref": pilot_scope_ref,
        "lane_id": lane_id,
        "demo_run_refs": sorted(demo_run_refs),
        "cohort_size": len(demo_run_refs),
    }

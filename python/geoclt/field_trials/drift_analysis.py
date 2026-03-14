from __future__ import annotations

from typing import Any

from ..artifacts import build_artifact_entry


def compute_drift_metric(baseline: dict[str, int], current: dict[str, int]) -> float:
    keys = sorted(set(baseline) | set(current))
    total = sum(abs(current.get(key, 0) - baseline.get(key, 0)) for key in keys)
    denom = max(1, sum(baseline.values()))
    return total / denom


def build_drift_alert_record(
    *,
    cohort_ref: str,
    mechanism_family_id: str,
    drift_metric: float,
    threshold: float,
    supporting_refs: list[str],
    trace_id: str,
    run_id: str,
) -> dict[str, Any]:
    payload = {
        "cohort_ref": cohort_ref,
        "mechanism_family_id": mechanism_family_id,
        "drift_metric": drift_metric,
        "threshold": threshold,
        "alert_status": "alert" if drift_metric > threshold else "ok",
        "supporting_refs": sorted(supporting_refs),
    }
    return build_artifact_entry(
        artifact_type="drift_alert_record",
        schema_version=1,
        producer="geoclt:pilot:0.4.0",
        trace_id=trace_id,
        run_id=run_id,
        payload=payload,
        created_at="2026-01-01T00:00:00Z",
    )

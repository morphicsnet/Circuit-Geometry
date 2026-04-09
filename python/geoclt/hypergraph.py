from __future__ import annotations

from typing import Any

from ._kernel_math import (
    materialize_hyperpaths as _materialize_hyperpaths_fallback,
    propose_events as _propose_events_fallback,
)
from ._native import call_json_function


def propose_events(
    lane_id: str,
    behavior_id: str,
    transport: dict[str, Any],
    feature_hints: list[str] | None = None,
) -> dict[str, Any]:
    payload = {
        "lane_id": lane_id,
        "behavior_id": behavior_id,
        "transport": transport,
        "feature_hints": feature_hints or [],
    }
    native = call_json_function("propose_events_json", payload)
    if native is not None:
        return native
    return _propose_events_fallback(**payload)


def materialize_hyperpaths(
    lane_id: str,
    behavior_id: str,
    candidate_event_table: dict[str, Any],
    atlas: dict[str, Any],
    transport: dict[str, Any],
    intervention_faithfulness: float,
    synergy_score_max: float,
    chart_stability: float,
    geodesic_deviation: float,
) -> dict[str, Any]:
    payload = {
        "lane_id": lane_id,
        "behavior_id": behavior_id,
        "candidate_event_table": candidate_event_table,
        "atlas": atlas,
        "transport": transport,
        "intervention_faithfulness": intervention_faithfulness,
        "synergy_score_max": synergy_score_max,
        "chart_stability": chart_stability,
        "geodesic_deviation": geodesic_deviation,
    }
    native = call_json_function("materialize_hyperpaths_json", payload)
    if native is not None:
        return native
    return _materialize_hyperpaths_fallback(**payload)

from __future__ import annotations

from typing import Any

from .scorecards import classify_result, validate_fallback_semantics


def score_items(item_outputs: list[dict[str, Any]], scorecard: dict[str, Any]) -> dict[str, Any]:
    counts = {"success": 0, "fallback": 0, "failure": 0}
    fallback_counters = {"policy_fallback": 0, "model_fallback": 0, "operator_fallback": 0}
    latencies: list[float] = []
    memories: list[float] = []

    for output in item_outputs:
        status = classify_result(output["result"], scorecard)
        counts[status] += 1
        fallback_type = output.get("fallback_type")
        if fallback_type in fallback_counters:
            fallback_counters[fallback_type] += 1
        latencies.append(float(output["runtime"]["latency_ms"]))
        memories.append(float(output["runtime"]["memory_mb"]))

    total = max(1, len(item_outputs))
    success_rate = counts["success"] / total
    fallback_rate = counts["fallback"] / total
    failure_rate = counts["failure"] / total

    performance = {
        "median_latency_ms": sorted(latencies)[len(latencies) // 2] if latencies else 0.0,
        "peak_memory_mb": max(memories) if memories else 0.0,
    }

    return {
        "counts": counts,
        "success_rate": success_rate,
        "fallback_rate": fallback_rate,
        "failure_rate": failure_rate,
        "fallback_counters": fallback_counters,
        "fallback_semantics_valid": validate_fallback_semantics(fallback_counters),
        "performance": performance,
    }

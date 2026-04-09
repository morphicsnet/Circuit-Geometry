from __future__ import annotations

from typing import Any

from ._kernel_math import estimate_pullback_metric as _metric_fallback
from ._native import call_json_function


def estimate_pullback_metric(
    lane_id: str,
    atlas: dict[str, Any],
    feature_hints: list[str] | None = None,
) -> dict[str, Any]:
    payload = {
        "lane_id": lane_id,
        "atlas": atlas,
        "feature_hints": feature_hints or [],
    }
    native = call_json_function("estimate_pullback_metric_json", payload)
    if native is not None:
        return native
    return _metric_fallback(**payload)

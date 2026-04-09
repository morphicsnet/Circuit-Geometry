from __future__ import annotations

from typing import Any

from ._kernel_math import fit_transport as _transport_fallback
from ._native import call_json_function


def fit_transport(lane_id: str, atlas: dict[str, Any], metric: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "lane_id": lane_id,
        "atlas": atlas,
        "metric": metric,
    }
    native = call_json_function("fit_transport_json", payload)
    if native is not None:
        return native
    return _transport_fallback(**payload)

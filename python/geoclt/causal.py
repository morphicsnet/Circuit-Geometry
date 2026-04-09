from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from ._kernel_math import verify_mechanisms as _verify_mechanisms_fallback
from ._native import call_json_function


def verify_mechanisms(
    lane: Any,
    hyperpaths: dict[str, Any],
) -> dict[str, Any]:
    lane_payload = asdict(lane) if is_dataclass(lane) else dict(lane)
    payload = {
        "lane": lane_payload,
        "hyperpaths": hyperpaths,
    }
    native = call_json_function("verify_mechanisms_json", payload)
    if native is not None:
        return native
    return _verify_mechanisms_fallback(**payload)

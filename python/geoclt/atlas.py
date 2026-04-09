from __future__ import annotations

from typing import Any

from ._kernel_math import fit_atlas as _fit_atlas_fallback
from ._native import call_json_function


def fit_atlas(
    model_id: str = "gpt2-small",
    lane_id: str = "atlas",
    profile: str = "default",
    feature_hints: list[str] | None = None,
) -> dict[str, Any]:
    payload = {
        "model_id": model_id,
        "lane_id": lane_id,
        "profile": profile,
        "feature_hints": feature_hints or [],
    }
    native = call_json_function("fit_atlas_json", payload)
    if native is not None:
        return native
    return _fit_atlas_fallback(**payload)

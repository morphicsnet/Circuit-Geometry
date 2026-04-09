from __future__ import annotations

import json
from typing import Any

try:  # pragma: no cover - exercised when the extension is available
    from . import geoclt_native as _native
except Exception:  # pragma: no cover - pure-Python fallback path
    _native = None


def native_available() -> bool:
    return _native is not None


def call_json_function(name: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    if _native is None:
        return None
    fn = getattr(_native, name, None)
    if fn is None:
        return None
    return json.loads(fn(json.dumps(payload, sort_keys=True)))


def call_workspace_kernels(payload: dict[str, Any]) -> dict[str, Any] | None:
    return call_json_function("run_workspace_kernels_json", payload)


def call_workspace_bundle(payload: dict[str, Any]) -> dict[str, Any] | None:
    return call_json_function("run_workspace_bundle_json", payload)

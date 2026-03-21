from __future__ import annotations

from typing import Iterable


def summarize_series(values: Iterable[float]) -> dict[str, float]:
    series = [float(value) for value in values]
    if not series:
        return {"count": 0.0, "min": 0.0, "max": 0.0, "mean": 0.0}
    total = sum(series)
    return {
        "count": float(len(series)),
        "min": min(series),
        "max": max(series),
        "mean": total / len(series),
    }

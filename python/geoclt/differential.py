from __future__ import annotations

from collections import Counter
from typing import Any

from .artifacts import stable_hash


ALLOWED_ID_KEYS = ("mechanism_id", "mechanism_class_id", "mechanism_family_id")


def _extract_ids(records: list[dict[str, Any]]) -> list[str]:
    ids: list[str] = []
    for record in records:
        for key in ALLOWED_ID_KEYS:
            value = record.get(key)
            if isinstance(value, str) and value:
                ids.append(f"{key}:{value}")
    return sorted(ids)


def diff_mechanism_sets(
    baseline: list[dict[str, Any]],
    candidate: list[dict[str, Any]],
) -> dict[str, Any]:
    baseline_ids = _extract_ids(baseline)
    candidate_ids = _extract_ids(candidate)

    baseline_counter = Counter(baseline_ids)
    candidate_counter = Counter(candidate_ids)

    added = sorted((candidate_counter - baseline_counter).elements())
    removed = sorted((baseline_counter - candidate_counter).elements())
    shared = sorted((baseline_counter & candidate_counter).elements())

    payload = {
        "added": added,
        "removed": removed,
        "shared": shared,
        "baseline_count": len(baseline_ids),
        "candidate_count": len(candidate_ids),
    }
    payload["diff_hash"] = stable_hash(payload)
    return payload


def cohort_summary(cohorts: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    frequency: dict[str, dict[str, int]] = {}
    for cohort_name, records in sorted(cohorts.items()):
        counter = Counter(_extract_ids(records))
        frequency[cohort_name] = dict(sorted(counter.items()))

    summary = {
        "cohort_count": len(cohorts),
        "mechanism_frequency": frequency,
    }
    summary["summary_hash"] = stable_hash(summary)
    return summary

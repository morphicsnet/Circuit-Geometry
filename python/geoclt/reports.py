from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifacts import stable_hash, write_json


def build_analysis_report_bundle(
    *,
    report_id: str,
    lane_id: str,
    decision_receipt: dict[str, Any],
    differential_result: dict[str, Any],
    created_at: str = "2026-01-01T00:00:00Z",
) -> dict[str, Any]:
    payload = {
        "report_id": report_id,
        "lane_id": lane_id,
        "decision_receipt": decision_receipt,
        "differential_result": differential_result,
    }
    report_hash = stable_hash(payload)
    bundle = {
        "bundle_type": "analysis_report_bundle",
        "report_id": report_id,
        "lane_id": lane_id,
        "created_at": created_at,
        "payload": payload,
        "report_hash": report_hash,
    }
    bundle["bundle_hash"] = stable_hash({k: v for k, v in bundle.items() if k != "bundle_hash"})
    return bundle


def export_analysis_report_bundle(bundle: dict[str, Any], path: str | Path) -> dict[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, bundle)
    return {
        "status": "ok",
        "path": str(target.resolve()),
        "bundle_hash": bundle["bundle_hash"],
    }


def report_bundle_identity_stable(bundle: dict[str, Any]) -> bool:
    expected = stable_hash({k: v for k, v in bundle.items() if k != "bundle_hash"})
    return expected == bundle.get("bundle_hash")

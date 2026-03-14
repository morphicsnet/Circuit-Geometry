from __future__ import annotations

from pathlib import Path
from typing import Any

from ..artifacts import build_artifact_entry, read_json, stable_hash, validate_instance


def _schema_path(filename: str) -> Path:
    return Path(__file__).resolve().parents[3] / "schemas" / filename


def compute_dataset_hash(items: list[dict[str, Any]]) -> str:
    canonical_items = sorted(items, key=lambda item: item["item_id"])
    return stable_hash(canonical_items)


def build_manifest(
    *,
    dataset_id: str,
    dataset_version: str,
    lane_id: str,
    items: list[dict[str, Any]],
    provenance: dict[str, Any],
    expected_schema: dict[str, Any],
    labels: list[str],
    ambiguity_flags: list[str],
    trace_id: str,
    run_id: str,
) -> dict[str, Any]:
    payload = {
        "dataset_id": dataset_id,
        "dataset_version": dataset_version,
        "lane_id": lane_id,
        "items": items,
        "provenance": provenance,
        "expected_schema": expected_schema,
        "labels": labels,
        "ambiguity_flags": ambiguity_flags,
        "dataset_hash": compute_dataset_hash(items),
    }
    manifest = build_artifact_entry(
        artifact_type="golden_dataset_manifest",
        schema_version=1,
        producer="geoclt:demo:0.4.0",
        trace_id=trace_id,
        run_id=run_id,
        payload=payload,
        created_at="2026-01-01T00:00:00Z",
    )
    validate_instance(manifest, _schema_path("golden_dataset_manifest.schema.json"))
    return manifest


def load_manifest(path: str | Path) -> dict[str, Any]:
    manifest = read_json(path)
    validate_instance(manifest, _schema_path("golden_dataset_manifest.schema.json"))
    payload = manifest["payload"]
    expected_hash = compute_dataset_hash(payload["items"])
    if expected_hash != payload["dataset_hash"]:
        raise ValueError("dataset hash mismatch")
    return manifest


def freeze_gate_input_set(manifest: dict[str, Any]) -> list[str]:
    item_ids = [item["item_id"] for item in manifest["payload"]["items"]]
    return sorted(item_ids)

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..artifacts import build_artifact_entry, build_artifact_bundle, stable_hash, validate_instance
from ..receipts import emit_decision_receipt
from .scoring import score_items


def _schema_path(filename: str) -> Path:
    return Path(__file__).resolve().parents[3] / "schemas" / filename


def build_run_config_record(
    *,
    lane_id: str,
    model_profile_ref: str,
    dataset_manifest_ref: str,
    scorecard_ref: str,
    runtime_flags: dict[str, Any],
    fallback_config: dict[str, Any],
    replay_mode: str,
    seed_policy: str,
    trace_id: str,
    run_id: str,
) -> dict[str, Any]:
    record = build_artifact_entry(
        artifact_type="run_config_record",
        schema_version=1,
        producer="geoclt:demo:0.4.0",
        trace_id=trace_id,
        run_id=run_id,
        payload={
            "lane_id": lane_id,
            "model_profile_ref": model_profile_ref,
            "dataset_manifest_ref": dataset_manifest_ref,
            "scorecard_ref": scorecard_ref,
            "runtime_flags": runtime_flags,
            "fallback_config": fallback_config,
            "replay_mode": replay_mode,
            "seed_policy": seed_policy,
        },
        created_at="2026-01-01T00:00:00Z",
    )
    validate_instance(record, _schema_path("run_config_record.schema.json"))
    return record


def run_demo_lane(
    *,
    lane_id: str,
    model_runner: Any,
    dataset_manifest: dict[str, Any],
    run_config: dict[str, Any],
    scorecard: dict[str, Any],
    trace_id: str,
    run_id: str,
    caller_id: str | None = None,
) -> dict[str, Any]:
    items = dataset_manifest["payload"]["items"]
    outputs: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    mechanism_ids: list[str] = []

    for item in items:
        result = model_runner.generate_structured_output(lane_id, item["input"])
        runtime = model_runner.collect_runtime_stats(lane_id, item["input"])
        fallback_type = "policy_fallback" if result["routing_label"] != "allow" else None
        mechanism_id = f"mechanism-{item['item_id']}"
        output = {
            "item_id": item["item_id"],
            "result": result,
            "runtime": runtime,
            "fallback_type": fallback_type,
            "lane_action": result["routing_label"],
            "mechanism_id": mechanism_id,
        }
        outputs.append(output)
        mechanism_ids.append(mechanism_id)

        receipt = emit_decision_receipt(
            run_id=f"{run_id}:{item['item_id']}",
            trace_id=f"{trace_id}:{item['item_id']}",
            lane_id=lane_id,
            model_id=model_runner.profile.model_id,
            decision=result["routing_label"],
            action_selected=result["routing_label"],
            policy_version="pilot-policy.v1",
            evaluated_claims=[item["label"]],
            artifact_inputs=[{"artifact_id": dataset_manifest["artifact_id"], "artifact_type": "golden_dataset_manifest"}],
            mechanism_classes_used=[mechanism_id],
            thresholds_applied=scorecard["payload"]["thresholds"],
            falsifiers_checked=[],
            active_mechanism_class_ids=[mechanism_id],
            policy_clauses_triggered=[],
            geometry_anomaly_flags=[],
            chart_instability_flags=[],
            caller_id=caller_id,
        )
        receipts.append(receipt)

    scoring = score_items(outputs, scorecard)
    demo_payload = {
        "lane_id": lane_id,
        "dataset_version": dataset_manifest["payload"]["dataset_version"],
        "model_profile_ref": run_config["payload"]["model_profile_ref"],
        "run_config_ref": run_config["artifact_id"],
        "run_config_hash": run_config["content_hash"],
        "item_results": outputs,
        "receipt_refs": [receipt["artifact_id"] for receipt in receipts],
        "mechanism_ids": sorted(mechanism_ids),
        "fallback_stats": {
            "policy_fallback": scoring["fallback_counters"]["policy_fallback"],
            "model_fallback": scoring["fallback_counters"]["model_fallback"],
            "operator_fallback": scoring["fallback_counters"]["operator_fallback"],
        },
        "performance_stats": scoring["performance"],
    }

    demo_run_record = build_artifact_entry(
        artifact_type="demo_run_record",
        schema_version=1,
        producer="geoclt:demo:0.4.0",
        trace_id=trace_id,
        run_id=run_id,
        payload=demo_payload,
        created_at="2026-01-01T00:00:00Z",
    )
    validate_instance(
        demo_run_record,
        _schema_path("demo_run_record.schema.json"),
    )

    bundle = build_artifact_bundle(
        run_id=run_id,
        trace_id=trace_id,
        producer="geoclt:demo:0.4.0",
        artifacts=[demo_run_record],
        created_at="2026-01-01T00:00:00Z",
    )

    return {
        "lane_id": lane_id,
        "run_id": run_id,
        "trace_id": trace_id,
        "outputs": outputs,
        "mechanism_ids": sorted(mechanism_ids),
        "receipts": receipts,
        "demo_run_record": demo_run_record,
        "bundle": bundle,
        "scoring": scoring,
        "run_hash": stable_hash(
            {
                "manifest_hash": dataset_manifest["payload"]["dataset_hash"],
                "run_config_hash": run_config["content_hash"],
                "outputs": outputs,
            }
        ),
    }

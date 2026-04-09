from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .artifacts import stable_hash, write_json
from .profiles import BenchmarkLaneConfig
from .receipts import emit_decision_receipt

try:
    from mair.manifest import load_manifest
    from mair.validate import validate_artifact
except Exception as exc:  # pragma: no cover - exercised in integration usage
    load_manifest = None  # type: ignore
    validate_artifact = None  # type: ignore
    _IMPORT_ERROR = exc


REQUIRED_ARTIFACTS = {
    "mair_semantic_trace",
    "mair_graph_ir",
    "mair_numeric_lowering",
    "blt_codes",
    "tract_state_snapshot",
    "topology_summary",
    "grouped_clt_bundle",
    "intervention_sweep",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _decision_from_falsifiers(falsifiers: dict[str, bool]) -> str:
    hard_failures = ["trace_completeness", "replay_determinism"]
    if any(falsifiers[name] for name in hard_failures):
        return "reject"
    if any(falsifiers.values()):
        return "allow_with_review"
    return "allow"


def run_mair_benchmark(workspace: Any, manifest_path: str | Path, lane: BenchmarkLaneConfig) -> dict[str, Any]:
    if load_manifest is None or validate_artifact is None:
        raise RuntimeError(
            "MAIR benchmarking requires the installed mair package. "
            "Run python -m pip install -e '/Volumes/128/MAIR[dev]' -e '/Volumes/128/BLT[dev]'"
        ) from _IMPORT_ERROR
    workspace._ensure_layout()
    manifest_file = Path(manifest_path)
    manifest = load_manifest(manifest_file)
    artifact_by_type = {artifact["artifact_type"]: artifact for artifact in manifest["artifacts"]}
    trace_id = manifest["trace_id"]
    run_id = workspace._new_run_id(lane.lane_id)
    run_dir = workspace.root / "runs" / run_id
    artifacts_dir = run_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    grouped_bundle = _load_json(manifest_file.parent / artifact_by_type["grouped_clt_bundle"]["path"])
    topology_summary = _load_json(manifest_file.parent / artifact_by_type["topology_summary"]["path"])
    intervention_rows = _load_jsonl(manifest_file.parent / artifact_by_type["intervention_sweep"]["path"])
    numeric_lowering = _load_json(manifest_file.parent / artifact_by_type["mair_numeric_lowering"]["path"])

    metrics = {
        "bridge_dependence": round(float(grouped_bundle["summary_metrics"].get("mean_bridge_dependence", 0.0)), 6),
        "reconstruction_divergence": round(float(grouped_bundle["summary_metrics"].get("mean_reconstruction_divergence", 0.0)), 6),
        "topological_susceptibility": round(float(topology_summary["summary_metrics"].get("topological_susceptibility", 0.0)), 6),
        "trace_completeness": REQUIRED_ARTIFACTS.issubset(artifact_by_type.keys()),
        "replay_determinism": bool(numeric_lowering.get("equivalence_witness")),
        "intervention_count": len(intervention_rows),
    }

    falsifiers = {
        "bridge_dependence": metrics["bridge_dependence"] > max(0.8, lane.transport_coherence_threshold),
        "reconstruction_divergence": metrics["reconstruction_divergence"] > lane.intervention_delta_threshold,
        "topological_susceptibility": metrics["topological_susceptibility"] > (1.0 - lane.chart_stability_threshold),
        "trace_completeness": not bool(metrics["trace_completeness"]),
        "replay_determinism": not bool(metrics["replay_determinism"]),
    }
    decision = _decision_from_falsifiers(falsifiers)
    artifact_inputs = [
        {
            "artifact_id": artifact["artifact_id"],
            "artifact_type": artifact["artifact_type"],
            "content_hash": artifact["content_hash"],
        }
        for artifact in manifest["artifacts"]
    ]
    assurance_receipt = {
        "trace_id": trace_id,
        "decision": decision,
        "gates": {
            "bridge_dependence": not falsifiers["bridge_dependence"],
            "reconstruction_divergence": not falsifiers["reconstruction_divergence"],
            "topological_susceptibility": not falsifiers["topological_susceptibility"],
            "trace_completeness": not falsifiers["trace_completeness"],
            "replay_determinism": not falsifiers["replay_determinism"],
        },
        "falsifiers": falsifiers,
        "artifact_inputs": artifact_inputs,
        "summary": {
            "lane_id": lane.lane_id,
            "behavior_id": lane.behavior_id,
            "metrics": metrics,
            "bundle_hash": stable_hash({"trace_id": trace_id, "artifacts": artifact_inputs}),
        },
    }
    receipt_path = artifacts_dir / "assurance_receipt.v1.json"
    write_json(receipt_path, assurance_receipt)
    validate_artifact(receipt_path, "assurance_receipt")

    decision_receipt = emit_decision_receipt(
        run_id=run_id,
        trace_id=trace_id,
        model_id=str(workspace.metadata.get("model_id", "qwen3.5-hybrid-fixture")),
        lane_id=lane.lane_id,
        decision=decision,
        artifact_inputs=artifact_inputs,
        thresholds_applied={
            "intervention_delta_threshold": lane.intervention_delta_threshold,
            "chart_stability_threshold": lane.chart_stability_threshold,
            "transport_coherence_threshold": lane.transport_coherence_threshold,
        },
        falsifiers_checked=sorted(falsifiers.keys()),
        mechanism_classes_used=["grouped_clt", "topology_sketch", "bridge_dependence_gate"],
        bundle_hash=assurance_receipt["summary"]["bundle_hash"],
        geometry_anomaly_flags=[name for name, triggered in falsifiers.items() if triggered],
    )

    result = {
        "run_id": run_id,
        "trace_id": trace_id,
        "lane_id": lane.lane_id,
        "manifest_path": str(manifest_file),
        "metrics": metrics,
        "falsifiers": falsifiers,
        "assurance_receipt": assurance_receipt,
        "decision_receipt": decision_receipt,
        "artifacts": {
            "assurance_receipt": str(receipt_path),
        },
    }
    write_json(artifacts_dir / "mair_benchmark_bundle.json", result)
    return result

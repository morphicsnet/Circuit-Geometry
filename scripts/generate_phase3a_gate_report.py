from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SRC = REPO_ROOT / "python"
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

from geoclt.adapters import TransformersAdapter
from geoclt.artifacts import read_json, stable_hash, validate_instance
from geoclt.mechanisms import cluster_family, derive_cluster_id, derive_mechanism_id
from geoclt.receipts import emit_decision_receipt, persist_receipt
from geoclt.sidecar import connect_sidecar

LANE_ROOT = REPO_ROOT / "crates" / "geoclt-benchmark" / "lanes"
LOCK_PATH = LANE_ROOT / "IMMUTABLE_LOCK.json"


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _lane_definitions() -> list[dict[str, Any]]:
    lanes: list[dict[str, Any]] = []
    for lane_file in sorted(LANE_ROOT.glob("*/v*.json")):
        lanes.append(read_json(lane_file))
    return lanes


def _lane_registry_immutable() -> bool:
    lock = read_json(LOCK_PATH)
    for relative, expected_hash in lock["locked_files"].items():
        target = LANE_ROOT / relative
        if not target.exists() or _hash_file(target) != expected_hash:
            return False
    return True


def _evaluate_policy(receipt: dict[str, Any]) -> str:
    if receipt["decision"] == "block":
        return "block"
    if receipt["decision"] == "escalate":
        return "escalate"
    if receipt["fallback_selected"]:
        return "route_to_fallback"
    if receipt["policy_clauses_triggered"] or receipt["provisional_mechanism_class_ids"]:
        return "allow_with_review"
    return "allow"


def _high_cardinality_family() -> tuple[str, str, int]:
    members: list[dict[str, str]] = []
    for index in range(512):
        members.append({"mechanism_id": f"mechanism-{index % 127}"})
    family_one = cluster_family(members)
    family_two = cluster_family(list(reversed(members)))
    return family_one["cluster_id"], family_two["cluster_id"], family_one["member_count"]


def _receipt_immutability_check(receipt: dict[str, Any]) -> tuple[bool, bool]:
    with tempfile.TemporaryDirectory(prefix="phase3a-receipt-") as directory:
        path = Path(directory) / "receipt.json"
        first = persist_receipt(path, receipt)
        second = persist_receipt(path, receipt)
        mutated = dict(receipt)
        mutated["decision"] = "block" if receipt["decision"] != "block" else "allow"
        mutation_rejected = False
        try:
            persist_receipt(path, mutated)
        except ValueError:
            mutation_rejected = True
        return bool(first.get("immutable")) and bool(second.get("idempotent")), mutation_rejected


def main() -> int:
    schema_path = REPO_ROOT / "schemas" / "decision_receipt.schema.json"

    base_hyperpath = {
        "path_id": "path-1",
        "behavior_id": "factual_retrieval",
        "event_ids": ["event-2", "event-1"],
        "chart_ids": ["chart-b", "chart-a"],
        "layer_ids": [5, 6],
        "transport_edge_ids": ["edge-2", "edge-1"],
        "geodesic_deviation": 0.2,
        "chart_stability": 0.84,
        "transport_coherence": 0.83,
        "intervention_faithfulness": 0.18,
        "synergy_score_max": 0.09,
        "trace_id": "trace-noise",
        "run_id": "run-noise",
        "adapter_id": "transformers-noise",
        "timestamp": "2026-03-14T00:00:00Z",
    }

    mechanism_id_one = derive_mechanism_id(
        mechanism_class_type="causal_hyperpath",
        hyperpath=base_hyperpath,
        causal_dependency_set=["feature-b", "feature-a"],
        invariant_features=["inv-2", "inv-1"],
    )

    noisy_hyperpath = dict(base_hyperpath)
    noisy_hyperpath.update(
        {
            "trace_id": "trace-other",
            "run_id": "run-other",
            "adapter_id": "adapter-other",
            "timestamp": "2027-01-01T00:00:00Z",
        }
    )
    mechanism_id_two = derive_mechanism_id(
        mechanism_class_type="causal_hyperpath",
        hyperpath=noisy_hyperpath,
        causal_dependency_set=["feature-a", "feature-b"],
        invariant_features=["inv-1", "inv-2"],
    )
    chart_substitution_hyperpath = dict(base_hyperpath)
    chart_substitution_hyperpath["chart_ids"] = list(reversed(base_hyperpath["chart_ids"]))
    mechanism_id_chart_substitution = derive_mechanism_id(
        mechanism_class_type="causal_hyperpath",
        hyperpath=chart_substitution_hyperpath,
        causal_dependency_set=["feature-a", "feature-b"],
        invariant_features=["inv-1", "inv-2"],
    )
    schema_replay_hyperpath = dict(base_hyperpath)
    schema_replay_hyperpath["schema_version"] = 1
    mechanism_id_schema_replay = derive_mechanism_id(
        mechanism_class_type="causal_hyperpath",
        hyperpath=schema_replay_hyperpath,
        causal_dependency_set=["feature-a", "feature-b"],
        invariant_features=["inv-1", "inv-2"],
    )
    mechanism_id_semantic_change = derive_mechanism_id(
        mechanism_class_type="causal_hyperpath",
        hyperpath={**base_hyperpath, "event_ids": ["event-3", "event-1"]},
        causal_dependency_set=["feature-a", "feature-b"],
        invariant_features=["inv-1", "inv-2"],
    )

    mechanism_family = cluster_family(
        [
            {"mechanism_id": mechanism_id_one},
            {"mechanism_id": mechanism_id_two},
            {"mechanism_id": mechanism_id_one},
        ]
    )
    cluster_id_one = derive_cluster_id(mechanism_family["member_mechanism_ids"])
    cluster_id_two = derive_cluster_id(list(reversed(mechanism_family["member_mechanism_ids"])))
    high_cardinality_cluster_one, high_cardinality_cluster_two, high_cardinality_member_count = (
        _high_cardinality_family()
    )

    adapter = TransformersAdapter("gpt2-small")
    sidecar = connect_sidecar()
    trace_prompt = "claims triage requires evidence review before approval"
    trace_activations = adapter.capture_activations(trace_prompt, adapter.list_blocks()[:2])
    roundtrip = sidecar.stream_trace(
        trace_id="phase3a-trace",
        adapter_id=adapter.capabilities().adapter_id,
        model_id="gpt2-small",
        lane_id="claims-triage.v1",
        run_id="phase3a-run",
        chunks=[
            json.dumps(item, sort_keys=True).encode("utf-8")
            for item in trace_activations["activations"]
        ],
    )
    bundle_hash = roundtrip["bundle"]["bundle_hash"]

    receipt_one = emit_decision_receipt(
        run_id="phase3a-run",
        trace_id="phase3a-trace",
        lane_id="claims-triage.v1",
        decision="allow_with_review",
        action_selected="allow_with_review",
        policy_version="policy.v1",
        evaluated_claims=["claim-1"],
        artifact_inputs=[{"artifact_id": "artifact-a", "artifact_type": "benchmark_result"}],
        mechanism_classes_used=[mechanism_id_one],
        thresholds_applied={"intervention_delta_threshold": 0.1},
        falsifiers_checked=["pairwise_sufficiency"],
        bundle_hash=bundle_hash,
        active_mechanism_class_ids=[mechanism_id_one],
        provisional_mechanism_class_ids=[],
        policy_clauses_triggered=["manual-review"],
        geometry_anomaly_flags=[],
        chart_instability_flags=[],
    )
    receipt_two = emit_decision_receipt(
        run_id="phase3a-run",
        trace_id="phase3a-trace",
        lane_id="claims-triage.v1",
        decision="allow_with_review",
        action_selected="allow_with_review",
        policy_version="policy.v1",
        evaluated_claims=["claim-1"],
        artifact_inputs=[{"artifact_id": "artifact-a", "artifact_type": "benchmark_result"}],
        mechanism_classes_used=[mechanism_id_one],
        thresholds_applied={"intervention_delta_threshold": 0.1},
        falsifiers_checked=["pairwise_sufficiency"],
        bundle_hash=bundle_hash,
        active_mechanism_class_ids=[mechanism_id_one],
        provisional_mechanism_class_ids=[],
        policy_clauses_triggered=["manual-review"],
        geometry_anomaly_flags=[],
        chart_instability_flags=[],
    )
    receipt_three = emit_decision_receipt(
        run_id="phase3a-run-alt",
        trace_id="phase3a-trace",
        lane_id="claims-triage.v1",
        decision="allow",
        action_selected="allow",
        policy_version="policy.v1",
        evaluated_claims=["claim-1"],
        artifact_inputs=[{"artifact_id": "artifact-a", "artifact_type": "benchmark_result"}],
        mechanism_classes_used=[mechanism_id_one],
        thresholds_applied={"intervention_delta_threshold": 0.1},
        falsifiers_checked=["pairwise_sufficiency"],
        bundle_hash=bundle_hash,
        active_mechanism_class_ids=[mechanism_id_one],
        provisional_mechanism_class_ids=[],
        policy_clauses_triggered=[],
        geometry_anomaly_flags=[],
        chart_instability_flags=[],
    )

    receipt_repersist_idempotent, receipt_mutation_rejected = _receipt_immutability_check(
        receipt_one
    )

    validate_instance(receipt_one, schema_path)

    lanes = _lane_definitions()
    lane_thresholds_valid = all(
        value >= 0.0 for lane in lanes for value in lane.get("thresholds", {}).values()
    )
    lane_falsifiers_valid = all(bool(lane.get("falsifiers")) for lane in lanes)
    allowed_policy_actions = {
        "allow",
        "allow_with_review",
        "route_to_fallback",
        "block",
        "escalate",
    }
    lane_policy_actions_valid = all(
        set(lane.get("policy_actions", [])) == allowed_policy_actions for lane in lanes
    )

    receipt_required_fields = [
        "receipt_id",
        "trace_id",
        "model_id",
        "lane_id",
        "policy_version",
        "evaluated_claims",
        "artifact_inputs",
        "mechanism_classes_used",
        "evaluation_results",
        "thresholds_applied",
        "falsifiers_checked",
        "action_selected",
        "fallback_selected",
        "immutable_bundle_hash",
        "receipt_hash",
    ]

    report: dict[str, Any] = {
        "git_commit": _git_commit(),
        "mechanism_identity_stable": mechanism_id_one == mechanism_id_two,
        "mechanism_identity_runtime_field_exclusion": mechanism_id_one == mechanism_id_two,
        "mechanism_identity_changes_on_semantic_change": mechanism_id_one != mechanism_id_semantic_change,
        "mechanism_id_deterministic": mechanism_id_one == derive_mechanism_id(
            mechanism_class_type="causal_hyperpath",
            hyperpath=base_hyperpath,
            causal_dependency_set=["feature-b", "feature-a"],
            invariant_features=["inv-2", "inv-1"],
        ),
        "mechanism_identity_chart_substitution_stable": mechanism_id_one
        == mechanism_id_chart_substitution,
        "mechanism_identity_schema_replay_stable": mechanism_id_one == mechanism_id_schema_replay,
        "cluster_deterministic": cluster_id_one == cluster_id_two,
        "cluster_identity_deterministic": cluster_id_one == mechanism_family["cluster_id"],
        "cluster_high_cardinality_deterministic": high_cardinality_cluster_one
        == high_cardinality_cluster_two,
        "cluster_high_cardinality_member_count_valid": high_cardinality_member_count == 127,
        "mechanism_family_assignment_valid": mechanism_family["member_count"] >= 1,
        "decision_receipt_schema_valid": True,
        "decision_receipt_complete": all(field in receipt_one for field in receipt_required_fields),
        "receipt_hash_stable": receipt_one["receipt_hash"] == receipt_two["receipt_hash"],
        "receipt_repersist_idempotent": receipt_repersist_idempotent,
        "receipt_mutation_rejected": receipt_mutation_rejected,
        "receipt_immutability_enforced": receipt_repersist_idempotent and receipt_mutation_rejected,
        "lane_registry_loaded": bool(lanes),
        "lane_thresholds_valid": lane_thresholds_valid,
        "lane_falsifiers_valid": lane_falsifiers_valid,
        "lane_policy_actions_valid": lane_policy_actions_valid,
        "lane_registry_immutable": _lane_registry_immutable(),
        "policy_evaluation_deterministic": _evaluate_policy(receipt_one) == _evaluate_policy(receipt_two),
        "artifact_bundle_linkage_valid": all(
            receipt["immutable_bundle_hash"] == bundle_hash
            for receipt in [receipt_one, receipt_two, receipt_three]
        ),
        "canonicalization_preserved": stable_hash({"z": 1, "a": [1, 2]})
        == stable_hash({"a": [1, 2], "z": 1}),
        "receipt_policy_action": _evaluate_policy(receipt_one),
        "lane_count": len(lanes),
        "lane_ids": [lane["lane_id"] for lane in lanes],
    }

    report["overall_pass"] = all(
        report[key]
        for key in [
            "mechanism_identity_stable",
            "mechanism_identity_runtime_field_exclusion",
            "mechanism_identity_changes_on_semantic_change",
            "mechanism_id_deterministic",
            "mechanism_identity_chart_substitution_stable",
            "mechanism_identity_schema_replay_stable",
            "cluster_deterministic",
            "cluster_identity_deterministic",
            "cluster_high_cardinality_deterministic",
            "cluster_high_cardinality_member_count_valid",
            "mechanism_family_assignment_valid",
            "decision_receipt_schema_valid",
            "decision_receipt_complete",
            "receipt_hash_stable",
            "receipt_repersist_idempotent",
            "receipt_mutation_rejected",
            "receipt_immutability_enforced",
            "lane_registry_loaded",
            "lane_thresholds_valid",
            "lane_falsifiers_valid",
            "lane_policy_actions_valid",
            "lane_registry_immutable",
            "policy_evaluation_deterministic",
            "artifact_bundle_linkage_valid",
            "canonicalization_preserved",
        ]
    )

    output = REPO_ROOT / "outputs" / "phase3a_gate_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

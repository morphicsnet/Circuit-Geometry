from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SRC = REPO_ROOT / "python"
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

from geoclt import BenchmarkLaneConfig, Workspace
from geoclt.benchmark import (
    compare_baselines,
    conformance_class,
    evaluate_admission,
    evaluate_falsifiers,
)

FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "factual_retrieval_v1"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate machine-readable Phase 0/1 gate report.")
    parser.add_argument(
        "--workspace",
        default="runs/phase-gate",
        help="Workspace used to generate run/inspect/export gate checks.",
    )
    parser.add_argument(
        "--output",
        default="outputs/phase_gate_report.json",
        help="Output path for phase gate report JSON.",
    )
    return parser.parse_args()


def evaluate_fixture_cases() -> dict[str, Any]:
    manifest = load_json(FIXTURE_DIR / "fixture_manifest.json")
    cases: list[dict[str, Any]] = []
    for fixture in manifest["fixtures"]:
        payload = load_json(FIXTURE_DIR / fixture["path"])
        lane_payload = payload["lane"]
        lane = BenchmarkLaneConfig(
            lane_id=lane_payload["lane_id"],
            behavior_id=lane_payload["behavior_id"],
            intervention_delta_threshold=lane_payload["intervention_delta_threshold"],
            synergy_threshold=lane_payload["synergy_threshold"],
            chart_stability_threshold=lane_payload["chart_stability_threshold"],
            transport_coherence_threshold=lane_payload["transport_coherence_threshold"],
            baseline_margin_threshold=lane_payload["baseline_margin_threshold"],
        )
        metrics = payload["metrics"]
        baseline_scores = {
            baseline["baseline_id"]: baseline["intervention_faithfulness"]
            for baseline in payload["baselines"]
        }
        admission = evaluate_admission(
            lane=lane,
            intervention_faithfulness=metrics["intervention_faithfulness"],
            synergy_score_max=metrics["synergy_score_max"],
            chart_stability=metrics["chart_stability"],
            transport_coherence=metrics["transport_coherence"],
        )
        baseline = compare_baselines(
            intervention_faithfulness=metrics["intervention_faithfulness"],
            baseline_scores=baseline_scores,
            margin_threshold=lane.baseline_margin_threshold,
        )
        falsifiers = evaluate_falsifiers(
            lane=lane,
            intervention_faithfulness=metrics["intervention_faithfulness"],
            synergy_score_max=metrics["synergy_score_max"],
            chart_stability=metrics["chart_stability"],
            transport_coherence=metrics["transport_coherence"],
            geodesic_deviation=metrics["geodesic_deviation"],
            strongest_baseline=baseline["strongest_baseline"],
        )
        actual_class = conformance_class(
            admission_passed=admission["passed"],
            beats_baseline=baseline["beats_baseline"],
            falsifiers=falsifiers,
        )

        expected_class = fixture["expected_conformance_class"]
        expected_falsifiers = fixture["expected_falsifiers"]
        expected_match = actual_class == expected_class and all(
            falsifiers[key] == value for key, value in expected_falsifiers.items()
        )
        cases.append(
            {
                "id": fixture["id"],
                "expected_conformance_class": expected_class,
                "actual_conformance_class": actual_class,
                "expected_falsifiers": expected_falsifiers,
                "actual_falsifiers": falsifiers,
                "beats_baseline": baseline["beats_baseline"],
                "expected_match": expected_match,
            }
        )

    positive = next(case for case in cases if case["id"] == "positive_default")
    rejected_with_falsifier = any(
        case["actual_conformance_class"] == "rejected" and case["actual_falsifiers"]["any_triggered"]
        for case in cases
        if case["id"] != "positive_default"
    )
    return {
        "cases": cases,
        "phase0_contract_checks": {
            "fixture_expectations_match": all(case["expected_match"] for case in cases),
            "positive_fixture_conformant": positive["actual_conformance_class"] == "conformant",
            "positive_fixture_beats_baseline": positive["beats_baseline"],
            "negative_fixture_rejected_with_falsifier": rejected_with_falsifier,
        },
    }


def run_phase1_workflow(workspace_path: str) -> dict[str, Any]:
    ws = Workspace.create(workspace_path)
    ws.attach_model("gpt2-small")
    ws.fit_atlas(profile="factual_retrieval")
    ws.fit_transport()
    ws.propose_events()
    ws.verify_mechanisms()

    lane = BenchmarkLaneConfig(lane_id="factual_retrieval.v1", behavior_id="factual_retrieval")
    run_one = ws.run_benchmark(lane)
    run_two = ws.run_benchmark(lane)
    inspected = ws.get_run(run_two["run_id"])
    exported = ws.export_report(run_two["run_id"])
    loaded = ws.load_report(run_two["run_id"])
    determinism = ws.determinism_for_run(run_two["run_id"])

    artifacts_exist = all(Path(path).exists() for path in run_two["artifact_paths"].values())
    artifact_payloads = {}
    for artifact_type, path in run_two["artifact_paths"].items():
        artifact_payloads[artifact_type] = json.loads(Path(path).read_text(encoding="utf-8"))

    artifact_checks = {
        "atlas_overlap_map": {
            "ok": all(
                key in artifact_payloads.get("atlas_overlap_map", {})
                for key in ("model_id", "lane_id", "chart_count", "overlap_score", "profile")
            )
        },
        "transport_diagnostics": {
            "ok": all(
                key in artifact_payloads.get("transport_diagnostics", {})
                for key in (
                    "lane_id",
                    "loop_consistency",
                    "distortion",
                    "coherence",
                    "geodesic_deviation",
                )
            )
        },
        "candidate_event_table": {
            "ok": (
                "events" in artifact_payloads.get("candidate_event_table", {})
                and "candidate_count" in artifact_payloads.get("candidate_event_table", {})
                and len(artifact_payloads["candidate_event_table"]["events"])
                == artifact_payloads["candidate_event_table"]["candidate_count"]
            )
        },
        "admitted_hyperpath_table": {
            "ok": (
                "hyperpaths" in artifact_payloads.get("admitted_hyperpath_table", {})
                and "admitted_count" in artifact_payloads.get("admitted_hyperpath_table", {})
                and len(artifact_payloads["admitted_hyperpath_table"]["hyperpaths"])
                == artifact_payloads["admitted_hyperpath_table"]["admitted_count"]
            )
        },
        "falsifier_sheet": {
            "ok": all(
                key in artifact_payloads.get("falsifier_sheet", {})
                for key in (
                    "falsifiers",
                    "admission",
                    "baseline_report",
                    "conformance_class",
                    "benchmark_result",
                )
            )
        },
    }
    artifacts_valid = all(entry["ok"] for entry in artifact_checks.values())
    return {
        "run_one_id": run_one["run_id"],
        "run_two_id": run_two["run_id"],
        "phase1_checks": {
            "run_completed": run_two["status"] == "completed",
            "artifact_count_is_five": len(run_two["artifact_paths"]) == 5,
            "artifacts_exist": artifacts_exist,
            "artifacts_validate": artifacts_valid,
            "run_inspect_export_load_roundtrip": (
                inspected["run"]["run_id"] == run_two["run_id"]
                and exported["status"] == "ok"
                and loaded["run"]["run_id"] == run_two["run_id"]
            ),
            "determinism_endpoint_consistent": determinism["is_deterministic"],
            "bundle_hash_stable_across_reruns": (
                run_one["artifact_bundle_hash"] == run_two["artifact_bundle_hash"]
            ),
        },
        "artifact_checks": artifact_checks,
    }


def main() -> int:
    args = parse_args()
    fixture_results = evaluate_fixture_cases()
    workflow_results = run_phase1_workflow(args.workspace)

    phase0_checks = fixture_results["phase0_contract_checks"]
    phase1_checks = workflow_results["phase1_checks"]

    payload = {
        "phase0": phase0_checks,
        "phase1": phase1_checks,
        "fixture_results": fixture_results["cases"],
        "workflow": {
            "run_one_id": workflow_results["run_one_id"],
            "run_two_id": workflow_results["run_two_id"],
        },
    }
    payload["overall_pass"] = all(phase0_checks.values()) and all(phase1_checks.values())

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

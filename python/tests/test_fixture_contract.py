from __future__ import annotations

import json
from pathlib import Path

from geoclt.benchmark import (
    compare_baselines,
    conformance_class,
    evaluate_admission,
    evaluate_falsifiers,
)
from geoclt.profiles import BenchmarkLaneConfig

FIXTURE_DIR = Path("tests/fixtures/factual_retrieval_v1")
GOLDEN_DIR = Path("tests/golden/factual_retrieval_v1/positive_default")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def make_lane(payload: dict) -> BenchmarkLaneConfig:
    return BenchmarkLaneConfig(
        lane_id=payload["lane_id"],
        behavior_id=payload["behavior_id"],
        intervention_delta_threshold=payload["intervention_delta_threshold"],
        synergy_threshold=payload["synergy_threshold"],
        chart_stability_threshold=payload["chart_stability_threshold"],
        transport_coherence_threshold=payload["transport_coherence_threshold"],
        baseline_margin_threshold=payload["baseline_margin_threshold"],
    )


def build_fixture_artifacts(fixture_id: str, case: dict) -> dict[str, dict]:
    lane = make_lane(case["lane"])
    metrics = case["metrics"]
    baseline_scores = {
        baseline["baseline_id"]: baseline["intervention_faithfulness"]
        for baseline in case["baselines"]
    }

    admission = evaluate_admission(
        lane=lane,
        intervention_faithfulness=metrics["intervention_faithfulness"],
        synergy_score_max=metrics["synergy_score_max"],
        chart_stability=metrics["chart_stability"],
        transport_coherence=metrics["transport_coherence"],
    )
    admission["min_margin"] = round(admission["min_margin"], 4)
    baseline_report = compare_baselines(
        intervention_faithfulness=metrics["intervention_faithfulness"],
        baseline_scores=baseline_scores,
        margin_threshold=lane.baseline_margin_threshold,
    )
    baseline_report["strongest_baseline"] = round(baseline_report["strongest_baseline"], 4)
    baseline_report["delta_vs_strongest"] = round(baseline_report["delta_vs_strongest"], 4)
    falsifiers = evaluate_falsifiers(
        lane=lane,
        intervention_faithfulness=metrics["intervention_faithfulness"],
        synergy_score_max=metrics["synergy_score_max"],
        chart_stability=metrics["chart_stability"],
        transport_coherence=metrics["transport_coherence"],
        geodesic_deviation=metrics["geodesic_deviation"],
        strongest_baseline=baseline_report["strongest_baseline"],
    )
    conformance = conformance_class(
        admission_passed=admission["passed"],
        beats_baseline=baseline_report["beats_baseline"],
        falsifiers=falsifiers,
    )

    fixture_key = f"fixture-{fixture_id.split('_')[0]}"
    candidate_events = [
        {
            "event_id": f"event-{fixture_key}-1",
            "participant_set": ["sae:f123", "head:5:3", "mlp:6:17"],
            "participant_types": ["sae", "attention_head", "mlp_gate"],
            "causal_weight": round(metrics["intervention_faithfulness"] * 0.85, 4),
            "reliability_score": round(metrics["chart_stability"] * 0.88, 4),
        },
        {
            "event_id": f"event-{fixture_key}-2",
            "participant_set": ["sae:f208", "head:6:2", "mlp:6:31"],
            "participant_types": ["sae", "attention_head", "mlp_gate"],
            "causal_weight": round(metrics["intervention_faithfulness"] * 0.72, 4),
            "reliability_score": round(metrics["chart_stability"] * 0.79, 4),
        },
    ]

    admitted_hyperpaths: list[dict] = []
    if admission["passed"]:
        admitted_hyperpaths.append(
            {
                "path_id": f"path-{fixture_key}-1",
                "behavior_id": lane.behavior_id,
                "event_ids": [event["event_id"] for event in candidate_events],
                "layer_ids": [5, 6],
                "chart_stability": round(metrics["chart_stability"], 4),
                "transport_coherence": round(metrics["transport_coherence"], 4),
                "intervention_faithfulness": round(metrics["intervention_faithfulness"], 4),
                "synergy_score_max": round(metrics["synergy_score_max"], 4),
                "geodesic_deviation": round(metrics["geodesic_deviation"], 4),
                "admitted": conformance != "rejected",
            }
        )

    benchmark_result = {
        "run_id": f"benchmark-{fixture_key}",
        "model_id": case.get("model_id", "gpt2-small"),
        "task_id": lane.behavior_id,
        "baseline_id": baseline_report.get("strongest_baseline_id", "none"),
        "metric_name": "intervention_faithfulness",
        "metric_value": round(metrics["intervention_faithfulness"], 4),
        "threshold": lane.intervention_delta_threshold,
        "passed": conformance != "rejected",
    }

    return {
        "atlas_overlap_map": {
            "model_id": case.get("model_id", "gpt2-small"),
            "lane_id": lane.lane_id,
            "chart_count": 4,
            "overlap_score": round(metrics["chart_stability"], 4),
            "profile": lane.behavior_id,
        },
        "transport_diagnostics": {
            "lane_id": lane.lane_id,
            "loop_consistency": round(metrics["transport_coherence"], 4),
            "distortion": round(max(0.0, 1.0 - metrics["transport_coherence"]), 4),
            "coherence": round(metrics["transport_coherence"], 4),
            "geodesic_deviation": round(metrics["geodesic_deviation"], 4),
        },
        "candidate_event_table": {
            "lane_id": lane.lane_id,
            "candidate_count": len(candidate_events),
            "events": candidate_events,
        },
        "admitted_hyperpath_table": {
            "lane_id": lane.lane_id,
            "admitted_count": len(admitted_hyperpaths),
            "hyperpaths": admitted_hyperpaths,
        },
        "falsifier_sheet": {
            "lane_id": lane.lane_id,
            "falsifiers": falsifiers,
            "admission": admission,
            "baseline_report": baseline_report,
            "conformance_class": conformance,
            "benchmark_result": benchmark_result,
        },
    }


def test_fixture_manifest_conformance_contract():
    manifest = load_json(FIXTURE_DIR / "fixture_manifest.json")
    for fixture in manifest["fixtures"]:
        case = load_json(FIXTURE_DIR / fixture["path"])
        lane = make_lane(case["lane"])
        metrics = case["metrics"]
        baseline_scores = {
            baseline["baseline_id"]: baseline["intervention_faithfulness"]
            for baseline in case["baselines"]
        }

        admission = evaluate_admission(
            lane=lane,
            intervention_faithfulness=metrics["intervention_faithfulness"],
            synergy_score_max=metrics["synergy_score_max"],
            chart_stability=metrics["chart_stability"],
            transport_coherence=metrics["transport_coherence"],
        )
        baseline_report = compare_baselines(
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
            strongest_baseline=baseline_report["strongest_baseline"],
        )
        actual_class = conformance_class(
            admission_passed=admission["passed"],
            beats_baseline=baseline_report["beats_baseline"],
            falsifiers=falsifiers,
        )
        assert actual_class == fixture["expected_conformance_class"]
        for key, expected in fixture["expected_falsifiers"].items():
            assert falsifiers[key] == expected


def test_positive_fixture_golden_outputs_present_and_consistent():
    required = {
        "atlas_overlap_map.json",
        "transport_diagnostics.json",
        "candidate_event_table.json",
        "admitted_hyperpath_table.json",
        "falsifier_sheet.json",
    }
    assert required.issubset({path.name for path in GOLDEN_DIR.iterdir() if path.is_file()})

    manifest = load_json(FIXTURE_DIR / "fixture_manifest.json")
    fixture = next(item for item in manifest["fixtures"] if item["id"] == "positive_default")
    case = load_json(FIXTURE_DIR / fixture["path"])
    expected = build_fixture_artifacts(fixture["id"], case)
    assert {f"{key}.json" for key in expected} == required

    for artifact_key, payload in expected.items():
        actual = load_json(GOLDEN_DIR / f"{artifact_key}.json")
        assert actual == payload

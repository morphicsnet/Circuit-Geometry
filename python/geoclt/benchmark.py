from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .profiles import BenchmarkLaneConfig

BASELINE_IDS = ("single_sae", "ensemble_sae", "pairwise_graph", "geometry_free")


def evaluate_admission(
    lane: BenchmarkLaneConfig,
    intervention_faithfulness: float,
    synergy_score_max: float,
    chart_stability: float,
    transport_coherence: float,
) -> dict[str, Any]:
    failed_checks: list[str] = []

    intervention_margin = intervention_faithfulness - lane.intervention_delta_threshold
    if intervention_margin < 0:
        failed_checks.append("intervention_faithfulness")

    synergy_margin = synergy_score_max - lane.synergy_threshold
    if synergy_margin < 0:
        failed_checks.append("synergy_score_max")

    chart_margin = chart_stability - lane.chart_stability_threshold
    if chart_margin < 0:
        failed_checks.append("chart_stability")

    transport_margin = transport_coherence - lane.transport_coherence_threshold
    if transport_margin < 0:
        failed_checks.append("transport_coherence")

    return {
        "passed": not failed_checks,
        "failed_checks": failed_checks,
        "min_margin": min(intervention_margin, synergy_margin, chart_margin, transport_margin),
        "thresholds": asdict(lane),
    }


def compare_baselines(
    intervention_faithfulness: float, baseline_scores: dict[str, float], margin_threshold: float
) -> dict[str, Any]:
    if not baseline_scores:
        return {
            "status": "missing-baselines",
            "strongest_baseline": 0.0,
            "delta_vs_strongest": intervention_faithfulness,
            "beats_baseline": True,
            "baseline_scores": {},
        }

    ordered = sorted(baseline_scores.items(), key=lambda item: item[0])
    strongest_baseline_id, strongest_baseline = max(ordered, key=lambda item: item[1])
    delta_vs_strongest = intervention_faithfulness - strongest_baseline
    beats_baseline = delta_vs_strongest >= margin_threshold
    return {
        "status": "ok",
        "strongest_baseline_id": strongest_baseline_id,
        "strongest_baseline": strongest_baseline,
        "delta_vs_strongest": delta_vs_strongest,
        "beats_baseline": beats_baseline,
        "baseline_scores": baseline_scores,
    }


def evaluate_falsifiers(
    lane: BenchmarkLaneConfig,
    intervention_faithfulness: float,
    synergy_score_max: float,
    chart_stability: float,
    transport_coherence: float,
    geodesic_deviation: float | None,
    strongest_baseline: float,
) -> dict[str, bool]:
    report = {
        "pairwise_sufficiency_triggered": strongest_baseline + lane.baseline_margin_threshold
        >= intervention_faithfulness,
        "chart_fragility_triggered": chart_stability < lane.chart_stability_threshold,
        "transport_irrelevance_triggered": transport_coherence < lane.transport_coherence_threshold,
        "geometry_non_predictiveness_triggered": geodesic_deviation is None
        or abs(geodesic_deviation) < 0.01,
        "spurious_synergy_triggered": synergy_score_max < lane.synergy_threshold,
    }
    report["any_triggered"] = any(report.values())
    return report


def conformance_class(
    admission_passed: bool, beats_baseline: bool, falsifiers: dict[str, bool]
) -> str:
    if admission_passed and beats_baseline and not falsifiers.get("any_triggered", False):
        return "conformant"
    if admission_passed and beats_baseline:
        return "provisional"
    return "rejected"

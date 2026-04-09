from __future__ import annotations

from .artifacts import build_artifact_bundle, build_artifact_entry
from ._kernel_math import (
    canonicalize_mechanisms as _canonicalize_mechanisms_fallback,
    estimate_pullback_metric as _estimate_pullback_metric_fallback,
    fit_atlas as _fit_atlas_fallback,
    fit_transport as _fit_transport_fallback,
    materialize_hyperpaths as _materialize_hyperpaths_fallback,
    propose_events as _propose_events_fallback,
    verify_mechanisms as _verify_mechanisms_fallback,
)
from ._native import call_workspace_bundle, call_workspace_kernels

_RUN_GRAPH_STAGES = [
    "Ingest",
    "Atlas",
    "Metric",
    "Transport",
    "Hypergraph",
    "VerifyMechanisms",
    "Canonicalize",
    "Validate",
    "AssembleBundle",
    "Persist",
    "Report",
]


def _resolved_ids(lane_id: str, run_id: str | None, trace_id: str | None) -> tuple[str, str]:
    return (run_id or f"kernel-run-{lane_id}", trace_id or f"kernel-trace-{lane_id}")


def _build_workspace_bundle_output(
    *,
    input_payload: dict[str, object],
    kernel_output: dict[str, object],
) -> dict[str, object]:
    lane_id = str(input_payload["lane_id"])
    behavior_id = str(input_payload["behavior_id"])
    model_id = str(input_payload["model_id"])
    threshold = float(input_payload["intervention_delta_threshold"])
    run_id, trace_id = _resolved_ids(
        lane_id,
        input_payload.get("run_id") if isinstance(input_payload.get("run_id"), str) else None,
        input_payload.get("trace_id") if isinstance(input_payload.get("trace_id"), str) else None,
    )
    producer = "geoclt:runtime:0.2.0"
    created_at = "2026-01-01T00:00:00Z"
    sample_id = f"sample-{behavior_id}"

    artifacts: list[dict[str, object]] = []

    for event in kernel_output["candidate_event_table"]["events"]:
        artifacts.append(
            build_artifact_entry(
                artifact_type="event_record",
                schema_version=2,
                producer=producer,
                trace_id=trace_id,
                run_id=run_id,
                created_at=created_at,
                payload={
                    "event_id": event["event_id"],
                    "sample_id": sample_id,
                    "layer_span": event["layer_span"],
                    "time_window": "workspace-kernel",
                    "participant_set": event["participant_set"],
                    "participant_types": event["participant_types"],
                    "transport_context_id": event.get("transport_context_id"),
                    "causal_weight": event["causal_weight"],
                    "reliability_score": event["reliability_score"],
                    "proposer_score": event.get("proposer_score"),
                },
            )
        )

    for path in kernel_output["admitted_hyperpath_table"]["hyperpaths"]:
        artifacts.append(
            build_artifact_entry(
                artifact_type="hyperpath_record",
                schema_version=2,
                producer=producer,
                trace_id=trace_id,
                run_id=run_id,
                created_at=created_at,
                payload={
                    "path_id": path["path_id"],
                    "behavior_id": path["behavior_id"],
                    "event_ids": path["event_ids"],
                    "chart_ids": path["chart_ids"],
                    "layer_ids": path["layer_ids"],
                    "transport_edge_ids": path["transport_edge_ids"],
                    "geodesic_deviation": path["geodesic_deviation"],
                    "chart_stability": path["chart_stability"],
                    "transport_coherence": path["transport_coherence"],
                    "intervention_faithfulness": path["intervention_faithfulness"],
                    "synergy_score_max": path["synergy_score_max"],
                    "admitted": path["admitted"],
                },
            )
        )

    best_intervention = max(
        (
            float(path["intervention_faithfulness"])
            for path in kernel_output["admitted_hyperpath_table"]["hyperpaths"]
        ),
        default=0.0,
    )
    artifacts.append(
        build_artifact_entry(
            artifact_type="benchmark_result",
            schema_version=2,
            producer=producer,
            trace_id=trace_id,
            run_id=run_id,
            created_at=created_at,
            payload={
                "run_id": run_id,
                "model_id": model_id,
                "task_id": behavior_id,
                "baseline_id": "kernel_stage",
                "metric_name": "intervention_faithfulness",
                "metric_value": round(best_intervention, 6),
                "threshold": threshold,
                "passed": kernel_output["mechanism_verification"]["passed_count"] > 0,
            },
        )
    )

    for candidate in kernel_output["canonicalized_mechanisms"]["candidates"]:
        artifacts.append(
            build_artifact_entry(
                artifact_type="mechanism_candidate",
                schema_version=1,
                producer=producer,
                trace_id=trace_id,
                run_id=run_id,
                created_at=created_at,
                payload={
                    "candidate_id": candidate["candidate_id"],
                    "mechanism_class_type": candidate["mechanism_class_type"],
                    "canonical_hyperpath_signature": candidate["canonical_hyperpath_signature"],
                    "normalized_causal_dependency_set": candidate[
                        "normalized_causal_dependency_set"
                    ],
                    "invariant_feature_signature": candidate["invariant_feature_signature"],
                    "candidate_score": candidate["candidate_score"],
                },
            )
        )

    for class_record in kernel_output["canonicalized_mechanisms"]["classes"]:
        artifacts.append(
            build_artifact_entry(
                artifact_type="mechanism_class_record",
                schema_version=2,
                producer=producer,
                trace_id=trace_id,
                run_id=run_id,
                created_at=created_at,
                payload={
                    "mechanism_class_id": class_record["mechanism_class_id"],
                    "member_path_ids": class_record["member_path_ids"],
                    "atlas_variants_tested": class_record["atlas_variants_tested"],
                    "persistence_score": class_record["persistence_score"],
                    "minimality_score": class_record["minimality_score"],
                    "geometry_predictiveness": class_record["geometry_predictiveness"],
                    "pass_fail_status": class_record["pass_fail_status"],
                },
            )
        )

    artifact_bundle = build_artifact_bundle(
        run_id=run_id,
        trace_id=trace_id,
        producer=producer,
        created_at=created_at,
        artifacts=artifacts,
    )
    return {
        "run_graph": {"stages": _RUN_GRAPH_STAGES},
        "kernel_output": kernel_output,
        "artifact_bundle": artifact_bundle,
    }


def run_workspace_kernels(
    *,
    model_id: str,
    lane_id: str,
    behavior_id: str,
    profile: str,
    feature_hints: list[str] | None = None,
    intervention_faithfulness: float,
    synergy_score_max: float,
    chart_stability_hint: float,
    transport_coherence_hint: float,
    geodesic_deviation_hint: float,
    intervention_delta_threshold: float = 0.10,
    synergy_threshold: float = 0.05,
    chart_stability_threshold: float = 0.70,
    transport_coherence_threshold: float = 0.70,
    baseline_margin_threshold: float = 0.05,
    run_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, object]:
    payload = {
        "model_id": model_id,
        "lane_id": lane_id,
        "behavior_id": behavior_id,
        "profile": profile,
        "run_id": run_id,
        "trace_id": trace_id,
        "feature_hints": feature_hints or [],
        "intervention_faithfulness": intervention_faithfulness,
        "synergy_score_max": synergy_score_max,
        "chart_stability_hint": chart_stability_hint,
        "transport_coherence_hint": transport_coherence_hint,
        "geodesic_deviation_hint": geodesic_deviation_hint,
        "intervention_delta_threshold": intervention_delta_threshold,
        "synergy_threshold": synergy_threshold,
        "chart_stability_threshold": chart_stability_threshold,
        "transport_coherence_threshold": transport_coherence_threshold,
        "baseline_margin_threshold": baseline_margin_threshold,
    }
    native = call_workspace_kernels(payload)
    if native is not None:
        return native

    atlas = _fit_atlas_fallback(
        model_id=model_id,
        lane_id=lane_id,
        profile=profile,
        feature_hints=feature_hints or [],
    )
    atlas["overlap_score"] = round(
        max(0.60, min(0.99, (atlas["overlap_score"] + chart_stability_hint) / 2.0)),
        6,
    )
    metric = _estimate_pullback_metric_fallback(
        lane_id=lane_id,
        atlas=atlas,
        feature_hints=feature_hints or [],
    )
    transport = _fit_transport_fallback(lane_id=lane_id, atlas=atlas, metric=metric)
    transport["coherence"] = round(
        max(0.60, min(0.99, (transport["coherence"] + transport_coherence_hint) / 2.0)),
        6,
    )
    transport["loop_consistency"] = round(
        max(0.60, min(0.99, (transport["loop_consistency"] + transport_coherence_hint) / 2.0)),
        6,
    )
    transport["geodesic_deviation"] = round(
        max(0.01, min(0.40, (transport["geodesic_deviation"] + geodesic_deviation_hint) / 2.0)),
        6,
    )
    candidate_event_table = _propose_events_fallback(
        lane_id=lane_id,
        behavior_id=behavior_id,
        transport=transport,
        feature_hints=feature_hints or [],
    )
    admitted_hyperpath_table = _materialize_hyperpaths_fallback(
        lane_id=lane_id,
        behavior_id=behavior_id,
        candidate_event_table=candidate_event_table,
        atlas=atlas,
        transport=transport,
        intervention_faithfulness=intervention_faithfulness,
        synergy_score_max=synergy_score_max,
        chart_stability=chart_stability_hint,
        geodesic_deviation=geodesic_deviation_hint,
    )
    lane = {
        "lane_id": lane_id,
        "behavior_id": behavior_id,
        "intervention_delta_threshold": intervention_delta_threshold,
        "synergy_threshold": synergy_threshold,
        "chart_stability_threshold": chart_stability_threshold,
        "transport_coherence_threshold": transport_coherence_threshold,
        "baseline_margin_threshold": baseline_margin_threshold,
    }
    mechanism_verification = _verify_mechanisms_fallback(
        lane=lane,
        hyperpaths=admitted_hyperpath_table,
    )
    canonicalized_mechanisms = _canonicalize_mechanisms_fallback(
        mechanism_verification=mechanism_verification,
        atlas=atlas,
        run_id=run_id or f"kernel-run-{lane_id}",
        trace_id=trace_id or f"kernel-trace-{lane_id}",
    )
    return {
        "atlas": atlas,
        "metric": metric,
        "transport": transport,
        "candidate_event_table": candidate_event_table,
        "admitted_hyperpath_table": admitted_hyperpath_table,
        "mechanism_verification": mechanism_verification,
        "canonicalized_mechanisms": canonicalized_mechanisms,
    }


def run_workspace_bundle(
    *,
    model_id: str,
    lane_id: str,
    behavior_id: str,
    profile: str,
    feature_hints: list[str] | None = None,
    intervention_faithfulness: float,
    synergy_score_max: float,
    chart_stability_hint: float,
    transport_coherence_hint: float,
    geodesic_deviation_hint: float,
    intervention_delta_threshold: float = 0.10,
    synergy_threshold: float = 0.05,
    chart_stability_threshold: float = 0.70,
    transport_coherence_threshold: float = 0.70,
    baseline_margin_threshold: float = 0.05,
    run_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, object]:
    payload = {
        "model_id": model_id,
        "lane_id": lane_id,
        "behavior_id": behavior_id,
        "profile": profile,
        "run_id": run_id,
        "trace_id": trace_id,
        "feature_hints": feature_hints or [],
        "intervention_faithfulness": intervention_faithfulness,
        "synergy_score_max": synergy_score_max,
        "chart_stability_hint": chart_stability_hint,
        "transport_coherence_hint": transport_coherence_hint,
        "geodesic_deviation_hint": geodesic_deviation_hint,
        "intervention_delta_threshold": intervention_delta_threshold,
        "synergy_threshold": synergy_threshold,
        "chart_stability_threshold": chart_stability_threshold,
        "transport_coherence_threshold": transport_coherence_threshold,
        "baseline_margin_threshold": baseline_margin_threshold,
    }
    native = call_workspace_bundle(payload)
    if native is not None:
        return native

    kernel_output = run_workspace_kernels(
        model_id=model_id,
        lane_id=lane_id,
        behavior_id=behavior_id,
        profile=profile,
        feature_hints=feature_hints,
        intervention_faithfulness=intervention_faithfulness,
        synergy_score_max=synergy_score_max,
        chart_stability_hint=chart_stability_hint,
        transport_coherence_hint=transport_coherence_hint,
        geodesic_deviation_hint=geodesic_deviation_hint,
        intervention_delta_threshold=intervention_delta_threshold,
        synergy_threshold=synergy_threshold,
        chart_stability_threshold=chart_stability_threshold,
        transport_coherence_threshold=transport_coherence_threshold,
        baseline_margin_threshold=baseline_margin_threshold,
        run_id=run_id,
        trace_id=trace_id,
    )
    return _build_workspace_bundle_output(input_payload=payload, kernel_output=kernel_output)

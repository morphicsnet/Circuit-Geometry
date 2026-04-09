from __future__ import annotations

from typing import Any

from .artifacts import stable_hash


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _ratio(seed: dict[str, Any], label: str) -> float:
    digest = stable_hash({"label": label, "seed": seed})
    return int(digest[:16], 16) / float(0xFFFFFFFFFFFFFFFF)


def _bounded_float(seed: dict[str, Any], label: str, lower: float, upper: float) -> float:
    return lower + (upper - lower) * _ratio(seed, label)


def _bounded_int(seed: dict[str, Any], label: str, lower: int, upper: int) -> int:
    if lower == upper:
        return lower
    return lower + round(_ratio(seed, label) * (upper - lower))


def normalized_features(feature_hints: list[str] | None, *fallbacks: str) -> list[str]:
    ordered = sorted({value for value in (feature_hints or []) if value})
    if ordered:
        return ordered
    return [value for value in fallbacks if value]


def feature_hints_from_candidate_events(
    candidate_events: list[dict[str, Any]], behavior_id: str
) -> list[str]:
    hints: list[str] = []
    for event in candidate_events:
        hints.extend(str(value) for value in event.get("participant_set", []))
    if not hints:
        hints.append(f"behavior:{behavior_id}")
    return sorted(dict.fromkeys(hints))


def fit_atlas(
    *,
    model_id: str,
    lane_id: str,
    profile: str,
    feature_hints: list[str] | None = None,
) -> dict[str, Any]:
    features = normalized_features(feature_hints, f"behavior:{profile}", f"lane:{lane_id}", "atlas:default")
    seed = {
        "model_id": model_id,
        "lane_id": lane_id,
        "profile": profile,
        "feature_hints": features,
    }
    chart_count = _bounded_int(seed, "atlas_chart_count", 3, 6)
    chart_ids = [f"chart-{index + 1}" for index in range(chart_count)]
    chart_overlaps = []
    for index, from_chart_id in enumerate(chart_ids):
        to_chart_id = chart_ids[(index + 1) % chart_count]
        overlap_score = _bounded_float(
            {"seed": seed, "from": from_chart_id, "to": to_chart_id},
            "atlas_overlap",
            0.62,
            0.97,
        )
        shared_features = [features[(index + offset) % len(features)] for offset in range(min(3, len(features)))]
        chart_overlaps.append(
            {
                "from_chart_id": from_chart_id,
                "to_chart_id": to_chart_id,
                "overlap_score": round(overlap_score, 6),
                "shared_features": shared_features,
            }
        )
    overlap_score = sum(item["overlap_score"] for item in chart_overlaps) / len(chart_overlaps)
    return {
        "model_id": model_id,
        "lane_id": lane_id,
        "profile": profile,
        "chart_count": chart_count,
        "overlap_score": round(_clamp(overlap_score, 0.60, 0.99), 6),
        "chart_ids": chart_ids,
        "chart_overlaps": chart_overlaps,
    }


def estimate_pullback_metric(
    *,
    lane_id: str,
    atlas: dict[str, Any],
    feature_hints: list[str] | None = None,
) -> dict[str, Any]:
    features = normalized_features(feature_hints, "metric:default")
    seed = {"lane_id": lane_id, "atlas": atlas, "feature_hints": features}
    distortion_score = _bounded_float(seed, "metric_distortion", 0.06, 0.34)
    curvature_summary = _bounded_float(seed, "metric_curvature", 0.41, 0.93)
    geodesic_stability = _clamp((atlas["overlap_score"] + (1.0 - distortion_score)) / 2.0, 0.55, 0.99)
    patch_count = _bounded_int(seed, "metric_patch_count", max(1, int(atlas["chart_count"])), int(atlas["chart_count"]) + 3)
    chart_energy = _clamp((curvature_summary + atlas["overlap_score"]) / 2.0, 0.35, 0.99)
    return {
        "lane_id": lane_id,
        "chart_id": (atlas.get("chart_ids") or ["chart-1"])[0],
        "curvature_summary": round(curvature_summary, 6),
        "distortion_score": round(distortion_score, 6),
        "geodesic_stability": round(geodesic_stability, 6),
        "patch_count": patch_count,
        "chart_energy": round(chart_energy, 6),
        "feature_signature": features,
    }


def fit_transport(*, lane_id: str, atlas: dict[str, Any], metric: dict[str, Any]) -> dict[str, Any]:
    coherence = _clamp(
        (atlas["overlap_score"] + metric["geodesic_stability"] + metric["chart_energy"]) / 3.0,
        0.60,
        0.99,
    )
    distortion = _clamp((metric["distortion_score"] * 0.7) + ((1.0 - coherence) * 0.3), 0.01, 0.45)
    loop_consistency = _clamp((coherence + atlas["overlap_score"]) / 2.0, 0.60, 0.99)
    geodesic_deviation = _clamp((1.0 - loop_consistency) + distortion * 0.2, 0.01, 0.40)
    chart_ids = atlas.get("chart_ids") or ["chart-1", "chart-2"]
    transport_edge_ids = [f"{left}->{right}" for left, right in zip(chart_ids, chart_ids[1:])]
    return {
        "lane_id": lane_id,
        "context_id": f"transport-{lane_id}",
        "loop_consistency": round(loop_consistency, 6),
        "distortion": round(distortion, 6),
        "coherence": round(coherence, 6),
        "geodesic_deviation": round(geodesic_deviation, 6),
        "transport_edge_ids": transport_edge_ids,
    }


def _participant_type(participant: str) -> str:
    if participant.startswith("sae:"):
        return "sae"
    if participant.startswith("head:"):
        return "attention_head"
    if participant.startswith("mlp:"):
        return "mlp_gate"
    return "feature"


def propose_events(
    *,
    lane_id: str,
    behavior_id: str,
    transport: dict[str, Any],
    feature_hints: list[str] | None = None,
) -> dict[str, Any]:
    features = normalized_features(feature_hints, f"behavior:{behavior_id}", "sae:fallback", "head:5:1")
    seed = {
        "lane_id": lane_id,
        "behavior_id": behavior_id,
        "transport": transport,
        "feature_hints": features,
    }
    candidate_count = _bounded_int(seed, "hypergraph_candidate_count", 2, 3)
    events: list[dict[str, Any]] = []
    for index in range(candidate_count):
        layer_start = 4 + index
        feature = features[index % len(features)]
        alternate = features[(index + 1) % len(features)]
        participant_set = [
            f"sae:{feature}",
            f"head:{layer_start}:{index % 12}",
            f"mlp:{layer_start + 1}:{(index * 7) % 64}",
        ]
        causal_weight = _clamp(transport["coherence"] - (index * 0.04), 0.05, 0.99)
        reliability_score = _clamp(transport["loop_consistency"] - (index * 0.03), 0.05, 0.99)
        proposer_score = _clamp((causal_weight + reliability_score) / 2.0, 0.05, 0.99)
        event_seed = f"{lane_id}:{behavior_id}:{index}:{'|'.join(participant_set)}"
        events.append(
            {
                "event_id": stable_hash({"event_seed": event_seed})[:32],
                "participant_set": participant_set,
                "participant_types": [_participant_type(value) for value in participant_set],
                "layer_span": [layer_start, layer_start + 1],
                "feature_signature": [feature, alternate],
                "transport_context_id": transport["context_id"],
                "causal_weight": round(causal_weight, 6),
                "reliability_score": round(reliability_score, 6),
                "proposer_score": round(proposer_score, 6),
            }
        )
    return {
        "lane_id": lane_id,
        "candidate_count": len(events),
        "events": events,
    }


def materialize_hyperpaths(
    *,
    lane_id: str,
    behavior_id: str,
    candidate_event_table: dict[str, Any],
    atlas: dict[str, Any],
    transport: dict[str, Any],
    intervention_faithfulness: float,
    synergy_score_max: float,
    chart_stability: float,
    geodesic_deviation: float,
) -> dict[str, Any]:
    events = candidate_event_table.get("events", [])
    if not events:
        return {"lane_id": lane_id, "admitted_count": 0, "hyperpaths": []}
    hyperpaths: list[dict[str, Any]] = []
    group_size = min(2, len(events))
    for index in range(0, len(events), group_size):
        chunk = events[index:index + group_size]
        path_seed = f"{lane_id}:{behavior_id}:{index}:{'|'.join(event['event_id'] for event in chunk)}"
        admitted = (
            intervention_faithfulness >= 0.10
            and synergy_score_max >= 0.05
            and chart_stability >= 0.70
            and transport["coherence"] >= 0.70
        )
        layer_ids = sorted({layer for event in chunk for layer in event.get("layer_span", [])})
        hyperpaths.append(
            {
                "path_id": stable_hash({"path_seed": path_seed})[:32],
                "behavior_id": behavior_id,
                "event_ids": [event["event_id"] for event in chunk],
                "chart_ids": list((atlas.get("chart_ids") or ["chart-1", "chart-2"])[:2]),
                "layer_ids": layer_ids,
                "transport_edge_ids": list((transport.get("transport_edge_ids") or ["edge-1"])[:2]),
                "geodesic_deviation": round(geodesic_deviation, 6),
                "chart_stability": round(chart_stability, 6),
                "transport_coherence": round(transport["coherence"], 6),
                "intervention_faithfulness": round(intervention_faithfulness, 6),
                "synergy_score_max": round(synergy_score_max, 6),
                "admitted": admitted,
            }
        )
    admitted_count = sum(1 for path in hyperpaths if path["admitted"])
    return {
        "lane_id": lane_id,
        "admitted_count": admitted_count,
        "hyperpaths": hyperpaths,
    }


def verify_mechanisms(*, lane: dict[str, Any], hyperpaths: dict[str, Any]) -> dict[str, Any]:
    mechanisms: list[dict[str, Any]] = []
    for path in hyperpaths.get("hyperpaths", []):
        failed_checks: list[str] = []
        if path["intervention_faithfulness"] < lane["intervention_delta_threshold"]:
            failed_checks.append("intervention_faithfulness")
        if path["synergy_score_max"] < lane["synergy_threshold"]:
            failed_checks.append("synergy_score_max")
        if path["chart_stability"] < lane["chart_stability_threshold"]:
            failed_checks.append("chart_stability")
        if path["transport_coherence"] < lane["transport_coherence_threshold"]:
            failed_checks.append("transport_coherence")
        signature = {
            "path_id": path["path_id"],
            "event_ids": sorted(path["event_ids"]),
            "chart_ids": sorted(path["chart_ids"]),
            "transport_edge_ids": sorted(path["transport_edge_ids"]),
            "behavior_id": path["behavior_id"],
        }
        dependencies = sorted(path["transport_edge_ids"] + path["chart_ids"])
        invariant_features = sorted(path["event_ids"])
        candidate_score = (
            path["intervention_faithfulness"]
            + path["synergy_score_max"]
            + path["chart_stability"]
            + path["transport_coherence"]
        ) / 4.0
        mechanisms.append(
            {
                "mechanism_id": f"mechanism-{stable_hash({'signature': signature, 'dependencies': dependencies, 'invariants': invariant_features})}",
                "path_id": path["path_id"],
                "mechanism_class_type": "causal_hyperpath",
                "canonical_hyperpath_signature": signature,
                "normalized_causal_dependency_set": dependencies,
                "invariant_feature_signature": invariant_features,
                "candidate_score": round(candidate_score, 6),
                "causal_delta": round(path["intervention_faithfulness"] - lane["intervention_delta_threshold"], 6),
                "synergy": round(path["synergy_score_max"], 6),
                "passed": not failed_checks and bool(path["admitted"]),
                "failed_checks": failed_checks,
            }
        )
    passed_count = sum(1 for mechanism in mechanisms if mechanism["passed"])
    return {
        "lane_id": lane["lane_id"],
        "behavior_id": lane["behavior_id"],
        "verified_count": len(mechanisms),
        "passed_count": passed_count,
        "mechanisms": mechanisms,
    }


def canonicalize_mechanisms(
    *,
    mechanism_verification: dict[str, Any],
    atlas: dict[str, Any],
    run_id: str,
    trace_id: str,
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = {}
    for mechanism in mechanism_verification.get("mechanisms", []):
        candidate_payload = {
            "mechanism_id": mechanism["mechanism_id"],
            "path_id": mechanism["path_id"],
            "class_type": mechanism["mechanism_class_type"],
            "signature": mechanism["canonical_hyperpath_signature"],
            "dependencies": mechanism["normalized_causal_dependency_set"],
            "invariants": mechanism["invariant_feature_signature"],
            "candidate_score": mechanism["candidate_score"],
        }
        candidate_hash = stable_hash(candidate_payload)
        candidates.append(
            {
                "artifact_id": f"artifact-{candidate_hash}",
                "artifact_type": "mechanism_candidate",
                "schema_version": 2,
                "producer": "geoclt:canonicalize:0.2.0",
                "trace_id": trace_id,
                "run_id": run_id,
                "content_hash": candidate_hash,
                "created_at": "2026-01-01T00:00:00Z",
                "candidate_id": mechanism["mechanism_id"],
                "mechanism_class_type": mechanism["mechanism_class_type"],
                "canonical_hyperpath_signature": mechanism["canonical_hyperpath_signature"],
                "normalized_causal_dependency_set": mechanism["normalized_causal_dependency_set"],
                "invariant_feature_signature": mechanism["invariant_feature_signature"],
                "candidate_score": mechanism["candidate_score"],
            }
        )
        class_key = f"{mechanism['mechanism_class_type']}::{mechanism_verification['behavior_id']}"
        grouped.setdefault(class_key, []).append(mechanism)

    classes: list[dict[str, Any]] = []
    for class_key, members in sorted(grouped.items()):
        member_path_ids = [member["path_id"] for member in members]
        class_hash = stable_hash(
            {
                "class_key": class_key,
                "member_path_ids": member_path_ids,
                "atlas_variants_tested": atlas.get("chart_ids", []),
            }
        )
        passed_count = sum(1 for member in members if member["passed"])
        status = "passed" if passed_count == len(members) else "mixed" if passed_count else "rejected"
        average_candidate_score = sum(member["candidate_score"] for member in members) / len(members)
        average_synergy = sum(member["synergy"] for member in members) / len(members)
        class_id = f"cluster-{stable_hash({'members': sorted(member['mechanism_id'] for member in members)})}"
        classes.append(
            {
                "artifact_id": f"artifact-{class_hash}",
                "artifact_type": "mechanism_class_record",
                "schema_version": 2,
                "producer": "geoclt:canonicalize:0.2.0",
                "trace_id": trace_id,
                "run_id": run_id,
                "content_hash": class_hash,
                "created_at": "2026-01-01T00:00:00Z",
                "mechanism_class_id": class_id,
                "member_path_ids": member_path_ids,
                "atlas_variants_tested": list(atlas.get("chart_ids", [])),
                "persistence_score": round(average_candidate_score, 6),
                "minimality_score": round(passed_count / len(members), 6),
                "geometry_predictiveness": round(average_synergy, 6),
                "pass_fail_status": status,
            }
        )
    return {
        "candidates": candidates,
        "classes": classes,
    }

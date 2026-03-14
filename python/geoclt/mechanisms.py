from __future__ import annotations

from typing import Any

from .artifacts import stable_hash


def canonical_hyperpath_signature(path: dict[str, Any]) -> dict[str, Any]:
    return {
        "path_id": path.get("path_id", ""),
        "behavior_id": path.get("behavior_id", ""),
        "event_ids": sorted(path.get("event_ids", [])),
        "chart_ids": sorted(path.get("chart_ids", [])),
        "layer_ids": path.get("layer_ids", []),
        "transport_edge_ids": sorted(path.get("transport_edge_ids", [])),
        "geodesic_deviation": path.get("geodesic_deviation"),
        "chart_stability": path.get("chart_stability"),
        "transport_coherence": path.get("transport_coherence"),
        "intervention_faithfulness": path.get("intervention_faithfulness"),
        "synergy_score_max": path.get("synergy_score_max"),
    }


def derive_mechanism_id(
    *,
    mechanism_class_type: str,
    hyperpath: dict[str, Any],
    causal_dependency_set: list[str],
    invariant_features: list[str],
) -> str:
    payload = {
        "mechanism_class_type": mechanism_class_type,
        "canonical_hyperpath_signature": canonical_hyperpath_signature(hyperpath),
        "normalized_causal_dependency_set": sorted(causal_dependency_set),
        "invariant_feature_signature": sorted(invariant_features),
    }
    return f"mechanism-{stable_hash(payload)}"


def derive_cluster_id(member_mechanism_ids: list[str]) -> str:
    return f"cluster-{stable_hash(sorted(set(member_mechanism_ids)))}"


def cluster_family(members: list[dict[str, Any]]) -> dict[str, Any]:
    ids = sorted({member["mechanism_id"] for member in members})
    return {
        "cluster_id": derive_cluster_id(ids),
        "member_mechanism_ids": ids,
        "member_count": len(ids),
    }

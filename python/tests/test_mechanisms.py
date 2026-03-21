from geoclt.mechanisms import cluster_family, derive_cluster_id, derive_mechanism_id


def _hyperpath() -> dict:
    return {
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
    }


def test_mechanism_id_deterministic_and_noise_invariant():
    first = derive_mechanism_id(
        mechanism_class_type="causal_hyperpath",
        hyperpath={**_hyperpath(), "trace_id": "trace-1", "run_id": "run-1"},
        causal_dependency_set=["dep-b", "dep-a"],
        invariant_features=["inv-2", "inv-1"],
    )
    second = derive_mechanism_id(
        mechanism_class_type="causal_hyperpath",
        hyperpath={**_hyperpath(), "trace_id": "trace-2", "run_id": "run-2"},
        causal_dependency_set=["dep-a", "dep-b"],
        invariant_features=["inv-1", "inv-2"],
    )
    assert first == second


def test_mechanism_id_stable_for_chart_substitution_and_schema_replay():
    chart_substituted = derive_mechanism_id(
        mechanism_class_type="causal_hyperpath",
        hyperpath={**_hyperpath(), "chart_ids": ["chart-a", "chart-b"], "schema_version": 1},
        causal_dependency_set=["dep-a", "dep-b"],
        invariant_features=["inv-1", "inv-2"],
    )
    baseline = derive_mechanism_id(
        mechanism_class_type="causal_hyperpath",
        hyperpath={**_hyperpath(), "chart_ids": ["chart-b", "chart-a"], "schema_version": 2},
        causal_dependency_set=["dep-b", "dep-a"],
        invariant_features=["inv-2", "inv-1"],
    )
    assert chart_substituted == baseline


def test_cluster_identity_is_order_invariant():
    one = derive_cluster_id(["m2", "m1"])
    two = derive_cluster_id(["m1", "m2"])
    assert one == two



def test_cluster_family_assigns_deterministically():
    family = cluster_family([
        {"mechanism_id": "m2"},
        {"mechanism_id": "m1"},
        {"mechanism_id": "m1"},
    ])
    assert family["member_count"] == 2
    assert family["member_mechanism_ids"] == ["m1", "m2"]


def test_cluster_family_high_cardinality_is_deterministic():
    members = [{"mechanism_id": f"m{index % 127}"} for index in range(512)]
    family_one = cluster_family(members)
    family_two = cluster_family(list(reversed(members)))
    assert family_one["cluster_id"] == family_two["cluster_id"]
    assert family_one["member_count"] == 127

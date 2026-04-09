from __future__ import annotations

from geoclt import BenchmarkLaneConfig, Workspace, run_workspace_bundle, run_workspace_kernels
from geoclt.real_pipeline import RealPipelineOutput
import geoclt.workspace as workspace_module


def test_run_workspace_kernels_returns_canonicalized_mechanisms():
    output = run_workspace_kernels(
        model_id="gpt2",
        lane_id="factual_retrieval.v1",
        behavior_id="factual_retrieval",
        profile="factual_retrieval",
        feature_hints=["sae:f12", "head:5:3"],
        intervention_faithfulness=0.22,
        synergy_score_max=0.12,
        chart_stability_hint=0.88,
        transport_coherence_hint=0.84,
        geodesic_deviation_hint=0.04,
        run_id="run-1",
        trace_id="trace-1",
    )

    assert set(output) == {
        "atlas",
        "metric",
        "transport",
        "candidate_event_table",
        "admitted_hyperpath_table",
        "mechanism_verification",
        "canonicalized_mechanisms",
    }
    assert output["mechanism_verification"]["verified_count"] >= 1
    assert len(output["canonicalized_mechanisms"]["candidates"]) >= 1
    assert len(output["canonicalized_mechanisms"]["classes"]) >= 1


def test_run_workspace_bundle_returns_typed_artifact_bundle():
    output = run_workspace_bundle(
        model_id="gpt2",
        lane_id="factual_retrieval.v1",
        behavior_id="factual_retrieval",
        profile="factual_retrieval",
        feature_hints=["sae:f12", "head:5:3"],
        intervention_faithfulness=0.22,
        synergy_score_max=0.12,
        chart_stability_hint=0.88,
        transport_coherence_hint=0.84,
        geodesic_deviation_hint=0.04,
    )

    assert set(output) == {"run_graph", "kernel_output", "artifact_bundle"}
    assert output["artifact_bundle"]["bundle_hash"]
    artifact_types = {
        artifact["artifact_type"] for artifact in output["artifact_bundle"]["artifacts"]
    }
    assert {
        "event_record",
        "hyperpath_record",
        "benchmark_result",
        "mechanism_candidate",
        "mechanism_class_record",
    }.issubset(artifact_types)


def test_workspace_benchmark_records_canonicalized_mechanisms(monkeypatch, tmp_path):
    def fake_real_pipeline(model_id: str, lane_id: str, behavior_id: str) -> RealPipelineOutput:
        _ = (model_id, lane_id, behavior_id)
        return RealPipelineOutput(
            model_id="gpt2",
            backend="transformers-real",
            prompt="real-prompt",
            token_count=12,
            intervention_faithfulness=0.22,
            synergy_score_max=0.15,
            chart_stability=0.91,
            transport_coherence=0.88,
            geodesic_deviation=0.04,
            baseline_scores={
                "single_sae": 0.10,
                "ensemble_sae": 0.11,
                "pairwise_graph": 0.12,
                "geometry_free": 0.13,
            },
            candidate_events=[
                {
                    "event_id": "event-a",
                    "participant_set": ["sae:f1", "head:5:2", "mlp:6:3"],
                    "participant_types": ["sae", "attention_head", "mlp_gate"],
                    "causal_weight": 0.2,
                    "reliability_score": 0.9,
                }
            ],
        )

    monkeypatch.setattr("geoclt.workspace.run_real_pipeline", fake_real_pipeline)

    workspace = Workspace.create(tmp_path / "workspace")
    workspace.attach_model("gpt2-small")
    workspace.fit_atlas(profile="factual_retrieval")
    workspace.fit_transport()
    workspace.propose_events()
    workspace.verify_mechanisms()

    run = workspace.run_benchmark(
        BenchmarkLaneConfig(lane_id="factual_retrieval.v1", behavior_id="factual_retrieval")
    )
    falsifier_sheet = workspace.get_run(run["run_id"])["artifacts"]["falsifier_sheet"]["payload"]
    assert "canonicalized_mechanisms" in falsifier_sheet
    assert falsifier_sheet["canonicalized_mechanisms"]["candidates"]
    assert workspace.metadata["canonicalized_mechanisms"]["classes"]
    artifact_bundle = workspace.get_run(run["run_id"])["artifacts"]["artifact_bundle"]["payload"]
    assert artifact_bundle["bundle_hash"] == run["artifact_bundle_hash"]

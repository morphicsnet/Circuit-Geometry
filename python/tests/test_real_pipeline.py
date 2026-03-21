from __future__ import annotations

from geoclt.profiles import BenchmarkLaneConfig
from geoclt.real_pipeline import RealPipelineOutput, resolve_real_model_id
from geoclt.workspace import Workspace


def test_resolve_real_model_id_aliases():
    assert resolve_real_model_id("gpt2-small") == "gpt2"
    assert resolve_real_model_id("gpt2") == "gpt2"
    assert resolve_real_model_id("custom-model") == "custom-model"


def test_workspace_real_mode_uses_real_pipeline(monkeypatch, tmp_path):
    monkeypatch.setenv("GEOCLT_REAL_MODE", "1")

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

    run = workspace.run_benchmark(BenchmarkLaneConfig(lane_id="factual_retrieval.v1", behavior_id="factual_retrieval"))

    assert run["metadata"]["pipeline_mode"] == "real-transformers"
    assert run["metadata"]["backend_type"] == "transformers-real"
    assert run["metadata"]["real_mode_enabled"] is True

    falsifier_sheet = workspace.get_run(run["run_id"])["artifacts"]["falsifier_sheet"]["payload"]
    assert falsifier_sheet["pipeline_mode"] == "real-transformers"
    assert falsifier_sheet["backend_type"] == "transformers-real"
    assert falsifier_sheet["token_count"] == 12
    assert isinstance(falsifier_sheet["prompt_hash"], str)

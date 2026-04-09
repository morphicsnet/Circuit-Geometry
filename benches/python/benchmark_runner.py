from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from geoclt import BenchmarkLaneConfig, Workspace
from geoclt.real_pipeline import RealPipelineOutput
import geoclt.workspace as workspace_module


def _fake_real_pipeline(model_id: str, lane_id: str, behavior_id: str) -> RealPipelineOutput:
    _ = (model_id, lane_id, behavior_id)
    return RealPipelineOutput(
        model_id="gpt2",
        backend="transformers-bench",
        prompt="bench-prompt",
        token_count=12,
        intervention_faithfulness=0.22,
        synergy_score_max=0.12,
        chart_stability=0.90,
        transport_coherence=0.84,
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
                "causal_weight": 0.20,
                "reliability_score": 0.91,
            }
        ],
    )


def main() -> None:
    with TemporaryDirectory() as tempdir:
        original = workspace_module.run_real_pipeline
        workspace_module.run_real_pipeline = _fake_real_pipeline
        try:
            ws = Workspace.create(Path(tempdir) / "bench")
            ws.attach_model("gpt2-small")
            ws.fit_atlas(profile="factual_retrieval")
            ws.fit_transport()
            ws.propose_events()
            ws.verify_mechanisms()
            report = ws.run_benchmark(
                BenchmarkLaneConfig(
                    lane_id="factual_retrieval.v1",
                    behavior_id="factual_retrieval",
                )
            )
            print(
                {
                    "run_id": report["run_id"],
                    "artifact_bundle_hash": report["artifact_bundle_hash"],
                    "artifact_types": sorted(report["artifact_paths"]),
                }
            )
        finally:
            workspace_module.run_real_pipeline = original


if __name__ == "__main__":
    main()

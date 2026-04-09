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
        backend="transformers-profile",
        prompt="profile-prompt",
        token_count=9,
        intervention_faithfulness=0.24,
        synergy_score_max=0.14,
        chart_stability=0.92,
        transport_coherence=0.87,
        geodesic_deviation=0.03,
        baseline_scores={
            "single_sae": 0.11,
            "ensemble_sae": 0.12,
            "pairwise_graph": 0.13,
            "geometry_free": 0.14,
        },
        candidate_events=[
            {
                "event_id": "event-b",
                "participant_set": ["sae:f7", "head:6:1", "mlp:7:4"],
                "participant_types": ["sae", "attention_head", "mlp_gate"],
                "causal_weight": 0.24,
                "reliability_score": 0.93,
            }
        ],
    )


def main() -> None:
    with TemporaryDirectory() as tempdir:
        original = workspace_module.run_real_pipeline
        workspace_module.run_real_pipeline = _fake_real_pipeline
        try:
            ws = Workspace.create(Path(tempdir) / "profile")
            ws.attach_model("gpt2-small")
            ws.fit_atlas(profile="claims-triage")
            ws.fit_transport()
            ws.propose_events()
            ws.verify_mechanisms()
            report = ws.run_benchmark(
                BenchmarkLaneConfig(
                    lane_id="claims-triage.v1",
                    behavior_id="claims-triage",
                )
            )
            exported = ws.export_report(report["run_id"])
            print(
                {
                    "run_id": report["run_id"],
                    "conformance_class": report["conformance_class"],
                    "report_path": exported["report_path"],
                }
            )
        finally:
            workspace_module.run_real_pipeline = original


if __name__ == "__main__":
    main()

from geoclt import BenchmarkLaneConfig, Workspace
from geoclt.artifacts import read_json


def test_workspace_benchmark_artifacts_and_report(tmp_path):
    ws = Workspace.create(tmp_path / "ws")
    ws.attach_model("gpt2-small")
    ws.fit_atlas(profile="factual_retrieval")
    ws.fit_transport()
    ws.propose_events()
    ws.verify_mechanisms()

    lane = BenchmarkLaneConfig(lane_id="factual_retrieval.v1", behavior_id="factual_retrieval")
    run_one = ws.run_benchmark(lane)
    run_two = ws.run_benchmark(lane)

    assert run_two["status"] == "completed"
    assert len(run_two["artifact_paths"]) == 6

    payloads = {key: read_json(path) for key, path in run_two["artifact_paths"].items()}
    assert set(payloads.keys()) == {
        "atlas_overlap_map",
        "transport_diagnostics",
        "candidate_event_table",
        "admitted_hyperpath_table",
        "falsifier_sheet",
        "artifact_bundle",
    }

    atlas = payloads["atlas_overlap_map"]
    assert all(key in atlas for key in ("model_id", "lane_id", "chart_count", "overlap_score", "profile"))

    transport = payloads["transport_diagnostics"]
    assert all(
        key in transport
        for key in ("lane_id", "loop_consistency", "distortion", "coherence", "geodesic_deviation")
    )

    candidate = payloads["candidate_event_table"]
    assert candidate["candidate_count"] == len(candidate["events"])

    admitted = payloads["admitted_hyperpath_table"]
    assert admitted["admitted_count"] == len(admitted["hyperpaths"])

    falsifier_sheet = payloads["falsifier_sheet"]
    assert all(
        key in falsifier_sheet
        for key in (
            "falsifiers",
            "admission",
            "baseline_report",
            "conformance_class",
            "benchmark_result",
        )
    )

    bundle = payloads["artifact_bundle"]
    assert bundle["bundle_hash"] == run_two["artifact_bundle_hash"]
    artifact_types = {artifact["artifact_type"] for artifact in bundle["artifacts"]}
    assert "mechanism_candidate" in artifact_types
    assert "mechanism_class_record" in artifact_types

    determinism = ws.determinism_for_run(run_two["run_id"])
    assert determinism["is_deterministic"] is True
    assert run_one["artifact_bundle_hash"] == run_two["artifact_bundle_hash"]

    exported = ws.export_report(run_two["run_id"])
    assert exported["status"] == "ok"
    loaded = ws.load_report(run_two["run_id"])
    assert loaded["run"]["run_id"] == run_two["run_id"]

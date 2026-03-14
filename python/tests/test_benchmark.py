from geoclt import Workspace, BenchmarkLaneConfig
from geoclt.benchmark import compare_baselines


def test_benchmark_run(tmp_path):
    ws = Workspace.create(tmp_path / "ws")
    ws.attach_model("gpt2-small")
    ws.fit_atlas(profile="factual_retrieval")
    report = ws.run_benchmark(
        BenchmarkLaneConfig(
            lane_id="factual_retrieval.v1",
            behavior_id="factual_retrieval",
        )
    )
    assert report["status"] == "completed"
    assert report["lane_id"] == "factual_retrieval.v1"
    assert set(report["baseline_report"]["baseline_scores"]) == {
        "single_sae",
        "ensemble_sae",
        "pairwise_graph",
        "geometry_free",
    }
    assert len(report["artifact_paths"]) == 5
    assert report["input_signature"]


def test_export_report(tmp_path):
    ws = Workspace.create(tmp_path / "ws")
    report = ws.run_benchmark(
        BenchmarkLaneConfig(
            lane_id="factual_retrieval.v1",
            behavior_id="factual_retrieval",
        )
    )

    export = ws.export_report(report["run_id"])
    assert export["status"] == "ok"
    assert len(export["report_hash"]) == 64


def test_get_run_and_load_report(tmp_path):
    ws = Workspace.create(tmp_path / "ws")
    report = ws.run_benchmark(
        BenchmarkLaneConfig(
            lane_id="factual_retrieval.v1",
            behavior_id="factual_retrieval",
        )
    )
    run_id = report["run_id"]

    run_data = ws.get_run(run_id)
    assert run_data["run"]["run_id"] == run_id
    assert "candidate_event_table" in run_data["artifacts"]

    loaded = ws.load_report(run_id)
    assert loaded["run"]["run_id"] == run_id
    assert "decision_receipt" in loaded


def test_deterministic_rerun_hash(tmp_path):
    ws = Workspace.create(tmp_path / "ws")
    ws.attach_model("gpt2-small")
    ws.fit_atlas(profile="factual_retrieval")
    ws.fit_transport()
    ws.propose_events()
    ws.verify_mechanisms()

    lane = BenchmarkLaneConfig(
        lane_id="factual_retrieval.v1",
        behavior_id="factual_retrieval",
    )
    run_one = ws.run_benchmark(lane)
    run_two = ws.run_benchmark(lane)

    assert run_one["run_id"] != run_two["run_id"]
    assert run_one["input_signature"] == run_two["input_signature"]
    assert run_one["artifact_bundle_hash"] == run_two["artifact_bundle_hash"]

    determinism = ws.determinism_for_run(run_two["run_id"])
    assert determinism["is_deterministic"] is True
    assert determinism["matching_run_count"] >= 2


def test_baseline_margin_tie_is_pass():
    report = compare_baselines(
        intervention_faithfulness=0.20,
        baseline_scores={"single_sae": 0.15},
        margin_threshold=0.05,
    )
    assert report["beats_baseline"] is True


def test_baseline_tie_break_is_deterministic():
    report = compare_baselines(
        intervention_faithfulness=0.20,
        baseline_scores={"zeta": 0.14, "alpha": 0.14},
        margin_threshold=0.05,
    )
    assert report["strongest_baseline_id"] == "alpha"

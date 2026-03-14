from geoclt import BenchmarkLaneConfig, Workspace


def main() -> None:
    ws = Workspace.create("runs/python-roundtrip")
    ws.attach_model("gpt2-small")
    ws.fit_atlas(profile="factual_retrieval")
    ws.fit_transport()
    ws.propose_events()
    ws.verify_mechanisms()

    run = ws.run_benchmark(
        BenchmarkLaneConfig(
            lane_id="factual_retrieval.v1",
            behavior_id="factual_retrieval",
        )
    )
    inspected = ws.get_run(run["run_id"])
    exported = ws.export_report(run["run_id"])
    loaded = ws.load_report(run["run_id"])

    assert run["status"] == "completed"
    assert inspected["run"]["run_id"] == run["run_id"]
    assert "candidate_event_table" in inspected["artifacts"]
    assert exported["status"] == "ok"
    assert loaded["run"]["run_id"] == run["run_id"]
    assert loaded["decision_receipt"]["status"] == "ok"


if __name__ == "__main__":
    main()

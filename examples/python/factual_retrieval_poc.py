from geoclt import Workspace, BenchmarkLaneConfig


def main() -> None:
    ws = Workspace.create("runs/factual-retrieval")
    ws.attach_model("gpt2-small")
    ws.fit_atlas(profile="factual_retrieval")
    ws.fit_transport()
    ws.propose_events()
    ws.verify_mechanisms()
    report = ws.run_benchmark(BenchmarkLaneConfig(
        lane_id="factual_retrieval.v1",
        behavior_id="factual_retrieval",
    ))
    print(report)


if __name__ == "__main__":
    main()

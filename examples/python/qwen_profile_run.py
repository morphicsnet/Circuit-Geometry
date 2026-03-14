from geoclt import Workspace, BenchmarkLaneConfig


def main() -> None:
    ws = Workspace.create("runs/qwen-profile")
    ws.attach_model("qwen3")
    ws.fit_atlas(profile="qwen3_profile")
    ws.fit_transport()
    ws.propose_events()
    ws.verify_mechanisms()
    print(ws.run_benchmark(BenchmarkLaneConfig(lane_id="qwen3.v1", behavior_id="qwen3")))


if __name__ == "__main__":
    main()

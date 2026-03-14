from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SRC = REPO_ROOT / "python"
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

from geoclt import BenchmarkLaneConfig, Workspace


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic benchmark rerun check.")
    parser.add_argument(
        "--workspace",
        default="runs/determinism-check",
        help="Workspace directory for deterministic reruns.",
    )
    parser.add_argument(
        "--lane-id",
        default="factual_retrieval.v1",
        help="Benchmark lane identifier.",
    )
    parser.add_argument(
        "--behavior-id",
        default="factual_retrieval",
        help="Behavior identifier.",
    )
    parser.add_argument(
        "--model-id",
        default="gpt2-small",
        help="Model identifier.",
    )
    parser.add_argument(
        "--output",
        default="outputs/determinism_evidence.json",
        help="Path for machine-readable determinism evidence JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace = Workspace.create(args.workspace)
    workspace.attach_model(args.model_id)
    workspace.fit_atlas(profile=args.behavior_id)
    workspace.fit_transport()
    workspace.propose_events()
    workspace.verify_mechanisms()

    lane = BenchmarkLaneConfig(lane_id=args.lane_id, behavior_id=args.behavior_id)
    run_one = workspace.run_benchmark(lane)
    run_two = workspace.run_benchmark(lane)
    check = workspace.determinism_for_run(run_two["run_id"])

    payload = {
        "first_run_id": run_one["run_id"],
        "second_run_id": run_two["run_id"],
        "input_signature_equal": run_one["input_signature"] == run_two["input_signature"],
        "bundle_hash_equal": run_one["artifact_bundle_hash"] == run_two["artifact_bundle_hash"],
        "determinism": check,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))

    if not payload["input_signature_equal"] or not payload["bundle_hash_equal"]:
        return 1
    if not check["is_deterministic"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

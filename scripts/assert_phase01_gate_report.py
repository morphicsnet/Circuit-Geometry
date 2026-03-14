from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "outputs" / "phase_gate_report.json"

PHASE0_REQUIRED = [
    "fixture_expectations_match",
    "positive_fixture_conformant",
    "positive_fixture_beats_baseline",
    "negative_fixture_rejected_with_falsifier",
]

PHASE1_REQUIRED = [
    "run_completed",
    "artifact_count_is_five",
    "artifacts_exist",
    "artifacts_validate",
    "run_inspect_export_load_roundtrip",
    "determinism_endpoint_consistent",
    "bundle_hash_stable_across_reruns",
]


def main() -> int:
    if not REPORT_PATH.exists():
        print(f"missing phase 0/1 gate report: {REPORT_PATH}")
        return 1

    payload = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    if payload.get("overall_pass") is not True:
        print("phase 0/1 overall_pass is not true")
        return 1

    phase0 = payload.get("phase0", {})
    phase1 = payload.get("phase1", {})

    for key in PHASE0_REQUIRED:
        if phase0.get(key) is not True:
            print(f"phase0 assertion failed: {key}={phase0.get(key)}")
            return 1

    for key in PHASE1_REQUIRED:
        if phase1.get(key) is not True:
            print(f"phase1 assertion failed: {key}={phase1.get(key)}")
            return 1

    fixtures = payload.get("fixture_results", [])
    if len(fixtures) < 3:
        print("insufficient fixture coverage in phase 0/1 report")
        return 1

    if not any(case.get("id") == "positive_default" for case in fixtures):
        print("missing positive_default fixture case")
        return 1

    negatives = [case for case in fixtures if case.get("id") != "positive_default"]
    if not negatives:
        print("missing negative fixture cases")
        return 1

    if not all(case.get("actual_conformance_class") == "rejected" for case in negatives):
        print("one or more negative fixtures were not rejected")
        return 1

    if not any(case.get("actual_falsifiers", {}).get("any_triggered") for case in negatives):
        print("negative fixtures did not trigger falsifiers")
        return 1

    print("phase0/1 gate report assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

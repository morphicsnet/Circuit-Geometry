from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "outputs" / "release_readiness_report.json"

REQUIRED_BOOLEAN_PATHS = [
    "overall_pass",
    "delta_closeout.d0_release_baseline_frozen",
    "delta_closeout.d0_synthetic_inventory_complete",
    "delta_closeout.d0_desynthetic_status_green",
    "delta_closeout.d0_rc_merge_policy_enforced",
    "delta_closeout.d1_release_automation_complete",
    "delta_closeout.d2_ci_nightly_reliability",
    "delta_closeout.d3_placeholder_hygiene",
    "delta_closeout.d4_packaging_install_ready",
    "delta_closeout.d4_release_docs_present",
    "delta_closeout.d5_evidence_bundle_present",
    "full_recertification.r0_phase01_recert_pass",
    "full_recertification.r1_phase2_recert_pass",
    "full_recertification.r2_phase3a_recert_pass",
    "full_recertification.r2_phase3b_recert_pass",
    "full_recertification.r3_phase4a_recert_pass",
    "full_recertification.r3_phase4a_nightly_recert_pass",
    "full_recertification.r4_phase4b_recert_pass",
    "full_recertification.r5_report_packs_present",
]


def _resolve_path(payload: dict[str, object], dotted_path: str) -> object:
    current: object = payload
    for part in dotted_path.split("."):
        if not isinstance(current, dict):
            raise KeyError(dotted_path)
        current = current[part]
    return current


def main() -> int:
    if not REPORT_PATH.exists():
        print(f"missing release readiness report: {REPORT_PATH}")
        return 1

    payload = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    for path in REQUIRED_BOOLEAN_PATHS:
        try:
            value = _resolve_path(payload, path)
        except KeyError:
            print(f"missing required key in release readiness report: {path}")
            return 1
        if value is not True:
            print(f"release readiness assertion failed at {path}: {value}")
            return 1

    print("release readiness report assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

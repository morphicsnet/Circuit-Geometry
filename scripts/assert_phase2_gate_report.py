from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "outputs" / "phase2_gate_report.json"


REQUIRED_BOOLEAN_PATHS = [
    "overall_pass",
    "mock_roundtrip",
    "real_adapter_conformance",
    "passive_non_perturbation.token_parity",
    "passive_non_perturbation.logits_hash_parity",
    "canonical_serialization.stable_hash_key_order_invariant",
    "canonical_serialization.artifact_id_deterministic",
    "determinism.bundle_hash_present",
    "determinism.immutable",
    "determinism.stable_bundle_hash",
    "duplicate_chunk_policy.duplicate_noop_ok",
    "duplicate_chunk_policy.conflict_hard_fail",
]


def get_path(payload: dict, path: str):
    cursor = payload
    for part in path.split('.'):
        if not isinstance(cursor, dict) or part not in cursor:
            raise KeyError(path)
        cursor = cursor[part]
    return cursor


def main() -> int:
    if not REPORT_PATH.exists():
        print(f"missing phase2 gate report: {REPORT_PATH}")
        return 1

    payload = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    if payload.get("compatibility_matrix", {}).get("policy") != "strict_n_n_minus_1":
        print("compatibility policy mismatch")
        return 1

    for path in REQUIRED_BOOLEAN_PATHS:
        value = get_path(payload, path)
        if value is not True:
            print(f"phase2 gate failed at {path}: {value}")
            return 1

    checks = payload.get("compatibility_matrix", {}).get("checks", {})
    if not checks:
        print("missing compatibility checks")
        return 1

    for artifact_type, result in checks.items():
        if not (result.get("n") and result.get("n_minus_1") and result.get("n_minus_2_rejected")):
            print(f"compatibility check failed for {artifact_type}: {result}")
            return 1

    print("phase2 gate report assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

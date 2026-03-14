# Phase 0/1 Traceability Matrix

## 1. Requirements-to-Assertions Matrix

| Requirement ID | Requirement | Assertion / Signal | Verification Location(s) | Status |
|---|---|---|---|---|
| P0-R1 | Fixture contract must match expected conformance/falsifier outcomes | `phase0.fixture_expectations_match` | `scripts/generate_phase_gate_report.py`, `scripts/assert_phase01_gate_report.py` | PASS |
| P0-R2 | Positive fixture must be conformant | `phase0.positive_fixture_conformant` | same as above | PASS |
| P0-R3 | Positive fixture must beat baseline margin | `phase0.positive_fixture_beats_baseline` | same as above | PASS |
| P0-R4 | Negative fixtures must be rejected with falsifier evidence | `phase0.negative_fixture_rejected_with_falsifier` | same as above | PASS |
| P1-R1 | Phase 1 run must complete | `phase1.run_completed` | `scripts/generate_phase_gate_report.py` | PASS |
| P1-R2 | Exactly five required artifacts must be emitted | `phase1.artifact_count_is_five` | `scripts/generate_phase_gate_report.py` | PASS |
| P1-R3 | Artifact files must exist and validate structurally | `phase1.artifacts_exist`, `phase1.artifacts_validate` | `scripts/generate_phase_gate_report.py` | PASS |
| P1-R4 | Non-author workflow run->inspect->export->load must pass | `phase1.run_inspect_export_load_roundtrip` | `scripts/generate_phase_gate_report.py` | PASS |
| P1-R5 | Determinism endpoint and rerun hash stability must pass | `phase1.determinism_endpoint_consistent`, `phase1.bundle_hash_stable_across_reruns` | `scripts/generate_phase_gate_report.py`, `scripts/check_determinism.py` | PASS |

## 2. Assertions-to-Tests Matrix

| Assertion Group | Test / Script Coverage |
|---|---|
| Phase 0 fixture conformance and falsifiers | `scripts/generate_phase_gate_report.py` with `tests/fixtures/factual_retrieval_v1/*` |
| Phase 1 workflow and artifact checks | `scripts/generate_phase_gate_report.py`, `python/geoclt/workspace.py` |
| Gate hard-fail assertions | `scripts/assert_phase01_gate_report.py` |
| End-to-end local validation flow | `scripts/validate_artifacts.sh` |

## 3. Integration with Phase 2+
- Phase 0/1 assertions remain active in the same validation flow used for Phase 2.
- This preserves backward gate coverage while later-phase hardening evolves.

## 4. Sign-off Dependency Chain
1. Fixture manifest correctness.
2. Deterministic benchmark pipeline behavior.
3. Stable artifact hashing and validation.
4. Assertion script hard-fail enforcement.

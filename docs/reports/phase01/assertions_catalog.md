# Phase 0/1 Assertions Catalog

## A. Gate Assertion Definitions
Primary assertion script: `scripts/assert_phase01_gate_report.py`

### A1. Preflight Assertions
1. `REPORT_EXISTS`
- Definition: `outputs/phase_gate_report.json` exists.
- Pass: file exists.
- Fail: missing report.

2. `OVERALL_PASS_TRUE`
- Definition: `overall_pass == true`.
- Pass: literal `true`.
- Fail: missing/false/non-boolean.

### A2. Required Phase 0 Assertions
1. `phase0.fixture_expectations_match`
2. `phase0.positive_fixture_conformant`
3. `phase0.positive_fixture_beats_baseline`
4. `phase0.negative_fixture_rejected_with_falsifier`

Pass criterion for each: literal boolean `true`.

### A3. Required Phase 1 Assertions
1. `phase1.run_completed`
2. `phase1.artifact_count_is_five`
3. `phase1.artifacts_exist`
4. `phase1.artifacts_validate`
5. `phase1.run_inspect_export_load_roundtrip`
6. `phase1.determinism_endpoint_consistent`
7. `phase1.bundle_hash_stable_across_reruns`

Pass criterion for each: literal boolean `true`.

### A4. Fixture Coverage Assertions
- At least `3` fixture results exist.
- `positive_default` fixture is present.
- At least one negative fixture exists.
- All negative fixtures resolve to `actual_conformance_class == rejected`.
- At least one negative fixture has `actual_falsifiers.any_triggered == true`.

## B. Assertion Sources
- Gate checks: `scripts/assert_phase01_gate_report.py`
- Report materialization: `scripts/generate_phase_gate_report.py`
- Determinism utility: `scripts/check_determinism.py`
- Integration execution path: `scripts/validate_artifacts.sh`

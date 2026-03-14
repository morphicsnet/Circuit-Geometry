# Phase 0/1 Test Results

## 1. Commands
- `python3 scripts/generate_phase_gate_report.py --workspace runs/phase-gate --output outputs/phase_gate_report.json`
- `python3 scripts/assert_phase01_gate_report.py`

## 2. Latest Snapshot
- Report generation: **PASS**
- Assertion script: **PASS** (`phase0/1 gate report assertions passed`)
- Gate verdict (`overall_pass`): **true**

## 3. Assertion Outcomes
- Phase 0 checks: `4/4` passing
- Phase 1 checks: `7/7` passing
- Fixture checks: `3/3` fixture cases match expected conformance/falsifier behavior

## 4. Workflow Outcomes
- Two benchmark runs completed with distinct run IDs.
- Bundle hash stability across reruns: passing.
- Inspect/export/load roundtrip: passing.
- Required five artifacts produced and structurally validated.

## 5. Failure Analysis
- Current snapshot: no assertion failures.
- If failure occurs, first triage points:
  - fixture manifest mismatch (`tests/fixtures/factual_retrieval_v1/fixture_manifest.json`)
  - non-deterministic payload fields entering hash path
  - artifact generation regressions in workspace pipeline

## 6. Regression Status
- Phase 0/1 gate remains pass after Phase 2 hardening integration.

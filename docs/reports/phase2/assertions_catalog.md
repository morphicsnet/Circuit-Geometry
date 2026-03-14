# Phase 2 Assertions Catalog

## A. Gate Assertion Definitions
Primary gate assertion script: `scripts/assert_phase2_gate_report.py`

### A1. Preflight Assertions
1. `REPORT_EXISTS`
- Definition: `outputs/phase2_gate_report.json` exists.
- Pass: file exists.
- Fail: missing report file.

2. `COMPAT_POLICY_LOCKED`
- Definition: `compatibility_matrix.policy == strict_n_n_minus_1`.
- Pass: exact match.
- Fail: any other policy value.

3. `COMPAT_CHECKS_PRESENT`
- Definition: `compatibility_matrix.checks` is non-empty.
- Pass: at least one artifact policy row.
- Fail: missing or empty mapping.

### A2. Required Boolean Assertions
These are explicitly enumerated in `REQUIRED_BOOLEAN_PATHS`:
1. `overall_pass`
2. `mock_roundtrip`
3. `real_adapter_conformance`
4. `passive_non_perturbation.token_parity`
5. `passive_non_perturbation.logits_hash_parity`
6. `canonical_serialization.stable_hash_key_order_invariant`
7. `canonical_serialization.artifact_id_deterministic`
8. `determinism.bundle_hash_present`
9. `determinism.immutable`
10. `determinism.stable_bundle_hash`
11. `duplicate_chunk_policy.duplicate_noop_ok`
12. `duplicate_chunk_policy.conflict_hard_fail`

Pass criterion for each: must be literal boolean `true`.

### A3. Compatibility Row Assertions (Per Artifact)
For each artifact row in `compatibility_matrix.checks`:
- `n == true`
- `n_minus_1 == true`
- `n_minus_2_rejected == true`

Current artifact rows exercised:
- `artifact_bundle`
- `benchmark_result`
- `decision_receipt`
- `event_record`
- `hyperpath_record`
- `mechanism_class_record`

## B. Runtime/Protocol Assertions in Tests

### B1. Sidecar Duplicate Semantics
- Same `trace_id + chunk_idempotency_key` + identical payload: accept (`duplicate-noop`).
- Same key + different payload: fail (`duplicate chunk conflict`).

Locations:
- Rust: `crates/geoclt-sidecar/src/server.rs`
- Python: `python/tests/test_sidecar_roundtrip.py`

### B2. Trace Separation Assertions
- Concurrent traces remain isolated.
- Bundle hashes diverge for differing per-trace payloads.

Locations:
- Rust: `crates/geoclt-sidecar/src/server.rs` (`concurrent_trace_separation`)
- Python: `python/tests/test_sidecar_roundtrip.py`

### B3. Determinism Assertions
- Same run signature yields stable bundle hash.
- Batch and stream deterministic behavior remains stable where expected.

Locations:
- Rust runtime: `crates/geoclt-runtime/src/run.rs`
- Python workspace: `python/tests/test_benchmark.py`, `python/tests/test_workspace_benchmark.py`

## C. Assertion Grouping Hierarchy
1. **Gate-level hard assertions** (`assert_phase2_gate_report.py`)
2. **Report-generation assertions** (`generate_phase2_gate_report.py`)
3. **Protocol/runtime unit + integration assertions** (Rust/Python tests)
4. **Cross-phase validation assertions** (`validate_artifacts.sh`, Phase 0/1 + Phase 2)

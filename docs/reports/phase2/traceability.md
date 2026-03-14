# Phase 2 Traceability Matrix

## 1. Requirements-to-Assertions Matrix

| Requirement ID | Requirement | Primary Assertion/Signal | Verification Location(s) | Status |
|---|---|---|---|---|
| P2-R1 | Compatibility policy must be strict N/N-1 | `compatibility_matrix.policy` | `scripts/assert_phase2_gate_report.py` | PASS |
| P2-R2 | All required gate booleans must be true | `REQUIRED_BOOLEAN_PATHS` | `scripts/assert_phase2_gate_report.py` | PASS |
| P2-R3 | Compatibility rows must satisfy N/N-1/N-2 rule | `compatibility_matrix.checks[*]` | `scripts/assert_phase2_gate_report.py`, `crates/geoclt-artifacts/src/compatibility.rs` tests | PASS |
| P2-R4 | Duplicate identical chunk is no-op | `duplicate_noop_ok` | `scripts/generate_phase2_gate_report.py`, `python/tests/test_sidecar_roundtrip.py`, `crates/geoclt-sidecar/src/server.rs` tests | PASS |
| P2-R5 | Duplicate conflicting chunk hard-fails | `conflict_hard_fail` | same as above | PASS |
| P2-R6 | Passive mode must not perturb outputs | `token_parity`, `logits_hash_parity` | `python/tests/test_passive_nonperturbation.py`, gate report | PASS |
| P2-R7 | Canonical hash must be key-order invariant | `stable_hash_key_order_invariant` | `scripts/generate_phase2_gate_report.py`, `python/tests/test_artifacts.py`, `crates/geoclt-artifacts/src/canonicalize.rs` tests | PASS |
| P2-R8 | Artifact IDs must be deterministic | `artifact_id_deterministic` | `scripts/generate_phase2_gate_report.py`, `python/tests/test_artifacts.py`, `crates/geoclt-artifacts/src/canonicalize.rs` tests | PASS |
| P2-R9 | Bundle determinism and immutability required | `determinism.*` | `scripts/generate_phase2_gate_report.py`, `python/tests/test_sidecar_roundtrip.py`, `crates/geoclt-runtime/src/run.rs` tests | PASS |
| P2-R10 | Multi-trace isolation required | trace separation assertions | `python/tests/test_sidecar_roundtrip.py`, `crates/geoclt-sidecar/src/server.rs`, `tests/integration/sidecar_roundtrip.rs` | PASS |

## 2. Assertions-to-Tests Matrix

| Assertion Group | Test/Script Coverage |
|---|---|
| Gate report boolean checks | `scripts/assert_phase2_gate_report.py` |
| Compatibility policy and matrix | `scripts/assert_phase2_gate_report.py`, Rust compatibility unit tests |
| Duplicate chunk semantics | Python sidecar roundtrip tests + Rust sidecar server tests |
| Determinism | Python benchmark/workspace tests + Rust runtime tests + gate report checks |
| Adapter conformance | `python/tests/test_adapter_contracts.py` + gate report adapter checks |
| Passive non-perturbation | `python/tests/test_passive_nonperturbation.py` + gate report |

## 3. Integration with Other Phases
- Phase 2 gate is executed in the same validation flow as Phase 0/1 (`scripts/validate_artifacts.sh`).
- This preserves cross-phase regression visibility while keeping Phase 2 hard-gate semantics explicit.

## 4. Version Control / Provenance
- `phase2_gate_report.json` includes `git_commit` field.
- In current environment it may be `unknown` due git root discovery limitations across mount boundaries.

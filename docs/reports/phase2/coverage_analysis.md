# Phase 2 Coverage Analysis

## 1. Assertion Coverage Metrics

### 1.1 Gate Assertion Script Coverage
- Preflight assertions:
  - `REPORT_EXISTS`: exercised
  - `COMPAT_POLICY_LOCKED`: exercised
  - `COMPAT_CHECKS_PRESENT`: exercised
- Required boolean paths: **12/12 exercised and true**
- Compatibility row checks:
  - Artifact classes: **6**
  - Conditions per class: **3** (`n`, `n_minus_1`, `n_minus_2_rejected`)
  - Evaluated conditions: **18/18 passing**

### 1.2 Runtime Assertion Coverage
- Duplicate chunk no-op: exercised (Python + Rust)
- Duplicate chunk conflict hard-fail: exercised (Python + Rust)
- Concurrent trace separation: exercised (Python + Rust)
- Deterministic bundle hash rerun: exercised (Python + Rust runtime paths)
- Passive non-perturbation token/logits parity: exercised (Python)

## 2. Exercised vs Unexercised Areas

### Exercised
- Contract compatibility checks (`N`, `N-1`, `N-2`) across all registered artifacts.
- Sidecar core lifecycle operations (`start`, `push`, `end`, `abort`) in in-process tests.
- Artifact canonical hash and deterministic identity derivation.

### Partially or Not Yet Exercised
- End-to-end networked gRPC client/server interoperability in CI (service code exists; gate currently uses fake client path for deterministic checks).
- Adversarial load/backpressure stress profiling under high concurrency.
- Fault injection for storage-layer failures.

## 3. Coverage Quality Assessment
- Gate assertions provide strong binary assurance for Phase 2 contract guarantees.
- Runtime edge-condition coverage is adequate for deterministic CI but not yet stress-complete for production scale.

## 4. Performance Impact Assessment
- Phase 2 gate runtime: ~6.29s wall-clock (snapshot).
- Memory footprint (max RSS): ~78.9 MiB.
- Observed overhead is acceptable for CI hard-gate usage.

## 5. Resource Utilization Metrics
From `/usr/bin/time -l` snapshot of `scripts/run_phase2_gate.sh`:
- Real: 6.29s
- User: 0.51s
- Sys: 0.40s
- Max RSS: 82,722,816 bytes
- Voluntary context switches: 3,482
- Involuntary context switches: 5,541

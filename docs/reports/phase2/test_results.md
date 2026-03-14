# Phase 2 Test Results

## 1. Gate Execution Commands
- `bash scripts/run_phase2_gate.sh`
- `python3 scripts/assert_phase2_gate_report.py`
- `bash scripts/validate_artifacts.sh` (includes Phase 0/1 + Phase 2)

## 2. Latest Results Snapshot
- Phase 2 gate report verdict: **PASS**
- Assertion script verdict: **PASS** (`phase2 gate report assertions passed`)
- Python Phase 2-focused tests in gate script: **8 passed**
- Rust Phase 2-focused crates in gate script:
  - `geoclt-artifacts`: **10 passed**
  - `geoclt-sidecar`: **3 passed**

## 3. Regression Status
- Full Rust workspace tests: passing.
- Full Python test suite: passing (`31 passed`, 1 warning from dependency parser package).
- Phase 0/1 gates remain passing after Phase 2 hardening.

## 4. Simulation/Waveform Notes
- No HDL simulation is present in this repository.
- Waveform-level annotations are **N/A** for this software-only stack.
- Equivalent runtime traces are validated via lifecycle assertions and deterministic bundle outputs.

## 5. Failure Analysis
- Current run: no violated assertions.
- Historical during hardening:
  - Determinism drift fixed by removing run-variant trace fields from canonical hashed payload paths.
  - Compatibility edge case for version=1 fixed in gate report logic (`N-1` vacuous true).

## 6. Known Issues / Workarounds
- `git_commit` may be `unknown` in gate report when repository root is not discoverable by git in the current execution context.
- Workaround: run from a discoverable git root or set `GIT_DISCOVERY_ACROSS_FILESYSTEM=1` if appropriate for environment policy.

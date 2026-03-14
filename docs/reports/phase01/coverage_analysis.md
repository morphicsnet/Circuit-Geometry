# Phase 0/1 Coverage Analysis

## 1. Gate Assertion Coverage
- Preflight assertions exercised: `2/2`
  - report exists
  - overall pass true
- Phase 0 required booleans exercised: `4/4`
- Phase 1 required booleans exercised: `7/7`
- Fixture coverage assertions exercised: `5/5`

## 2. Fixture Coverage Metrics
- Total fixture cases exercised: `3`
- Positive fixtures: `1`
- Negative fixtures: `2`
- Negative fixtures with falsifier trigger: `2`

## 3. Exercised vs Unexercised Areas
### Exercised
- Conformance class derivation for positive and negative fixture types.
- Baseline comparison pass/fail behavior.
- Falsifier-trigger rejection path.
- End-to-end Phase 1 run/inspect/export/load workflow.

### Not Fully Exercised in Gate Script
- Adversarial corruption of artifact payload files before load.
- High-volume run registry stress behavior.
- Multi-user concurrent workflow contention.

## 4. Coverage Adequacy Assessment
Coverage is adequate for Phase 0/1 gate enforcement and regression blocking of core contract behavior, determinism, and non-author workflow reproducibility.

# geoclt-benchmark Release Readiness Plan
## Summary
- `geoclt-benchmark` is a supported internal algorithm crate in the Python-first `geoclt` release train, not a public lead Rust API.
- The crate already covers the core release surface: lane loading, admission evaluation, falsifier evaluation, and bundle-level contract evaluation.
- Readiness work is mainly about packaging verification, release-facing documentation, and preserving the fixture-backed regression path.

## Current State
- `Cargo.toml` already has workspace-managed versioning plus docs.rs metadata, README, keywords, and categories.
- `src/lib.rs` exposes four modules: `admission`, `contract`, `falsifiers`, and `lanes`.
- Module tests cover threshold handling, falsifier behavior, and contract classification.
- The crate also has an integration test at `tests/fixture_contract.rs` that evaluates real fixture bundles from `tests/fixtures/factual_retrieval_v1`.
- The crate ships non-code lane data under `lanes/`, including `IMMUTABLE_LOCK.json` and versioned lane definitions.
- The README exists, but it is intentionally minimal and does not yet explain the release-facing usage or data layout.

## Required Changes
- Verify `cargo package --locked` for this crate succeeds without dropping the README, `lanes/` data, or any file needed by the fixture test path.
- If packaging omits any required non-code asset, add the minimum package-inclusion fix so the published crate remains self-contained.
- Expand the README with a short release-facing explanation of the lane registry, admission/falsifier/contract flow, and the staged fixture path used by the integration test.
- Keep the fixture-based contract test as the release gate for bundle conformance, and add coverage only if the packaging surface or lane layout changes.
- Confirm the typed inputs and outputs remain deterministic and aligned with the shared `geoclt-schema` contract surface.

## Acceptance Criteria
- `cargo test -p geoclt-benchmark` passes.
- `cargo package --locked -p geoclt-benchmark` passes.
- The packaged crate includes the README and the lane registry data required by `load_lane_definitions`.
- The integration fixture test continues to pass against `tests/fixtures/factual_retrieval_v1`.
- The README explicitly states the crate's supported internal algorithm scope and its role in the Python-first release train.

## Dependencies and Coordination
- Coordinate with owners of `geoclt-schema`, `geoclt-causal`, `geoclt-ids`, and `geoclt-units`, since this crate consumes their typed contracts and must remain lockstep with them.
- Coordinate with anyone touching shared lane JSON or fixture data, because the integration test depends on those paths staying stable.
- If the staged runtime bundle layout changes, update the fixture path and the README together so the release story stays coherent.

## Non-Goals
- No public Python API changes in this plan.
- No schema redesign or new benchmark semantics.
- No workspace-wide release policy edits.
- No changes outside `crates/geoclt-benchmark/`.

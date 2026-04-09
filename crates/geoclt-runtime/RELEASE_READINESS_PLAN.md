# geoclt-runtime Release Readiness Plan

## Summary
`geoclt-runtime` stays a supported internal algorithm crate in the Python-first Geo-CLT release train. Release readiness here means: keep the staged runtime bundle path deterministic, make the crate packageable with locked dependencies, and keep the crate docs/tests aligned with the support-class policy. This is not a public Rust API promotion.

## Current State
- `Cargo.toml` already has package metadata, docs.rs wiring, README linkage, and workspace-managed dependencies.
- `src/lib.rs` exposes the staged runtime modules: `batch`, `policy_engine`, `run`, `run_graph`, and `stream`.
- Crate-local unit tests already cover policy decisions, run-graph shape/JSON round-tripping, batch/stream hash stability, and workspace bundle determinism.
- The README already states that this is a supported internal algorithm crate for the Python-first release train.
- Gaps remain: there are no crate-local integration tests or examples, and the embedded runtime producer strings are hardcoded in multiple places rather than being clearly centralized to the release version.

## Required Changes
- Confirm the crate is packageable under the release train with locked dependencies and no missing artifacts.
- Align all runtime metadata/version strings used in bundle assembly and tests so the emitted artifacts reflect one lockstep release identity.
- Add or tighten crate-local documentation/examples that describe the staged runtime bundle path and the crate’s internal-support role.
- Expand coverage only where it closes release risk: bundle assembly, deterministic outputs, and metadata/schema invariants. Do not add new product behavior.
- Verify the crate stays aligned with its direct support-class dependencies: `geoclt-artifacts`, `geoclt-schema`, `geoclt-sidecar`, `geoclt-atlas`, `geoclt-metric`, `geoclt-transport`, `geoclt-hypergraph`, `geoclt-canonicalize`, `geoclt-causal`, and `geoclt-units`.

## Acceptance Criteria
- `cargo test -p geoclt-runtime` passes.
- `cargo package --locked -p geoclt-runtime` succeeds.
- The crate README and module docs clearly describe the staged runtime bundle path and the supported-internal scope.
- Bundle assembly emits deterministic hashes and typed artifacts for the same inputs.
- Runtime producer/version metadata is internally consistent across code paths and matches the lockstep release train.
- The crate remains an internal support crate for the Python-first release train, with no added promise of a standalone public Rust API.

## Dependencies and Coordination
- Coordinate any metadata/version alignment with the crates that define bundle inputs and outputs, especially `geoclt-schema` and `geoclt-artifacts`.
- Coordinate with `geoclt-sidecar` if stream-path behavior or trace metadata changes affect emitted bundles.
- Keep the crate in the same lockstep release cadence as the rest of the `geoclt-*` graph.
- If schema compatibility changes are needed, they must be handled in `geoclt-schema` and the shared schema docs, not here.

## Non-Goals
- No new runtime features or algorithm redesign.
- No schema redesign, compatibility-policy rewrite, or public-release-cadence change.
- No FFI, CLI, or Python binding work in this crate plan.
- No cross-crate refactor beyond what is required to make `geoclt-runtime` release-ready.

# geoclt-ffi Release Readiness Plan
## Summary
`geoclt-ffi` is the operational internal PyO3 bridge for the Python-first Geo-CLT release train. It already has workspace-driven package metadata, an explicit internal README, and a single Rust module that registers the Python-facing bridge functions used by `bindings/python`. Release readiness here is about proving packaging and behavior stability for that bridge, not turning it into a standalone public Rust API.

## Current State
- `Cargo.toml` is wired to workspace versioning and documents the crate as an internal PyO3 bridge.
- `README.md` clearly states that the crate is internal and not intended as a user-facing Rust API.
- `src/lib.rs` exposes the bridge surface through `native_version`, JSON helpers for atlas/metric/transport/hypergraph/causal/runtime, `run_benchmark_hook`, and `register_module` / `geoclt_native`.
- No crate-local tests were found under `crates/geoclt-ffi`.
- The repo-wide support-class policy places this crate in the `Operational internal crates` bucket, which requires packageability and clear scope documentation, but not a public API commitment.

## Required Changes
- Add crate-local tests for the bridge boundary: successful JSON parsing/serialization, malformed-input error mapping, and at least one representative path for atlas, metric/transport, hypergraph, causal, and runtime.
- Add a lightweight smoke check for module registration so the Python binding crate continues to import and register `geoclt_ffi` without drift.
- Keep the README and module-level documentation aligned with the operational/internal scope and the exported bridge entrypoints whenever the surface changes.
- Verify the crate remains packageable with `cargo package --locked` in the workspace release environment.

## Acceptance Criteria
- `cargo package --locked` succeeds for `geoclt-ffi`.
- The crate-local test suite passes and covers both success and failure paths for the JSON bridge.
- The Python binding crate still builds with `geoclt-ffi::register_module` wired into `geoclt_native`.
- The crate documentation still states that this is an internal operational bridge, not the primary public Rust API.
- No support-class policy violations remain for the crate.

## Dependencies and Coordination
- `bindings/python` is the consumer that finalizes the extension module; any exported function or signature change in `geoclt-ffi` must be coordinated there.
- The bridge depends on the internal algorithm and schema crates, so the release-order constraints in `docs/release/crate-support-classes.md` apply.
- Because the broader release train is lockstep, version bumps and packaging checks must stay aligned with the rest of `geoclt-*`.

## Non-Goals
- Publishing `geoclt-ffi` as the primary public Rust API.
- Restructuring the Python release architecture or moving the extension-module boundary out of `bindings/python`.
- Changing core kernel behavior in downstream algorithm crates.
- Adding unrelated feature work outside release-readiness validation and coverage.

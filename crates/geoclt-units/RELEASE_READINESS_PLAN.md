# geoclt-units Release Readiness Plan

## Summary
`geoclt-units` is a stable foundation / internal-contract crate in the Python-first Geo-CLT release train. It exposes three serde-serializable typed units, has a crate README, and already includes a basic JSON roundtrip test. The crate is small and intentionally stable, so release readiness is primarily about validating packaging and preserving compatibility, not expanding the API.

## Current State
- `Cargo.toml` declares a documented library crate with `serde` as the only runtime dependency and `serde_json` as a dev-dependency.
- `src/lib.rs` exports `LayerIndex(u32)`, `TokenIndex(i32)`, and `Score(f64)` with `Serialize` / `Deserialize` and the usual copy/clone/equality traits.
- The crate has one inline test that roundtrips all three units through JSON.
- `README.md` already states that this crate is a shared typed-units foundation for Geo-CLT kernels and records and that it belongs to the Python-first release train.
- The repo support-class policy explicitly lists `geoclt-units` as a stable foundation / internal-contract crate and requires it to be packageable with `cargo package --locked`, documented, and reviewed for compatibility changes.
- There are no crate-local integration tests or example binaries.

## Required Changes
1. Validate release packaging from the crate or workspace with `cargo package --locked`; fix any metadata or packaging issues that block publication readiness.
2. Confirm the public unit types and serde behavior are intentionally minimal and stable for downstream Python-facing contracts; do not add new exported units unless there is an explicit compatibility review.
3. Keep the README and crate docs aligned with the support-class policy so the crate remains clearly identified as a stable internal contract, not an operational or algorithm crate.
4. If packaging or validation exposes edge cases, add focused crate-local tests for the affected unit behavior rather than broadening the API surface.

## Acceptance Criteria
- `cargo package --locked` succeeds for `geoclt-units`.
- `cargo test` passes for the crate, including the JSON roundtrip coverage in `src/lib.rs`.
- The crate README and module docs clearly match the stable foundation / internal-contract role described in `docs/release/crate-support-classes.md`.
- No public API changes are introduced without an explicit compatibility review.

## Dependencies and Coordination
- Coordinate with any workspace-wide release train changes that affect lockstep versioning, since all `geoclt-*` crates ship together.
- If another worker changes shared release policy or versioning assumptions, re-check this plan against the updated policy before release.
- No coordination is needed with Python binding implementation work beyond preserving the typed contract that `geoclt-units` exports.

## Non-Goals
- No redesign of the unit taxonomy or addition of broader domain types.
- No Python binding work, CLI work, or runtime orchestration changes.
- No schema changes or cross-crate contract expansion.
- No attempt to make this crate the primary public Rust API; it remains a supporting typed-contract crate.

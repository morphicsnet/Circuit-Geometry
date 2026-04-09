# geoclt-hypergraph Release Readiness Plan

## Summary
`geoclt-hypergraph` is a supported internal algorithm crate in the Python-first Geo-CLT release train. It already presents a narrow release surface: deterministic candidate-event and hyperpath kernels in `src/induce.rs`, workspace-managed package metadata, a crate README, and one deterministic unit test. Release readiness for this crate is therefore about packageability, deterministic behavior, and schema compatibility, not a separate public Rust API commitment.

## Current State
- `Cargo.toml` marks the crate as `geoclt-hypergraph`, uses workspace-managed versioning/metadata, and depends only on `serde_json` plus the internal typed-contract crates `geoclt-core`, `geoclt-ids`, `geoclt-schema`, and `geoclt-units`.
- `README.md` already states that the crate builds deterministic candidate events and admitted hyperpaths and that it is a supported internal algorithm crate for the Python-first release train.
- `src/lib.rs` exposes a single public module, `induce`, and `src/induce.rs` contains the actual release surface: `propose_events` and `materialize_hyperpaths`.
- The crate-local test in `src/induce.rs` checks deterministic event generation and basic hyperpath materialization.
- No standalone crate-local `tests/` directory is present.

## Required Changes
- Verify the crate packages cleanly with `cargo package --locked` under the workspace lockfile.
- Keep the README and crate-level docs aligned with the support-class policy: this is a supported internal algorithm crate, not an independent public Rust API.
- Expand crate-local tests to cover the observable release contract beyond the existing smoke check:
  - identical inputs produce identical candidate events,
  - empty event tables return empty admitted hyperpath tables,
  - hyperpath admission is gated by the current threshold logic.
- Confirm the crate continues to use only the internal typed-contract dependencies it already imports, without adding release-only external dependencies.

## Acceptance Criteria
- `cargo test -p geoclt-hypergraph` passes.
- `cargo package --locked -p geoclt-hypergraph` passes.
- The README and crate docs clearly describe the crate as a supported internal algorithm crate in the Python-first release train.
- Deterministic behavior is covered by crate-local tests for both event proposal and hyperpath materialization.
- No schema or dependency drift is introduced outside the existing `geoclt-core`, `geoclt-ids`, `geoclt-schema`, and `geoclt-units` contract surface.

## Dependencies and Coordination
- Coordinate with the owners of `geoclt-core`, `geoclt-ids`, `geoclt-schema`, and `geoclt-units` because this crate’s records are typed against their contracts.
- Follow the workspace lockstep versioning policy from the repo release guidance; do not introduce version skew in intra-workspace dependencies.
- If `geoclt-schema` changes its event or hyperpath types, treat that as a compatibility event for this crate as well.

## Non-Goals
- No Python binding work, FFI changes, or CLI integration.
- No change to the release order or support-class classification for the wider crate graph.
- No redesign of candidate-event or hyperpath semantics beyond release-hardening.
- No new public Rust API commitment beyond the current internal algorithm surface.

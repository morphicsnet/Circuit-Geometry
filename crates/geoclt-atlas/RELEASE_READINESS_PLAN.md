# geoclt-atlas Release Readiness Plan

## Summary
`geoclt-atlas` is a supported internal algorithm crate in the Python-first Geo-CLT release train. The crate already has package metadata, a crate README, a minimal public surface, and a deterministic unit test. Release readiness is therefore about verification and small packaging/test hardening, not API redesign.

## Current State
- `Cargo.toml` marks the crate as `geoclt-atlas`, sets docs.rs metadata, and depends only on workspace crates `geoclt-core`, `geoclt-schema`, and `geoclt-units` plus `serde`/`serde_json`.
- `README.md` already states the crate's role as deterministic atlas fitting and overlap diagnostics for the staged runtime.
- `src/lib.rs` exports a single module, `atlas`.
- `src/atlas.rs` contains the deterministic `fit_atlas` kernel and one crate-local unit test that checks determinism and basic output shape.
- No crate-local integration tests or examples are present.

## Required Changes
- Verify `cargo package --locked` succeeds for this crate without introducing unpublished dependencies or missing metadata.
- Keep the crate documentation aligned with the support-class policy: internal algorithm crate, deterministic typed I/O, and part of the Python-first release train.
- Add crate-local coverage if packaging or release validation needs it, especially an integration or example test that exercises the staged-runtime bundle path rather than only the unit-level kernel test.
- Confirm the release bundle still works with exact workspace-versioned dependencies on `geoclt-core`, `geoclt-schema`, and `geoclt-units`.
- If package checks expose any missing manifest fields or doc gaps, fix them in this crate before release.

## Acceptance Criteria
- `cargo package --locked` passes for `crates/geoclt-atlas`.
- The deterministic `fit_atlas` behavior remains stable for identical inputs.
- Crate-local tests cover the core kernel, and any required release-path coverage is present or explicitly justified.
- The crate README and manifest remain consistent with the supported internal algorithm classification.
- The crate is ready to ship in lockstep with the Python-first Geo-CLT release train.

## Dependencies and Coordination
- Coordinate with `geoclt-core`, `geoclt-schema`, and `geoclt-units` because `geoclt-atlas` relies on their typed contracts and exact workspace versions.
- Follow the repo release order: lower-level contract crates first, then supported internal algorithm crates like `geoclt-atlas`.
- Keep this crate's scope aligned with the shared release policy; do not use this plan to change workspace policy or schema ownership.

## Non-Goals
- No public API redesign.
- No changes to shared schemas, root docs, or workspace-level release policy.
- No publish-order changes.
- No expansion into operational crate responsibilities such as FFI, sidecar, or CLI behavior.

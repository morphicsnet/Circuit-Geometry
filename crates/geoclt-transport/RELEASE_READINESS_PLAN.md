# geoclt-transport Release Readiness Plan

## Summary
`geoclt-transport` is a supported internal algorithm crate in the Python-first Geo-CLT release train. It already has release-oriented package metadata, a crate README, a narrow public surface, and a deterministic unit test around `fit_transport`. The remaining work is release validation, plus any small release-facing coverage or packaging cleanup needed once the lower-level registry dependencies are available.

## Current State
- `Cargo.toml` already declares package metadata, docs.rs metadata, README linkage, and workspace-managed dependencies on `geoclt-core`, `geoclt-schema`, and `geoclt-units`.
- `README.md` explicitly states that the crate belongs to the supported internal algorithm tier for the Python-first release train.
- `src/lib.rs` exposes only the `transport` module, so the public API stays intentionally small.
- `src/transport.rs` contains the deterministic `fit_transport` kernel and one inline unit test that checks repeatability and basic output shape.
- No crate-local `tests/` directory or examples are present.

## Required Changes
- Keep the crate’s public surface minimal and stable; do not widen exports beyond the documented transport module without a compatibility review.
- Preserve deterministic typed I/O behavior in `fit_transport` and keep the existing unit test green.
- Add crate-local release coverage only if validation needs it, preferably a small integration or example test that exercises the staged runtime bundle path rather than a new API surface.
- Re-run packaging validation once `geoclt-core`, `geoclt-schema`, and `geoclt-units` are available from the registry; the current `cargo package --locked` failure is an expected publish-order constraint, not a local metadata defect.
- Fix any missing manifest or documentation detail only within this crate, and keep changes minimal.

## Acceptance Criteria
- `cargo test -p geoclt-transport --locked` passes.
- The deterministic `fit_transport` unit test continues to pass for identical inputs.
- `cargo package --locked -p geoclt-transport` or the equivalent publish dry-run succeeds once the lower-level workspace crates are registry-available.
- README and crate docs continue to identify the crate as a supported internal algorithm crate in the Python-first release train.
- If release validation requests it, at least one crate-local example or integration test exists and exercises the staged runtime bundle path deterministically.

## Dependencies and Coordination
- Coordinate with `geoclt-core`, `geoclt-schema`, and `geoclt-units`, since this crate cannot fully pass isolated package validation until those lower-level crates are published first.
- Follow the repo release order: foundational crates first, then supported internal algorithm crates like `geoclt-transport`.
- Keep this plan aligned with the shared support-class policy and avoid changing shared docs, workspace policy, or versioning rules from this crate.
- Other workers may be updating neighboring crate plans in parallel; do not depend on changes outside this file.

## Non-Goals
- No public API redesign.
- No schema changes or compatibility-policy changes.
- No Python binding, FFI, sidecar, or CLI work.
- No workspace-wide release-order or versioning changes.
- No edits outside `/Volumes/128/Geo-CLT-SAE/crates/geoclt-transport/RELEASE_READINESS_PLAN.md`.

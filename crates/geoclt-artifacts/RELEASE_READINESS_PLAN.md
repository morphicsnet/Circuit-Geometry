# geoclt-artifacts Release Readiness Plan

## Summary
`geoclt-artifacts` is a stable-foundation / internal-contract crate in the Python-first Geo-CLT release train. The crate already has the expected package metadata, README, public module surface, embedded registry fixture, and passing unit coverage. No code redesign is required before release; the remaining work is release-order verification and keeping the crate packageable once `geoclt-schema` is available through the registry path used for publication.

## Current State
- `Cargo.toml` already includes package metadata needed for external support: `license`, `repository`, `homepage`, `documentation`, `readme`, `keywords`, and `categories`.
- `README.md` is present and states the crate’s external-support intent within the Python-first release train.
- `src/lib.rs` exposes a small, focused surface: `bundle`, `canonicalize`, `io`, `compatibility`, `registry`, and `validate`.
- The crate embeds `registry/registry.json` and uses it for compatibility checks and packaged-registry loading.
- Crate-local tests already cover canonical hashing, artifact identity, bundle hashing, immutability checks, registry loading, N/N-1 compatibility, transitional mixed-version behavior, and JSON-schema validation.
- Local `cargo test -p geoclt-artifacts` passes.
- Local `cargo package -p geoclt-artifacts --locked` currently fails because `geoclt-schema` is not yet available from crates.io, which is a publish-order dependency constraint rather than a crate defect.

## Required Changes
- Keep the manifest metadata, README, and `docs.rs` link intact so the crate remains externally supportable.
- Preserve the current public module surface unless there is a release-reviewed reason to expand it.
- Keep the embedded registry fixture aligned with the typed schema compatibility policy in `docs/release/crate-support-classes.md`.
- Verify `cargo package --locked` again after `geoclt-schema` is published or otherwise resolvable in the release environment.
- If any release-time drift is introduced, update the crate-local docs and tests together before tagging the release.

## Acceptance Criteria
- `cargo test -p geoclt-artifacts` passes cleanly.
- `cargo package -p geoclt-artifacts --locked` succeeds in the release environment once dependency order is satisfied.
- The README remains present and accurately describes the crate as Python-first release infrastructure, not a standalone end-user product.
- The package metadata continues to advertise the crate correctly for docs.rs and crates.io-style publication.
- Compatibility checks still enforce strict N/N-1 behavior, with mixed schema versions allowed only when `bundle.transitional=true`.
- Bundle validation still rejects non-immutable bundles, bundle-hash mismatches, and signature mismatches when bundle signing is enabled.

## Dependencies and Coordination
- `geoclt-schema` must publish before this crate can be packaged in isolation; this is the key external-release dependency.
- Coordinate any artifact or schema-version changes with the schema and registry owners, since this crate treats typed contracts as stability-critical.
- Coordinate with the Python release train owners so the crate’s publication order stays aligned with the external product rollout.
- If the registry policy changes, update the compatibility expectations here in lockstep with the shared release policy.

## Non-Goals
- No redesign of artifact formats, hashing, signing, or compatibility policy.
- No expansion of the public Rust API beyond the current module surface.
- No standalone Rust product positioning or end-user documentation rewrite.
- No changes to shared schemas, root workspace metadata, or other crate plans.

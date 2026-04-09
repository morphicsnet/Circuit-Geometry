# geoclt-ids Release Readiness Plan

## Summary
`geoclt-ids` is a stable foundation / internal-contract crate in the Python-first Geo-CLT release train. It exposes a small, deterministic `StableId` wrapper built from SHA-256, already has crate docs and a README, and satisfies the release-policy expectation that it be packageable and treated as compatibility-critical.

## Current State
- Cargo metadata is release-shaped: package name, workspace versioning, docs URL, README, keywords, and categories are all present.
- The public Rust surface is minimal: `StableId(pub String)` plus `StableId::from_parts`, with `Serialize` / `Deserialize` support.
- Crate-local unit tests exist and cover determinism plus a golden hash for the current input vector.
- No crate-local integration tests, examples, or benches were found.
- The crate matches the support-class policy for stable foundation crates and is intended to ship in lockstep with the rest of the `geoclt-*` release train.

## Required Changes
- Keep the public identifier format and hashing behavior frozen unless a compatibility review explicitly approves a breaking change.
- Preserve the README and crate-level docs so the crate remains clearly scoped as a stable foundation/internal-contract package for the Python-first release path.
- Use the existing release gates as the final readiness check: `cargo test -p geoclt-ids` and `cargo package -p geoclt-ids --locked`.
- Coordinate any version bump with the workspace lockstep release version used by the other `geoclt-*` crates.

## Acceptance Criteria
- `cargo test -p geoclt-ids` passes with the current deterministic and golden-hash tests.
- `cargo package -p geoclt-ids --locked` succeeds without manifest or packaging defects.
- The crate README and module docs still state the crate's stable foundation / internal-contract role.
- No unresolved compatibility concerns remain for `StableId` serialization, hashing, or string representation.
- Release coordination confirms the crate stays in lockstep with the Python-first external train.

## Dependencies and Coordination
- Release must stay aligned with the shared `geoclt-*` workspace versioning policy.
- Any change to identifier derivation or serialization needs explicit compatibility review because downstream Python-facing artifacts may depend on the exact hash output.
- Coordinate with the lockstep release owner before tagging so this crate ships with the rest of the train rather than as an isolated publish.

## Non-Goals
- No API redesign or expansion beyond `StableId` is in scope.
- No shared-schema, workspace-root, or cross-crate policy edits belong in this crate-local plan.
- No migration of `geoclt-ids` out of the stable foundation / internal-contract support class is proposed.

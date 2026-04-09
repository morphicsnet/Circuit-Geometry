# geoclt-schema Release Readiness Plan

## Summary
`geoclt-schema` is a stable foundation / internal-contract crate in the Python-first Geo-CLT release train. It already has package metadata, a crate README, a small public module surface, and a JSON roundtrip test that exercises the major exported records. Release readiness here is mostly about proving the crate is packageable, keeping schema versions and compatibility notes aligned, and preserving deterministic serialization for the downstream Python and API surfaces.

## Current State
- `Cargo.toml` already includes the crate identity, docs metadata, keywords, categories, and workspace-managed dependencies.
- `README.md` exists and states the crate's role as typed records and versioned contract structs shared across Rust, Python, API, and sidecar surfaces.
- `src/lib.rs` exports nine schema modules: `artifact`, `atlas`, `benchmark`, `event`, `hyperpath`, `mechanism`, `metric`, `receipt`, and `transport`.
- `tests/roundtrip.rs` already covers the main serialized contract types, including flattened artifact metadata, optional fields, and the artifact bundle container.
- The support-class policy explicitly places this crate in the stable foundation / internal-contract tier, which means lockstep versioning and explicit compatibility review apply.

## Required Changes
1. Confirm the crate is packageable with `cargo package --locked` in its workspace context and fix any packaging blockers that appear.
2. Keep the exported schema structs and the `artifact.rs` schema-version constants aligned with the repo-wide JSON schema compatibility surface.
3. Ensure the crate-local roundtrip test continues to cover every exported record that is part of the release contract, including new structs if any are added later.
4. Keep the README and crate docs explicit that this crate is support infrastructure for the Python-first release train, not a standalone evolving public Rust API.
5. Verify that any future schema-version bump in this crate is paired with the matching compatibility-note update outside this crate, per the repo policy.

## Acceptance Criteria
- `cargo package --locked` succeeds for `geoclt-schema`.
- `cargo test -p geoclt-schema` succeeds, including the JSON roundtrip coverage.
- The published crate docs and README clearly describe the crate's stable contract role in the Python-first release train.
- The public module set and serialized field shapes are unchanged unless a release-approved compatibility update is explicitly recorded.
- Any schema-version change is tracked as a coordinated contract change, not a local-only Rust edit.

## Dependencies and Coordination
- Coordinate with the owners of the repo-wide JSON schema definitions and compatibility notes before changing any schema version or serialized field name.
- Coordinate with the Python packaging/release track so downstream consumers can validate the same contract shapes used by Rust.
- Coordinate with the maintainers of the stable foundation crates (`geoclt-core`, `geoclt-ids`, `geoclt-units`) because this crate depends on them and ships in lockstep.
- Treat the support-class policy in `docs/release/crate-support-classes.md` as the release gate for scope and ordering decisions.

## Non-Goals
- No attempt to widen this crate into the primary public Rust API.
- No schema redesign, field renaming, or version bump unless the repo-wide compatibility process is being executed separately.
- No changes to shared schemas, root workspace metadata, or downstream language bindings from this plan file alone.
- No release-order deviation from the documented lockstep train.

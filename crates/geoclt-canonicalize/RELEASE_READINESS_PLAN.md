# geoclt-canonicalize Release Readiness Plan

## Summary
`geoclt-canonicalize` is a supported internal algorithm crate in the Python-first Geo-CLT release train. It already exposes a small deterministic surface for canonical mechanism IDs, clustering, falsifier pattern keys, hyperpath signatures, and stability scoring, with crate docs and a README that match that role. Release readiness here is mainly about preserving those deterministic contracts and validating packageability in the lockstep publish environment.

## Current State
- `Cargo.toml` has the expected package metadata, docs.rs URL, README, keywords, categories, and workspace-managed dependencies on `geoclt-schema`, `geoclt-ids`, and `geoclt-units`.
- `src/lib.rs` exports six focused modules: `canonicalize`, `falsifier_patterns`, `hyperpath_signature`, `mechanism_cluster`, `mechanism_identity`, and `stability_metrics`.
- Crate-local unit tests already cover the key deterministic behaviors: canonicalization stability, order-invariant mechanism IDs, order-invariant cluster IDs, canonical hyperpath signatures, falsifier key sorting, and a simple stability ratio.
- `README.md` already describes the crate as a supported internal algorithm crate for the Python-first release train.
- `cargo test -p geoclt-canonicalize` passes, but `cargo package --locked` fails in this workspace because the direct workspace dependencies are not yet resolvable from crates.io, so packaging readiness depends on the release registry / publish order rather than on a local code fix in this crate.

## Required Changes
- Keep the canonicalization inputs and output shapes frozen unless a compatibility review explicitly approves a breaking change; any hash-input change will alter downstream mechanism and cluster identities.
- Validate `cargo package --locked` in the release environment where the direct dependencies are available, and fix any manifest or packaging defects that appear there.
- Preserve the current crate-local determinism coverage, and add only release-path coverage if the staged runtime bundle checks show a gap in end-to-end exercise of this crate.
- Keep the README and crate docs explicit that this crate is internal support infrastructure for the Python-first release train, not a standalone public Rust API.

## Acceptance Criteria
- `cargo test -p geoclt-canonicalize` passes.
- `cargo package --locked` succeeds in the intended release-packaging environment once the lockstep dependencies are available there.
- The public module set, hashing behavior, and canonical output shapes remain unchanged unless a compatibility review records an approved change.
- The README and crate-level docs still identify this crate as a supported internal algorithm crate for the Python-first release train.
- Release coordination confirms the crate remains aligned with the documented publish order and does not outpace its lower-level dependencies.

## Dependencies and Coordination
- Coordinate with `geoclt-ids`, `geoclt-units`, and `geoclt-schema`, since this crate cannot be packaged independently until those lockstep dependencies are available in the same release context.
- Coordinate with `geoclt-runtime` and `geoclt-ffi` so staged-runtime bundle coverage continues to exercise canonicalization end to end through the Python release path.
- Follow the support-class policy in `docs/release/crate-support-classes.md`; this crate belongs in the supported internal algorithm tier and should ship after the lower-level contract crates are ready.

## Non-Goals
- No API redesign or expansion.
- No schema changes or compatibility-policy edits.
- No changes to workspace-root docs, shared schemas, or other crate plan files.
- No move into operational crate responsibilities or standalone public Rust API ownership.

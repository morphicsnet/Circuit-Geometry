# geoclt-causal Release Readiness Plan

## Summary
`geoclt-causal` is a supported internal algorithm crate in the Python-first Geo-CLT release train. The crate is already small, documented, and covered by a deterministic unit test, so release readiness is primarily about packaging validation, dependency-order coordination, and keeping the crate aligned with the staged runtime bundle path rather than redesigning its API.

## Current State
- `Cargo.toml` already has release-oriented metadata: README, docs.rs URL, keywords, categories, and workspace-managed dependencies on `geoclt-canonicalize`, `geoclt-core`, `geoclt-ids`, `geoclt-schema`, and `geoclt-units`.
- `README.md` explicitly states the crate’s role as a supported internal algorithm crate for mechanism verification in the Python-first release train.
- `src/lib.rs` exposes a single public module, `verify`, which keeps the surface narrow.
- `src/verify.rs` contains the mechanism-verification kernel and one crate-local unit test that checks deterministic behavior.
- There is no separate crate-local `tests/` directory or example program.
- An isolated `cargo test -p geoclt-causal --locked` run passes, while `cargo package --locked -p geoclt-causal --no-verify --allow-dirty` currently fails because `geoclt-canonicalize` is not yet available from the registry; that is a release-order constraint, not a local manifest defect.

## Required Changes
- Verify `geoclt-causal` in the staged release environment after the lower-level dependency crates are available through the intended release path, then rerun package validation.
- Keep the README and crate docs aligned with the support-class policy: supported internal algorithm crate, deterministic typed I/O, and part of the Python-first release train.
- Add crate-local release coverage if the staged bundle path needs more than the existing unit test, ideally a small integration or example-style check that exercises the verification flow end to end.
- Preserve the narrow public API unless a compatibility review explicitly approves a change; any change to the verification kernel’s inputs or output shape is release-significant for downstream Python bindings.
- If packaging validation still fails after dependency-order constraints are satisfied, fix only this crate’s local metadata or docs gaps.

## Acceptance Criteria
- `cargo test -p geoclt-causal --locked` passes.
- `cargo package --locked -p geoclt-causal --no-verify --allow-dirty` succeeds in the staged release environment once `geoclt-canonicalize` and the rest of the exact dependency chain are available there.
- The crate README, manifest metadata, and module surface remain consistent with the supported internal algorithm classification.
- Any new release-path coverage is deterministic and tied to the staged runtime bundle path.
- No breaking API change is introduced without explicit compatibility review.

## Dependencies and Coordination
- Coordinate with `geoclt-canonicalize`, `geoclt-core`, `geoclt-ids`, `geoclt-schema`, and `geoclt-units`, since `geoclt-causal` depends on their exact workspace versions and cannot be packaged ahead of the publish order.
- Follow the repo release order: canonicalization and lower-level contract crates first, then causal as part of the supported internal algorithm group.
- Keep this crate aligned with the Python-first external release train; do not use this plan to alter workspace-wide release policy, schema ownership, or publish sequencing.

## Non-Goals
- No public API redesign.
- No schema changes.
- No workspace-level release-policy changes.
- No Python binding work, FFI work, or CLI/sidecar operational concerns.

# geoclt-core Release Readiness Plan

## Summary
`geoclt-core` is the shared stable foundation for the Geo-CLT crate graph. It already exposes a narrow, reusable surface for deterministic helpers, typed errors, and core traits, and it has crate-local tests covering the main serialization and determinism paths. For the Python-first external release train, the remaining work is release verification and any packaging hygiene issues surfaced by `cargo package --locked`.

## Current State
- Manifest metadata is already release-oriented: README is declared, docs.rs is configured, and the dependency set is workspace-managed.
- Public API is intentionally small: `GeoCltError`, `GeoCltResult<T>`, deterministic hashing/bounding helpers, and the `Validate`, `StableHash`, and `KernelStage` traits.
- The crate has inline unit tests for error JSON round-tripping and deterministic helper behavior; there is no separate crate-local `tests/` directory.
- The repo-wide support-class policy places this crate in the stable foundation / internal-contract tier, which means packageability, docs, and explicit compatibility review are required.

## Required Changes
- Verify the crate packages cleanly with `cargo package --locked` and that the packaged artifact includes the README and docs metadata expected for a future crates.io publication path.
- Verify the crate test surface with `cargo test -p geoclt-core`, including the inline tests in `src/error.rs` and `src/deterministic.rs`.
- Keep the API surface stable unless a compatibility review explicitly approves a change; any changes to `GeoCltError`, `GeoCltResult`, or the deterministic helper signatures are release-significant.
- Preserve lockstep workspace versioning and exact intra-workspace dependency alignment, since this crate is the base contract for downstream Geo-CLT crates.
- If packaging validation exposes a missing file, manifest field, or doc gap, fix it locally in this crate only and keep the surface minimal.

## Acceptance Criteria
- `cargo test -p geoclt-core` passes.
- `cargo package --locked -p geoclt-core` passes without missing-file or manifest errors.
- The crate remains limited to the documented contract surface in `src/lib.rs`, with deterministic helpers, typed errors, and core traits available as intended.
- README and crate documentation remain present and consistent with the support-class policy for a stable foundation crate.
- Any breaking or semantically significant change has explicit compatibility review before release-train promotion.

## Dependencies and Coordination
- Coordinate with downstream crates that consume this contract surface, especially the core dependency chain under the lockstep release train.
- Follow the repo-wide release order: `geoclt-core` is in the first publish group alongside the other foundational crates.
- Do not assume isolated publication; this crate must stay aligned with the Python-first release train and any shared version bump decisions.
- If another crate requires a contract change here, treat that as a cross-crate compatibility event rather than a local cleanup.

## Non-Goals
- No new public features, helper expansions, or trait redesigns.
- No Python binding work, schema changes, or release automation changes.
- No workspace-wide versioning policy changes.
- No publish enablement beyond making this crate ready for the existing release train.

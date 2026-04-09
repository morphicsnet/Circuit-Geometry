# geoclt-metric Release Readiness Plan

## Summary
`geoclt-metric` is a supported internal algorithm crate in the Python-first Geo-CLT release train. It already has crate metadata, a README, a minimal public surface, and a determinism unit test, so the remaining work is release validation and coverage hardening rather than structural redesign.

## Current State
- `Cargo.toml` already carries workspace-managed versioning plus the expected package metadata (`license`, `repository`, `homepage`, `documentation`, `readme`, `keywords`, `categories`).
- `src/lib.rs` exposes only `pub mod metric;`, so the public Rust surface is intentionally narrow.
- `src/metric.rs` implements a deterministic pullback-metric kernel over `geoclt-core`, `geoclt-schema`, `geoclt-units`, and `serde_json`.
- A crate-local unit test already checks determinism for identical inputs and basic patch-count bounds.
- `README.md` already states the crate is a supported internal algorithm crate for the Python-first release train.

## Required Changes
- Verify the crate is packageable with `cargo package --locked` without manifest, path, or metadata failures.
- Expand crate-local tests to cover the release-relevant branches in `estimate_pullback_metric`, including the empty `feature_hints` fallback, the empty `chart_ids` fallback, and lower-bound behavior when `chart_count` is small.
- Add at least one staged-runtime-aligned smoke/example path so the kernel is exercised in the same style expected by the release bundle, not only through a unit test.
- Keep the public API narrow unless a downstream Python binding or schema change explicitly requires expansion.
- Treat any change to `geoclt-schema::atlas::AtlasOverlapMap` or `geoclt-schema::metric::MetricEstimate` as compatibility-sensitive and coordinate it with the lockstep release train.

## Acceptance Criteria
- `cargo test -p geoclt-metric` passes.
- `cargo package --locked -p geoclt-metric` succeeds.
- Determinism coverage exists for the kernel and its fallback branches.
- The crate remains documented as a supported internal algorithm crate and matches the repo-wide support-class policy.
- No hidden crate-local API churn blocks the Python-first release train.

## Dependencies and Coordination
- Coordinate with `geoclt-core`, `geoclt-schema`, and `geoclt-units` owners because this crate depends directly on their typed contracts and deterministic helpers.
- Treat schema changes in `geoclt-schema` as release-train events, not isolated metric work.
- If the staged runtime bundle path or Python-facing integration changes, update the smoke/example coverage in the same change set.

## Non-Goals
- Do not turn `geoclt-metric` into a public top-level API crate.
- Do not change the metric algorithm semantics as part of release-readiness work.
- Do not edit shared schemas, workspace manifests, or Python packaging from this crate-local plan.
- Do not publish this crate independently of the lockstep `geoclt-*` release train.

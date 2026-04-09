# geoclt-cli Release Readiness Plan

## Summary
`geoclt-cli` is an operational internal crate in the Python-first Geo-CLT release train. The release goal is not a public Rust API commitment; it is a packaged, documented, and reproducible operator CLI that stays aligned with the lockstep `geoclt-*` train and the shared schema/runtime surface.

## Current State
- `Cargo.toml` already carries the expected package metadata for a publishable crate: README, docs.rs link, keywords, and science/CLI categories.
- `README.md` correctly frames the crate as an operational internal surface, but it is minimal and does not yet document the available commands or the benchmark fixture/replay constraint.
- `src/main.rs` exposes `version`, `run-profile`, `benchmark`, `validate-artifacts`, and `sidecar serve`; it also embeds deterministic benchmark replay logic and a runtime guard that requires a fixture when `GEOCLT_MODEL_MODE=real`.
- The crate has only lightweight unit coverage in `src/main.rs` for help text and version parsing; there are no crate-local integration or smoke tests for the operator flows.
- There is a visible versioning inconsistency to resolve before release: the CLI `version` command prints `0.1.0`, while artifact metadata hard-codes `geoclt:cli:0.2.0`.

## Required Changes
- Keep the crate explicitly classified as operational internal in user-facing docs; do not present it as the lead public Rust API.
- Expand `README.md` so it names the supported operator commands, explains the benchmark replay requirement, and states the Python-first release-train dependency and scope limits.
- Align release identifiers so the CLI version output, embedded producer string, and workspace release version move together.
- Add or extend crate-local smoke coverage for the primary surfaces: CLI help/version, `run-profile`, fixture-backed `benchmark`, `validate-artifacts`, and the `sidecar` subcommand plumbing.
- Validate packaging from the crate root with locked metadata, and keep the crate ready for downstream publish-order checks once its dependencies are available in the release train.

## Acceptance Criteria
- `cargo test -p geoclt-cli` passes with the existing unit tests plus any added smoke coverage.
- `cargo package --locked` succeeds for `crates/geoclt-cli`.
- The CLI documentation clearly states operational scope, command surface, and benchmark fixture/replay behavior.
- The release identifiers are internally consistent across `version` output and embedded artifact metadata.
- Any release checklist or dry-run step used for this crate records dependency-order issues as sequencing constraints, not crate defects.

## Dependencies and Coordination
- Coordinate with `geoclt-schema`, `geoclt-runtime`, `geoclt-benchmark`, `geoclt-artifacts`, and `geoclt-sidecar` because this CLI is a thin orchestrator over those crates.
- Treat schema or contract changes in the shared benchmark/artifact surfaces as lockstep release work; if those surfaces move, this plan must be rechecked.
- Align with the broader Python-first release train so this crate does not drift ahead of the supported internal crates or their packaging order.

## Non-Goals
- Publishing `geoclt-cli` as a standalone public Rust product.
- Adding new user-facing subcommands or changing the operator workflow shape beyond release-readiness fixes.
- Changing shared schemas, runtime contracts, or sidecar protocol behavior from this crate.
- Reworking the benchmark model execution path to require live external model access during release validation.

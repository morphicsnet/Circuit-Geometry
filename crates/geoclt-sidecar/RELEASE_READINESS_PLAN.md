# geoclt-sidecar Release Readiness Plan

## Summary
`geoclt-sidecar` is the operational sidecar and artifact-bundle emission crate for the Python-first Geo-CLT release train. It already has crate metadata, a documented internal role, generated gRPC bindings, and passing unit tests, but it is not yet ready for an external release train check because packaging is still blocked by unpublished internal dependencies and the runtime version string is not aligned with the crate manifest version.

## Current State
- The crate is a library + build script package with documented docs.rs metadata and a minimal README that already states it is an operational internal crate.
- The public module surface is `batching`, `emit`, `proto`, `server`, and `trace_state`.
- `src/server.rs` contains the only crate-local tests found here; they cover duplicate chunk noop/conflict behavior, valid bundle finalization, and concurrent trace separation.
- `cargo test -p geoclt-sidecar` passes locally.
- `cargo package --locked --no-verify` currently fails in this workspace because `geoclt-artifacts` is not available from crates.io in the package resolution path.
- The server code hard-codes `geoclt:sidecar:0.2.0`, while the crate manifest version is `0.1.0`, so the release identity is not yet single-sourced.

## Required Changes
- Align the crate version and the hard-coded producer/version string so the sidecar release identity comes from one source of truth.
- Expand the crate README to cover operational scope, supported flows, auth/environment behavior, and the fact that this crate is not the lead public Rust API.
- Add release-critical tests for the behaviors not currently covered here: auth rejection/acceptance, abort and status paths, and any backpressure threshold logic that is part of the supported surface.
- Verify `cargo package --locked` in the intended external-release dependency order, after the internal dependency chain needed by this crate is available in the target registry path.
- Keep the crate aligned with the artifact/schema compatibility surface; any bundle or validation changes must remain compatible with the current Python-first release train.

## Acceptance Criteria
- The README clearly says this is an operational internal crate for the Python-first release train and documents the supported runtime boundaries.
- The crate version, producer string, and release metadata are consistent.
- All crate-local tests pass, including the new coverage for operational failure modes and server behavior.
- `cargo package --locked` succeeds in the release-train environment, or the failure is explicitly attributable only to the documented publish-order dependency constraint.
- The crate remains packageable and documented well enough that selective publication stays possible later.

## Dependencies and Coordination
- Coordinate with `geoclt-artifacts` and `geoclt-schema` owners, since bundle assembly and validation depend on them and packaging currently stops at the unpublished `geoclt-artifacts` dependency.
- Follow the repository support-class policy: `geoclt-sidecar` is an operational internal crate and should move in lockstep with the Python-first release train, after the lower-level artifact/schema crates are available.
- Coordinate any auth or runtime contract changes with the Python release owners so the sidecar behavior matches the packaged Python workflow.

## Non-Goals
- Promoting `geoclt-sidecar` to the lead public Rust API.
- Changing shared release policy, root workspace packaging policy, or the crate-support-class order.
- Redesigning the gRPC protocol or artifact schema beyond what is needed for release-readiness alignment.

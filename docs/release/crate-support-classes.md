# Geo-CLT Crate Support Classes

This document defines the support class and external-release expectations for the Rust crate graph behind the Python-first `geoclt` product.

## Support classes

### Stable foundation / internal-contract crates
- `geoclt-core`
- `geoclt-ids`
- `geoclt-units`
- `geoclt-schema`
- `geoclt-artifacts`

Expectations:
- packageable with `cargo package --locked`
- crate docs and README present
- typed contracts treated as stability-critical within a lockstep release train
- changes require explicit compatibility review

### Supported internal algorithm crates
- `geoclt-atlas`
- `geoclt-metric`
- `geoclt-transport`
- `geoclt-hypergraph`
- `geoclt-causal`
- `geoclt-canonicalize`
- `geoclt-benchmark`
- `geoclt-runtime`

Expectations:
- packageable with `cargo package --locked`
- deterministic typed I/O
- examples and tests tied to the staged runtime bundle path
- supported as internal building blocks of the public Python release

### Operational internal crates
- `geoclt-ffi`
- `geoclt-sidecar`
- `geoclt-cli`

Expectations:
- packageable with `cargo package --locked`
- documentation must clearly state operational scope and limitations
- no commitment that these are the lead public Rust API
- required to stay aligned with the public Python release train

## Versioning policy

- All `geoclt-*` crates ship in lockstep for the current release train.
- Intra-workspace crate dependencies use exact matching versions.
- `geoclt-schema` typed structs and the JSON schemas under `schemas/` are treated as one compatibility surface.
- Any schema version bump must update both:
  - typed Rust records in `geoclt-schema`
  - the corresponding JSON schema and compatibility notes

## Packaging policy

- The root workspace package remains unpublished.
- `bindings/python` remains unpublished support infrastructure.
- Every `geoclt-*` crate must be packageable and documented well enough that selective crates.io publication remains possible later.

## Release order

If the project later decides to publish selected Rust crates, publish them in dependency order:

1. `geoclt-core`, `geoclt-ids`, `geoclt-units`
2. `geoclt-schema`, `geoclt-artifacts`
3. `geoclt-atlas`, `geoclt-metric`, `geoclt-transport`, `geoclt-hypergraph`
4. `geoclt-canonicalize`, `geoclt-causal`
5. `geoclt-benchmark`, `geoclt-sidecar`, `geoclt-runtime`
6. `geoclt-ffi`, `geoclt-cli`

Higher-level crates may fail isolated `cargo package` or `cargo publish --dry-run` checks until their lower-level internal dependencies are available through a registry. That is a publish-order constraint, not a remaining metadata defect.

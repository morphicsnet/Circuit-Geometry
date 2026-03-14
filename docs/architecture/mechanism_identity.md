# Mechanism Identity

## Normative Identity Contract

Mechanism IDs are canonical semantic identities. They are derived only from:

- `mechanism_class_type`
- `canonical_hyperpath_signature`
- `normalized_causal_dependency_set`
- `invariant_feature_signature`

Formula:

`mechanism_id = hash(mechanism_class_type, canonical_hyperpath_signature, normalized_causal_dependency_set, invariant_feature_signature)`

Excluded fields (must never affect `mechanism_id`):

- `timestamp`
- `trace_id`
- `run_id`
- `adapter_id`
- `bundle_id`

## Determinism Requirements

- Same semantic inputs must produce identical `mechanism_id`.
- Input ordering in dependency/feature sets must not affect identity.
- Canonical serialization uses RFC8785-style normalization.

## Cluster Identity

Mechanism family cluster IDs are deterministic:

`cluster_id = hash(sorted(member_mechanism_ids))`

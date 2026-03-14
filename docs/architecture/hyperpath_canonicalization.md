# Hyperpath Canonicalization

## Canonicalization Rules

Before hashing for mechanism identity, hyperpaths are normalized as follows:

- Node IDs are deterministically sorted.
- Hyperedge incidence sets are deterministically sorted.
- Feature identifiers are normalized to canonical strings.
- Semantic-order arrays remain in semantic order.
- Set-like arrays are sorted.
- Float values are normalized with RFC8785-compatible canonical JSON serialization.

## Identity Safety Constraints

- Metadata fields not tied to semantics are excluded from identity payloads.
- Canonical payloads are hashed after normalization only.
- Any canonicalization change requires explicit compatibility review.

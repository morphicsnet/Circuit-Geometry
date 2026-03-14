# Canonicalization Rules

Canonical bytes are derived from JSON payloads using these rules:

- UTF-8 encoding.
- Object keys sorted lexicographically.
- Number normalization using RFC8785-style JSON canonicalization.
- Distinguish absent vs explicit `null` exactly as provided.
- Normalize line endings to `\n` for string values before hashing.
- Array order:
  - `semantic_order`: preserve original order.
  - `set_like`: sort deterministically according to canonical JSON item encoding.

`content_hash` is computed from canonical payload bytes only, excluding mutable transport/container metadata.

`artifact_id` is derived deterministically from `artifact_type + schema_version + content_hash`.

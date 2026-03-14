# Artifact Model

Phase 2 canonical artifact identity fields:

- `artifact_id`
- `artifact_type`
- `schema_version`
- `producer`
- `trace_id`
- `run_id`
- `content_hash`
- `created_at`

`artifact_id` is derived from `artifact_type + schema_version + content_hash`.

`content_hash` is computed from canonical payload bytes only.

`created_at` semantics:

- artifact payload: production time
- bundle manifest: finalization time

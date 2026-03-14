# Artifact Schemas

Canonical JSON schemas live in `/schemas`.

Phase 0/1 hardening rules:

- run artifacts must validate before persistence; invalid artifacts abort run.
- deterministic reruns must preserve artifact bundle hash for identical input signature.
- golden artifact outputs for positive fixture live in:
  - `tests/golden/factual_retrieval_v1/positive_default/atlas_overlap_map.json`
  - `tests/golden/factual_retrieval_v1/positive_default/transport_diagnostics.json`
  - `tests/golden/factual_retrieval_v1/positive_default/candidate_event_table.json`
  - `tests/golden/factual_retrieval_v1/positive_default/admitted_hyperpath_table.json`
  - `tests/golden/factual_retrieval_v1/positive_default/falsifier_sheet.json`

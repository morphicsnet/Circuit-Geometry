# Phase 3B Traceability

| Requirement | Assertion | Source |
|---|---|---|
| Explorer/API operational | `explorer_api_smoke_pass`, `analysis_endpoint_responsive` | `services/api/app.py`, gate script |
| Replay/diff determinism | `replay_deterministic`, `differential_analysis_deterministic`, `mechanism_diff_deterministic`, `cohort_analysis_valid` | `python/geoclt/differential.py`, gate script |
| Report bundle determinism | `report_bundle_hash_stable`, `report_bundle_identity_stable` | `python/geoclt/reports.py`, gate script |
| Receipt export path valid | `decision_receipt_export_valid` | API + gate script |
| Read-only explorer semantics | `explorer_read_only_semantics` | gate script |

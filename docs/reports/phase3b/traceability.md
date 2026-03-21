# Phase 3B Traceability

| Requirement | Assertion | Source |
|---|---|---|
| Explorer/API operational | `explorer_api_smoke_pass`, `analysis_endpoint_responsive` | `services/api/app.py`, gate script |
| Replay + endpoint determinism | `replay_deterministic`, `trace_endpoint_deterministic`, `evaluate_lane_deterministic`, `receipt_endpoint_deterministic`, `analysis_report_deterministic` | API + gate script |
| Diff determinism | `differential_analysis_deterministic`, `mechanism_diff_deterministic`, `mechanism_diff_uses_ids_only`, `cohort_analysis_valid` | `python/geoclt/differential.py`, gate script |
| Report bundle determinism | `report_bundle_hash_stable`, `report_bundle_identity_stable`, `report_pack_regeneration_deterministic` | `python/geoclt/reports.py`, `scripts/generate_phase3_report_pack.py`, gate script |
| Receipt export path valid | `decision_receipt_export_valid` | API + gate script |
| Read-only explorer semantics | `explorer_read_only_semantics` | gate script |

# Phase 4B Traceability

| Requirement | Assertion | Source |
|---|---|---|
| Pilot scope is auditable artifact | `pilot_scope_policy_valid` | `python/geoclt/field_trials/pilot_scope.py`, gate script |
| Out-of-scope requests are rejected | `pilot_submission_flow_valid` | `services/api/app.py` |
| Human review loop is canonical | `human_review_flow_valid`, `operator_review_schema_valid` | `python/geoclt/field_trials/adjudication.py`, gate script |
| Receipt linkage remains complete | `receipt_completeness_100pct` | `/pilot/receipt` path + gate script |
| Policy routing quality bounded | `policy_routing_quality_valid`, `false_allow_within_threshold`, `false_block_within_threshold` | lane thresholds + gate script |
| Drift monitoring deterministic | `drift_alert_thresholds_valid`, `mechanism_drift_monitoring_valid`, `cohort_analysis_deterministic` | `python/geoclt/field_trials/drift_analysis.py`, `geoclt.differential` |
| Pilot metrics bundle remains stable | `report_bundle_identity_stable` | `python/geoclt/field_trials/trust_metrics.py` |

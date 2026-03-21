# Phase 3B Executive Summary

- Source report digest: `{"analysis_endpoint_...`
- Gate result: **PASS**
- Source artifact: `outputs/phase3b_gate_report.json`
- Gate runner: `scripts/run_phase3b_gate.sh`
- Assertion runner: `scripts/assert_phase3b_gate_report.py`
- Boolean checks passing: **19/19**

## Key Signals
```json
{
  "analysis_endpoint_responsive": true,
  "analysis_report_deterministic": true,
  "atlas_switch_consistent": true,
  "cohort_analysis_valid": true,
  "decision_receipt_export_valid": true,
  "differential_analysis_deterministic": true,
  "evaluate_lane_deterministic": true,
  "explorer_api_smoke_pass": true,
  "explorer_read_only_semantics": true,
  "mechanism_diff_deterministic": true,
  "mechanism_diff_uses_ids_only": true,
  "overall_pass": true,
  "receipt_endpoint_deterministic": true,
  "replay_deterministic": true,
  "report_bundle_hash_stable": true,
  "report_bundle_identity_stable": true,
  "report_bundle_schema_valid": true,
  "report_pack_regeneration_deterministic": true,
  "trace_endpoint_deterministic": true
}
```

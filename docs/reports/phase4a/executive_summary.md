# Phase 4A Executive Summary

- Gate result: **PASS**
- Source artifact (CI stub): `outputs/phase4a_gate_report.json`
- Source artifact (nightly real-model): `outputs/phase4a_nightly_model_report.json`
- CI stub gate status: **PASS**
- Nightly real-model validation status: **PASS**
- CI stub checks passing: **17/17**
- Nightly checks passing: **9/9**

## CI Stub Booleans
```json
{
  "demo_lane_registry_loaded": true,
  "fallback_rate_within_threshold": true,
  "fallback_semantics_valid": true,
  "golden_dataset_manifest_valid": true,
  "lane_scorecards_valid": true,
  "median_latency_within_budget": true,
  "memory_within_budget": true,
  "model_profile_frozen": true,
  "operator_demo_flow_valid": true,
  "overall_pass": true,
  "policy_action_present": true,
  "receipt_generation_valid": true,
  "replay_trace_deterministic": true,
  "report_bundle_identity_stable": true,
  "run_config_record_valid": true,
  "structured_output_schema_valid": true,
  "success_rate_above_threshold": true
}
```

## Nightly Booleans
```json
{
  "nightly_datasets_valid": true,
  "nightly_divergence_enabled": true,
  "nightly_latency_memory_recorded": true,
  "nightly_profiles_valid": true,
  "nightly_receipt_bundle_valid": true,
  "nightly_report_complete": true,
  "nightly_shared_lane_dual_model_valid": true,
  "nightly_stub_divergence_within_bounds": true,
  "overall_pass": true
}
```

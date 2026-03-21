# Phase 4A Assertions Catalog

Required booleans asserted from `outputs/phase4a_gate_report.json`:

- `overall_pass`
- `demo_lane_registry_loaded`
- `model_profile_frozen`
- `run_config_record_valid`
- `golden_dataset_manifest_valid`
- `lane_scorecards_valid`
- `fallback_semantics_valid`
- `replay_trace_deterministic`
- `receipt_generation_valid`
- `policy_action_present`
- `structured_output_schema_valid`
- `operator_demo_flow_valid`
- `median_latency_within_budget`
- `memory_within_budget`
- `success_rate_above_threshold`
- `fallback_rate_within_threshold`
- `report_bundle_identity_stable`

Required booleans asserted from `outputs/phase4a_nightly_model_report.json`:

- `overall_pass`
- `nightly_profiles_valid`
- `nightly_datasets_valid`
- `nightly_shared_lane_dual_model_valid`
- `nightly_receipt_bundle_valid`
- `nightly_latency_memory_recorded`
- `nightly_divergence_within_bounds`
- `nightly_report_complete`

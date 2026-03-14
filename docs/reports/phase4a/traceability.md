# Phase 4A Traceability

| Requirement | Assertion | Source |
|---|---|---|
| Frozen model runtime profile | `model_profile_frozen` | `scripts/generate_phase4a_gate_report.py` |
| Immutable run configuration contract | `run_config_record_valid` | `python/geoclt/demo/harness.py`, gate script |
| Golden dataset provenance + hash stability | `golden_dataset_manifest_valid` | `python/geoclt/demo/datasets.py`, gate script |
| Lane scorecards + fallback semantics | `lane_scorecards_valid`, `fallback_semantics_valid` | `python/geoclt/demo/scorecards.py`, gate script |
| Deterministic replay | `replay_trace_deterministic` | `python/geoclt/demo/replay.py`, gate script |
| Receipt/report bundle integrity | `receipt_generation_valid`, `report_bundle_identity_stable` | `python/geoclt/receipts.py`, `geoclt.artifacts` |
| Budget compliance | `median_latency_within_budget`, `memory_within_budget`, `success_rate_above_threshold`, `fallback_rate_within_threshold` | gate script |
| Nightly dual-model validation | `nightly_shared_lane_dual_model_valid` | `scripts/generate_phase4a_nightly_model_report.py` |

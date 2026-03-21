# Phase 3A Executive Summary

- Source report digest: `{"artifact_bundle_li...`
- Gate result: **PASS**
- Source artifact: `outputs/phase3a_gate_report.json`
- Gate runner: `scripts/run_phase3a_gate.sh`
- Assertion runner: `scripts/assert_phase3a_gate_report.py`
- Boolean checks passing: **26/26**

## Key Signals
```json
{
  "artifact_bundle_linkage_valid": true,
  "canonicalization_preserved": true,
  "cluster_deterministic": true,
  "cluster_high_cardinality_deterministic": true,
  "cluster_high_cardinality_member_count_valid": true,
  "cluster_identity_deterministic": true,
  "decision_receipt_complete": true,
  "decision_receipt_schema_valid": true,
  "lane_falsifiers_valid": true,
  "lane_policy_actions_valid": true,
  "lane_registry_immutable": true,
  "lane_registry_loaded": true,
  "lane_thresholds_valid": true,
  "mechanism_family_assignment_valid": true,
  "mechanism_id_deterministic": true,
  "mechanism_identity_changes_on_semantic_change": true,
  "mechanism_identity_chart_substitution_stable": true,
  "mechanism_identity_runtime_field_exclusion": true,
  "mechanism_identity_schema_replay_stable": true,
  "mechanism_identity_stable": true,
  "overall_pass": true,
  "policy_evaluation_deterministic": true,
  "receipt_hash_stable": true,
  "receipt_immutability_enforced": true,
  "receipt_mutation_rejected": true,
  "receipt_repersist_idempotent": true
}
```

# Phase 3A Test Results

- Overall pass: `True`
- Total boolean checks: `19`
- Failed checks: `0`

## Failed Checks
- none

## Raw Report
```json
{
  "artifact_bundle_linkage_valid": true,
  "canonicalization_preserved": true,
  "cluster_deterministic": true,
  "cluster_identity_deterministic": true,
  "decision_receipt_complete": true,
  "decision_receipt_schema_valid": true,
  "git_commit": "unknown",
  "lane_count": 4,
  "lane_falsifiers_valid": true,
  "lane_ids": [
    "claims-triage.v1",
    "hallucination-detection.v1",
    "reasoning-path-consistency.v1",
    "safety-mechanism-check.v1"
  ],
  "lane_policy_actions_valid": true,
  "lane_registry_immutable": true,
  "lane_registry_loaded": true,
  "lane_thresholds_valid": true,
  "mechanism_family_assignment_valid": true,
  "mechanism_id_deterministic": true,
  "mechanism_identity_changes_on_semantic_change": true,
  "mechanism_identity_runtime_field_exclusion": true,
  "mechanism_identity_stable": true,
  "overall_pass": true,
  "policy_evaluation_deterministic": true,
  "receipt_hash_stable": true,
  "receipt_policy_action": "allow_with_review"
}
```

# Phase 3A Test Results

- Overall pass: `True`
- Total boolean checks: `26`
- Failed checks: `0`

## Failed Checks
- none

## Raw Report
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
  "git_commit": "2007008f340a17efdca1a38d0d9f6c48e0a907ea",
  "lane_count": 7,
  "lane_falsifiers_valid": true,
  "lane_ids": [
    "claims-triage.v1",
    "hallucination-detection.v1",
    "realworld-claims-triage.v1",
    "realworld-policy-qa.v1",
    "realworld-structured-intake.v1",
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
  "mechanism_identity_chart_substitution_stable": true,
  "mechanism_identity_runtime_field_exclusion": true,
  "mechanism_identity_schema_replay_stable": true,
  "mechanism_identity_stable": true,
  "overall_pass": true,
  "policy_evaluation_deterministic": true,
  "receipt_hash_stable": true,
  "receipt_immutability_enforced": true,
  "receipt_mutation_rejected": true,
  "receipt_policy_action": "allow_with_review",
  "receipt_repersist_idempotent": true
}
```

use geoclt_schema::receipt::DecisionReceipt;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PolicyAction {
    Allow,
    AllowWithReview,
    RouteToFallback,
    Block,
    Escalate,
}

impl PolicyAction {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Allow => "allow",
            Self::AllowWithReview => "allow_with_review",
            Self::RouteToFallback => "route_to_fallback",
            Self::Block => "block",
            Self::Escalate => "escalate",
        }
    }
}

pub fn evaluate_policy(receipt: &DecisionReceipt) -> PolicyAction {
    if receipt.decision == "block" {
        return PolicyAction::Block;
    }
    if receipt.decision == "escalate" {
        return PolicyAction::Escalate;
    }
    if receipt.fallback_selected.is_some() {
        return PolicyAction::RouteToFallback;
    }
    if !receipt.policy_clauses_triggered.is_empty()
        || !receipt.provisional_mechanism_class_ids.is_empty()
    {
        return PolicyAction::AllowWithReview;
    }
    PolicyAction::Allow
}

#[cfg(test)]
mod tests {
    use geoclt_schema::artifact::ArtifactMetadata;
    use geoclt_schema::receipt::DecisionReceipt;

    use super::{evaluate_policy, PolicyAction};

    fn sample_receipt() -> DecisionReceipt {
        DecisionReceipt {
            metadata: ArtifactMetadata {
                artifact_id: "artifact-1".to_string(),
                artifact_type: "decision_receipt".to_string(),
                schema_version: 2,
                producer: "geoclt:runtime:0.3.0".to_string(),
                trace_id: "trace-1".to_string(),
                run_id: "run-1".to_string(),
                content_hash: "a".repeat(64),
                created_at: "2026-01-01T00:00:00Z".to_string(),
            },
            receipt_id: "receipt-1".to_string(),
            input_hash: "in".to_string(),
            output_hash: "out".to_string(),
            active_mechanism_class_ids: vec!["m1".to_string()],
            provisional_mechanism_class_ids: vec![],
            policy_clauses_triggered: vec![],
            geometry_anomaly_flags: vec![],
            chart_instability_flags: vec![],
            decision: "allow".to_string(),
            policy_version: Some("policy.v1".to_string()),
            evaluated_claims: Some(vec!["claim".to_string()]),
            thresholds_applied: Some(serde_json::json!({"threshold": 0.5})),
            falsifiers_checked: Some(vec!["pairwise_sufficiency".to_string()]),
            fallback_selected: None,
            immutable_bundle_hash: Some("b".repeat(64)),
        }
    }

    #[test]
    fn policy_is_deterministic_for_same_receipt() {
        let receipt = sample_receipt();
        assert_eq!(evaluate_policy(&receipt), evaluate_policy(&receipt));
    }

    #[test]
    fn policy_routes_to_review_for_triggered_clauses() {
        let mut receipt = sample_receipt();
        receipt.policy_clauses_triggered = vec!["manual-review".to_string()];
        assert_eq!(evaluate_policy(&receipt), PolicyAction::AllowWithReview);
    }
}

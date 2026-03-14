use serde::{Deserialize, Serialize};
use crate::artifact::ArtifactMetadata;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DecisionReceipt {
    #[serde(flatten)]
    pub metadata: ArtifactMetadata,
    pub receipt_id: String,
    pub input_hash: String,
    pub output_hash: String,
    pub active_mechanism_class_ids: Vec<String>,
    pub provisional_mechanism_class_ids: Vec<String>,
    pub policy_clauses_triggered: Vec<String>,
    pub geometry_anomaly_flags: Vec<String>,
    pub chart_instability_flags: Vec<String>,
    pub decision: String,
    pub policy_version: Option<String>,
    pub evaluated_claims: Option<Vec<String>>,
    pub thresholds_applied: Option<serde_json::Value>,
    pub falsifiers_checked: Option<Vec<String>>,
    pub fallback_selected: Option<String>,
    pub immutable_bundle_hash: Option<String>,
}

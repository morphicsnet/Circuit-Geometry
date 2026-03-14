use serde::{Deserialize, Serialize};
use geoclt_ids::StableId;
use geoclt_units::Score;
use crate::artifact::ArtifactMetadata;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MechanismCandidate {
    #[serde(flatten)]
    pub metadata: ArtifactMetadata,
    pub candidate_id: StableId,
    pub mechanism_class_type: String,
    pub canonical_hyperpath_signature: serde_json::Value,
    pub normalized_causal_dependency_set: Vec<String>,
    pub invariant_feature_signature: Vec<String>,
    pub candidate_score: Score,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MechanismClassRecord {
    #[serde(flatten)]
    pub metadata: ArtifactMetadata,
    pub mechanism_class_id: StableId,
    pub member_path_ids: Vec<StableId>,
    pub atlas_variants_tested: Vec<String>,
    pub persistence_score: Score,
    pub minimality_score: Option<Score>,
    pub geometry_predictiveness: Option<Score>,
    pub pass_fail_status: String,
}

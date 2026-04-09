use crate::artifact::ArtifactMetadata;
use geoclt_ids::StableId;
use geoclt_units::Score;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
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

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
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

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct VerifiedMechanism {
    pub mechanism_id: String,
    pub path_id: StableId,
    pub mechanism_class_type: String,
    pub canonical_hyperpath_signature: serde_json::Value,
    pub normalized_causal_dependency_set: Vec<String>,
    pub invariant_feature_signature: Vec<String>,
    pub candidate_score: Score,
    pub causal_delta: Score,
    pub synergy: Score,
    pub passed: bool,
    pub failed_checks: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct MechanismVerification {
    pub lane_id: String,
    pub behavior_id: String,
    pub verified_count: usize,
    pub passed_count: usize,
    pub mechanisms: Vec<VerifiedMechanism>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CanonicalizedMechanisms {
    pub candidates: Vec<MechanismCandidate>,
    pub classes: Vec<MechanismClassRecord>,
}

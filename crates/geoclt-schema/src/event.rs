use crate::artifact::ArtifactMetadata;
use geoclt_ids::StableId;
use geoclt_units::Score;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventRecord {
    #[serde(flatten)]
    pub metadata: ArtifactMetadata,
    pub event_id: StableId,
    pub sample_id: String,
    pub layer_span: Vec<u32>,
    pub time_window: String,
    pub participant_set: Vec<String>,
    pub participant_types: Vec<String>,
    pub transport_context_id: Option<String>,
    pub causal_weight: Score,
    pub reliability_score: Score,
    pub proposer_score: Option<Score>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CandidateEvent {
    pub event_id: StableId,
    pub participant_set: Vec<String>,
    pub participant_types: Vec<String>,
    pub layer_span: Vec<u32>,
    pub feature_signature: Vec<String>,
    pub transport_context_id: Option<String>,
    pub causal_weight: Score,
    pub reliability_score: Score,
    pub proposer_score: Option<Score>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CandidateEventTable {
    pub lane_id: String,
    pub candidate_count: usize,
    pub events: Vec<CandidateEvent>,
}

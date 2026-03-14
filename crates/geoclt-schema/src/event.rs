use serde::{Deserialize, Serialize};
use geoclt_ids::StableId;
use geoclt_units::Score;
use crate::artifact::ArtifactMetadata;

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

use crate::artifact::ArtifactMetadata;
use geoclt_ids::StableId;
use geoclt_units::Score;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HyperpathRecord {
    #[serde(flatten)]
    pub metadata: ArtifactMetadata,
    pub path_id: StableId,
    pub behavior_id: String,
    pub event_ids: Vec<StableId>,
    pub chart_ids: Vec<String>,
    pub layer_ids: Vec<u32>,
    pub transport_edge_ids: Vec<String>,
    pub geodesic_deviation: Option<Score>,
    pub chart_stability: Score,
    pub transport_coherence: Score,
    pub intervention_faithfulness: Score,
    pub synergy_score_max: Score,
    pub admitted: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct AdmittedHyperpath {
    pub path_id: StableId,
    pub behavior_id: String,
    pub event_ids: Vec<StableId>,
    pub chart_ids: Vec<String>,
    pub layer_ids: Vec<u32>,
    pub transport_edge_ids: Vec<String>,
    pub geodesic_deviation: Option<Score>,
    pub chart_stability: Score,
    pub transport_coherence: Score,
    pub intervention_faithfulness: Score,
    pub synergy_score_max: Score,
    pub admitted: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct AdmittedHyperpathTable {
    pub lane_id: String,
    pub admitted_count: usize,
    pub hyperpaths: Vec<AdmittedHyperpath>,
}

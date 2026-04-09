use geoclt_units::Score;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ChartOverlapDiagnostic {
    pub from_chart_id: String,
    pub to_chart_id: String,
    pub overlap_score: Score,
    pub shared_features: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct AtlasOverlapMap {
    pub model_id: String,
    pub lane_id: String,
    pub profile: String,
    pub chart_count: u32,
    pub overlap_score: Score,
    pub chart_ids: Vec<String>,
    pub chart_overlaps: Vec<ChartOverlapDiagnostic>,
}

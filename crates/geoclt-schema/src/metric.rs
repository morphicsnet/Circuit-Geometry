use geoclt_units::Score;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct MetricEstimate {
    pub lane_id: String,
    pub chart_id: String,
    pub curvature_summary: Score,
    pub distortion_score: Score,
    pub geodesic_stability: Score,
    pub patch_count: u32,
    pub chart_energy: Score,
    pub feature_signature: Vec<String>,
}

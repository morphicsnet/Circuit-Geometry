use serde::{Deserialize, Serialize};
use geoclt_units::Score;
use crate::artifact::ArtifactMetadata;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BenchmarkResult {
    #[serde(flatten)]
    pub metadata: ArtifactMetadata,
    pub model_id: String,
    pub task_id: String,
    pub baseline_id: String,
    pub metric_name: String,
    pub metric_value: Score,
    pub threshold: Option<Score>,
    pub passed: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BenchmarkLane {
    pub lane_id: String,
    pub behavior_id: String,
    pub intervention_delta_threshold: f64,
    pub synergy_threshold: f64,
    pub chart_stability_threshold: f64,
    pub transport_coherence_threshold: f64,
    pub baseline_margin_threshold: f64,
}

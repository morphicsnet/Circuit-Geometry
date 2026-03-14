#[derive(Debug, Clone)]
pub struct MetricPatch {
    pub chart_id: String,
    pub curvature_summary: f64,
    pub distortion_score: f64,
}

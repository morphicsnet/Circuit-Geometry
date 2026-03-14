#[derive(Debug, Clone)]
pub struct AtlasSummary {
    pub chart_count: usize,
    pub overlap_score: f64,
}

pub fn summarize_atlas(chart_count: usize, overlap_score: f64) -> AtlasSummary {
    AtlasSummary { chart_count, overlap_score }
}

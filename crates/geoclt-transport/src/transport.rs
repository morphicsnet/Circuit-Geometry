use geoclt_core::deterministic::clamp;
use geoclt_core::GeoCltResult;
use geoclt_schema::atlas::AtlasOverlapMap;
use geoclt_schema::metric::MetricEstimate;
use geoclt_schema::transport::TransportDiagnostics;
use geoclt_units::Score;

pub fn fit_transport(
    lane_id: &str,
    atlas: &AtlasOverlapMap,
    metric: &MetricEstimate,
) -> GeoCltResult<TransportDiagnostics> {
    let coherence = clamp(
        (atlas.overlap_score.0 * metric.geodesic_stability.0) / (atlas.overlap_score.0 + metric.geodesic_stability.0),
        0.60,
        0.99,
    );
    let distortion = clamp(
        metric.distortion_score.0 * (1.0 + metric.curvature_summary.0),
        0.01,
        0.45,
    );
    let loop_consistency = clamp(coherence * (1.0 - distortion), 0.60, 0.99);
    let geodesic_deviation = clamp((1.0 - loop_consistency) + distortion * 0.2, 0.01, 0.40);
    let transport_edge_ids = atlas
        .chart_ids
        .windows(2)
        .map(|window| format!("{}->{}", window[0], window[1]))
        .collect::<Vec<_>>();

    Ok(TransportDiagnostics {
        lane_id: lane_id.to_string(),
        context_id: format!("transport-{lane_id}"),
        loop_consistency: Score(loop_consistency),
        distortion: Score(distortion),
        coherence: Score(coherence),
        geodesic_deviation: Score(geodesic_deviation),
        transport_edge_ids,
    })
}

#[cfg(test)]
mod tests {
    use geoclt_schema::atlas::AtlasOverlapMap;
    use geoclt_schema::metric::MetricEstimate;
    use geoclt_units::Score;

    use super::fit_transport;

    #[test]
    fn transport_kernel_is_deterministic() {
        let atlas = AtlasOverlapMap {
            model_id: "gpt2".to_string(),
            lane_id: "lane-1".to_string(),
            profile: "profile".to_string(),
            chart_count: 3,
            overlap_score: Score(0.81),
            chart_ids: vec![
                "chart-1".to_string(),
                "chart-2".to_string(),
                "chart-3".to_string(),
            ],
            chart_overlaps: Vec::new(),
        };
        let metric = MetricEstimate {
            lane_id: "lane-1".to_string(),
            chart_id: "chart-1".to_string(),
            curvature_summary: Score(0.72),
            distortion_score: Score(0.18),
            geodesic_stability: Score(0.84),
            patch_count: 4,
            chart_energy: Score(0.79),
            feature_signature: vec!["sae:f12".to_string()],
        };
        let one = fit_transport("lane-1", &atlas, &metric).expect("transport one");
        let two = fit_transport("lane-1", &atlas, &metric).expect("transport two");
        assert_eq!(one, two);
        assert!(!one.transport_edge_ids.is_empty());
    }
}

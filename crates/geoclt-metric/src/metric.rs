use geoclt_core::deterministic::{bounded_f64, bounded_u32, clamp};
use geoclt_core::GeoCltResult;
use geoclt_schema::atlas::AtlasOverlapMap;
use geoclt_schema::metric::MetricEstimate;
use geoclt_units::Score;

pub fn estimate_pullback_metric(
    lane_id: &str,
    atlas: &AtlasOverlapMap,
    feature_hints: &[String],
) -> GeoCltResult<MetricEstimate> {
    let seed = serde_json::json!({
        "lane_id": lane_id,
        "atlas": atlas,
        "feature_hints": feature_hints,
    });
    let chart_id = atlas
        .chart_ids
        .first()
        .cloned()
        .unwrap_or_else(|| "chart-1".to_string());
    let distortion = bounded_f64(&seed, "metric_distortion", 0.06, 0.34)?;
    let curvature = bounded_f64(&seed, "metric_curvature", 0.41, 0.93)?;
    let stability = clamp(
        (atlas.overlap_score.0 + (1.0 - distortion)) / 2.0,
        0.55,
        0.99,
    );
    let patch_count = bounded_u32(
        &seed,
        "metric_patch_count",
        atlas.chart_count.max(1),
        atlas.chart_count + 3,
    )?;
    let chart_energy = clamp((curvature + atlas.overlap_score.0) / 2.0, 0.35, 0.99);

    Ok(MetricEstimate {
        lane_id: lane_id.to_string(),
        chart_id,
        curvature_summary: Score(curvature),
        distortion_score: Score(distortion),
        geodesic_stability: Score(stability),
        patch_count,
        chart_energy: Score(chart_energy),
        feature_signature: if feature_hints.is_empty() {
            vec!["metric:default".to_string()]
        } else {
            feature_hints.to_vec()
        },
    })
}

#[cfg(test)]
mod tests {
    use geoclt_schema::atlas::{AtlasOverlapMap, ChartOverlapDiagnostic};
    use geoclt_units::Score;

    use super::estimate_pullback_metric;

    #[test]
    fn metric_kernel_is_deterministic() {
        let atlas = AtlasOverlapMap {
            model_id: "gpt2".to_string(),
            lane_id: "lane-1".to_string(),
            profile: "profile".to_string(),
            chart_count: 3,
            overlap_score: Score(0.82),
            chart_ids: vec![
                "chart-1".to_string(),
                "chart-2".to_string(),
                "chart-3".to_string(),
            ],
            chart_overlaps: vec![ChartOverlapDiagnostic {
                from_chart_id: "chart-1".to_string(),
                to_chart_id: "chart-2".to_string(),
                overlap_score: Score(0.82),
                shared_features: vec!["sae:f1".to_string()],
            }],
        };
        let features = vec!["sae:f12".to_string()];
        let one = estimate_pullback_metric("lane-1", &atlas, &features).expect("metric one");
        let two = estimate_pullback_metric("lane-1", &atlas, &features).expect("metric two");
        assert_eq!(one, two);
        assert!(one.patch_count >= atlas.chart_count);
    }
}

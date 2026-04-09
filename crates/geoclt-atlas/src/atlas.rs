use std::collections::BTreeSet;

use geoclt_core::deterministic::{bounded_f64, bounded_u32, clamp};
use geoclt_core::{GeoCltError, GeoCltResult};
use geoclt_schema::atlas::{AtlasOverlapMap, ChartOverlapDiagnostic};
use geoclt_units::Score;

fn normalized_features(feature_hints: &[String], lane_id: &str, profile: &str) -> Vec<String> {
    let mut ordered = feature_hints
        .iter()
        .filter(|value| !value.trim().is_empty())
        .cloned()
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect::<Vec<_>>();
    if ordered.is_empty() {
        ordered.push(format!("behavior:{profile}"));
        ordered.push(format!("lane:{lane_id}"));
        ordered.push("atlas:default".to_string());
    }
    ordered
}

pub fn fit_atlas(
    model_id: &str,
    lane_id: &str,
    profile: &str,
    feature_hints: &[String],
) -> GeoCltResult<AtlasOverlapMap> {
    let features = normalized_features(feature_hints, lane_id, profile);
    let seed = serde_json::json!({
        "model_id": model_id,
        "lane_id": lane_id,
        "profile": profile,
        "feature_hints": features,
    });

    let chart_count = bounded_u32(&seed, "atlas_chart_count", 3, 6)?;
    let chart_ids = (0..chart_count)
        .map(|index| format!("chart-{}", index + 1))
        .collect::<Vec<_>>();

    let mut chart_overlaps = Vec::new();
    for index in 0..chart_count {
        let from_chart_id = chart_ids[index as usize].clone();
        let to_chart_id = chart_ids[((index + 1) % chart_count) as usize].clone();
        let overlap = bounded_f64(
            &serde_json::json!({
                "seed": seed,
                "from": from_chart_id,
                "to": to_chart_id,
            }),
            "atlas_overlap",
            0.62,
            0.97,
        )?;
        let shared_features = features
            .iter()
            .cycle()
            .skip(index as usize)
            .take(3)
            .cloned()
            .collect::<Vec<_>>();
        chart_overlaps.push(ChartOverlapDiagnostic {
            from_chart_id,
            to_chart_id,
            overlap_score: Score(overlap),
            shared_features,
        });
    }

    if chart_overlaps.is_empty() {
        return Err(GeoCltError::Validation(
            "atlas construction produced no overlap diagnostics".to_string(),
        ));
    }

    let average_overlap = chart_overlaps
        .iter()
        .map(|diagnostic| diagnostic.overlap_score.0)
        .sum::<f64>()
        / chart_overlaps.len() as f64;

    Ok(AtlasOverlapMap {
        model_id: model_id.to_string(),
        lane_id: lane_id.to_string(),
        profile: profile.to_string(),
        chart_count,
        overlap_score: Score(clamp(average_overlap, 0.60, 0.99)),
        chart_ids,
        chart_overlaps,
    })
}

#[cfg(test)]
mod tests {
    use super::fit_atlas;

    #[test]
    fn atlas_kernel_is_deterministic() {
        let features = vec!["sae:f12".to_string(), "head:5:3".to_string()];
        let one = fit_atlas("gpt2", "lane-1", "factual_retrieval", &features).expect("atlas one");
        let two = fit_atlas("gpt2", "lane-1", "factual_retrieval", &features).expect("atlas two");
        assert_eq!(one, two);
        assert!(one.chart_count >= 3);
        assert_eq!(one.chart_overlaps.len() as u32, one.chart_count);
    }
}

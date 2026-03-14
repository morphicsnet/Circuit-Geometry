use geoclt_schema::hyperpath::HyperpathRecord;

fn sort_strings(values: &[String]) -> Vec<String> {
    let mut sorted = values.to_vec();
    sorted.sort();
    sorted
}

fn sort_stable_ids(values: &[geoclt_ids::StableId]) -> Vec<String> {
    let mut sorted = values.iter().map(|value| value.0.clone()).collect::<Vec<_>>();
    sorted.sort();
    sorted
}

fn normalize_float(value: f64) -> String {
    // RFC8785-compatible decimal normalization with bounded precision.
    let rounded = (value * 1_000_000.0).round() / 1_000_000.0;
    format!("{rounded:.6}")
}

pub fn canonical_hyperpath_signature(path: &HyperpathRecord) -> serde_json::Value {
    serde_json::json!({
        "path_id": path.path_id.0.clone(),
        "behavior_id": path.behavior_id,
        "event_ids": sort_stable_ids(&path.event_ids),
        "chart_ids": sort_strings(&path.chart_ids),
        "layer_ids": path.layer_ids,
        "transport_edge_ids": sort_strings(&path.transport_edge_ids),
        "geodesic_deviation": path.geodesic_deviation.map(|value| normalize_float(value.0)),
        "chart_stability": normalize_float(path.chart_stability.0),
        "transport_coherence": normalize_float(path.transport_coherence.0),
        "intervention_faithfulness": normalize_float(path.intervention_faithfulness.0),
        "synergy_score_max": normalize_float(path.synergy_score_max.0),
        "admitted": path.admitted,
    })
}

#[cfg(test)]
mod tests {
    use geoclt_ids::StableId;
    use geoclt_schema::artifact::ArtifactMetadata;
    use geoclt_schema::hyperpath::HyperpathRecord;
    use geoclt_units::Score;

    use super::canonical_hyperpath_signature;

    fn sample_path() -> HyperpathRecord {
        HyperpathRecord {
            metadata: ArtifactMetadata {
                artifact_id: "artifact-x".to_string(),
                artifact_type: "hyperpath_record".to_string(),
                schema_version: 2,
                producer: "geoclt:test:0.2.0".to_string(),
                trace_id: "trace-1".to_string(),
                run_id: "run-1".to_string(),
                content_hash: "a".repeat(64),
                created_at: "2026-01-01T00:00:00Z".to_string(),
            },
            path_id: StableId::from_parts(&["path", "1"]),
            behavior_id: "factual_retrieval".to_string(),
            event_ids: vec![
                StableId::from_parts(&["event", "b"]),
                StableId::from_parts(&["event", "a"]),
            ],
            chart_ids: vec!["chart-b".to_string(), "chart-a".to_string()],
            layer_ids: vec![5, 6],
            transport_edge_ids: vec!["edge-b".to_string(), "edge-a".to_string()],
            geodesic_deviation: Some(Score(0.123456789)),
            chart_stability: Score(0.87654321),
            transport_coherence: Score(0.7654321),
            intervention_faithfulness: Score(0.654321),
            synergy_score_max: Score(0.54321),
            admitted: true,
        }
    }

    #[test]
    fn canonical_signature_is_stable() {
        let one = canonical_hyperpath_signature(&sample_path());
        let two = canonical_hyperpath_signature(&sample_path());
        assert_eq!(one, two);
        let event_ids = one["event_ids"]
            .as_array()
            .expect("event ids array")
            .iter()
            .map(|value| value.as_str().expect("event id string").to_string())
            .collect::<Vec<_>>();
        let mut sorted = event_ids.clone();
        sorted.sort();
        assert_eq!(event_ids, sorted);
        assert_eq!(one["chart_ids"], serde_json::json!(["chart-a", "chart-b"]));
    }
}

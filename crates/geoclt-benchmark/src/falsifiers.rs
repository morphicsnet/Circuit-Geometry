use geoclt_schema::benchmark::BenchmarkLane;
use geoclt_schema::hyperpath::HyperpathRecord;

#[derive(Debug, Clone)]
pub struct FalsifierReport {
    pub pairwise_sufficiency_triggered: bool,
    pub chart_fragility_triggered: bool,
    pub transport_irrelevance_triggered: bool,
    pub geometry_non_predictiveness_triggered: bool,
    pub spurious_synergy_triggered: bool,
}

impl FalsifierReport {
    pub fn any_triggered(&self) -> bool {
        self.pairwise_sufficiency_triggered
            || self.chart_fragility_triggered
            || self.transport_irrelevance_triggered
            || self.geometry_non_predictiveness_triggered
            || self.spurious_synergy_triggered
    }
}

pub fn evaluate_falsifiers(
    path: &HyperpathRecord,
    strongest_baseline: f64,
    lane: &BenchmarkLane,
) -> FalsifierReport {
    FalsifierReport {
        pairwise_sufficiency_triggered: strongest_baseline + lane.baseline_margin_threshold
            >= path.intervention_faithfulness.0,
        chart_fragility_triggered: path.chart_stability.0 < lane.chart_stability_threshold,
        transport_irrelevance_triggered: path.transport_coherence.0
            < lane.transport_coherence_threshold,
        geometry_non_predictiveness_triggered: path
            .geodesic_deviation
            .map(|score| score.0.abs() < 0.01)
            .unwrap_or(true),
        spurious_synergy_triggered: path.synergy_score_max.0 < lane.synergy_threshold,
    }
}

#[cfg(test)]
mod tests {
    use super::evaluate_falsifiers;
    use geoclt_ids::StableId;
    use geoclt_schema::artifact::ArtifactMetadata;
    use geoclt_schema::benchmark::BenchmarkLane;
    use geoclt_schema::hyperpath::HyperpathRecord;
    use geoclt_units::Score;

    fn lane() -> BenchmarkLane {
        BenchmarkLane {
            lane_id: "factual_retrieval.v1".to_string(),
            behavior_id: "factual_retrieval".to_string(),
            intervention_delta_threshold: 0.10,
            synergy_threshold: 0.05,
            chart_stability_threshold: 0.70,
            transport_coherence_threshold: 0.70,
            baseline_margin_threshold: 0.05,
        }
    }

    fn path() -> HyperpathRecord {
        HyperpathRecord {
            metadata: ArtifactMetadata {
                artifact_id: "artifact-1".to_string(),
                artifact_type: "hyperpath_record".to_string(),
                schema_version: 2,
                producer: "geoclt:test:0.2.0".to_string(),
                trace_id: "trace-1".to_string(),
                run_id: "run-1".to_string(),
                content_hash:
                    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                        .to_string(),
                created_at: "2026-01-01T00:00:00Z".to_string(),
            },
            path_id: StableId::from_parts(&["path", "x"]),
            behavior_id: "factual_retrieval".to_string(),
            event_ids: vec![StableId::from_parts(&["event", "1"])],
            chart_ids: vec!["chart-a".to_string()],
            layer_ids: vec![5, 6],
            transport_edge_ids: vec!["edge-1".to_string()],
            geodesic_deviation: Some(Score(0.2)),
            chart_stability: Score(0.83),
            transport_coherence: Score(0.79),
            intervention_faithfulness: Score(0.18),
            synergy_score_max: Score(0.08),
            admitted: false,
        }
    }

    #[test]
    fn falsifiers_stay_clear_for_strong_paths() {
        let lane = lane();
        let report = evaluate_falsifiers(&path(), 0.10, &lane);
        assert!(!report.any_triggered());
    }

    #[test]
    fn falsifiers_trigger_when_baseline_is_too_close() {
        let lane = lane();
        let report = evaluate_falsifiers(&path(), 0.16, &lane);
        assert!(report.pairwise_sufficiency_triggered);
        assert!(report.any_triggered());
    }

    #[test]
    fn falsifiers_can_trigger_in_combination() {
        let lane = lane();
        let mut weak = path();
        weak.chart_stability = Score(0.61);
        weak.transport_coherence = Score(0.55);
        weak.synergy_score_max = Score(0.02);
        weak.geodesic_deviation = None;

        let report = evaluate_falsifiers(&weak, 0.20, &lane);
        assert!(report.pairwise_sufficiency_triggered);
        assert!(report.chart_fragility_triggered);
        assert!(report.transport_irrelevance_triggered);
        assert!(report.geometry_non_predictiveness_triggered);
        assert!(report.spurious_synergy_triggered);
        assert!(report.any_triggered());
    }
}

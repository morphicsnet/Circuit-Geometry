use geoclt_schema::hyperpath::HyperpathRecord;
use geoclt_schema::benchmark::BenchmarkLane;

#[derive(Debug, Clone, PartialEq)]
pub struct AdmissionEvaluation {
    pub passed: bool,
    pub failed_checks: Vec<&'static str>,
    pub min_margin: f64,
}

pub fn evaluate_admission(path: &HyperpathRecord, lane: &BenchmarkLane) -> AdmissionEvaluation {
    let mut failed_checks = Vec::new();

    let intervention_margin = path.intervention_faithfulness.0 - lane.intervention_delta_threshold;
    if intervention_margin < 0.0 {
        failed_checks.push("intervention_faithfulness");
    }

    let synergy_margin = path.synergy_score_max.0 - lane.synergy_threshold;
    if synergy_margin < 0.0 {
        failed_checks.push("synergy_score_max");
    }

    let chart_margin = path.chart_stability.0 - lane.chart_stability_threshold;
    if chart_margin < 0.0 {
        failed_checks.push("chart_stability");
    }

    let transport_margin = path.transport_coherence.0 - lane.transport_coherence_threshold;
    if transport_margin < 0.0 {
        failed_checks.push("transport_coherence");
    }

    AdmissionEvaluation {
        passed: failed_checks.is_empty(),
        failed_checks,
        min_margin: intervention_margin
            .min(synergy_margin)
            .min(chart_margin)
            .min(transport_margin),
    }
}

pub fn admitted(path: &HyperpathRecord, lane: &BenchmarkLane) -> bool {
    evaluate_admission(path, lane).passed
}

#[cfg(test)]
mod tests {
    use super::{admitted, evaluate_admission};
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

    fn path(intervention: f64, synergy: f64, chart: f64, transport: f64) -> HyperpathRecord {
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
            chart_stability: Score(chart),
            transport_coherence: Score(transport),
            intervention_faithfulness: Score(intervention),
            synergy_score_max: Score(synergy),
            admitted: false,
        }
    }

    #[test]
    fn admission_passes_when_all_thresholds_are_met() {
        let lane = lane();
        let path = path(0.14, 0.07, 0.82, 0.79);
        assert!(admitted(&path, &lane));

        let evaluation = evaluate_admission(&path, &lane);
        assert!(evaluation.passed);
        assert!(evaluation.failed_checks.is_empty());
        assert!(evaluation.min_margin >= 0.0);
    }

    #[test]
    fn admission_reports_failed_clauses() {
        let lane = lane();
        let path = path(0.09, 0.03, 0.85, 0.65);

        let evaluation = evaluate_admission(&path, &lane);
        assert!(!evaluation.passed);
        assert_eq!(
            evaluation.failed_checks,
            vec![
                "intervention_faithfulness",
                "synergy_score_max",
                "transport_coherence",
            ]
        );
        assert!(evaluation.min_margin < 0.0);
    }

    #[test]
    fn admission_accepts_values_at_exact_threshold() {
        let lane = lane();
        let path = path(
            lane.intervention_delta_threshold,
            lane.synergy_threshold,
            lane.chart_stability_threshold,
            lane.transport_coherence_threshold,
        );

        let evaluation = evaluate_admission(&path, &lane);
        assert!(evaluation.passed);
        assert!(evaluation.failed_checks.is_empty());
        assert_eq!(evaluation.min_margin, 0.0);
    }
}

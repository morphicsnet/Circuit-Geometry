use crate::admission::{evaluate_admission, AdmissionEvaluation};
use crate::falsifiers::{evaluate_falsifiers, FalsifierReport};
use geoclt_schema::benchmark::BenchmarkLane;
use geoclt_schema::hyperpath::HyperpathRecord;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct BaselineResult {
    pub baseline_id: String,
    pub intervention_faithfulness: f64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ConformanceClass {
    Conformant,
    Provisional,
    Rejected,
}

impl ConformanceClass {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Conformant => "conformant",
            Self::Provisional => "provisional",
            Self::Rejected => "rejected",
        }
    }
}

#[derive(Debug, Clone)]
pub struct ContractEvaluation {
    pub admission: AdmissionEvaluation,
    pub falsifiers: FalsifierReport,
    pub strongest_baseline_id: Option<String>,
    pub strongest_baseline: f64,
    pub beats_baseline: bool,
    pub conformance_class: ConformanceClass,
}

fn strongest_baseline(baselines: &[BaselineResult]) -> (Option<String>, f64) {
    let mut ordered = baselines
        .iter()
        .filter(|baseline| baseline.intervention_faithfulness.is_finite())
        .collect::<Vec<_>>();
    ordered.sort_by(|a, b| a.baseline_id.cmp(&b.baseline_id));

    let mut strongest_id: Option<String> = None;
    let mut strongest_value = f64::NEG_INFINITY;
    for baseline in ordered {
        if baseline.intervention_faithfulness > strongest_value {
            strongest_value = baseline.intervention_faithfulness;
            strongest_id = Some(baseline.baseline_id.clone());
        }
    }

    if strongest_value.is_finite() {
        (strongest_id, strongest_value)
    } else {
        (None, 0.0)
    }
}

pub fn evaluate_contract(
    path: &HyperpathRecord,
    lane: &BenchmarkLane,
    baselines: &[BaselineResult],
) -> ContractEvaluation {
    let (strongest_baseline_id, strongest_baseline) = strongest_baseline(baselines);

    let admission = evaluate_admission(path, lane);
    let beats_baseline =
        path.intervention_faithfulness.0 >= strongest_baseline + lane.baseline_margin_threshold;
    let falsifiers = evaluate_falsifiers(path, strongest_baseline, lane);

    let conformance_class = if admission.passed && beats_baseline && !falsifiers.any_triggered() {
        ConformanceClass::Conformant
    } else if admission.passed && beats_baseline {
        ConformanceClass::Provisional
    } else {
        ConformanceClass::Rejected
    };

    ContractEvaluation {
        admission,
        falsifiers,
        strongest_baseline_id,
        strongest_baseline,
        beats_baseline,
        conformance_class,
    }
}

#[cfg(test)]
mod tests {
    use super::{evaluate_contract, BaselineResult, ConformanceClass};
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

    fn path(intervention: f64, geodesic_deviation: f64) -> HyperpathRecord {
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
            geodesic_deviation: Some(Score(geodesic_deviation)),
            chart_stability: Score(0.85),
            transport_coherence: Score(0.82),
            intervention_faithfulness: Score(intervention),
            synergy_score_max: Score(0.09),
            admitted: false,
        }
    }

    #[test]
    fn strong_paths_become_conformant() {
        let lane = lane();
        let baselines = vec![
            BaselineResult {
                baseline_id: "single_sae".to_string(),
                intervention_faithfulness: 0.11,
            },
            BaselineResult {
                baseline_id: "pairwise_graph".to_string(),
                intervention_faithfulness: 0.12,
            },
        ];

        let evaluation = evaluate_contract(&path(0.20, 0.20), &lane, &baselines);
        assert!(evaluation.admission.passed);
        assert!(evaluation.beats_baseline);
        assert_eq!(evaluation.strongest_baseline_id.as_deref(), Some("pairwise_graph"));
        assert_eq!(evaluation.conformance_class, ConformanceClass::Conformant);
    }

    #[test]
    fn weak_paths_become_rejected() {
        let lane = lane();
        let baselines = vec![BaselineResult {
            baseline_id: "single_sae".to_string(),
            intervention_faithfulness: 0.16,
        }];

        let evaluation = evaluate_contract(&path(0.14, 0.20), &lane, &baselines);
        assert!(evaluation.admission.passed);
        assert!(!evaluation.beats_baseline);
        assert_eq!(evaluation.conformance_class, ConformanceClass::Rejected);
    }

    #[test]
    fn margin_tie_is_treated_as_pass() {
        let lane = lane();
        let baselines = vec![BaselineResult {
            baseline_id: "single_sae".to_string(),
            intervention_faithfulness: 0.15,
        }];
        let evaluation = evaluate_contract(&path(0.20, 0.20), &lane, &baselines);
        assert!(evaluation.beats_baseline);
        assert_eq!(evaluation.conformance_class, ConformanceClass::Provisional);
    }

    #[test]
    fn strongest_baseline_tie_breaks_by_id() {
        let lane = lane();
        let baselines = vec![
            BaselineResult {
                baseline_id: "zeta".to_string(),
                intervention_faithfulness: 0.14,
            },
            BaselineResult {
                baseline_id: "alpha".to_string(),
                intervention_faithfulness: 0.14,
            },
        ];
        let evaluation = evaluate_contract(&path(0.20, 0.20), &lane, &baselines);
        assert_eq!(evaluation.strongest_baseline, 0.14);
        assert_eq!(evaluation.strongest_baseline_id.as_deref(), Some("alpha"));
    }

    #[test]
    fn strong_but_falsified_paths_are_provisional() {
        let lane = lane();
        let baselines = vec![BaselineResult {
            baseline_id: "single_sae".to_string(),
            intervention_faithfulness: 0.12,
        }];
        let evaluation = evaluate_contract(&path(0.20, 0.0), &lane, &baselines);
        assert!(evaluation.admission.passed);
        assert!(evaluation.beats_baseline);
        assert!(evaluation.falsifiers.geometry_non_predictiveness_triggered);
        assert_eq!(evaluation.conformance_class, ConformanceClass::Provisional);
    }
}

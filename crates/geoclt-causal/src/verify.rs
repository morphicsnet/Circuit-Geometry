use geoclt_canonicalize::hyperpath_signature::canonical_hyperpath_signature;
use geoclt_canonicalize::mechanism_identity::{derive_mechanism_id, MechanismIdentityInput};
use geoclt_core::{GeoCltError, GeoCltResult};
use geoclt_schema::artifact::ArtifactMetadata;
use geoclt_schema::benchmark::BenchmarkLane;
use geoclt_schema::hyperpath::{AdmittedHyperpath, AdmittedHyperpathTable, HyperpathRecord};
use geoclt_schema::mechanism::{MechanismVerification, VerifiedMechanism};
use geoclt_units::Score;

fn to_record(path: &AdmittedHyperpath) -> HyperpathRecord {
    HyperpathRecord {
        metadata: ArtifactMetadata {
            artifact_id: String::new(),
            artifact_type: "hyperpath_record".to_string(),
            schema_version: 2,
            producer: "geoclt:causal:0.2.0".to_string(),
            trace_id: "trace-internal".to_string(),
            run_id: "run-internal".to_string(),
            content_hash: String::new(),
            created_at: "2026-01-01T00:00:00Z".to_string(),
        },
        path_id: path.path_id.clone(),
        behavior_id: path.behavior_id.clone(),
        event_ids: path.event_ids.clone(),
        chart_ids: path.chart_ids.clone(),
        layer_ids: path.layer_ids.clone(),
        transport_edge_ids: path.transport_edge_ids.clone(),
        geodesic_deviation: path.geodesic_deviation,
        chart_stability: path.chart_stability,
        transport_coherence: path.transport_coherence,
        intervention_faithfulness: path.intervention_faithfulness,
        synergy_score_max: path.synergy_score_max,
        admitted: path.admitted,
    }
}

pub fn verify_mechanisms(
    lane: &BenchmarkLane,
    paths: &AdmittedHyperpathTable,
) -> GeoCltResult<MechanismVerification> {
    let mut mechanisms = Vec::new();
    for path in &paths.hyperpaths {
        let mut failed_checks = Vec::new();
        if path.intervention_faithfulness.0 < lane.intervention_delta_threshold {
            failed_checks.push("intervention_faithfulness".to_string());
        }
        if path.synergy_score_max.0 < lane.synergy_threshold {
            failed_checks.push("synergy_score_max".to_string());
        }
        if path.chart_stability.0 < lane.chart_stability_threshold {
            failed_checks.push("chart_stability".to_string());
        }
        if path.transport_coherence.0 < lane.transport_coherence_threshold {
            failed_checks.push("transport_coherence".to_string());
        }

        let canonical_signature = canonical_hyperpath_signature(&to_record(path));
        let normalized_causal_dependency_set = path
            .transport_edge_ids
            .iter()
            .chain(path.chart_ids.iter())
            .cloned()
            .collect::<Vec<_>>();
        let invariant_feature_signature = path
            .event_ids
            .iter()
            .map(|value| value.0.clone())
            .collect::<Vec<_>>();
        let mechanism_id = derive_mechanism_id(&MechanismIdentityInput {
            mechanism_class_type: "causal_hyperpath".to_string(),
            canonical_hyperpath_signature: canonical_signature.clone(),
            normalized_causal_dependency_set: normalized_causal_dependency_set.clone(),
            invariant_feature_signature: invariant_feature_signature.clone(),
        })
        .map_err(GeoCltError::Internal)?;
        let candidate_score = (path.intervention_faithfulness.0
            + path.synergy_score_max.0
            + path.chart_stability.0
            + path.transport_coherence.0)
            / 4.0;
        let causal_delta = path.intervention_faithfulness.0 - lane.intervention_delta_threshold;
        let passed = failed_checks.is_empty() && path.admitted;
        mechanisms.push(VerifiedMechanism {
            mechanism_id,
            path_id: path.path_id.clone(),
            mechanism_class_type: "causal_hyperpath".to_string(),
            canonical_hyperpath_signature: canonical_signature,
            normalized_causal_dependency_set,
            invariant_feature_signature,
            candidate_score: Score(candidate_score.max(0.0)),
            causal_delta: Score(causal_delta),
            synergy: path.synergy_score_max,
            passed,
            failed_checks,
        });
    }
    let passed_count = mechanisms
        .iter()
        .filter(|mechanism| mechanism.passed)
        .count();
    Ok(MechanismVerification {
        lane_id: lane.lane_id.clone(),
        behavior_id: lane.behavior_id.clone(),
        verified_count: mechanisms.len(),
        passed_count,
        mechanisms,
    })
}

#[cfg(test)]
mod tests {
    use geoclt_ids::StableId;
    use geoclt_schema::benchmark::BenchmarkLane;
    use geoclt_schema::hyperpath::{AdmittedHyperpath, AdmittedHyperpathTable};
    use geoclt_units::Score;

    use super::verify_mechanisms;

    #[test]
    fn mechanism_verification_is_deterministic() {
        let lane = BenchmarkLane {
            lane_id: "lane-1".to_string(),
            behavior_id: "behavior".to_string(),
            intervention_delta_threshold: 0.10,
            synergy_threshold: 0.05,
            chart_stability_threshold: 0.70,
            transport_coherence_threshold: 0.70,
            baseline_margin_threshold: 0.05,
        };
        let paths = AdmittedHyperpathTable {
            lane_id: "lane-1".to_string(),
            admitted_count: 1,
            hyperpaths: vec![AdmittedHyperpath {
                path_id: StableId::from_parts(&["path", "1"]),
                behavior_id: "behavior".to_string(),
                event_ids: vec![StableId::from_parts(&["event", "1"])],
                chart_ids: vec!["chart-1".to_string()],
                layer_ids: vec![5, 6],
                transport_edge_ids: vec!["chart-1->chart-2".to_string()],
                geodesic_deviation: Some(Score(0.04)),
                chart_stability: Score(0.88),
                transport_coherence: Score(0.83),
                intervention_faithfulness: Score(0.22),
                synergy_score_max: Score(0.12),
                admitted: true,
            }],
        };
        let one = verify_mechanisms(&lane, &paths).expect("one");
        let two = verify_mechanisms(&lane, &paths).expect("two");
        assert_eq!(one, two);
        assert_eq!(one.passed_count, 1);
    }
}

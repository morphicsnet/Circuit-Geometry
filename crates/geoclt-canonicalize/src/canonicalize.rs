use crate::mechanism_cluster::derive_cluster_id;
use geoclt_ids::StableId;
use geoclt_schema::artifact::ArtifactMetadata;
use geoclt_schema::atlas::AtlasOverlapMap;
use geoclt_schema::mechanism::{
    CanonicalizedMechanisms, MechanismCandidate, MechanismClassRecord, MechanismVerification,
};
use geoclt_units::Score;
use std::collections::BTreeMap;

pub fn canonical_mechanism_key(parts: &[&str]) -> String {
    parts.join("::")
}

fn metadata(
    artifact_type: &str,
    artifact_id: &str,
    run_id: &str,
    trace_id: &str,
    content_hash: &str,
) -> ArtifactMetadata {
    ArtifactMetadata {
        artifact_id: artifact_id.to_string(),
        artifact_type: artifact_type.to_string(),
        schema_version: 2,
        producer: "geoclt:canonicalize:0.2.0".to_string(),
        trace_id: trace_id.to_string(),
        run_id: run_id.to_string(),
        content_hash: content_hash.to_string(),
        created_at: "2026-01-01T00:00:00Z".to_string(),
    }
}

pub fn canonicalize_mechanisms(
    verification: &MechanismVerification,
    atlas: &AtlasOverlapMap,
    run_id: &str,
    trace_id: &str,
) -> Result<CanonicalizedMechanisms, String> {
    let mut candidates = Vec::new();
    let mut grouped: BTreeMap<String, Vec<geoclt_schema::mechanism::VerifiedMechanism>> =
        BTreeMap::new();

    for mechanism in &verification.mechanisms {
        let candidate_hash = geoclt_artifacts_hash(&serde_json::json!({
            "mechanism_id": mechanism.mechanism_id,
            "path_id": mechanism.path_id.0,
            "class_type": mechanism.mechanism_class_type,
            "signature": mechanism.canonical_hyperpath_signature,
            "dependencies": mechanism.normalized_causal_dependency_set,
            "invariants": mechanism.invariant_feature_signature,
            "candidate_score": mechanism.candidate_score.0,
        }))?;
        let candidate_id = StableId(mechanism.mechanism_id.clone());
        candidates.push(MechanismCandidate {
            metadata: metadata(
                "mechanism_candidate",
                &format!("artifact-{candidate_hash}"),
                run_id,
                trace_id,
                &candidate_hash,
            ),
            candidate_id,
            mechanism_class_type: mechanism.mechanism_class_type.clone(),
            canonical_hyperpath_signature: mechanism.canonical_hyperpath_signature.clone(),
            normalized_causal_dependency_set: mechanism.normalized_causal_dependency_set.clone(),
            invariant_feature_signature: mechanism.invariant_feature_signature.clone(),
            candidate_score: mechanism.candidate_score,
        });
        let class_key = canonical_mechanism_key(&[
            mechanism.mechanism_class_type.as_str(),
            verification.behavior_id.as_str(),
        ]);
        grouped
            .entry(class_key)
            .or_default()
            .push(mechanism.clone());
    }

    let mut classes = Vec::new();
    for (class_key, members) in grouped {
        let member_ids = members
            .iter()
            .map(|mechanism| mechanism.path_id.0.clone())
            .collect::<Vec<_>>();
        let class_hash = geoclt_artifacts_hash(&serde_json::json!({
            "class_key": class_key,
            "member_path_ids": member_ids,
            "atlas_variants_tested": atlas.chart_ids,
        }))?;
        let average_candidate_score = members
            .iter()
            .map(|mechanism| mechanism.candidate_score.0)
            .sum::<f64>()
            / members.len() as f64;
        let average_synergy = members
            .iter()
            .map(|mechanism| mechanism.synergy.0)
            .sum::<f64>()
            / members.len() as f64;
        let passed_count = members.iter().filter(|mechanism| mechanism.passed).count();
        let status = if passed_count == members.len() {
            "passed"
        } else if passed_count > 0 {
            "mixed"
        } else {
            "rejected"
        };
        classes.push(MechanismClassRecord {
            metadata: metadata(
                "mechanism_class_record",
                &format!("artifact-{class_hash}"),
                run_id,
                trace_id,
                &class_hash,
            ),
            mechanism_class_id: StableId(derive_cluster_id(
                &members
                    .iter()
                    .map(|mechanism| mechanism.mechanism_id.clone())
                    .collect::<Vec<_>>(),
            )),
            member_path_ids: members
                .iter()
                .map(|mechanism| mechanism.path_id.clone())
                .collect(),
            atlas_variants_tested: atlas.chart_ids.clone(),
            persistence_score: Score(average_candidate_score),
            minimality_score: Some(Score(
                (passed_count as f64 / members.len() as f64).clamp(0.0, 1.0),
            )),
            geometry_predictiveness: Some(Score(average_synergy.clamp(0.0, 1.0))),
            pass_fail_status: status.to_string(),
        });
    }

    Ok(CanonicalizedMechanisms {
        candidates,
        classes,
    })
}

fn geoclt_artifacts_hash(payload: &serde_json::Value) -> Result<String, String> {
    let bytes =
        serde_jcs::to_vec(payload).map_err(|error| format!("canonicalization failed: {error}"))?;
    use sha2::{Digest, Sha256};
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    Ok(format!("{:x}", hasher.finalize()))
}

#[cfg(test)]
mod tests {
    use super::canonicalize_mechanisms;
    use geoclt_ids::StableId;
    use geoclt_schema::atlas::{AtlasOverlapMap, ChartOverlapDiagnostic};
    use geoclt_schema::mechanism::{MechanismVerification, VerifiedMechanism};
    use geoclt_units::Score;

    #[test]
    fn canonicalization_is_deterministic() {
        let verification = MechanismVerification {
            lane_id: "lane-1".to_string(),
            behavior_id: "behavior".to_string(),
            verified_count: 1,
            passed_count: 1,
            mechanisms: vec![VerifiedMechanism {
                mechanism_id: "mechanism-1".to_string(),
                path_id: StableId::from_parts(&["path", "1"]),
                mechanism_class_type: "causal_hyperpath".to_string(),
                canonical_hyperpath_signature: serde_json::json!({"path":"a"}),
                normalized_causal_dependency_set: vec!["edge-1".to_string()],
                invariant_feature_signature: vec!["event-1".to_string()],
                candidate_score: Score(0.83),
                causal_delta: Score(0.12),
                synergy: Score(0.11),
                passed: true,
                failed_checks: Vec::new(),
            }],
        };
        let atlas = AtlasOverlapMap {
            model_id: "gpt2".to_string(),
            lane_id: "lane-1".to_string(),
            profile: "profile".to_string(),
            chart_count: 3,
            overlap_score: Score(0.84),
            chart_ids: vec!["chart-1".to_string(), "chart-2".to_string()],
            chart_overlaps: vec![ChartOverlapDiagnostic {
                from_chart_id: "chart-1".to_string(),
                to_chart_id: "chart-2".to_string(),
                overlap_score: Score(0.84),
                shared_features: vec!["sae:f1".to_string()],
            }],
        };
        let one = canonicalize_mechanisms(&verification, &atlas, "run-1", "trace-1").expect("one");
        let two = canonicalize_mechanisms(&verification, &atlas, "run-1", "trace-1").expect("two");
        assert_eq!(one, two);
        assert_eq!(one.candidates.len(), 1);
        assert_eq!(one.classes.len(), 1);
    }
}

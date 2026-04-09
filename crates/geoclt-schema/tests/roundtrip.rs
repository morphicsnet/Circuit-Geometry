use geoclt_ids::StableId;
use geoclt_schema::artifact::{ArtifactBundle, ArtifactEntry, ArtifactMetadata};
use geoclt_schema::atlas::{AtlasOverlapMap, ChartOverlapDiagnostic};
use geoclt_schema::benchmark::{BenchmarkLane, BenchmarkResult};
use geoclt_schema::event::{CandidateEvent, CandidateEventTable, EventRecord};
use geoclt_schema::hyperpath::{AdmittedHyperpath, AdmittedHyperpathTable, HyperpathRecord};
use geoclt_schema::mechanism::{
    CanonicalizedMechanisms, MechanismCandidate, MechanismClassRecord, MechanismVerification,
    VerifiedMechanism,
};
use geoclt_schema::metric::MetricEstimate;
use geoclt_schema::receipt::DecisionReceipt;
use geoclt_schema::transport::TransportDiagnostics;
use geoclt_units::Score;

fn metadata(artifact_type: &str, schema_version: u32) -> ArtifactMetadata {
    ArtifactMetadata {
        artifact_id: format!("artifact-{artifact_type}"),
        artifact_type: artifact_type.to_string(),
        schema_version,
        producer: "geoclt:test:0.1.0".to_string(),
        trace_id: "trace-1".to_string(),
        run_id: "run-1".to_string(),
        content_hash: "a".repeat(64),
        created_at: "2026-01-01T00:00:00Z".to_string(),
    }
}

fn assert_roundtrip<T: serde::Serialize + serde::de::DeserializeOwned>(value: &T) {
    let encoded = serde_json::to_string(value).expect("encode");
    let decoded: T = serde_json::from_str(&encoded).expect("decode");
    assert_eq!(
        serde_json::to_value(decoded).expect("value"),
        serde_json::to_value(value).expect("value"),
    );
}

#[test]
fn typed_records_roundtrip_through_json() {
    let atlas = AtlasOverlapMap {
        model_id: "gpt2".to_string(),
        lane_id: "lane-1".to_string(),
        profile: "default".to_string(),
        chart_count: 2,
        overlap_score: Score(0.81),
        chart_ids: vec!["chart-a".to_string(), "chart-b".to_string()],
        chart_overlaps: vec![ChartOverlapDiagnostic {
            from_chart_id: "chart-a".to_string(),
            to_chart_id: "chart-b".to_string(),
            overlap_score: Score(0.81),
            shared_features: vec!["head:3".to_string(), "sae:f12".to_string()],
        }],
    };
    assert_roundtrip(&atlas);

    let metric = MetricEstimate {
        lane_id: "lane-1".to_string(),
        chart_id: "chart-a".to_string(),
        curvature_summary: Score(0.12),
        distortion_score: Score(0.08),
        geodesic_stability: Score(0.92),
        patch_count: 4,
        chart_energy: Score(0.41),
        feature_signature: vec!["sae:f12".to_string()],
    };
    assert_roundtrip(&metric);

    let transport = TransportDiagnostics {
        lane_id: "lane-1".to_string(),
        context_id: "ctx-1".to_string(),
        loop_consistency: Score(0.87),
        distortion: Score(0.13),
        coherence: Score(0.88),
        geodesic_deviation: Score(0.04),
        transport_edge_ids: vec!["edge-a".to_string()],
    };
    assert_roundtrip(&transport);

    let event_record = EventRecord {
        metadata: metadata("event_record", 2),
        event_id: StableId::from_parts(&["event", "1"]),
        sample_id: "sample-1".to_string(),
        layer_span: vec![5, 6],
        time_window: "window-1".to_string(),
        participant_set: vec!["mlp".to_string()],
        participant_types: vec!["feature".to_string()],
        transport_context_id: Some("ctx-1".to_string()),
        causal_weight: Score(0.31),
        reliability_score: Score(0.95),
        proposer_score: Some(Score(0.74)),
    };
    assert_roundtrip(&event_record);

    let event_table = CandidateEventTable {
        lane_id: "lane-1".to_string(),
        candidate_count: 1,
        events: vec![CandidateEvent {
            event_id: StableId::from_parts(&["event", "1"]),
            participant_set: vec!["mlp".to_string()],
            participant_types: vec!["feature".to_string()],
            layer_span: vec![5, 6],
            feature_signature: vec!["sae:f12".to_string()],
            transport_context_id: Some("ctx-1".to_string()),
            causal_weight: Score(0.31),
            reliability_score: Score(0.95),
            proposer_score: Some(Score(0.74)),
        }],
    };
    assert_roundtrip(&event_table);

    let hyperpath_record = HyperpathRecord {
        metadata: metadata("hyperpath_record", 2),
        path_id: StableId::from_parts(&["path", "1"]),
        behavior_id: "factual_retrieval".to_string(),
        event_ids: vec![StableId::from_parts(&["event", "1"])],
        chart_ids: vec!["chart-a".to_string()],
        layer_ids: vec![5],
        transport_edge_ids: vec!["edge-a".to_string()],
        geodesic_deviation: Some(Score(0.04)),
        chart_stability: Score(0.91),
        transport_coherence: Score(0.88),
        intervention_faithfulness: Score(0.22),
        synergy_score_max: Score(0.12),
        admitted: true,
    };
    assert_roundtrip(&hyperpath_record);

    let hyperpath_table = AdmittedHyperpathTable {
        lane_id: "lane-1".to_string(),
        admitted_count: 1,
        hyperpaths: vec![AdmittedHyperpath {
            path_id: StableId::from_parts(&["path", "1"]),
            behavior_id: "factual_retrieval".to_string(),
            event_ids: vec![StableId::from_parts(&["event", "1"])],
            chart_ids: vec!["chart-a".to_string()],
            layer_ids: vec![5],
            transport_edge_ids: vec!["edge-a".to_string()],
            geodesic_deviation: Some(Score(0.04)),
            chart_stability: Score(0.91),
            transport_coherence: Score(0.88),
            intervention_faithfulness: Score(0.22),
            synergy_score_max: Score(0.12),
            admitted: true,
        }],
    };
    assert_roundtrip(&hyperpath_table);

    let mechanism_verification = MechanismVerification {
        lane_id: "lane-1".to_string(),
        behavior_id: "factual_retrieval".to_string(),
        verified_count: 1,
        passed_count: 1,
        mechanisms: vec![VerifiedMechanism {
            mechanism_id: "mech-1".to_string(),
            path_id: StableId::from_parts(&["path", "1"]),
            mechanism_class_type: "faithful".to_string(),
            canonical_hyperpath_signature: serde_json::json!({"path": "1"}),
            normalized_causal_dependency_set: vec!["dep-a".to_string()],
            invariant_feature_signature: vec!["sae:f12".to_string()],
            candidate_score: Score(0.83),
            causal_delta: Score(0.22),
            synergy: Score(0.12),
            passed: true,
            failed_checks: vec![],
        }],
    };
    assert_roundtrip(&mechanism_verification);

    let canonicalized = CanonicalizedMechanisms {
        candidates: vec![MechanismCandidate {
            metadata: metadata("mechanism_candidate", 1),
            candidate_id: StableId::from_parts(&["candidate", "1"]),
            mechanism_class_type: "faithful".to_string(),
            canonical_hyperpath_signature: serde_json::json!({"path": "1"}),
            normalized_causal_dependency_set: vec!["dep-a".to_string()],
            invariant_feature_signature: vec!["sae:f12".to_string()],
            candidate_score: Score(0.83),
        }],
        classes: vec![MechanismClassRecord {
            metadata: metadata("mechanism_class_record", 2),
            mechanism_class_id: StableId::from_parts(&["class", "1"]),
            member_path_ids: vec![StableId::from_parts(&["path", "1"])],
            atlas_variants_tested: vec!["default".to_string()],
            persistence_score: Score(0.76),
            minimality_score: Some(Score(0.52)),
            geometry_predictiveness: Some(Score(0.81)),
            pass_fail_status: "pass".to_string(),
        }],
    };
    assert_roundtrip(&canonicalized);

    let benchmark = BenchmarkResult {
        metadata: metadata("benchmark_result", 2),
        model_id: "gpt2".to_string(),
        task_id: "factual_retrieval".to_string(),
        baseline_id: "kernel-stage".to_string(),
        metric_name: "intervention_faithfulness".to_string(),
        metric_value: Score(0.22),
        threshold: Some(Score(0.10)),
        passed: true,
    };
    assert_roundtrip(&benchmark);

    let receipt = DecisionReceipt {
        metadata: metadata("decision_receipt", 2),
        receipt_id: "receipt-1".to_string(),
        input_hash: "b".repeat(64),
        output_hash: "c".repeat(64),
        active_mechanism_class_ids: vec!["class-1".to_string()],
        provisional_mechanism_class_ids: vec![],
        policy_clauses_triggered: vec!["allow".to_string()],
        geometry_anomaly_flags: vec![],
        chart_instability_flags: vec![],
        decision: "allow".to_string(),
        policy_version: Some("v1".to_string()),
        evaluated_claims: Some(vec!["claim-1".to_string()]),
        thresholds_applied: Some(serde_json::json!({"intervention": 0.1})),
        falsifiers_checked: Some(vec!["none".to_string()]),
        fallback_selected: Some("none".to_string()),
        immutable_bundle_hash: Some("d".repeat(64)),
    };
    assert_roundtrip(&receipt);

    let bundle = ArtifactBundle {
        bundle_id: "bundle-1".to_string(),
        schema_version: 1,
        producer: "geoclt:test:0.1.0".to_string(),
        run_id: "run-1".to_string(),
        trace_id: "trace-1".to_string(),
        created_at: "2026-01-01T00:00:00Z".to_string(),
        transitional: false,
        immutable: true,
        artifacts: vec![ArtifactEntry {
            metadata: metadata("event_record", 2),
            payload: serde_json::to_value(event_record).expect("payload"),
        }],
        bundle_hash: "e".repeat(64),
        bundle_signing_mode: Some("off".to_string()),
        bundle_signature: None,
    };
    assert_roundtrip(&bundle);

    let lane = BenchmarkLane {
        lane_id: "lane-1".to_string(),
        behavior_id: "factual_retrieval".to_string(),
        intervention_delta_threshold: 0.10,
        synergy_threshold: 0.05,
        chart_stability_threshold: 0.70,
        transport_coherence_threshold: 0.70,
        baseline_margin_threshold: 0.05,
    };
    assert_roundtrip(&lane);
}

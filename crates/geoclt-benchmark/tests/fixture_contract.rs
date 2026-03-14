use geoclt_benchmark::contract::{evaluate_contract, BaselineResult, ConformanceClass};
use geoclt_ids::StableId;
use geoclt_schema::artifact::ArtifactMetadata;
use geoclt_schema::benchmark::BenchmarkLane;
use geoclt_schema::hyperpath::HyperpathRecord;
use geoclt_units::Score;
use serde_json::Value;
use std::fs;
use std::path::PathBuf;

fn fixtures_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../tests/fixtures/factual_retrieval_v1")
}

fn load_json(path: &PathBuf) -> Value {
    let raw = fs::read_to_string(path).expect("fixture should exist");
    serde_json::from_str(&raw).expect("fixture should be valid json")
}

fn build_lane(value: &Value) -> BenchmarkLane {
    BenchmarkLane {
        lane_id: value["lane_id"].as_str().unwrap().to_string(),
        behavior_id: value["behavior_id"].as_str().unwrap().to_string(),
        intervention_delta_threshold: value["intervention_delta_threshold"].as_f64().unwrap(),
        synergy_threshold: value["synergy_threshold"].as_f64().unwrap(),
        chart_stability_threshold: value["chart_stability_threshold"].as_f64().unwrap(),
        transport_coherence_threshold: value["transport_coherence_threshold"].as_f64().unwrap(),
        baseline_margin_threshold: value["baseline_margin_threshold"].as_f64().unwrap(),
    }
}

fn build_path(case_id: &str, lane: &BenchmarkLane, metrics: &Value) -> HyperpathRecord {
    HyperpathRecord {
        metadata: ArtifactMetadata {
            artifact_id: format!("artifact-{case_id}"),
            artifact_type: "hyperpath_record".to_string(),
            schema_version: 2,
            producer: "geoclt:test:0.2.0".to_string(),
            trace_id: format!("trace-{case_id}"),
            run_id: format!("run-{case_id}"),
            content_hash:
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa".to_string(),
            created_at: "2026-01-01T00:00:00Z".to_string(),
        },
        path_id: StableId::from_parts(&["fixture", case_id, "path"]),
        behavior_id: lane.behavior_id.clone(),
        event_ids: vec![StableId::from_parts(&["fixture", case_id, "event", "1"])],
        chart_ids: vec!["chart-a".to_string()],
        layer_ids: vec![5, 6],
        transport_edge_ids: vec!["edge-1".to_string()],
        geodesic_deviation: metrics["geodesic_deviation"].as_f64().map(Score),
        chart_stability: Score(metrics["chart_stability"].as_f64().unwrap()),
        transport_coherence: Score(metrics["transport_coherence"].as_f64().unwrap()),
        intervention_faithfulness: Score(metrics["intervention_faithfulness"].as_f64().unwrap()),
        synergy_score_max: Score(metrics["synergy_score_max"].as_f64().unwrap()),
        admitted: false,
    }
}

fn falsifier_value(evaluation: &geoclt_benchmark::contract::ContractEvaluation, key: &str) -> bool {
    match key {
        "pairwise_sufficiency_triggered" => evaluation.falsifiers.pairwise_sufficiency_triggered,
        "chart_fragility_triggered" => evaluation.falsifiers.chart_fragility_triggered,
        "transport_irrelevance_triggered" => evaluation.falsifiers.transport_irrelevance_triggered,
        "geometry_non_predictiveness_triggered" => {
            evaluation.falsifiers.geometry_non_predictiveness_triggered
        }
        "spurious_synergy_triggered" => evaluation.falsifiers.spurious_synergy_triggered,
        "any_triggered" => evaluation.falsifiers.any_triggered(),
        _ => panic!("unsupported falsifier key: {key}"),
    }
}

#[test]
fn fixture_manifest_matches_conformance_expectations() {
    let manifest_path = fixtures_dir().join("fixture_manifest.json");
    let manifest = load_json(&manifest_path);
    let fixtures = manifest["fixtures"].as_array().expect("fixtures array");

    for fixture in fixtures {
        let case_id = fixture["id"].as_str().unwrap();
        let case_path = fixtures_dir().join(fixture["path"].as_str().unwrap());
        let case = load_json(&case_path);
        let lane = build_lane(&case["lane"]);
        let path = build_path(case_id, &lane, &case["metrics"]);
        let baselines = case["baselines"]
            .as_array()
            .unwrap()
            .iter()
            .map(|baseline| BaselineResult {
                baseline_id: baseline["baseline_id"].as_str().unwrap().to_string(),
                intervention_faithfulness: baseline["intervention_faithfulness"].as_f64().unwrap(),
            })
            .collect::<Vec<_>>();

        let evaluation = evaluate_contract(&path, &lane, &baselines);
        let expected_class = fixture["expected_conformance_class"].as_str().unwrap();
        match expected_class {
            "conformant" => assert_eq!(evaluation.conformance_class, ConformanceClass::Conformant),
            "provisional" => {
                assert_eq!(evaluation.conformance_class, ConformanceClass::Provisional)
            }
            "rejected" => assert_eq!(evaluation.conformance_class, ConformanceClass::Rejected),
            other => panic!("unsupported expected class: {other}"),
        }

        let expected_falsifiers = fixture["expected_falsifiers"].as_object().unwrap();
        for (key, value) in expected_falsifiers {
            assert_eq!(
                falsifier_value(&evaluation, key),
                value.as_bool().unwrap(),
                "falsifier mismatch for fixture {case_id}: {key}"
            );
        }
    }
}

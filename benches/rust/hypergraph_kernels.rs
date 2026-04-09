use geoclt_hypergraph::induce::propose_events;
use geoclt_schema::transport::TransportDiagnostics;
use geoclt_units::Score;

fn main() {
    let transport = TransportDiagnostics {
        lane_id: "factual_retrieval.v1".to_string(),
        context_id: "transport-factual_retrieval.v1".to_string(),
        loop_consistency: Score(0.84),
        distortion: Score(0.12),
        coherence: Score(0.83),
        geodesic_deviation: Score(0.08),
        transport_edge_ids: vec!["chart-1->chart-2".to_string()],
    };
    let feature_hints = vec!["sae:f12".to_string(), "head:5:3".to_string()];
    let events = propose_events(
        "factual_retrieval.v1",
        "factual_retrieval",
        &transport,
        &feature_hints,
    )
    .expect("events");
    println!("{}", serde_json::to_string_pretty(&events).expect("events json"));
}

use geoclt_core::deterministic::{bounded_u32, clamp};
use geoclt_core::GeoCltResult;
use geoclt_ids::StableId;
use geoclt_schema::atlas::AtlasOverlapMap;
use geoclt_schema::event::{CandidateEvent, CandidateEventTable};
use geoclt_schema::hyperpath::{AdmittedHyperpath, AdmittedHyperpathTable};
use geoclt_schema::transport::TransportDiagnostics;
use geoclt_units::Score;

fn normalized_features(feature_hints: &[String], behavior_id: &str) -> Vec<String> {
    if feature_hints.is_empty() {
        return vec![
            format!("behavior:{behavior_id}"),
            "sae:fallback".to_string(),
            "head:5:1".to_string(),
        ];
    }
    feature_hints.to_vec()
}

fn infer_participant_type(participant: &str) -> String {
    if participant.starts_with("sae:") {
        return "sae".to_string();
    }
    if participant.starts_with("head:") {
        return "attention_head".to_string();
    }
    if participant.starts_with("mlp:") {
        return "mlp_gate".to_string();
    }
    "feature".to_string()
}

pub fn propose_events(
    lane_id: &str,
    behavior_id: &str,
    transport: &TransportDiagnostics,
    feature_hints: &[String],
) -> GeoCltResult<CandidateEventTable> {
    let features = normalized_features(feature_hints, behavior_id);
    let seed = serde_json::json!({
        "lane_id": lane_id,
        "behavior_id": behavior_id,
        "transport": transport,
        "feature_hints": features,
    });
    let candidate_count = bounded_u32(&seed, "hypergraph_candidate_count", 2, 3)? as usize;
    let mut events = Vec::new();

    for index in 0..candidate_count {
        let layer_start = 4 + index as u32;
        let feature = features[index % features.len()].clone();
        let alternate = features[(index + 1) % features.len()].clone();
        let participants = vec![
            format!("sae:{feature}"),
            format!("head:{}:{}", layer_start, index % 12),
            format!("mlp:{}:{}", layer_start + 1, (index * 7) % 64),
        ];
        let participant_types = participants
            .iter()
            .map(|participant| infer_participant_type(participant))
            .collect::<Vec<_>>();
        let feature_signature = vec![feature, alternate];
        let causal_weight = clamp(transport.coherence.0 - (index as f64 * 0.04), 0.05, 0.99);
        let reliability_score = clamp(
            transport.loop_consistency.0 - (index as f64 * 0.03),
            0.05,
            0.99,
        );
        let proposer_score = clamp((causal_weight + reliability_score) / 2.0, 0.05, 0.99);
        let event_seed = format!("{lane_id}:{behavior_id}:{index}:{}", participants.join("|"));
        events.push(CandidateEvent {
            event_id: StableId::from_parts(&["event", lane_id, behavior_id, &event_seed]),
            participant_set: participants,
            participant_types,
            layer_span: vec![layer_start, layer_start + 1],
            feature_signature,
            transport_context_id: Some(transport.context_id.clone()),
            causal_weight: Score(causal_weight),
            reliability_score: Score(reliability_score),
            proposer_score: Some(Score(proposer_score)),
        });
    }

    Ok(CandidateEventTable {
        lane_id: lane_id.to_string(),
        candidate_count: events.len(),
        events,
    })
}

#[allow(clippy::too_many_arguments)]
pub fn materialize_hyperpaths(
    lane_id: &str,
    behavior_id: &str,
    events: &CandidateEventTable,
    atlas: &AtlasOverlapMap,
    transport: &TransportDiagnostics,
    intervention_faithfulness: f64,
    synergy_score_max: f64,
    chart_stability: f64,
    geodesic_deviation: f64,
) -> GeoCltResult<AdmittedHyperpathTable> {
    let mut hyperpaths = Vec::new();
    if events.events.is_empty() {
        return Ok(AdmittedHyperpathTable {
            lane_id: lane_id.to_string(),
            admitted_count: 0,
            hyperpaths,
        });
    }

    let group_size = 2usize.min(events.events.len());
    for (index, chunk) in events.events.chunks(group_size).enumerate() {
        let path_seed = format!(
            "{lane_id}:{behavior_id}:{index}:{}",
            chunk
                .iter()
                .map(|event| event.event_id.0.clone())
                .collect::<Vec<_>>()
                .join("|")
        );
        let admitted = intervention_faithfulness >= 0.10
            && synergy_score_max >= 0.05
            && chart_stability >= 0.70
            && transport.coherence.0 >= 0.70;
        let mut layer_ids = chunk
            .iter()
            .flat_map(|event| event.layer_span.iter().copied())
            .collect::<Vec<_>>();
        layer_ids.sort_unstable();
        layer_ids.dedup();
        hyperpaths.push(AdmittedHyperpath {
            path_id: StableId::from_parts(&["path", lane_id, behavior_id, &path_seed]),
            behavior_id: behavior_id.to_string(),
            event_ids: chunk.iter().map(|event| event.event_id.clone()).collect(),
            chart_ids: atlas.chart_ids.iter().take(2).cloned().collect(),
            layer_ids,
            transport_edge_ids: transport
                .transport_edge_ids
                .iter()
                .take(2)
                .cloned()
                .collect(),
            geodesic_deviation: Some(Score(geodesic_deviation)),
            chart_stability: Score(chart_stability),
            transport_coherence: transport.coherence,
            intervention_faithfulness: Score(intervention_faithfulness),
            synergy_score_max: Score(synergy_score_max),
            admitted,
        });
    }

    let admitted_count = hyperpaths.iter().filter(|path| path.admitted).count();
    Ok(AdmittedHyperpathTable {
        lane_id: lane_id.to_string(),
        admitted_count,
        hyperpaths,
    })
}

#[cfg(test)]
mod tests {
    use geoclt_schema::atlas::AtlasOverlapMap;
    use geoclt_schema::transport::TransportDiagnostics;
    use geoclt_units::Score;

    use super::{materialize_hyperpaths, propose_events};

    #[test]
    fn hypergraph_kernels_are_deterministic() {
        let transport = TransportDiagnostics {
            lane_id: "lane-1".to_string(),
            context_id: "transport-lane-1".to_string(),
            loop_consistency: Score(0.84),
            distortion: Score(0.12),
            coherence: Score(0.83),
            geodesic_deviation: Score(0.08),
            transport_edge_ids: vec!["chart-1->chart-2".to_string()],
        };
        let features = vec!["f12".to_string(), "f18".to_string()];
        let one = propose_events("lane-1", "behavior", &transport, &features).expect("events one");
        let two = propose_events("lane-1", "behavior", &transport, &features).expect("events two");
        assert_eq!(one, two);

        let atlas = AtlasOverlapMap {
            model_id: "gpt2".to_string(),
            lane_id: "lane-1".to_string(),
            profile: "profile".to_string(),
            chart_count: 3,
            overlap_score: Score(0.81),
            chart_ids: vec![
                "chart-1".to_string(),
                "chart-2".to_string(),
                "chart-3".to_string(),
            ],
            chart_overlaps: Vec::new(),
        };
        let paths = materialize_hyperpaths(
            "lane-1", "behavior", &one, &atlas, &transport, 0.22, 0.12, 0.88, 0.04,
        )
        .expect("paths");
        assert!(!paths.hyperpaths.is_empty());
    }
}

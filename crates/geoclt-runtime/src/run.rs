use geoclt_artifacts::bundle::{compute_bundle_hash, finalize_artifact_entry};
use geoclt_atlas::atlas::fit_atlas;
use geoclt_canonicalize::canonicalize::canonicalize_mechanisms;
use geoclt_causal::verify::verify_mechanisms;
use geoclt_hypergraph::induce::{materialize_hyperpaths, propose_events};
use geoclt_metric::metric::estimate_pullback_metric;
use geoclt_schema::artifact::{
    ArtifactBundle, ArtifactEntry, ArtifactMetadata, ARTIFACT_BUNDLE_SCHEMA_VERSION,
    BENCHMARK_RESULT_SCHEMA_VERSION, EVENT_RECORD_SCHEMA_VERSION, HYPERPATH_RECORD_SCHEMA_VERSION,
    MECHANISM_CANDIDATE_SCHEMA_VERSION, MECHANISM_CLASS_RECORD_SCHEMA_VERSION,
};
use geoclt_schema::atlas::AtlasOverlapMap;
use geoclt_schema::benchmark::{BenchmarkLane, BenchmarkResult};
use geoclt_schema::event::{CandidateEventTable, EventRecord};
use geoclt_schema::hyperpath::{AdmittedHyperpathTable, HyperpathRecord};
use geoclt_schema::mechanism::{
    CanonicalizedMechanisms, MechanismCandidate, MechanismClassRecord, MechanismVerification,
};
use geoclt_schema::metric::MetricEstimate;
use geoclt_schema::transport::TransportDiagnostics;
use geoclt_transport::transport::fit_transport;
use geoclt_units::Score;
use serde::{Deserialize, Serialize};

use crate::batch::execute_batch;
use crate::run_graph::RunGraph;
use crate::stream::execute_stream;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkspaceKernelInput {
    pub model_id: String,
    pub lane_id: String,
    pub behavior_id: String,
    pub profile: String,
    #[serde(default)]
    pub run_id: Option<String>,
    #[serde(default)]
    pub trace_id: Option<String>,
    #[serde(default)]
    pub feature_hints: Vec<String>,
    pub intervention_faithfulness: f64,
    pub synergy_score_max: f64,
    pub chart_stability_hint: f64,
    pub transport_coherence_hint: f64,
    pub geodesic_deviation_hint: f64,
    #[serde(default = "default_intervention_threshold")]
    pub intervention_delta_threshold: f64,
    #[serde(default = "default_synergy_threshold")]
    pub synergy_threshold: f64,
    #[serde(default = "default_chart_threshold")]
    pub chart_stability_threshold: f64,
    #[serde(default = "default_transport_threshold")]
    pub transport_coherence_threshold: f64,
    #[serde(default = "default_baseline_margin")]
    pub baseline_margin_threshold: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkspaceKernelOutput {
    pub atlas: AtlasOverlapMap,
    pub metric: MetricEstimate,
    pub transport: TransportDiagnostics,
    pub candidate_event_table: CandidateEventTable,
    pub admitted_hyperpath_table: AdmittedHyperpathTable,
    pub mechanism_verification: MechanismVerification,
    pub canonicalized_mechanisms: CanonicalizedMechanisms,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkspaceBundleOutput {
    pub run_graph: RunGraph,
    pub kernel_output: WorkspaceKernelOutput,
    pub artifact_bundle: ArtifactBundle,
}

const WORKSPACE_ARTIFACT_CREATED_AT: &str = "2026-01-01T00:00:00Z";

const fn default_intervention_threshold() -> f64 {
    0.10
}

const fn default_synergy_threshold() -> f64 {
    0.05
}

const fn default_chart_threshold() -> f64 {
    0.70
}

const fn default_transport_threshold() -> f64 {
    0.70
}

const fn default_baseline_margin() -> f64 {
    0.05
}

fn resolved_ids(input: &WorkspaceKernelInput) -> (String, String) {
    let run_id = input
        .run_id
        .clone()
        .unwrap_or_else(|| format!("kernel-run-{}", input.lane_id));
    let trace_id = input
        .trace_id
        .clone()
        .unwrap_or_else(|| format!("kernel-trace-{}", input.lane_id));
    (run_id, trace_id)
}

pub fn execute_workspace_kernels(
    input: WorkspaceKernelInput,
) -> Result<WorkspaceKernelOutput, String> {
    let mut atlas = fit_atlas(
        &input.model_id,
        &input.lane_id,
        &input.profile,
        &input.feature_hints,
    )
    .map_err(|error| error.to_string())?;
    atlas.overlap_score =
        Score(((atlas.overlap_score.0 + input.chart_stability_hint) / 2.0).clamp(0.60, 0.99));

    let metric = estimate_pullback_metric(&input.lane_id, &atlas, &input.feature_hints)
        .map_err(|error| error.to_string())?;

    let mut transport =
        fit_transport(&input.lane_id, &atlas, &metric).map_err(|error| error.to_string())?;
    transport.coherence =
        Score(((transport.coherence.0 + input.transport_coherence_hint) / 2.0).clamp(0.60, 0.99));
    transport.loop_consistency = Score(
        ((transport.loop_consistency.0 + input.transport_coherence_hint) / 2.0).clamp(0.60, 0.99),
    );
    transport.geodesic_deviation = Score(
        ((transport.geodesic_deviation.0 + input.geodesic_deviation_hint) / 2.0).clamp(0.01, 0.40),
    );

    let candidate_event_table = propose_events(
        &input.lane_id,
        &input.behavior_id,
        &transport,
        &input.feature_hints,
    )
    .map_err(|error| error.to_string())?;

    let admitted_hyperpath_table = materialize_hyperpaths(
        &input.lane_id,
        &input.behavior_id,
        &candidate_event_table,
        &atlas,
        &transport,
        input.intervention_faithfulness,
        input.synergy_score_max,
        input.chart_stability_hint,
        input.geodesic_deviation_hint,
    )
    .map_err(|error| error.to_string())?;

    let lane = BenchmarkLane {
        lane_id: input.lane_id.clone(),
        behavior_id: input.behavior_id.clone(),
        intervention_delta_threshold: input.intervention_delta_threshold,
        synergy_threshold: input.synergy_threshold,
        chart_stability_threshold: input.chart_stability_threshold,
        transport_coherence_threshold: input.transport_coherence_threshold,
        baseline_margin_threshold: input.baseline_margin_threshold,
    };
    let mechanism_verification =
        verify_mechanisms(&lane, &admitted_hyperpath_table).map_err(|error| error.to_string())?;
    let (run_id, trace_id) = resolved_ids(&input);
    let canonicalized_mechanisms =
        canonicalize_mechanisms(&mechanism_verification, &atlas, &run_id, &trace_id)
            .map_err(|error| error.to_string())?;

    Ok(WorkspaceKernelOutput {
        atlas,
        metric,
        transport,
        candidate_event_table,
        admitted_hyperpath_table,
        mechanism_verification,
        canonicalized_mechanisms,
    })
}

fn typed_artifact_entry<T: Serialize>(
    metadata: ArtifactMetadata,
    payload: &T,
) -> Result<ArtifactEntry, String> {
    let payload = serde_json::to_value(payload)
        .map_err(|error| format!("failed to serialize artifact payload: {error}"))?;
    finalize_artifact_entry(ArtifactEntry { metadata, payload })
}

fn assemble_workspace_bundle(
    input: &WorkspaceKernelInput,
    output: &WorkspaceKernelOutput,
) -> Result<ArtifactBundle, String> {
    let (run_id, trace_id) = resolved_ids(input);
    let producer = "geoclt:runtime:0.2.0";
    let sample_id = format!("sample-{}", input.behavior_id);

    let mut artifacts = Vec::new();

    for event in &output.candidate_event_table.events {
        let metadata = ArtifactMetadata {
            artifact_id: String::new(),
            artifact_type: "event_record".to_string(),
            schema_version: EVENT_RECORD_SCHEMA_VERSION,
            producer: producer.to_string(),
            trace_id: trace_id.clone(),
            run_id: run_id.clone(),
            content_hash: String::new(),
            created_at: WORKSPACE_ARTIFACT_CREATED_AT.to_string(),
        };
        let record = EventRecord {
            metadata: metadata.clone(),
            event_id: event.event_id.clone(),
            sample_id: sample_id.clone(),
            layer_span: event.layer_span.clone(),
            time_window: "workspace-kernel".to_string(),
            participant_set: event.participant_set.clone(),
            participant_types: event.participant_types.clone(),
            transport_context_id: event.transport_context_id.clone(),
            causal_weight: event.causal_weight,
            reliability_score: event.reliability_score,
            proposer_score: event.proposer_score,
        };
        artifacts.push(typed_artifact_entry(metadata, &record)?);
    }

    for hyperpath in &output.admitted_hyperpath_table.hyperpaths {
        let metadata = ArtifactMetadata {
            artifact_id: String::new(),
            artifact_type: "hyperpath_record".to_string(),
            schema_version: HYPERPATH_RECORD_SCHEMA_VERSION,
            producer: producer.to_string(),
            trace_id: trace_id.clone(),
            run_id: run_id.clone(),
            content_hash: String::new(),
            created_at: WORKSPACE_ARTIFACT_CREATED_AT.to_string(),
        };
        let record = HyperpathRecord {
            metadata: metadata.clone(),
            path_id: hyperpath.path_id.clone(),
            behavior_id: hyperpath.behavior_id.clone(),
            event_ids: hyperpath.event_ids.clone(),
            chart_ids: hyperpath.chart_ids.clone(),
            layer_ids: hyperpath.layer_ids.clone(),
            transport_edge_ids: hyperpath.transport_edge_ids.clone(),
            geodesic_deviation: hyperpath.geodesic_deviation,
            chart_stability: hyperpath.chart_stability,
            transport_coherence: hyperpath.transport_coherence,
            intervention_faithfulness: hyperpath.intervention_faithfulness,
            synergy_score_max: hyperpath.synergy_score_max,
            admitted: hyperpath.admitted,
        };
        artifacts.push(typed_artifact_entry(metadata, &record)?);
    }

    let best_intervention = output
        .admitted_hyperpath_table
        .hyperpaths
        .iter()
        .map(|path| path.intervention_faithfulness.0)
        .fold(0.0, f64::max);
    let benchmark_metadata = ArtifactMetadata {
        artifact_id: String::new(),
        artifact_type: "benchmark_result".to_string(),
        schema_version: BENCHMARK_RESULT_SCHEMA_VERSION,
        producer: producer.to_string(),
        trace_id: trace_id.clone(),
        run_id: run_id.clone(),
        content_hash: String::new(),
        created_at: WORKSPACE_ARTIFACT_CREATED_AT.to_string(),
    };
    let benchmark = BenchmarkResult {
        metadata: benchmark_metadata.clone(),
        model_id: input.model_id.clone(),
        task_id: input.behavior_id.clone(),
        baseline_id: "kernel_stage".to_string(),
        metric_name: "intervention_faithfulness".to_string(),
        metric_value: Score(best_intervention),
        threshold: Some(Score(input.intervention_delta_threshold)),
        passed: output.mechanism_verification.passed_count > 0,
    };
    artifacts.push(typed_artifact_entry(benchmark_metadata, &benchmark)?);

    for candidate in &output.canonicalized_mechanisms.candidates {
        let metadata = ArtifactMetadata {
            artifact_id: String::new(),
            artifact_type: "mechanism_candidate".to_string(),
            schema_version: MECHANISM_CANDIDATE_SCHEMA_VERSION,
            producer: producer.to_string(),
            trace_id: trace_id.clone(),
            run_id: run_id.clone(),
            content_hash: String::new(),
            created_at: WORKSPACE_ARTIFACT_CREATED_AT.to_string(),
        };
        let record = MechanismCandidate {
            metadata: metadata.clone(),
            candidate_id: candidate.candidate_id.clone(),
            mechanism_class_type: candidate.mechanism_class_type.clone(),
            canonical_hyperpath_signature: candidate.canonical_hyperpath_signature.clone(),
            normalized_causal_dependency_set: candidate.normalized_causal_dependency_set.clone(),
            invariant_feature_signature: candidate.invariant_feature_signature.clone(),
            candidate_score: candidate.candidate_score,
        };
        artifacts.push(typed_artifact_entry(metadata, &record)?);
    }

    for class_record in &output.canonicalized_mechanisms.classes {
        let metadata = ArtifactMetadata {
            artifact_id: String::new(),
            artifact_type: "mechanism_class_record".to_string(),
            schema_version: MECHANISM_CLASS_RECORD_SCHEMA_VERSION,
            producer: producer.to_string(),
            trace_id: trace_id.clone(),
            run_id: run_id.clone(),
            content_hash: String::new(),
            created_at: WORKSPACE_ARTIFACT_CREATED_AT.to_string(),
        };
        let record = MechanismClassRecord {
            metadata: metadata.clone(),
            mechanism_class_id: class_record.mechanism_class_id.clone(),
            member_path_ids: class_record.member_path_ids.clone(),
            atlas_variants_tested: class_record.atlas_variants_tested.clone(),
            persistence_score: class_record.persistence_score,
            minimality_score: class_record.minimality_score,
            geometry_predictiveness: class_record.geometry_predictiveness,
            pass_fail_status: class_record.pass_fail_status.clone(),
        };
        artifacts.push(typed_artifact_entry(metadata, &record)?);
    }

    let mut bundle = ArtifactBundle {
        bundle_id: format!("bundle-workspace-{trace_id}"),
        schema_version: ARTIFACT_BUNDLE_SCHEMA_VERSION,
        producer: producer.to_string(),
        run_id,
        trace_id,
        created_at: WORKSPACE_ARTIFACT_CREATED_AT.to_string(),
        transitional: false,
        immutable: true,
        artifacts,
        bundle_hash: String::new(),
        bundle_signing_mode: None,
        bundle_signature: None,
    };
    bundle.bundle_hash = compute_bundle_hash(&bundle)?;
    Ok(bundle)
}

pub fn execute_workspace_bundle(
    input: WorkspaceKernelInput,
) -> Result<WorkspaceBundleOutput, String> {
    let run_graph = RunGraph::default();
    let kernel_output = execute_workspace_kernels(input.clone())?;
    let artifact_bundle = assemble_workspace_bundle(&input, &kernel_output)?;
    Ok(WorkspaceBundleOutput {
        run_graph,
        kernel_output,
        artifact_bundle,
    })
}

pub fn execute_batch_graph(
    run_id: &str,
    trace_id: &str,
) -> Result<(RunGraph, ArtifactBundle), String> {
    let graph = RunGraph::default();
    let bundle = execute_batch(run_id, trace_id)?;
    Ok((graph, bundle))
}

pub fn execute_stream_graph(
    run_id: &str,
    trace_id: &str,
    chunks: &[Vec<u8>],
) -> Result<(RunGraph, ArtifactBundle), String> {
    let graph = RunGraph::default();
    let bundle = execute_stream(run_id, trace_id, chunks)?;
    Ok((graph, bundle))
}

#[cfg(test)]
mod tests {
    use super::{
        execute_batch_graph, execute_stream_graph, execute_workspace_bundle,
        execute_workspace_kernels, WorkspaceKernelInput,
    };

    #[test]
    fn batch_and_stream_produce_stable_hash_for_identical_inputs() {
        let (_, first_batch) = execute_batch_graph("run-1", "trace-1").expect("batch one");
        let (_, second_batch) = execute_batch_graph("run-1", "trace-1").expect("batch two");
        assert_eq!(first_batch.bundle_hash, second_batch.bundle_hash);

        let chunks = vec![b"abc".to_vec(), b"def".to_vec()];
        let (_, first_stream) =
            execute_stream_graph("run-2", "trace-2", &chunks).expect("stream one");
        let (_, second_stream) =
            execute_stream_graph("run-2", "trace-2", &chunks).expect("stream two");
        assert_eq!(first_stream.bundle_hash, second_stream.bundle_hash);
    }

    #[test]
    fn workspace_kernels_are_deterministic() {
        let input = WorkspaceKernelInput {
            model_id: "gpt2".to_string(),
            lane_id: "factual_retrieval.v1".to_string(),
            behavior_id: "factual_retrieval".to_string(),
            profile: "factual_retrieval".to_string(),
            run_id: Some("run-1".to_string()),
            trace_id: Some("trace-1".to_string()),
            feature_hints: vec!["sae:f12".to_string(), "head:5:3".to_string()],
            intervention_faithfulness: 0.22,
            synergy_score_max: 0.12,
            chart_stability_hint: 0.88,
            transport_coherence_hint: 0.84,
            geodesic_deviation_hint: 0.04,
            intervention_delta_threshold: 0.10,
            synergy_threshold: 0.05,
            chart_stability_threshold: 0.70,
            transport_coherence_threshold: 0.70,
            baseline_margin_threshold: 0.05,
        };
        let one = execute_workspace_kernels(input.clone()).expect("one");
        let two = execute_workspace_kernels(input).expect("two");
        assert_eq!(one.atlas, two.atlas);
        assert_eq!(one.transport, two.transport);
        assert_eq!(one.mechanism_verification, two.mechanism_verification);
        assert_eq!(one.canonicalized_mechanisms, two.canonicalized_mechanisms);
    }

    #[test]
    fn workspace_bundle_is_deterministic_and_contains_stage_artifacts() {
        let input = WorkspaceKernelInput {
            model_id: "gpt2".to_string(),
            lane_id: "factual_retrieval.v1".to_string(),
            behavior_id: "factual_retrieval".to_string(),
            profile: "factual_retrieval".to_string(),
            run_id: Some("run-1".to_string()),
            trace_id: Some("trace-1".to_string()),
            feature_hints: vec!["sae:f12".to_string(), "head:5:3".to_string()],
            intervention_faithfulness: 0.22,
            synergy_score_max: 0.12,
            chart_stability_hint: 0.88,
            transport_coherence_hint: 0.84,
            geodesic_deviation_hint: 0.04,
            intervention_delta_threshold: 0.10,
            synergy_threshold: 0.05,
            chart_stability_threshold: 0.70,
            transport_coherence_threshold: 0.70,
            baseline_margin_threshold: 0.05,
        };

        let one = execute_workspace_bundle(input.clone()).expect("bundle one");
        let two = execute_workspace_bundle(input).expect("bundle two");

        assert_eq!(
            one.artifact_bundle.bundle_hash,
            two.artifact_bundle.bundle_hash
        );

        let artifact_types = one
            .artifact_bundle
            .artifacts
            .iter()
            .map(|entry| entry.metadata.artifact_type.as_str())
            .collect::<Vec<_>>();
        assert!(artifact_types.contains(&"event_record"));
        assert!(artifact_types.contains(&"hyperpath_record"));
        assert!(artifact_types.contains(&"benchmark_result"));
        assert!(artifact_types.contains(&"mechanism_candidate"));
        assert!(artifact_types.contains(&"mechanism_class_record"));
    }
}

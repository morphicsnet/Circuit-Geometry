use geoclt_artifacts::registry::load_packaged_registry;
use geoclt_schema::artifact::ArtifactBundle;
use geoclt_sidecar::server::SidecarServer;

pub fn execute_stream(run_id: &str, trace_id: &str, chunks: &[Vec<u8>]) -> Result<ArtifactBundle, String> {
    let registry = load_packaged_registry()?;
    let mut sidecar = SidecarServer::new("geoclt:sidecar:0.2.0", registry);
    sidecar.start_trace(
        trace_id,
        "transformers",
        "gpt2-small",
        "factual_retrieval.v1",
        run_id,
        &chrono::Utc::now().to_rfc3339(),
    )?;

    for (idx, chunk) in chunks.iter().enumerate() {
        sidecar.push_chunk(trace_id, &format!("{trace_id}-{idx}"), chunk.clone())?;
    }
    sidecar.end_trace(trace_id)
}

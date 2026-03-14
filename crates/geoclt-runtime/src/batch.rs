use geoclt_artifacts::bundle::{compute_bundle_hash, finalize_artifact_entry};
use geoclt_schema::artifact::{ArtifactBundle, ArtifactEntry, ArtifactMetadata};

pub fn execute_batch(run_id: &str, trace_id: &str) -> Result<ArtifactBundle, String> {
    let artifact = finalize_artifact_entry(ArtifactEntry {
        metadata: ArtifactMetadata {
            artifact_id: String::new(),
            artifact_type: "benchmark_result".to_string(),
            schema_version: 2,
            producer: "geoclt:runtime:0.2.0".to_string(),
            trace_id: trace_id.to_string(),
            run_id: run_id.to_string(),
            content_hash: String::new(),
            created_at: "2026-01-01T00:00:00Z".to_string(),
        },
        payload: serde_json::json!({"mode": "batch", "run_id": run_id, "trace_id": trace_id}),
    })?;

    let mut bundle = ArtifactBundle {
        bundle_id: format!("bundle-batch-{trace_id}"),
        schema_version: 1,
        producer: "geoclt:runtime:0.2.0".to_string(),
        run_id: run_id.to_string(),
        trace_id: trace_id.to_string(),
        created_at: "2026-01-01T00:00:00Z".to_string(),
        transitional: false,
        immutable: true,
        artifacts: vec![artifact],
        bundle_hash: String::new(),
    };
    bundle.bundle_hash = compute_bundle_hash(&bundle)?;
    Ok(bundle)
}

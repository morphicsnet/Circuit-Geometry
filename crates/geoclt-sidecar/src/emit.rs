use geoclt_artifacts::bundle::{compute_bundle_hash, finalize_artifact_entry};
use geoclt_schema::artifact::{ArtifactBundle, ArtifactEntry, ArtifactMetadata};

use crate::trace_state::TraceContext;

pub fn assemble_bundle(context: &TraceContext, producer: &str) -> Result<ArtifactBundle, String> {
    let payload = serde_json::json!({
        "trace_id": context.trace_id,
        "adapter_id": context.adapter_id,
        "model_id": context.model_id,
        "lane_id": context.lane_id,
        "chunk_count": context.chunk_count,
    });
    let artifact = finalize_artifact_entry(ArtifactEntry {
        metadata: ArtifactMetadata {
            artifact_id: String::new(),
            artifact_type: "benchmark_result".to_string(),
            schema_version: 2,
            producer: producer.to_string(),
            trace_id: context.trace_id.clone(),
            run_id: context.run_id.clone(),
            content_hash: String::new(),
            created_at: "2026-01-01T00:00:00Z".to_string(),
        },
        payload,
    })?;

    let mut bundle = ArtifactBundle {
        bundle_id: format!("bundle-{}", &context.trace_id),
        schema_version: 1,
        producer: producer.to_string(),
        run_id: context.run_id.clone(),
        trace_id: context.trace_id.clone(),
        created_at: "2026-01-01T00:00:00Z".to_string(),
        transitional: false,
        immutable: true,
        artifacts: vec![artifact],
        bundle_hash: String::new(),
        bundle_signing_mode: None,
        bundle_signature: None,
    };
    bundle.bundle_hash = compute_bundle_hash(&bundle)?;
    Ok(bundle)
}

use geoclt_schema::artifact::{ArtifactBundle, ArtifactEntry};
use hmac::{Hmac, Mac};
use sha2::Sha256;
use std::env;

use crate::canonicalize::{artifact_id, content_hash};
use crate::compatibility::check_bundle_compatibility;
use crate::registry::SchemaRegistry;

pub fn finalize_artifact_entry(mut entry: ArtifactEntry) -> Result<ArtifactEntry, String> {
    let hash = content_hash(&entry.payload)?;
    entry.metadata.content_hash = hash.clone();
    entry.metadata.artifact_id = artifact_id(
        &entry.metadata.artifact_type,
        entry.metadata.schema_version,
        &hash,
    );
    Ok(entry)
}

pub fn compute_bundle_hash(bundle: &ArtifactBundle) -> Result<String, String> {
    let canonical = serde_json::json!({
        "bundle_id": bundle.bundle_id,
        "schema_version": bundle.schema_version,
        "producer": bundle.producer,
        "run_id": bundle.run_id,
        "trace_id": bundle.trace_id,
        "created_at": bundle.created_at,
        "transitional": bundle.transitional,
        "immutable": bundle.immutable,
        "artifacts": bundle.artifacts
    });
    content_hash(&canonical)
}

pub fn validate_artifact_bundle(
    registry: &SchemaRegistry,
    bundle: &ArtifactBundle,
) -> Result<(), String> {
    if !bundle.immutable {
        return Err("bundle must be immutable".to_string());
    }
    check_bundle_compatibility(registry, bundle)?;
    let recomputed = compute_bundle_hash(bundle)?;
    if recomputed != bundle.bundle_hash {
        return Err("bundle hash mismatch".to_string());
    }
    validate_bundle_signature(bundle)?;
    Ok(())
}

fn validate_bundle_signature(bundle: &ArtifactBundle) -> Result<(), String> {
    let mode = env::var("GEOCLT_BUNDLE_SIGNING").unwrap_or_else(|_| "off".to_string());
    if mode != "hmac" {
        return Ok(());
    }
    let Some(signature) = bundle.bundle_signature.as_ref() else {
        return Err("missing bundle signature".to_string());
    };
    let secret =
        env::var("GEOCLT_BUNDLE_SIGNING_SECRET").unwrap_or_else(|_| "geoclt-signing-secret".to_string());
    let mut mac = Hmac::<Sha256>::new_from_slice(secret.as_bytes())
        .map_err(|error| format!("failed to init hmac: {error}"))?;
    mac.update(bundle.bundle_hash.as_bytes());
    let expected = hex::encode(mac.finalize().into_bytes());
    if &expected != signature {
        return Err("bundle signature mismatch".to_string());
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use geoclt_schema::artifact::{ArtifactBundle, ArtifactEntry, ArtifactMetadata};

    use super::{compute_bundle_hash, finalize_artifact_entry, validate_artifact_bundle};
    use crate::registry::load_packaged_registry;

    #[test]
    fn finalizes_artifact_entry_with_deterministic_identity() {
        let entry = ArtifactEntry {
            metadata: ArtifactMetadata {
                artifact_id: String::new(),
                artifact_type: "event_record".to_string(),
                schema_version: 2,
                producer: "geoclt:transformers-adapter:0.2.0".to_string(),
                trace_id: "trace-1".to_string(),
                run_id: "run-1".to_string(),
                content_hash: String::new(),
                created_at: "2026-01-01T00:00:00Z".to_string(),
            },
            payload: serde_json::json!({"x": 1, "y": 2}),
        };
        let one = finalize_artifact_entry(entry.clone()).expect("entry");
        let two = finalize_artifact_entry(entry).expect("entry");
        assert_eq!(one.metadata.artifact_id, two.metadata.artifact_id);
        assert_eq!(one.metadata.content_hash, two.metadata.content_hash);
    }

    #[test]
    fn validates_immutable_bundle_hash() {
        let registry = load_packaged_registry().expect("registry");

        let artifact = finalize_artifact_entry(ArtifactEntry {
            metadata: ArtifactMetadata {
                artifact_id: String::new(),
                artifact_type: "event_record".to_string(),
                schema_version: 2,
                producer: "geoclt:transformers-adapter:0.2.0".to_string(),
                trace_id: "trace-1".to_string(),
                run_id: "run-1".to_string(),
                content_hash: String::new(),
                created_at: "2026-01-01T00:00:00Z".to_string(),
            },
            payload: serde_json::json!({"a": 1}),
        })
        .expect("artifact");

        let mut bundle = ArtifactBundle {
            bundle_id: "bundle-1".to_string(),
            schema_version: 1,
            producer: "geoclt:sidecar:0.2.0".to_string(),
            run_id: "run-1".to_string(),
            trace_id: "trace-1".to_string(),
            created_at: "2026-01-01T00:00:01Z".to_string(),
            transitional: false,
            immutable: true,
            artifacts: vec![artifact],
            bundle_hash: String::new(),
            bundle_signing_mode: None,
            bundle_signature: None,
        };
        bundle.bundle_hash = compute_bundle_hash(&bundle).expect("bundle hash");
        assert!(validate_artifact_bundle(&registry, &bundle).is_ok());
    }
}

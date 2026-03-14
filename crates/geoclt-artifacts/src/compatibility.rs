use geoclt_schema::artifact::ArtifactBundle;

use crate::registry::SchemaRegistry;

pub fn check_version_compatibility(
    registry: &SchemaRegistry,
    artifact_type: &str,
    schema_version: u32,
) -> Result<(), String> {
    let policy = registry
        .artifact_policy(artifact_type)
        .ok_or_else(|| format!("unknown artifact type in registry: {artifact_type}"))?;
    let current = policy.current_version;
    let min = policy.min_compatible_version;

    if schema_version > current {
        return Err(format!(
            "artifact {artifact_type} schema version {schema_version} is newer than current {current}"
        ));
    }
    if schema_version < min {
        return Err(format!(
            "artifact {artifact_type} schema version {schema_version} is older than minimum compatible {min}"
        ));
    }
    Ok(())
}

pub fn check_bundle_compatibility(
    registry: &SchemaRegistry,
    bundle: &ArtifactBundle,
) -> Result<(), String> {
    let mut versions = std::collections::BTreeSet::new();
    for artifact in &bundle.artifacts {
        check_version_compatibility(
            registry,
            &artifact.metadata.artifact_type,
            artifact.metadata.schema_version,
        )?;
        versions.insert(artifact.metadata.schema_version);
    }

    if versions.len() > 1 && !bundle.transitional {
        return Err("mixed schema versions are forbidden unless bundle.transitional=true".to_string());
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use geoclt_schema::artifact::{ArtifactBundle, ArtifactEntry, ArtifactMetadata};

    use super::check_bundle_compatibility;
    use crate::registry::load_registry_from_path;

    fn sample_bundle(version: u32, transitional: bool) -> ArtifactBundle {
        ArtifactBundle {
            bundle_id: "bundle-1".to_string(),
            schema_version: 1,
            producer: "geoclt:sidecar:0.2.0".to_string(),
            run_id: "run-1".to_string(),
            trace_id: "trace-1".to_string(),
            created_at: "2026-01-01T00:00:00Z".to_string(),
            transitional,
            immutable: true,
            artifacts: vec![ArtifactEntry {
                metadata: ArtifactMetadata {
                    artifact_id: "artifact-1".to_string(),
                    artifact_type: "event_record".to_string(),
                    schema_version: version,
                    producer: "geoclt:sidecar:0.2.0".to_string(),
                    trace_id: "trace-1".to_string(),
                    run_id: "run-1".to_string(),
                    content_hash: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                        .to_string(),
                    created_at: "2026-01-01T00:00:00Z".to_string(),
                },
                payload: serde_json::json!({"ok": true}),
            }],
            bundle_hash: "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb".to_string(),
        }
    }

    fn mixed_bundle(transitional: bool) -> ArtifactBundle {
        ArtifactBundle {
            bundle_id: "bundle-mixed".to_string(),
            schema_version: 1,
            producer: "geoclt:sidecar:0.2.0".to_string(),
            run_id: "run-1".to_string(),
            trace_id: "trace-1".to_string(),
            created_at: "2026-01-01T00:00:00Z".to_string(),
            transitional,
            immutable: true,
            artifacts: vec![
                ArtifactEntry {
                    metadata: ArtifactMetadata {
                        artifact_id: "artifact-1".to_string(),
                        artifact_type: "event_record".to_string(),
                        schema_version: 2,
                        producer: "geoclt:sidecar:0.2.0".to_string(),
                        trace_id: "trace-1".to_string(),
                        run_id: "run-1".to_string(),
                        content_hash:
                            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                                .to_string(),
                        created_at: "2026-01-01T00:00:00Z".to_string(),
                    },
                    payload: serde_json::json!({"ok": true}),
                },
                ArtifactEntry {
                    metadata: ArtifactMetadata {
                        artifact_id: "artifact-2".to_string(),
                        artifact_type: "event_record".to_string(),
                        schema_version: 1,
                        producer: "geoclt:sidecar:0.2.0".to_string(),
                        trace_id: "trace-1".to_string(),
                        run_id: "run-1".to_string(),
                        content_hash:
                            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
                                .to_string(),
                        created_at: "2026-01-01T00:00:00Z".to_string(),
                    },
                    payload: serde_json::json!({"ok": true}),
                },
            ],
            bundle_hash: "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc".to_string(),
        }
    }

    #[test]
    fn accepts_n_and_n_minus_1() {
        let path = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../schemas/registry.json");
        let registry = load_registry_from_path(&path).expect("registry");
        assert!(check_bundle_compatibility(&registry, &sample_bundle(2, false)).is_ok());
        assert!(check_bundle_compatibility(&registry, &sample_bundle(1, false)).is_ok());
    }

    #[test]
    fn rejects_n_minus_2() {
        let path = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../schemas/registry.json");
        let registry = load_registry_from_path(&path).expect("registry");
        let result = check_bundle_compatibility(&registry, &sample_bundle(0, false));
        assert!(result.is_err());
    }

    #[test]
    fn mixed_versions_rejected_unless_transitional() {
        let path = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../schemas/registry.json");
        let registry = load_registry_from_path(&path).expect("registry");
        assert!(check_bundle_compatibility(&registry, &mixed_bundle(false)).is_err());
        assert!(check_bundle_compatibility(&registry, &mixed_bundle(true)).is_ok());
    }
}

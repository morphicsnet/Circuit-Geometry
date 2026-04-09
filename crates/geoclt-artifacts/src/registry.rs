use serde::Deserialize;
use std::collections::BTreeMap;

const PACKAGED_REGISTRY_JSON: &str = include_str!("../registry/registry.json");

#[derive(Debug, Clone, Deserialize)]
pub struct ArtifactPolicy {
    pub current_version: u32,
    pub min_compatible_version: u32,
    #[serde(default)]
    pub array_policy: BTreeMap<String, String>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct SchemaRegistry {
    pub version: u32,
    pub compatibility_policy: String,
    pub artifacts: BTreeMap<String, ArtifactPolicy>,
}

impl SchemaRegistry {
    pub fn artifact_policy(&self, artifact_type: &str) -> Option<&ArtifactPolicy> {
        self.artifacts.get(artifact_type)
    }
}

pub fn load_registry_from_path(path: &std::path::Path) -> Result<SchemaRegistry, String> {
    let raw = std::fs::read_to_string(path)
        .map_err(|error| format!("failed to read registry {}: {error}", path.display()))?;
    serde_json::from_str(&raw)
        .map_err(|error| format!("failed to parse registry {}: {error}", path.display()))
}

pub fn load_packaged_registry() -> Result<SchemaRegistry, String> {
    serde_json::from_str(PACKAGED_REGISTRY_JSON)
        .map_err(|error| format!("failed to parse packaged registry: {error}"))
}

#[cfg(test)]
mod tests {
    use super::{load_packaged_registry, load_registry_from_path};

    #[test]
    fn loads_schema_registry() {
        let path = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("registry/registry.json");
        let registry = load_registry_from_path(&path).expect("registry");
        assert_eq!(registry.compatibility_policy, "strict_n_n_minus_1");
        assert!(registry.artifact_policy("event_record").is_some());
    }

    #[test]
    fn packaged_registry_matches_expected_policy() {
        let registry = load_packaged_registry().expect("packaged registry");
        assert_eq!(registry.compatibility_policy, "strict_n_n_minus_1");
        assert!(registry.artifact_policy("artifact_bundle").is_some());
    }
}

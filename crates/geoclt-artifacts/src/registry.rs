use serde::Deserialize;
use std::collections::BTreeMap;

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

#[cfg(test)]
mod tests {
    use super::load_registry_from_path;

    #[test]
    fn loads_schema_registry() {
        let path = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../schemas/registry.json");
        let registry = load_registry_from_path(&path).expect("registry");
        assert_eq!(registry.compatibility_policy, "strict_n_n_minus_1");
        assert!(registry.artifact_policy("event_record").is_some());
    }
}

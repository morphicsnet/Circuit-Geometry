use serde::{Deserialize, Serialize};
use serde_json::Value;

pub const EVENT_RECORD_SCHEMA_VERSION: u32 = 2;
pub const HYPERPATH_RECORD_SCHEMA_VERSION: u32 = 2;
pub const BENCHMARK_RESULT_SCHEMA_VERSION: u32 = 2;
pub const MECHANISM_CANDIDATE_SCHEMA_VERSION: u32 = 1;
pub const MECHANISM_CLASS_RECORD_SCHEMA_VERSION: u32 = 2;
pub const DECISION_RECEIPT_SCHEMA_VERSION: u32 = 2;
pub const ARTIFACT_BUNDLE_SCHEMA_VERSION: u32 = 1;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArtifactMetadata {
    pub artifact_id: String,
    pub artifact_type: String,
    pub schema_version: u32,
    pub producer: String,
    pub trace_id: String,
    pub run_id: String,
    pub content_hash: String,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArtifactEntry {
    #[serde(flatten)]
    pub metadata: ArtifactMetadata,
    pub payload: Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArtifactBundle {
    pub bundle_id: String,
    pub schema_version: u32,
    pub producer: String,
    pub run_id: String,
    pub trace_id: String,
    pub created_at: String,
    #[serde(default)]
    pub transitional: bool,
    pub immutable: bool,
    pub artifacts: Vec<ArtifactEntry>,
    pub bundle_hash: String,
}

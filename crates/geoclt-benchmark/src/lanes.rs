use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct LaneDefinition {
    pub lane_id: String,
    pub required_artifacts: Vec<String>,
    pub evaluation_steps: Vec<String>,
    pub thresholds: BTreeMap<String, f64>,
    pub falsifiers: Vec<String>,
    pub policy_actions: Vec<String>,
}

pub fn default_lanes_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("lanes")
}

pub fn load_lane_definitions(dir: &Path) -> Result<Vec<LaneDefinition>, String> {
    let mut lanes = Vec::new();
    for entry in fs::read_dir(dir).map_err(|error| format!("failed to read lanes dir: {error}"))? {
        let entry = entry.map_err(|error| format!("failed to read lane entry: {error}"))?;
        let path = entry.path();
        if !path.is_dir() {
            continue;
        }
        for file in fs::read_dir(&path).map_err(|error| format!("failed to read lane version dir: {error}"))? {
            let file = file.map_err(|error| format!("failed to read lane file: {error}"))?;
            let file_path = file.path();
            if file_path.extension().and_then(|value| value.to_str()) != Some("json") {
                continue;
            }
            let raw = fs::read_to_string(&file_path)
                .map_err(|error| format!("failed to read lane {}: {error}", file_path.display()))?;
            let lane: LaneDefinition = serde_json::from_str(&raw)
                .map_err(|error| format!("failed to parse lane {}: {error}", file_path.display()))?;
            validate_lane_definition(&lane)?;
            lanes.push(lane);
        }
    }
    lanes.sort_by(|a, b| a.lane_id.cmp(&b.lane_id));
    Ok(lanes)
}

pub fn validate_lane_definition(lane: &LaneDefinition) -> Result<(), String> {
    if lane.lane_id.trim().is_empty() {
        return Err("lane_id must not be empty".to_string());
    }
    if lane.required_artifacts.is_empty() {
        return Err(format!("{} missing required_artifacts", lane.lane_id));
    }
    if lane.evaluation_steps.is_empty() {
        return Err(format!("{} missing evaluation_steps", lane.lane_id));
    }
    if lane.falsifiers.is_empty() {
        return Err(format!("{} missing falsifiers", lane.lane_id));
    }
    if lane.policy_actions.is_empty() {
        return Err(format!("{} missing policy_actions", lane.lane_id));
    }
    for (name, value) in &lane.thresholds {
        if !value.is_finite() || *value < 0.0 {
            return Err(format!("{} has invalid threshold {name}", lane.lane_id));
        }
    }
    Ok(())
}

pub fn lane_registry_loaded(dir: &Path) -> bool {
    load_lane_definitions(dir).map(|lanes| !lanes.is_empty()).unwrap_or(false)
}

#[cfg(test)]
mod tests {
    use super::{default_lanes_dir, lane_registry_loaded, load_lane_definitions};

    #[test]
    fn loads_default_registry() {
        let lanes = load_lane_definitions(&default_lanes_dir()).expect("lanes");
        assert!(lanes.len() >= 4);
        assert!(lanes.iter().any(|lane| lane.lane_id == "claims-triage.v1"));
    }

    #[test]
    fn registry_loaded_helper_returns_true() {
        assert!(lane_registry_loaded(&default_lanes_dir()));
    }
}

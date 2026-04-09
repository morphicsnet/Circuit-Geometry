//! Deterministic stable identifiers for Geo-CLT records, mechanisms, and artifacts.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub struct StableId(pub String);

impl StableId {
    pub fn from_parts(parts: &[&str]) -> Self {
        let mut hasher = Sha256::new();
        for p in parts {
            hasher.update(p.as_bytes());
            hasher.update([0u8]);
        }
        let bytes = hasher.finalize();
        Self(format!("{:x}", bytes))
    }
}

#[cfg(test)]
mod tests {
    use super::StableId;

    #[test]
    fn stable_id_is_deterministic() {
        let one = StableId::from_parts(&["geoclt", "atlas", "v1"]);
        let two = StableId::from_parts(&["geoclt", "atlas", "v1"]);
        assert_eq!(one, two);
    }

    #[test]
    fn stable_id_matches_golden_hash() {
        let stable = StableId::from_parts(&["geoclt", "atlas", "v1"]);
        assert_eq!(
            stable.0,
            "fc7e8ee6c77e8b8c8eab92f7165a01c58d3214efcf4760351b4420f84905f994"
        );
    }
}

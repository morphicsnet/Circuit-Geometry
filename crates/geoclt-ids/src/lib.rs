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

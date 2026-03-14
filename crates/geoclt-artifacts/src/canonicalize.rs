use sha2::{Digest, Sha256};

pub fn canonical_json_bytes(value: &serde_json::Value) -> Result<Vec<u8>, String> {
    serde_jcs::to_vec(value).map_err(|error| format!("canonicalization failed: {error}"))
}

pub fn content_hash(value: &serde_json::Value) -> Result<String, String> {
    let bytes = canonical_json_bytes(value)?;
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    Ok(format!("{:x}", hasher.finalize()))
}

pub fn artifact_id(artifact_type: &str, schema_version: u32, content_hash: &str) -> String {
    let seed = format!("{artifact_type}:{schema_version}:{content_hash}");
    let mut hasher = Sha256::new();
    hasher.update(seed.as_bytes());
    format!("artifact-{:x}", hasher.finalize())
}

#[cfg(test)]
mod tests {
    use super::{artifact_id, canonical_json_bytes, content_hash};

    #[test]
    fn canonicalization_is_stable() {
        let one = serde_json::json!({"z": 1.0, "a": [3, 2, 1]});
        let two = serde_json::json!({"a": [3, 2, 1], "z": 1});
        let hash_one = content_hash(&one).expect("hash one");
        let hash_two = content_hash(&two).expect("hash two");
        assert_eq!(hash_one, hash_two);
        assert_eq!(
            canonical_json_bytes(&one).expect("bytes one"),
            canonical_json_bytes(&two).expect("bytes two")
        );
    }

    #[test]
    fn artifact_id_is_deterministic() {
        let id_one = artifact_id("event_record", 2, "abcd");
        let id_two = artifact_id("event_record", 2, "abcd");
        assert_eq!(id_one, id_two);
    }
}

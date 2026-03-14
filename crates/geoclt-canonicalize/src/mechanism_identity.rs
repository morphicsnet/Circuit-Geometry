use sha2::{Digest, Sha256};

#[derive(Debug, Clone)]
pub struct MechanismIdentityInput {
    pub mechanism_class_type: String,
    pub canonical_hyperpath_signature: serde_json::Value,
    pub normalized_causal_dependency_set: Vec<String>,
    pub invariant_feature_signature: Vec<String>,
}

pub fn derive_mechanism_id(input: &MechanismIdentityInput) -> Result<String, String> {
    let mut dependencies = input.normalized_causal_dependency_set.clone();
    dependencies.sort();
    let mut invariant = input.invariant_feature_signature.clone();
    invariant.sort();

    let seed = serde_json::json!({
        "mechanism_class_type": input.mechanism_class_type,
        "canonical_hyperpath_signature": input.canonical_hyperpath_signature,
        "normalized_causal_dependency_set": dependencies,
        "invariant_feature_signature": invariant,
    });

    let bytes = serde_jcs::to_vec(&seed).map_err(|error| format!("canonicalization failed: {error}"))?;
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    Ok(format!("mechanism-{:x}", hasher.finalize()))
}

#[cfg(test)]
mod tests {
    use super::{derive_mechanism_id, MechanismIdentityInput};

    #[test]
    fn mechanism_identity_ignores_dependency_order() {
        let input_one = MechanismIdentityInput {
            mechanism_class_type: "causal_hyperpath".to_string(),
            canonical_hyperpath_signature: serde_json::json!({"path":"a"}),
            normalized_causal_dependency_set: vec!["feat-b".to_string(), "feat-a".to_string()],
            invariant_feature_signature: vec!["inv-2".to_string(), "inv-1".to_string()],
        };
        let input_two = MechanismIdentityInput {
            mechanism_class_type: "causal_hyperpath".to_string(),
            canonical_hyperpath_signature: serde_json::json!({"path":"a"}),
            normalized_causal_dependency_set: vec!["feat-a".to_string(), "feat-b".to_string()],
            invariant_feature_signature: vec!["inv-1".to_string(), "inv-2".to_string()],
        };

        let id_one = derive_mechanism_id(&input_one).expect("id one");
        let id_two = derive_mechanism_id(&input_two).expect("id two");
        assert_eq!(id_one, id_two);
    }
}
